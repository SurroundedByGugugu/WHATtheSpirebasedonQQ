# -*- coding: utf-8 -*-

from unittest.mock import patch

from app.game_service import GameService
from data.enemy.enemy_origin_1_1 import (
    create_spike_slime_large,
    create_spike_slime_middle,
)
from data.relic.AAAregistry import create_relics
from game.node.node_rest import create_rest_state, get_rest_options
from game.route import RouteNode
from game.run_state import RunState


def collect_intent_keys(enemy, count):
    result = []
    for _ in range(count):
        intent = enemy.get_current_intent()
        result.append("attack" if intent.kind == "multi" else "frail")
        enemy.advance_intent()
    return result


def assert_no_three_identical_actions(actions):
    for index in range(2, len(actions)):
        assert len(set(actions[index - 2:index + 1])) > 1


def test_spike_slime_cannot_repeat_frail_three_times():
    with patch(
        "data.enemy.pattern_enemy.random.choices",
        side_effect=lambda choices, weights, k: [choices[-1]],
    ):
        for factory in (create_spike_slime_large, create_spike_slime_middle):
            actions = collect_intent_keys(factory(), 12)
            assert actions[:3] == ["frail", "frail", "attack"]
            assert_no_three_identical_actions(actions)


def test_spike_slime_cannot_repeat_attack_three_times():
    with patch(
        "data.enemy.pattern_enemy.random.choices",
        side_effect=lambda choices, weights, k: [choices[0]],
    ):
        for factory in (create_spike_slime_large, create_spike_slime_middle):
            actions = collect_intent_keys(factory(), 12)
            assert actions[:3] == ["attack", "attack", "frail"]
            assert_no_three_identical_actions(actions)


def test_middle_spike_slime_uses_reduced_action_values():
    enemy = create_spike_slime_middle()
    pattern = enemy._intent_cycle[0]
    attack_intent = pattern[0][1]
    frail_intent = pattern[1][1]

    assert attack_intent.actions[0].kind == "attack"
    assert attack_intent.actions[0].value == 8
    assert attack_intent.actions[1].kind == "add_card_to_discard"
    assert attack_intent.actions[1].count == 1
    assert frail_intent.kind == "status"
    assert frail_intent.status == "frail"
    assert frail_intent.value == 1


def make_rest_run_state():
    current = RouteNode(
        node_id="act1.floor14.col0",
        node_type="rest",
        name="火堆",
        next_node_ids=["act1.floor15.col0"],
        floor=14,
        col=0,
    )
    next_node = RouteNode(
        node_id="act1.floor15.col0",
        node_type="boss",
        name="Boss",
        floor=15,
        col=0,
    )
    return RunState(
        session_id="rest-leave-test",
        character_id="character.armored_warrior",
        character_name="铁甲战士",
        max_hp=80,
        hp=80,
        relics=create_relics([
            "relic.coffee_dripper",
            "relic.fusion_hammer",
        ]),
        route_nodes=[current, next_node],
        current_node_id=current.node_id,
        pending_rest=create_rest_state(),
    )


def test_rest_always_has_leave_and_leave_command_completes_node():
    run_state = make_rest_run_state()
    assert get_rest_options(run_state)[-1] == ("leave", "离开")

    service = GameService()
    service.set_run(run_state.session_id, run_state, owner_user_id="owner")
    reply = service.handle_message(
        run_state.session_id,
        "owner",
        "/card leave",
    )

    assert run_state.pending_rest is None
    assert run_state.current_node_id in run_state.completed_node_ids
    assert "使用 /card next" in reply
