# -*- coding: utf-8 -*-

from app.game_service import CHARACTER_CHOICES, GameService
from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy
from data.route.route_templates import generate_act3_grid_route
from game.game_state import GameState
from game.intent_preview import format_enemy_intent_text
from game.multiplayer.service import CHARACTER_CHOICES as MULTIPLAYER_CHARACTER_CHOICES
from game.node.node_ancient import create_ancient_state
from game.player_state import PlayerState
from game.pvp.service import CHARACTER_CHOICES as PVP_CHARACTER_CHOICES
from game.route import build_route
from game.run_engine import start_run


def test_act3_ancient_is_transition_only():
    run_state, _reply = start_run(
        "regression:act3_ancient",
        "character.armored_warrior",
        seed=123,
    )
    run_state.route_nodes = build_route(generate_act3_grid_route(seed=123))
    run_state.current_node_id = run_state.route_nodes[0].node_id

    state = create_ancient_state(run_state, seed=456)

    assert len(state.choices) == 1
    assert state.choices[0].effect_type == "continue"


def test_test_character_is_not_publicly_selectable():
    single_ids = [item["character_id"] for item in CHARACTER_CHOICES]
    multiplayer_ids = [item[1] for item in MULTIPLAYER_CHARACTER_CHOICES]
    pvp_ids = [item[1] for item in PVP_CHARACTER_CHOICES]

    assert "character.test" not in single_ids
    assert "character.test" not in multiplayer_ids
    assert "character.test" not in pvp_ids
    assert [item["index"] for item in CHARACTER_CHOICES] == list(range(5))
    assert [item[0] for item in MULTIPLAYER_CHARACTER_CHOICES] == [str(i) for i in range(5)]
    assert [item[0] for item in PVP_CHARACTER_CHOICES] == [str(i) for i in range(5)]

    service = GameService()
    assert "测试角色" not in service.character_choices_text()
    assert service.resolve_character_id(["card", "new"]) == "character.armored_warrior"
    assert service.resolve_character_id(["card", "new", "character.test"]) is None


def test_ctrl_matches_and_adds_character_specific_strike_and_defend():
    service = GameService()
    session_id = "regression:ctrl_same_name"
    user_id = "debug_user"
    service.handle_message(session_id, user_id, "/card new 0")
    run_state = service.get_run(session_id)

    strike_id = "card.strike_armored_warrior"
    defend_id = "card.defend_armored_warrior"
    strike_count = sum(card.card_id == strike_id for card in run_state.master_deck)
    defend_count = sum(card.card_id == defend_id for card in run_state.master_deck)

    reply = service.handle_message(session_id, user_id, "/ctrl removecard 打击 deck")
    assert "已从deck移除 1 张【打击】" in reply
    assert sum(card.card_id == strike_id for card in run_state.master_deck) == strike_count - 1

    reply = service.handle_message(session_id, user_id, "/ctrl removecard 格挡 deck")
    assert "已从deck移除 1 张【格挡】" in reply
    assert sum(card.card_id == defend_id for card in run_state.master_deck) == defend_count - 1

    service.handle_message(session_id, user_id, "/ctrl addcard 打击 deck")
    service.handle_message(session_id, user_id, "/ctrl addcard 格挡 deck")
    assert run_state.master_deck[-2].card_id == strike_id
    assert run_state.master_deck[-1].card_id == defend_id


def test_modified_attack_preview_keeps_element_and_attack_type_tags():
    intent = EnemyIntent(
        kind="attack",
        value=10,
        attack_type="slash",
        attack_element="fire",
    )
    enemy = PatternEnemy(
        enemy_id="enemy.preview_regression",
        name="预览测试敌人",
        max_hp=10,
        intent_cycle=[intent],
    )
    enemy.gain_status("strength", 1)
    player = PlayerState(
        character_id="character.armored_warrior",
        name="玩家",
        max_hp=80,
        hp=80,
        max_cost=3,
        cost=3,
    )
    game_state = GameState(
        session_id="regression:intent_preview",
        character_id=player.character_id,
        player=player,
        enemies=[enemy],
    )

    text = format_enemy_intent_text(game_state, enemy)

    assert text == "火/斩击 攻击 11（基础 10）"
