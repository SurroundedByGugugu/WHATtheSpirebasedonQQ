# -*- coding: utf-8 -*-
import pytest

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.enemy.AAAregistry import create_enemy
from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy
from data.relic.yoirine_relic import FlowerInAbyssRelic, MatteFalseEyeRelic
from data.zones.element_zones import ElementZone
from game.card_preview import format_card_actual_preview
from game.damage import deal_damage
from game.effects import apply_card_effects, get_random_card_candidates
from game.engine import (_get_toolbox_colorless_pool, get_potion_card_pool,
                         play_card, process_enemy_action)
from game.game_state import GameState
from game.player_state import PlayerState


def make_battle():
    player = PlayerState("character.yoirine", "玩家", 100, 100, 3, 3)
    enemy = PatternEnemy("enemy.regression", "目标", 1000,
                         [EnemyIntent(kind="wait")])
    return GameState("regression:abyss", player.character_id, player, [enemy])


def strike(element):
    card = create_card("card.strike_yoirine")
    card.attack_element = element
    card.card_vars["damage"] = 10
    return card


@pytest.mark.parametrize("survivor", [False, True])
def test_replay_stops_before_any_followup_effect_when_target_dies(survivor):
    game = make_battle()
    game.enemies[0].hp = 1
    if survivor:
        game.enemies.append(make_battle().enemies[0])
    game.player.statuses.set("abyssal_form", 1)
    card = strike("crystal")
    card.replay_extra = 2
    # 第二次结算的非攻击效果也必须停止。
    card.effects.append({"op": "gain_status", "target": "self", "status": "strength", "amount": 1})
    logs = "\n".join(apply_card_effects(game, card, 0))
    assert "第 2/3 次结算" not in logs
    assert "后续重放不再结算" in logs
    assert game.player.hp == 100
    assert game.player.statuses.get("strength") == 1


@pytest.mark.parametrize("status", ["thorns", "temporary_thorns", "poison_thorns"])
def test_zero_damage_attacks_trigger_thorns(status):
    game = make_battle()
    game.player.statuses.set(status, 3)
    logs = deal_damage(game, game.enemies[0], game.player, 0)
    assert game.player.hp == 100
    if status == "poison_thorns":
        assert game.enemies[0].statuses.get("poison") == 3
    else:
        assert game.enemies[0].hp == 997
    assert any("荆棘" in line for line in logs)


def test_zero_damage_multihit_stops_when_thorns_kill_attacker():
    game = make_battle()
    enemy = PatternEnemy("enemy.zero", "零伤敌人", 5,
                         [EnemyIntent(kind="attack", value=0, repeat=5)])
    game.enemies = [enemy, game.enemies[0]]
    game.player.statuses.set("temporary_thorns", 5)
    logs = "\n".join(process_enemy_action(game, enemy))
    assert enemy.hp == 0
    assert logs.count("没有受到伤害") == 1


def test_time_eater_heals_and_cleanses_once():
    game = make_battle()
    enemy = create_enemy("enemy.time_eater")
    game.enemies = [enemy]
    enemy.hp = 100
    enemy._force_heal = True
    for key, amount in [("weak", 2), ("poison", 9), ("abyss_gaze", 10), ("strength", -2)]:
        enemy.statuses.set(key, amount)
    logs = "\n".join(process_enemy_action(game, enemy))
    assert enemy.hp == 228
    assert all(enemy.statuses.get(key) == 0 for key in ("weak", "poison", "abyss_gaze", "strength"))
    assert enemy.statuses.get("time_warp") == 12
    assert enemy._healed_once and not enemy._force_heal
    assert "未处理" not in logs
    enemy.hp = 100
    assert getattr(enemy.get_current_intent(), "_action_key", "") != "d"


def test_time_warp_names_the_actual_turn_end_source():
    game = make_battle()
    game.enemies[0].statuses.set("time_warp", 12)
    game.time_warp_card_count = 11
    game.player.hand = [create_card("card.defend_yoirine")]
    reply = play_card(game, 0)
    assert "时间扭曲结束了你的回合。" in reply
    assert "【格挡】结束了你的回合。" not in reply
    assert game.turn_count == 2
    assert game.force_end_turn_reason == ""


@pytest.mark.parametrize("enemy_id", ["enemy.slime_boss", "enemy.spike_slime_large", "enemy.acid_slime_large"])
def test_flower_distributes_gaze_to_split_children_and_existing_enemies(enemy_id):
    game = make_battle()
    slime = create_enemy(enemy_id)
    game.enemies.insert(0, slime)
    slime.hp = slime.max_hp // 2
    slime.statuses.set("abyss_gaze", 8)
    game.player.relics = [FlowerInAbyssRelic()]
    logs = slime.resolve_split(game)
    amounts = sorted(enemy.statuses.get("abyss_gaze") for enemy in game.enemies)
    assert amounts == [2, 3, 3]
    assert sum("【渊中花】触发" in line for line in logs) == 1


@pytest.mark.parametrize("enemy_id,index", [("enemy.dagger", 1), ("enemy.exploder", 2)])
@pytest.mark.parametrize("thorns", [0, 100])
def test_flower_distributes_self_destruct_gaze_exactly_once(enemy_id, index, thorns):
    game = make_battle()
    enemy = create_enemy(enemy_id)
    enemy._intent_index = index
    enemy.statuses.set("abyss_gaze", 9)
    game.enemies.insert(0, enemy)
    game.player.relics = [FlowerInAbyssRelic()]
    game.player.statuses.set("thorns", thorns)
    logs = process_enemy_action(game, enemy)
    assert enemy.hp == 0
    assert game.enemies[1].statuses.get("abyss_gaze") == 9
    assert sum("【渊中花】触发" in line for line in logs) == 1


