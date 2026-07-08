# -*- coding: utf-8 -*-

import random


from data.relic.base_relic import RelicTemplate


class _EnergyBossRelic(RelicTemplate):
    """每回合开始 +1 能量的 Boss 遗物基类。"""

    energy_only_in_boss_or_elite = False

    def _should_gain_energy(self, context):
        if not self.energy_only_in_boss_or_elite:
            return True
        run_state = getattr(context.game_state, "run_state", None)
        node_type = getattr(run_state, "current_battle_node_type", "") if run_state is not None else ""
        return node_type in ("boss", "elite", "event_elite")

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name != EVENT_TURN_START:
            return []
        if not self._should_gain_energy(context):
            return []
        context.player.cost += 1
        return ["【{}】触发：回合开始获得 1 点能量。当前费用：{}/{}。".format(
            self.name, context.player.cost, context.player.max_cost
        )]


class AstrolabeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.astrolabe", name="星盘",
            description="拾起时，选择 3 张牌进行变化，然后将这些牌升级。",
            story="可以从星星中探知宝贵知识的工具。", quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        queue = getattr(run_state, "pending_astrolabe_selections", None)
        if queue is None:
            queue = []
            setattr(run_state, "pending_astrolabe_selections", queue)
        queue.append({"count": 3, "source": self.name})
        return ["【{}】等待选择 3 张牌变化并升级。".format(self.name), "使用 /card astrolabe 0,1,2 选择。"]



class XanthosisRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.xanthosis", name="黄化",
            description="拾起时将你的初始遗物变化为先古版本。",
            story="内在之光的觉醒。炼金术的第三阶段……", quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        from data.relic.AAAregistry import create_relic
        from game.relic_logic.run_relic_utils import find_upgradeable_starting_relic

        found = find_upgradeable_starting_relic(run_state)
        if not found:
            return ["【{}】触发，但当前没有可变化的初始遗物。".format(self.name)]

        index, old_relic, target_id = found
        new_relic = create_relic(target_id)

        run_state.relics[index] = new_relic

        logs = [
            "【{}】触发：【{}】变化为【{}】。".format(
                self.name,
                old_relic.name,
                new_relic.name
            )
        ]

        # 黄化本身按原作“拾起时生效”遗物处理：触发后仍保留在遗物栏。

        if hasattr(new_relic, "on_obtained"):
            logs.extend(new_relic.on_obtained(run_state))

        return logs


class BlackStarRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.black_star", name="黑星",
            description="精英敌人在被打败时多掉落一件遗物。",
            story="最初在蛇镇上发现的遗物，当时被放在一根蜡烛旁边。", quantity="boss", owner_character_id="", allow_duplicate=False)


class WhiteStarRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.white_star", name="白星",
            description="精英敌人额外掉落一次稀有卡牌奖励。",
            story="", quantity="boss", owner_character_id="", allow_duplicate=False)


class CallingBellRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.calling_bell", name="召唤铃铛",
            description="获得一个独特的诅咒和 3 件遗物。",
            story="这个黑铁铃铛在你找到它时作响了3次，但现在它已经不再响了。", quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        from data.card.AAAregistry import create_card
        from data.relic.AAAregistry import create_relic
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics
        from game.reward import get_available_relic_ids
        logs = []
        curse = create_card("card.curse.bell")
        logs.extend(add_card_to_master_deck_with_relics(run_state, curse, source="召唤铃铛"))
        banned = {"relic.bottled_flame", "relic.bottled_lightning", "relic.bottled_tornado", "relic.whetstone"}
        available = [rid for rid in get_available_relic_ids(run_state) if rid not in banned]
        by_rarity = {"common": [], "uncommon": [], "rare": []}
        for relic_id in available:
            try:
                relic = create_relic(relic_id)
            except Exception:
                continue
            rarity = getattr(relic, "quantity", "")
            if rarity in by_rarity:
                by_rarity[rarity].append(relic_id)
        rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 14531 + len(getattr(run_state, "relics", []) or []))
        for rarity, cn in (("common", "普通"), ("uncommon", "罕见"), ("rare", "稀有")):
            pool = by_rarity.get(rarity, [])
            if not pool:
                logs.append("【{}】没有可获得的{}遗物。".format(self.name, cn))
                continue
            relic = create_relic(rng.choice(pool))
            run_state.relics.append(relic)
            logs.append("【{}】获得{}遗物：【{}】。".format(self.name, cn, relic.name))
            if hasattr(relic, "on_obtained"):
                logs.extend(relic.on_obtained(run_state))
        return logs


class CursedKeyRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.cursed_key", name="诅咒钥匙",
            description="你每次打开一个非 Boss 宝箱，都会获得一张诅咒。在每回合开始时获得 1 点能量。",
            story="你能感到这把钥匙上散发出邪恶的能量。力量总是需要付出代价的。", quantity="boss", owner_character_id="", allow_duplicate=False)


class MarkOfPainRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.mark_of_pain", name="痛楚印记",
            description="每回合开始获得 1 点能量。战斗开始时，将 2 张伤口放入你的抽牌堆。",
            story="北方部落中使用这个工具来给那些在战斗中掌握痛楚的战士们打上烙印。", quantity="boss", owner_character_id="character.armored_warrior", allow_duplicate=False)

    def on_event(self, event_name, context):
        logs = super().on_event(event_name, context)
        from game.constants import EVENT_BATTLE_START
        if event_name == EVENT_BATTLE_START:
            from data.card.AAAregistry import create_card
            for _ in range(2):
                card = create_card("card.status.wound")
                context.player.draw_pile.append(card)
            random.shuffle(context.player.draw_pile)
            logs.append("【{}】触发：将 2 张【伤口】放入抽牌堆并重洗。".format(self.name))
        return logs


class PandorasBoxRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.pandoras_box", name="潘多拉魔盒",
            description="拾起时，变化所有“打击”和“防御”牌。",
            story="你觉得打开这个盒子会很不吉利。", quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        from game.deck_utils import transform_card_in_master_deck
        rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 19390)
        indices = [i for i, card in enumerate(getattr(run_state, "master_deck", []) or []) if getattr(card, "name", "") in ("打击", "防御") or getattr(card, "card_id", "") in ("card.strike", "card.defend")]
        logs = ["【{}】触发：变化所有打击和防御牌。".format(self.name)]
        for idx in reversed(indices):
            old, new, sub = transform_card_in_master_deck(run_state, idx, rng=rng)
            logs.extend(sub)
        if not indices:
            logs.append("没有找到可变化的打击/防御。")
        return logs


class PhilosophersStoneRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.philosophers_stone", name="贤者之石",
            description="在每回合开始时获得 1 点能量。所有敌人初始获得 1 点力量。",
            story="这块石头中散发出纯粹的能量，所有周围的人与物都会因此而变强。\n“一篇炼金术顶刊！可惜并不是我做出来的。”——炼金师", 
            quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        logs = super().on_event(event_name, context)
        from game.constants import EVENT_BATTLE_START
        if event_name == EVENT_BATTLE_START:
            for enemy in getattr(context.game_state, "enemies", []) or []:
                if enemy.is_alive():
                    current = enemy.gain_status("strength", 1)
                    logs.append("【{}】触发：{} 获得 1 点力量。当前力量：{}。".format(self.name, enemy.name, current))
        return logs


class RunicCubeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.runic_cube", name="符文立方体",
            description="每当你失去生命时，抽 1 张牌。",
            story="上面的符文无法辨识。\n“噢噢是美妙的古代文明遗物……”——炼金师", quantity="boss", owner_character_id="character.armored_warrior", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_DAMAGE_AFTER
        if event_name != EVENT_DAMAGE_AFTER:
            return []
        if context.target is context.player and int(context.extra.get("real_damage", 0)) > 0:
            logs = ["【{}】触发：失去生命，抽 1 张牌。".format(self.name)]
            logs.extend(context.player.draw_cards(1, game_state=context.game_state, draw_source="runic_cube"))
            return logs
        return []


class RunicDomeRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.runic_dome", name="符文圆顶",
            description="你无法再看见敌人的意图。在每回合开始时获得 1 点能量。",
            story="上面的符文无法辨识。\n“为什么找不到任何解读的参考文献呢？”——炼金师", quantity="boss", owner_character_id="", allow_duplicate=False)


class RunicPyramidRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.runic_pyramid", name="符文金字塔",
            description="你在回合结束时不再自动丢弃所有手牌。",
            story="上面的符文无法辨识。\n“古人工作不留痕，学术不端的弊端来了。当然也可能是我还没找到文献……”——炼金师", quantity="boss", owner_character_id="", allow_duplicate=False)


class SneckoEyeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.snecko_eye", name="异蛇之眼",
            description="每回合多抽 2 张牌。每场战斗开始时获得混乱。",
            story="一条死去异蛇的眼珠，比你想象中的要大上不少。", quantity="boss", owner_character_id="", allow_duplicate=False)

    def get_turn_draw_bonus(self, game_state=None, player=None):
        return 2

    def get_opening_draw_bonus(self, game_state=None, player=None):
        return 2

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START

        if event_name == EVENT_BATTLE_START:
            current = context.player.gain_status("confusion", 1)
            return ["【{}】触发：获得混乱。当前混乱：{}。".format(
                self.name,
                current
            )]

        return []


class SozuRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.sozu", name="添水",
            description="你无法再获得药水。在每回合开始时获得 1 点能量。",
            story="你注意到所有带魔力的液体在接近这件遗物时都会失去效力。", quantity="boss", owner_character_id="", allow_duplicate=False)


class EctoplasmRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.ectoplasm", name="灵体外质",
            description="你不能再获得任何金币。在每回合开始时获得 1 点能量。",
            story="这团黏液与能量的混合物微微脉动，仿佛有着生命。", quantity="boss", owner_character_id="", allow_duplicate=False)
        self.max_reward_floor = 16


class TinyHouseRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.tiny_house", name="小屋子",
            description="拾起时，获得 1 瓶药水、50 金币、5 最大生命、1 张牌，并随机升级 1 张牌。",
            story="“一项近乎完美的微缩化工程。这是我至今最优秀的作品，但仍然远远不够。”——建筑师", quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        from data.potion.AAAregistry import create_potion
        from game.relic_logic.run_relic_utils import gain_gold_with_relics, increase_max_hp, add_card_to_master_deck_with_relics, try_gain_potion_with_relics
        from game.reward import roll_card_rewards, get_card_reward_upgrade_chance, roll_potion_id_by_rarity
        from data.card.upgrade_rules import has_upgrade, upgrade_card

        rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 22881)
        logs = ["【{}】触发。".format(self.name)]

        potion_id = roll_potion_id_by_rarity(
            rng=rng,
            run_state=run_state,
            include_event=False
        )

        if potion_id:
            potion = create_potion(potion_id)
            logs.extend(try_gain_potion_with_relics(run_state, potion, source=self.name))
        else:
            logs.append("没有可获得的药水。")


class VelvetChokerRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.velvet_choker", name="天鹅绒颈圈",
            description="你每回合不能打出超过 6 张牌。在每回合开始时获得 1 点能量。",
            story="“力量巨大，但过于局限。”——忽必烈大帝", quantity="boss", owner_character_id="", allow_duplicate=False)

    def can_play_card(self, game_state, card, play_reason):
        counts = getattr(game_state, "player_card_type_played_counts_this_turn", {}) or {}
        total = sum(int(v) for v in counts.values())
        if total >= 6:
            return False, "【{}】限制：本回合已经打出 6 张牌，不能继续打出。".format(self.name)
        return None


class BustedCrownRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.busted_crown", name="破碎金冠",
            description="在卡牌奖励画面，可供选择的牌数减少 2 张。在每回合开始时获得 1 点能量。",
            story="第一勇士的金冠……或者只是一个拙劣的仿制品？", quantity="boss", owner_character_id="", allow_duplicate=False)


class EmptyCageRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.empty_cage", name="空鸟笼",
            description="拾起时，选择移除牌组中的 2 张牌。",
            story="“将崇拜之物关进笼子，这是多么奇异的行为啊。”——兰伟德", quantity="boss", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        queue = getattr(run_state, "pending_empty_cage_selections", None)
        if queue is None:
            queue = []
            setattr(run_state, "pending_empty_cage_selections", queue)
        queue.append({"count": 2, "source": self.name})
        return ["【{}】等待选择 2 张牌移除。".format(self.name), "使用 /card cage 0,1 选择。"]


class FusionHammerRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.fusion_hammer", name="融合之锤",
            description="你无法再在休息处锻造升级卡牌。每回合开始时获得 1 点能量。",
            story="一旦握住，就永远无法放下。", quantity="boss", owner_character_id="", allow_duplicate=False)


class CoffeeDripperRelic(_EnergyBossRelic):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.coffee_dripper", name="咖啡滤杯",
            description="你无法再在休息处休息。在每回合开始时获得 1 点能量。",
            story="“好的，请再来一杯。继续工作，继续工作！”——建筑师\n“速溶咖啡适合工作节奏，但是新鲜咖啡会更好喝。”——炼金师", quantity="boss", owner_character_id="", allow_duplicate=False)


class HoveringKiteRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.hovering_kite", name="悬浮风筝",
            description="你在每回合第一次弃牌时，获得 1 点能量。",
            story="风筝在战斗中飘浮在你的身旁，不知是何种神秘的力量让它能浮在空中。", quantity="boss", owner_character_id="", allow_duplicate=False)
        self.used_this_turn = False

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name == EVENT_TURN_START:
            self.used_this_turn = False
        return []

    def on_card_discard(self, game_state, player, card, reason="丢弃"):
        if self.used_this_turn:
            return []
        self.used_this_turn = True
        player.cost += 1
        return ["【{}】触发：本回合第一次弃牌，获得 1 点能量。当前费用：{}/{}。".format(self.name, player.cost, player.max_cost)]


class WristBladeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.wrist_blade", name="袖剑",
            description="费用为 0 的攻击牌额外造成 4 点伤害。",
            story="实用的暗杀工具。", quantity="boss", owner_character_id="", allow_duplicate=False)


class SacredBarkRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.sacred_bark", name="神圣树皮",
            description="药水的效果翻倍。",
            story="传说中来自于世界树上的一块树皮。", quantity="boss", owner_character_id="", allow_duplicate=False)


class SlaversCollarRelic(_EnergyBossRelic):
    energy_only_in_boss_or_elite = True

    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.slavers_collar", name="奴隶贩子颈环",
            description="在 Boss 战与精英战中，你在每回合开始时获得 1 点能量。",
            story="锈蚀可憎的铁链。", quantity="boss", owner_character_id="", allow_duplicate=False)
