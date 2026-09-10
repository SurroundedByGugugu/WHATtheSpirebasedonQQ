# -*- coding: utf-8 -*-

import pytest

from app.game_service import GameService
from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy
from data.relic.rare_relics import FourColorNectarRelic
from data.relic.shop_relics import ToolboxRelic
from data.zones.element_zones import ElementZone
from game.card_cost import get_card_current_cost
from game.engine import (
    apply_turn_start_hand_ready_effects,
    choose_pending_toolbox_card,
    clear_turn_temporary_card_costs,
    get_pending_player_choice_hint,
    has_pending_player_choice,
    play_card,
    queue_four_color_nectar_selection,
    queue_toolbox_selection,
)
from game.game_state import GameState
from game.pending_choice import clear_pending_choice, pending_choice_is
from game.player_state import PlayerState


def make_battle():
    player = PlayerState("character.yoirine", "玩家", 100, 100, 3, 3)
    enemy = PatternEnemy(
        enemy_id="enemy.review", name="目标", max_hp=1000,
        intent_cycle=[EnemyIntent(kind="attack", value=0)],
    )
    return GameState("regression:pending", player.character_id, player, [enemy])


def make_service_battle():
    game = make_battle()
    service = GameService()
    service.handle_message(game.session_id, "tester", "/card new 3")
    run = service.get_run(game.session_id)
    run.pending_ancient = None
    run.current_battle = game
    return service, game


@pytest.mark.parametrize("alias", ["dance", "舞", "花蜜", "四色花蜜"])
def test_nectar_aliases_complete_choice_and_unblock_turn(alias):
    service, game = make_service_battle()
    game.player.relics = [FourColorNectarRelic()]
    apply_turn_start_hand_ready_effects(game)
    assert sum(card.upgraded for card in game.pending_choice.options) == 1
    selected = game.pending_choice.options[0]
    service.handle_message(game.session_id, "tester", "/card end")
    assert game.turn_count == 1
    reply = service.handle_message(game.session_id, "tester", "/card " + alias + " 0")
    assert "无效的指令" not in reply
    assert not has_pending_player_choice(game)
    assert game.player.hand[0].card_id == selected.card_id
    service.handle_message(game.session_id, "tester", "/card end")
    assert game.turn_count == 2


@pytest.mark.parametrize("upgraded, expected_hp", [(False, 100), (True, 95)])
@pytest.mark.parametrize("extreme, expected_damage", [(False, 15), (True, 20)])
def test_abyss_manifestation_only_uses_its_explicit_self_damage(upgraded, expected_hp, extreme, expected_damage):
    game = make_battle()
    card = create_card("card.abyss_manifestation")
    if upgraded:
        card = upgrade_card(card)
    game.player.hand = [card]
    game.active_zone = ElementZone("shade", is_extreme=extreme, duration=3)
    game.enemies[0].statuses.set("abyss_gaze", 10)
    play_card(game, 0, 0)
    assert card.attack_element == "shade"
    assert game.player.hp == expected_hp
    assert 1000 - game.enemies[0].hp == (expected_damage if upgraded else 10)


def test_dragon_inspiration_doubles_accuracy_damage_once():
    game = make_battle()
    game.player.hand = [create_card("card.shiv"), create_card("card.shiv")]
    game.player.statuses.set("accuracy", 4)
    game.player.statuses.set("dragon_sound_inspiration", 1)
    play_card(game, 0, 0)
    assert game.enemies[0].hp == 984
    assert game.player.statuses.get("dragon_sound_inspiration") == 0
    play_card(game, 0, 0)
    assert game.enemies[0].hp == 976


@pytest.mark.parametrize("nectar_first", [False, True])
def test_both_opening_relic_choices_are_completed_in_order(nectar_first):
    service, game = make_service_battle()
    relics = [ToolboxRelic(), FourColorNectarRelic()]
    if nectar_first:
        relics.reverse()
    game.player.relics = relics
    apply_turn_start_hand_ready_effects(game)
    apply_turn_start_hand_ready_effects(game)  # 每个开局遗物只触发一次。
    assert len(game.pending_choice_queue) == 1
    choices = [game.pending_choice, game.pending_choice_queue[0]]
    for index, choice in enumerate(choices):
        assert game.pending_choice is choice
        command = "dance" if choice.kind == "four_color_nectar" else "toolbox"
        reply = service.handle_message(game.session_id, "tester", "/card " + command + " 0")
        assert game.player.hand[-1].card_id == choice.options[0].card_id
        if index == 0:
            assert get_pending_player_choice_hint(game) in reply
    assert len(game.player.hand) == 2
    assert not has_pending_player_choice(game)
    assert not game.pending_choice_queue


def test_toolbox_invalid_index_and_full_hand():
    game = make_battle()
    queue_toolbox_selection(game)
    choice = game.pending_choice
    assert "选择编号无效" in choose_pending_toolbox_card(game, -1)
    assert "选择编号无效" in choose_pending_toolbox_card(game, len(choice.options))
    assert game.pending_choice is choice
    game.player.hand = [create_card("card.strike") for _ in range(game.player.max_hand_size)]
    assert "进入弃牌堆" in choose_pending_toolbox_card(game, 0)
    selected = game.player.discard_pile[-1]
    assert selected.card_id == choice.options[0].card_id
    assert selected is not choice.options[0]
    assert selected.temporary and selected.created_in_battle
    assert not has_pending_player_choice(game)


def test_discovery_discount_expires_without_affecting_next_toolbox(monkeypatch):
    game = make_battle()
    monkeypatch.setattr("game.effects.get_random_card_candidates", lambda **kwargs: ["card.strike"])
    game.player.hand = [create_card("card.discovery")]
    play_card(game, 0, 0)
    assert pending_choice_is(game, "toolbox")
    assert "本回合耗能为 0" in get_pending_player_choice_hint(game)
    choose_pending_toolbox_card(game, 0)
    card = game.player.hand[-1]
    assert get_card_current_cost(game, card) == 0
    clear_turn_temporary_card_costs(game.player)
    assert get_card_current_cost(game, card) == 1
    queue_toolbox_selection(game)
    chosen = game.pending_choice.options[0]
    choose_pending_toolbox_card(game, 0)
    assert get_card_current_cost(game, game.player.hand[-1]) == chosen.cost


@pytest.mark.parametrize("request_card_id, selected_id", [
    ("card.secret_technique", "card.defend"),
    ("card.secret_weapon", "card.strike"),
])
def test_draw_pile_selection_moves_the_original_card(request_card_id, selected_id):
    game = make_battle()
    chosen = create_card(selected_id)
    other = create_card("card.strike" if selected_id == "card.defend" else "card.defend")
    game.player.draw_pile = [other, chosen]
    game.player.hand = [create_card(request_card_id)]
    play_card(game, 0, 0)
    assert pending_choice_is(game, "toolbox")
    assert game.pending_choice.options == [chosen]
    choose_pending_toolbox_card(game, 0)
    assert game.player.hand[-1] is chosen
    assert game.player.draw_pile == [other]
    assert not has_pending_player_choice(game)


def test_pending_clear_only_advances_matching_choice_and_full_clear_cancels_queue():
    game = make_battle()
    queue_toolbox_selection(game)
    queue_four_color_nectar_selection(game)
    clear_pending_choice(game, "four_color_nectar")
    assert pending_choice_is(game, "toolbox")
    assert len(game.pending_choice_queue) == 1
    clear_pending_choice(game)
    assert not has_pending_player_choice(game)
    assert not game.pending_choice_queue