@pytest.mark.parametrize("element,zone,extreme,damage,hp", [
    ("shade", "crystal", False, 20, 100),
    ("shade", "crystal", True, 30, 100),
    ("crystal", "shade", False, 15, 95),
    ("crystal", "shade", True, 20, 95),
    ("crystal", "crystal", True, 39, 100),
    ("shade", "shade", True, 26, 95),
    ("crystal", None, False, 10, 100),
    ("shade", None, False, 10, 100),
    ("fire", "shade", True, 10, 100),
])
def test_abyssal_form_zone_effects_without_cross_element_base_multiplier(element, zone, extreme, damage, hp):
    game = make_battle()
    game.player.statuses.set("abyssal_form", 1)
    if zone:
        game.active_zone = ElementZone(zone, is_extreme=extreme, duration=3)
    apply_card_effects(game, strike(element), 0)
    assert game.enemies[0].hp == 1000 - damage
    assert game.player.hp == hp


def test_cross_zone_preview_and_ether_override():
    from data.relic.AAAregistry import create_relic
    game = make_battle()
    card = strike("shade")
    game.player.statuses.set("abyssal_form", 1)
    game.active_zone = ElementZone("crystal", is_extreme=True, duration=3)
    assert "[0]10" in format_card_actual_preview(game, card)
    game.player.relics = [create_relic("relic.ether_medium")]
    apply_card_effects(game, card, 0, {"card_first_play_this_battle": True})
    assert game.enemies[0].hp == 961


@pytest.mark.parametrize("upgraded,stacks", [(False, 1), (True, 2)])
def test_abyss_hunt_rework_and_gaze_after_shade_clear(upgraded, stacks):
    game = make_battle()
    card = create_card("card.abyss_hunt")
    if upgraded:
        card = upgrade_card(card)
    assert card.cost == 2
    apply_card_effects(game, card, None)
    assert game.player.statuses.get("abyss_hunt") == stacks
    game.enemies[0].statuses.set("abyss_gaze", 10)
    game.player.relics = [MatteFalseEyeRelic()]
    apply_card_effects(game, strike("shade"), 0)
    assert game.enemies[0].statuses.get("abyss_gaze") == stacks + 2
    deal_damage(game, game.player, game.enemies[0], 0)
    assert game.enemies[0].statuses.get("abyss_gaze") == stacks + 2
    deal_damage(game, game.player, game.enemies[0], 1, damage_kind="effect")
    assert game.enemies[0].statuses.get("abyss_gaze") == 2 * (stacks + 2)
    game.enemies[0].block = 10
    deal_damage(game, game.player, game.enemies[0], 5, damage_kind="effect")
    assert game.enemies[0].statuses.get("abyss_gaze") == 2 * (stacks + 2)


def test_hunt_counts_each_hit_and_target_without_old_turn_end_healing():
    from game.constants import EVENT_PLAYER_TURN_END
    from game.event_bus import dispatch_event
    game = make_battle()
    game.enemies.append(make_battle().enemies[0])
    game.player.statuses.set("abyss_hunt", 2)
    for _ in range(3):
        for enemy in game.enemies:
            deal_damage(game, game.player, enemy, 1, damage_kind="effect")
    assert [enemy.statuses.get("abyss_gaze") for enemy in game.enemies] == [6, 6]
    game.player.hp = 50
    game.enemies[0].statuses.set("abyss_gaze", 10000)
    before = game.enemies[0].hp
    dispatch_event(game, EVENT_PLAYER_TURN_END)
    assert game.player.hp == 50
    assert game.enemies[0].hp == before


def test_abyssal_form_does_not_cross_apply_to_skills():
    game = make_battle()
    game.player.statuses.set("abyssal_form", 1)
    game.active_zone = ElementZone("shade", is_extreme=True, duration=3)
    card = create_card("card.defend_yoirine")
    card.attack_element = "crystal"
    apply_card_effects(game, card, None)
    assert game.player.hp == 100
    assert game.player.block == 5


def test_abyssal_form_costs_and_description():
    card = create_card("card.abyssal_form")
    assert card.cost == 3
    assert "额外视为有极阴" not in card.description
    assert upgrade_card(card).cost == 2


def test_form_cross_effects_match_mist_logs():
    game = make_battle()
    game.player.statuses.set("abyssal_form", 1)
    game.player.statuses.set("abyss_mist_extreme", 1)
    game.player.hand = [strike("crystal")]
    reply = play_card(game, 0, 0)
    assert game.player.hp == 95
    assert game.enemies[0].hp == 980
    assert "未触发 Zone 效果" not in reply


def test_explicit_zone_modifier_without_form_is_preserved():
    from game.effects import resolve_amount
    game = make_battle()
    game.active_zone = ElementZone("crystal", is_extreme=True, duration=3)
    value = resolve_amount(game, strike("fire"),
                           {"base_var": "damage", "modifier_profile": "attack_damage"},
                           game.player, game.enemies[0],
                           effect_context={"zone_element": "crystal"})
    assert value == 13


def test_random_colorless_sources_exclude_dance_but_keep_regular_cards():
    from data.card.dance_cards import DANCE_CARD_IDS
    game = make_battle()
    for pool in [get_random_card_candidates(colorless_only=True),
                 get_potion_card_pool(game, colorless_only=True),
                 _get_toolbox_colorless_pool()]:
        assert pool
        assert not set(pool).intersection(DANCE_CARD_IDS)
        assert all(create_card(card_id).owner_character_id == "" for card_id in pool)
