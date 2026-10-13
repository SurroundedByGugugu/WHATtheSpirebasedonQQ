import copy
import random

import pytest

from data.enemy.AAAregistry import create_enemy
from game.node.node_event_0 import choose_event_option
from game.node.node_event_1_2 import build_joust_event
from game.run_engine import make_node_entry_snapshot, reset_current_node_from_snapshot
from test_py_save.test_ssserpent_head_regressions import make_run


@pytest.mark.parametrize('seed', [1, 2, 5, 8, 15])
@pytest.mark.parametrize('choice', [0, 1])
def test_joust_winner_survives_repeated_sl_and_failed_bets(seed, choice):
    run = make_run('event', ())
    run.pending_event = build_joust_event(run, rng=random.Random(seed))
    winner = run.pending_event.data['joust_winner']
    run.node_entry_snapshot = make_node_entry_snapshot(run)
    expected_win = winner == ('murderer' if choice == 0 else 'owner')
    for attempt in range(4):
        run, _ = reset_current_node_from_snapshot(run)
        run.gold = 0
        for _ in range(attempt):
            completed, _ = choose_event_option(run, choice)
            assert not completed
        run.gold = 100
        completed, reply = choose_event_option(run, choice, seed=999 + attempt)
        assert completed
        assert ('你赌赢了' in reply) == expected_win
        assert run.gold == 50 + ((100 if choice == 0 else 250) if expected_win else 0)


def test_joust_sides_always_have_opposite_outcomes_and_both_winners_exist():
    winners = set()
    for seed in range(30):
        run = make_run('event', ())
        run.pending_event = build_joust_event(run, seed=seed)
        winners.add(run.pending_event.data['joust_winner'])
        replies = [choose_event_option(copy.deepcopy(run), side)[1] for side in (0, 1)]
        assert sum('你赌赢了' in reply for reply in replies) == 1
    assert winners == {'murderer', 'owner'}


def test_legacy_joust_snapshot_is_independent_of_failed_choice_counter():
    run = make_run('event', ())
    run.pending_event = build_joust_event(run, seed=1)
    run.pending_event.data = {}
    replies = []
    for counter in (0, 1, 9):
        restored = copy.deepcopy(run)
        restored.pending_event.data['_rng_counter'] = counter
        replies.append(choose_event_option(restored, 0)[1])
    assert len(set(replies)) == 1


def is_attack(intent):
    return intent.kind == 'attack' or any(is_attack(action) for action in (intent.actions or []))


def test_donu_deca_alternate_attacks_for_six_turns_and_restore_phase():
    donu, deca = create_enemy('enemy.donu'), create_enemy('enemy.deca')
    for turn in range(6):
        donu_intent, deca_intent = donu.get_current_intent(), deca.get_current_intent()
        assert is_attack(donu_intent) == bool(turn % 2)
        assert is_attack(deca_intent) == (not bool(turn % 2))
        assert donu.get_current_intent() is donu_intent
        assert deca.get_current_intent() is deca_intent
        restored = copy.deepcopy([donu, deca])
        actions = [enemy.act().action for enemy in (donu, deca)]
        assert actions == [enemy.act().action for enemy in restored]
        if turn % 2 == 0:
            assert actions[0]['op'] == 'enemy_status_all_allies'
            assert actions[1]['op'] == 'enemy_multi_action'
        else:
            assert actions[0]['op'] == 'enemy_multi_action'
            assert [action['op'] for action in actions[0]['actions']] == ['enemy_attack', 'enemy_attack']
            assert actions[1]['op'] == 'enemy_all_gain_block'
