"""Focused adapter and static bundle checks; run with python -B web/verify.py."""
import json
import sys
import unittest
import zipfile
from pathlib import Path

WEB = Path(__file__).resolve().parent
sys.path.insert(0, str(WEB.parent))
import bridge
from app.game_service import GameService

class WebChecks(unittest.TestCase):
    def setUp(self):
        bridge.service = GameService()

    def send(self, text):
        return json.loads(bridge.dispatch(text))

    def test_five_characters_and_confirmations(self):
        for index in range(5):
            bridge.service = GameService()
            result = self.send(f"/card new {index}")
            self.assertIsNotNone(result["run"])
            self.assertTrue(result["run"]["choices"])
            old_name = result["run"]["name"]
            self.assertTrue(self.send(f"/card new {(index + 1) % 5}")["confirmation"])
            result = self.send("/card no")
            self.assertFalse(result["confirmation"])
            self.assertEqual(result["run"]["name"], old_name)

    def test_combat_and_turn(self):
        self.send("/card new 0")
        battle = self.send("/card testroom battle")
        self.assertTrue(battle["run"]["battle"])
        self.assertTrue(battle["run"]["hand"])
        self.assertTrue(battle["run"]["enemies"])
        # A deterministic normal attack verifies command dispatch and state refresh.
        self.send("/ctrl addcard 打击 手牌")
        card_index = len(self.send("/card view")["run"]["hand"]) - 1
        result = self.send(f"/card play {card_index} 0")
        self.assertIn("打击", result["reply"])
        self.assertEqual(result["run"]["energy"], 2)
        result = self.send("/card end")
        self.assertEqual(result["run"]["turn"], 2)

    def test_multiplayer_is_rejected(self):
        for command in ("/card multi create", ".card pvp create", "。card 多人", "/CARD PVP"):
            result = self.send(command)
            self.assertIn("仅支持单人", result["reply"])
            self.assertIsNone(result["run"])

    def test_relic_data_supports_old_and_new_clients(self):
        result = self.send("/card new 0")["run"]
        self.assertTrue(all(isinstance(name, str) for name in result["relics"]))
        details = result["relicDetails"][0]
        original = bridge.service.get_run(bridge.SESSION).relics[0]
        self.assertEqual(details["name"], original.name)
        self.assertEqual(details["info"], original.description)
        self.assertEqual(details["story"], original.story)

    def new_run(self):
        self.send("/card new 0")
        run = bridge.service.get_run(bridge.SESSION)
        run.clear_pending_nodes()
        return run

    def test_reward_buttons_pick_and_replace(self):
        from data.card.AAAregistry import create_card
        from data.potion.AAAregistry import create_potion
        from game.reward import RewardState, RewardOption
        run = self.new_run()
        run.pending_reward = RewardState(options=[
            RewardOption("gold", "金币", {"amount": 25}),
            RewardOption("card", "选择卡牌", {"cards": [create_card("card.strike")]}),
        ])
        choices = bridge.snapshot()["run"]["choices"]
        gold = run.gold
        self.send(choices[0]["command"])
        self.assertEqual(run.gold, gold + 25)
        self.send(choices[1]["command"])
        pick = bridge.snapshot()["run"]["choices"][0]
        deck_count = len(run.master_deck)
        self.send(pick["command"])
        self.assertEqual(len(run.master_deck), deck_count + 1)
        run.potions = [create_potion("potion.blood") for _ in range(run.max_potion_slots)]
        run.pending_reward = RewardState(options=[RewardOption("potion", "药水", {"potion": create_potion("potion.test_fire")})])
        replacement = bridge.snapshot()["run"]["choices"][0]["options"][1]
        self.send(replacement["command"])
        self.assertEqual(run.potions[1].potion_id, "potion.test_fire")

    def test_shop_price_sold_and_filtered_smith_indices(self):
        from data.card.AAAregistry import create_card
        from data.card.upgrade_rules import upgrade_card
        from game.node.node_shop import ShopState, ShopItem
        from game.node.node_rest import create_rest_state
        run = self.new_run()
        run.pending_shop = ShopState(items=[ShopItem("card", "打击", 20, {"card": create_card("card.strike")}),
                                           ShopItem("card", "昂贵商品", 999, {"card": create_card("card.strike")})])
        choices = bridge.snapshot()["run"]["choices"]
        self.assertFalse(choices[0]["disabled"])
        self.assertTrue(choices[1]["disabled"])
        gold = run.gold
        self.send(choices[0]["command"])
        self.assertEqual(run.gold, gold - 20)
        self.assertEqual(bridge.snapshot()["run"]["choices"][0]["reason"], "已售罄")
        run.clear_pending_nodes()
        run.pending_rest = create_rest_state()
        run.master_deck = [upgrade_card(create_card("card.strike")), create_card("card.defend")]
        smith = bridge.snapshot()["run"]["choices"][1]["options"]
        self.assertEqual(len(smith), 1)
        self.assertEqual(smith[0]["command"], "/card smith 0")
        self.send(smith[0]["command"])
        self.assertTrue(run.master_deck[1].upgraded)

    def test_battle_selection_uses_option_indices(self):
        from game.pending_choice import PendingChoice
        self.send("/card new 0")
        self.send("/card testroom battle")
        battle = bridge.service.get_run(bridge.SESSION).current_battle
        card = battle.player.hand[-1]
        battle.pending_choice = PendingChoice(kind="hand_to_draw_top", options=[card])
        choice = bridge.snapshot()["run"]["selection"]["options"][0]
        self.assertEqual(choice["command"], "/card handtop 0")
        self.send(choice["command"])
        self.assertIs(battle.player.draw_pile[-1], card)
        self.assertIsNone(bridge.snapshot()["run"]["selection"])

    def test_multiselect_scry_and_relic_precedence(self):
        from game.scry import request_scry
        self.send("/card new 0")
        self.send("/card testroom battle")
        run = bridge.service.get_run(bridge.SESSION)
        battle = run.current_battle
        request_scry(battle, 2)
        choice = bridge.snapshot()["run"]["selection"]
        self.assertTrue(choice["multiple"])
        self.assertEqual(choice["emptyValue"], "skip")
        self.send(choice["command"] + " skip")
        self.assertIsNone(battle.pending_choice)
        run.current_battle = None
        run.pending_empty_cage_selections = [{"count": 2}]
        state = bridge.snapshot()["run"]
        self.assertEqual(state["choices"], [])
        self.assertEqual(state["routes"], [])
        deck_count = len(run.master_deck)
        self.send(state["selection"]["command"] + " 0,1")
        self.assertEqual(len(run.master_deck), deck_count - 2)

    def test_treasure_and_rest_buttons(self):
        from game.node.node_treasure import create_treasure_state
        from game.node.node_rest import create_rest_state
        from data.relic.AAAregistry import create_relic
        run = self.new_run()
        run.pending_treasure = create_treasure_state(run, seed=42)
        self.send(bridge.snapshot()["run"]["choices"][0]["command"])
        self.assertTrue(run.pending_treasure.opened)
        self.assertTrue(any(c["command"].startswith("/card take") for c in bridge.snapshot()["run"]["choices"]))
        run.clear_pending_nodes()
        run.pending_rest = create_rest_state()
        run.relics.append(create_relic("relic.fusion_hammer"))
        self.assertTrue(bridge.snapshot()["run"]["choices"][1]["disabled"])

    def test_combat_status_tracks_stance_orbs_zone_and_clear(self):
        from game.stances import change_stance
        from game.orbs import channel, rack, set_slots
        from data.zones.element_zones import ElementZone
        self.send("/card new 0")
        self.send("/card testroom battle")
        run = bridge.service.get_run(bridge.SESSION)
        battle = run.current_battle
        self.assertEqual(rack(battle.player).capacity, 0)
        self.assertEqual(bridge.snapshot()["run"]["combatStatus"]["orbCapacity"], 0)
        self.assertEqual(rack(battle.player).capacity, 0)  # Rendering cannot grant slots.
        channel(battle, battle.player, "dark")
        set_slots(battle.player, 3)
        battle.player.statuses.set("focus", 2)
        battle.active_zone = ElementZone("shade", True, 3)
        change_stance(battle, "divinity")
        status = bridge.snapshot()["run"]["combatStatus"]
        self.assertEqual(status["stance"], "divinity")
        self.assertEqual(status["orbCapacity"], 3)
        self.assertEqual(len(status["orbs"]), 1)
        self.assertEqual(status["orbs"][0]["passive"], 16)
        self.assertEqual(status["orbs"][0]["value"], 6)
        self.assertEqual(status["zone"]["duration"], 3)
        self.assertTrue(status["zone"]["extreme"])
        battle.active_zone = None
        change_stance(battle, "none")
        self.assertIsNone(bridge.snapshot()["run"]["combatStatus"]["zone"])
        self.assertEqual(bridge.snapshot()["run"]["combatStatus"]["stance"], "none")
        run.current_battle = None
        self.assertIsNone(bridge.snapshot()["run"]["combatStatus"])

    def prepare_followup_card(self, card_id):
        from data.card.AAAregistry import create_card
        self.send("/card new 0")
        self.send("/card testroom battle")
        battle = bridge.service.get_run(bridge.SESSION).current_battle
        battle.active_zone = None
        battle.player.relics = []
        battle.player.statuses.values.clear()
        battle.player.cost = 10
        battle.player.hand = [create_card(card_id), create_card("card.defend"), create_card("card.strike")]
        battle.player.draw_pile = [create_card("card.strike"), create_card("card.strike")]
        battle.player.discard_pile = [create_card("card.strike")]
        return battle

    def test_plating_buttons_use_filtered_option_indices(self):
        battle = self.prepare_followup_card("card.crystal_plating")
        battle.player.hand[1].attack_element = "fire"
        target = battle.player.hand[2]
        state = self.send("/card play 0")["run"]
        choices = state["selection"]["options"]
        self.assertEqual(len(choices), 1)
        self.assertEqual(choices[0]["command"], "/card plate 0")
        self.send(choices[0]["command"])
        self.assertEqual(target.attack_element, "crystal")
        self.assertIn("·晶", target.name)
        self.assertEqual(battle.player.hand[0].attack_element, "fire")
        self.assertIsNone(bridge.snapshot()["run"]["selection"])

    def test_sync_buttons_distinguish_identical_cards_in_different_piles(self):
        from game.constants import KEYWORD_RESONANCE
        battle = self.prepare_followup_card("card.synchronization")
        state = self.send("/card play 0")["run"]
        choice = next(c for c in state["selection"]["options"] if c["name"].startswith("弃牌堆"))
        self.send(choice["command"])
        self.assertIn(KEYWORD_RESONANCE, battle.player.discard_pile[0].keywords)
        self.assertNotIn(KEYWORD_RESONANCE, battle.player.draw_pile[0].keywords)
        self.assertIsNone(battle.pending_choice)

    def test_abyss_index_button_applies_to_selected_draw_card(self):
        from data.card.enchantment_rules import get_card_enchantment_stacks
        battle = self.prepare_followup_card("card.abyss_index")
        state = self.send("/card play 0")["run"]
        self.send(state["selection"]["options"][1]["command"])
        self.assertEqual(get_card_enchantment_stacks(battle.player.draw_pile[1], "index_shade"), 1)
        self.assertEqual(get_card_enchantment_stacks(battle.player.draw_pile[0], "index_shade"), 0)

    def test_reflection_multiselect_from_different_piles(self):
        battle = self.prepare_followup_card("card.radiant_crystal_reflection")
        battle.player.hand[0].replay_extra = 1
        state = self.send("/card play 0")["run"]
        selection = state["selection"]
        self.assertEqual(selection["minimum"], 1)
        self.assertEqual(selection["maximum"], 2)
        choices = [next(c for c in selection["options"] if c["name"].startswith(pile))
                   for pile in ("手牌", "弃牌堆")]
        indices = ",".join(c["command"].split()[-1] for c in choices)
        self.send(selection["command"] + " " + indices)
        self.assertEqual(battle.player.hand[0].replay_extra, 1)
        self.assertEqual(battle.player.discard_pile[0].replay_extra, 1)
        self.assertEqual(getattr(battle.player.draw_pile[0], "replay_extra", 0), 0)
        self.assertIsNone(battle.pending_choice)

    def test_fossil_multiselect_and_empty_selection(self):
        from data.card.AAAregistry import create_card
        battle = self.prepare_followup_card("card.fossil")
        state = self.send("/card play 0")["run"]
        selection = state["selection"]
        self.assertEqual(selection["minimum"], 0)
        self.assertEqual(selection["maximum"], 2)
        targets = list(battle.player.hand)
        self.send(selection["command"] + " 0,1")
        self.assertEqual(battle.player.statuses.get("rock_layer"), 2)
        self.assertTrue(all(any(c is target for c in battle.player.exhaust_pile) for target in targets))
        battle.player.hand = [create_card("card.fossil"), create_card("card.strike")]
        selection = self.send("/card play 0")["run"]["selection"]
        self.send(selection["command"] + " " + selection["emptyValue"])
        self.assertEqual(battle.player.statuses.get("rock_layer"), 2)
        self.assertEqual(len(battle.player.hand), 1)
        self.assertIsNone(battle.pending_choice)

    def test_versioned_resource_chain(self):
        dist = WEB / "dist"
        manifest = json.loads((dist / "build.json").read_text(encoding="utf-8"))
        version = manifest["version"]
        chain = {
            "index.html": [f"bootstrap.{version}.js", f"style.{version}.css"],
            f"bootstrap.{version}.js": [f"app.{version}.js"],
            f"app.{version}.js": [f"worker.{version}.js"],
            f"worker.{version}.js": [f"build.{version}.json"],
        }
        with zipfile.ZipFile(WEB / "cloudflare-upload.zip") as archive:
            for name, references in chain.items():
                text = archive.read(name).decode("utf-8")
                for reference in references:
                    self.assertIn(reference, text)
                    self.assertIn(reference, archive.namelist())
            self.assertIn(f"engine.{manifest['engine']}.zip", archive.namelist())

    def test_bundle_has_required_files_only(self):
        with zipfile.ZipFile(WEB / "cloudflare-upload.zip") as archive:
            for name in ("index.html", "app.js", "bootstrap.js", "style.css", "worker.js", "engine.zip", "build.json"):
                self.assertIn(name, archive.namelist())
        with zipfile.ZipFile(WEB / "dist" / "engine.zip") as archive:
            self.assertIn("web_bridge.py", archive.namelist())
            self.assertNotIn("main.py", archive.namelist())
            self.assertTrue(all(name.endswith(".py") for name in archive.namelist()))
            self.assertFalse(any("bot_config" in name or ".git" in name for name in archive.namelist()))

if __name__ == "__main__":
    unittest.main()
