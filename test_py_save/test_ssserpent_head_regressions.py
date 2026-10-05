import pytest

from data.card.AAAregistry import create_card
from data.relic.AAAregistry import create_relic
from game.route import RouteNode
from game.run_engine import enter_current_node, reset_current_node_from_snapshot
from game.run_state import RunState


def make_run(node_type, relic_ids=("relic.ssserpent_head",)):
    node = RouteNode("act1.floor03.col0", node_type, "测试房间", floor=3, col=0)
    return RunState(
        session_id="regression:ssserpent", character_id="character.armored_warrior",
        character_name="玩家", max_hp=80, hp=60, gold=100, run_seed=123,
        relics=[create_relic(relic_id) for relic_id in relic_ids],
        master_deck=[create_card("card.strike")],
        route_nodes=[node], current_node_id=node.node_id,
    )


def test_direct_event_grants_gold_on_entry_and_snapshot_does_not_duplicate_it():
    run = make_run("event")
    reply = enter_current_node(run, seed=123)
    assert run.gold == 150
    assert reply.count("蛇的头：获得 50 金币") == 1
    assert run.pending_event is not None
    run.gold = 1
    run, _ = reset_current_node_from_snapshot(run)
    assert run.gold == 150


@pytest.mark.parametrize("result_type", ["event", "shop", "treasure", "normal_enemy", "elite"])
def test_mystery_rewards_once_regardless_of_resolved_room(monkeypatch, result_type):
    run = make_run("mystery")
    monkeypatch.setattr("game.run_engine.roll_mystery_result", lambda *args, **kwargs: result_type)
    reply = enter_current_node(run, seed=123)
    assert run.gold == 150
    assert reply.count("蛇的头：获得 50 金币") == 1


@pytest.mark.parametrize("node_type,relic_ids", [
    ("event", ()),
    ("rest", ("relic.ssserpent_head",)),
    ("shop", ("relic.ssserpent_head",)),
])
def test_unrelated_entries_do_not_grant_gold(node_type, relic_ids):
    run = make_run(node_type, relic_ids)
    reply = enter_current_node(run, seed=123)
    assert run.gold == 100
    assert "蛇的头：获得" not in reply


def test_event_entry_gold_respects_ectoplasm():
    run = make_run("event", ("relic.ssserpent_head", "relic.ectoplasm"))
    reply = enter_current_node(run, seed=123)
    assert run.gold == 100
    assert "灵体外质" in reply


def test_event_entry_gold_triggers_bloody_idol():
    run = make_run("event", ("relic.ssserpent_head", "relic.bloody_idol"))
    enter_current_node(run, seed=123)
    assert run.gold == 150
    assert run.hp == 65
