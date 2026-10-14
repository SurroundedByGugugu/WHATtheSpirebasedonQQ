from unittest.mock import Mock, patch

import pytest

from data.card.AAAregistry import create_card
from data.enemy.AAAregistry import create_enemy
from data.relic.AAAregistry import create_relic
from game.deck_utils import transform_card_in_master_deck
from game.effects import apply_card_effects, apply_card_effect
from game.engine import start_battle_with_player, choose_pending_potion_card, play_card
from game.event_bus import dispatch_event
from game.lizhou import free
from game.lizhou_relic import options
from game.reward import RewardState, RewardOption
from game.run_engine import (take_reward, skip_reward, choose_act4_entry,
                             choose_next_node, complete_current_node)
from game.route import RouteNode
from test_py_save.test_orbs import battle
from test_py_save.test_ssserpent_head_regressions import make_run


@pytest.mark.parametrize('enemy_id,artifact', [
    ('sentry_a', 1), ('sentry_b', 1), ('bronze_automaton', 3),
    ('spheric_guardian', 3), ('donu', 2), ('deca', 2),
    ('spire_shield', 1), ('spire_spear', 1), ('orb_walker', 0), ('bronze_orb', 0),
])
def test_artifact_exists_at_battle_entry_and_is_not_replenished(enemy_id, artifact):
    _, player = battle()
    player.character_id = 'character.armored_warrior'
    state, _ = start_battle_with_player('artifact', player.character_id, player, ['enemy.' + enemy_id])
    enemy = state.enemies[0]
    assert enemy.statuses.get('artifact') == artifact
    if artifact:
        result = enemy.gain_status_with_result('weak', 1)
        assert result['blocked'] and enemy.statuses.get('weak') == 0
        dispatch_event(state, 'turn_start')
        assert enemy.statuses.get('artifact') == artifact - 1


def test_byrd_resets_only_unbroken_flight_on_new_turn():
    state, _ = battle()
    enemy = create_enemy('enemy.byrd')
    state.enemies = [enemy]
    enemy.statuses.set('flying', 1)
    dispatch_event(state, 'turn_start')
    assert enemy.statuses.get('flying') == 3
    enemy.statuses.remove('flying')
    enemy.on_flying_broken(state)
    dispatch_event(state, 'turn_start')
    assert enemy.statuses.get('flying') == 0
    assert enemy._byrd_mode == 'grounded'


@pytest.mark.parametrize('order_amount', [0, 10])
@pytest.mark.parametrize('full_hand', [False, True])
def test_skill_potion_zodiac_is_free_for_order_this_turn(order_amount, full_hand):
    state, player = battle()
    player.statuses.set('lizhou_order', order_amount)
    if full_hand:
        player.hand = [create_card('card.strike') for _ in range(player.max_hand_size)]
    state.pending_potion_card_selection = True
    state.pending_potion_card_source = '技能药水'
    state.pending_potion_card_options = [create_card('card.lizhou.aries')]
    choose_pending_potion_card(state, 0)
    card = (player.discard_pile if full_hand else player.hand)[-1]
    assert free(state, card)
    player.hand = [card]
    player.cost = 0
    play_card(state, 0, 0)
    assert player.statuses.get('buffer') == 1
    assert player.statuses.get('lizhou_order') == order_amount
    state.turn_count += 1
    assert not free(state, card)


def test_event_transform_into_duplicate_zodiac_triggers_relic():
    run = make_run('event', ('relic.twelve_zodiacs',))
    run.character_id = 'character.lizhou'
    run.master_deck = [create_card('card.lizhou.strike'), create_card('card.lizhou.aries')]
    rng = Mock()
    rng.choice.return_value = 'card.lizhou.aries'
    _, new, logs = transform_card_in_master_deck(run, 0, rng)
    assert new.card_id == 'card.lizhou.aries'
    assert len(options(run)) == 2
    assert any('十二星座卡牌' in text for text in logs)


@pytest.mark.parametrize('strength', [-5, 0, 12])
def test_feather_dance_consumes_one_artifact_before_changing_strength(strength):
    state, _ = battle()
    enemy = state.enemies[0]
    enemy.statuses.set('strength', strength)
    enemy.statuses.set('artifact', 1)
    card = create_card('card.dance.feather_dance')
    logs = apply_card_effects(state, card, 0)
    assert enemy.statuses.get('strength') == strength
    assert enemy.statuses.get('artifact') == 0
    assert any('人工制品抵挡' in text for text in logs)
    apply_card_effects(state, card, 0)
    assert enemy.statuses.get('strength') == strength - max(3, max(0, strength) // 2)


@pytest.mark.parametrize('status', ['stun', 'flinch'])
def test_artifact_blocks_applied_stun_and_flinch(status):
    state, _ = battle()
    enemy = state.enemies[0]
    enemy.statuses.set('artifact', 1)
    effect = {'op': 'gain_status', 'target': 'selected_enemy', 'status': status, 'amount': 2}
    card = create_card('card.strike')
    apply_card_effect(state, card, effect, 0, {})
    assert enemy.statuses.get(status) == 0
    assert enemy.statuses.get('artifact') == 0
    apply_card_effect(state, card, effect, 0, {})
    assert enemy.statuses.get(status) == 2


def test_slow_display_tracks_replays_and_resets():
    state, player = battle()
    enemy = state.enemies[0]
    enemy.statuses.set('slow', 1)
    card = create_card('card.defend')
    card.replay_extra = 2
    player.hand = [card]
    play_card(state, 0)
    assert '缓慢（当前计数：3）' in enemy.status_text(state)
    dispatch_event(state, 'turn_start')
    assert '缓慢（当前计数：0）' in enemy.status_text(state)


def boss_run():
    run = make_run('boss', ())
    run.route_nodes = [RouteNode('act3.floor15.col0', 'boss', '三层Boss', floor=15, col=0)]
    run.current_node_id = run.route_nodes[0].node_id
    run.pending_reward = RewardState(node_type='boss', options=[
        RewardOption('gold', '金币', {'amount': 20}),
        RewardOption('relic', '遗物', {'relic': create_relic('relic.anchor')}),
    ])
    return run


@pytest.mark.parametrize('skip', [False, True])
def test_act4_prompt_waits_for_all_rewards_and_can_decline(skip):
    run = boss_run()
    take_reward(run, 0)
    assert not run.pending_act4_choice and not run.run_over
    reply = skip_reward(run) if skip else take_reward(run, 1)
    assert '是否上楼' in reply and run.pending_act4_choice
    assert not run.run_over and run.has_pending_node()
    assert '未完成' in choose_next_node(run, 0)
    with patch('game.run_engine.check_run_end_achievements', return_value=[]) as achievements:
        reply = choose_act4_entry(run, False)
        achievements.assert_called_once_with(run)
    assert run.run_over and run.victory and '胜利' in reply


def test_accept_act4_builds_route_once_and_finishes_heart_without_prompt():
    run = boss_run()
    skip_reward(run)
    reply = choose_act4_entry(run, True)
    assert '四层入口' in reply
    assert run.current_node_id == 'act4.floor00'
    assert run.hp == run.max_hp and not run.run_over
    assert run.boss_encounter_id == 'encounter.boss.corrupt_heart'
    assert len([n for n in run.route_nodes if n.node_id.startswith('act4.')]) == 5
    assert '没有待确认' in choose_act4_entry(run, True)
    choose_next_node(run, 0)
    assert run.pending_rest is not None
    run.clear_pending_nodes()
    run.current_node_id = 'act4.floor04.col0'
    complete_current_node(run)
    assert run.run_over and run.victory and not run.pending_act4_choice


def test_act4_route_reaches_shield_spear_and_heart_battles():
    from game.run_engine import finish_current_battle_if_needed, leave_shop
    run = boss_run()
    skip_reward(run)
    choose_act4_entry(run, True)
    choose_next_node(run, 0)
    run.pending_rest = None
    complete_current_node(run)
    choose_next_node(run, 0)
    assert run.pending_shop is not None
    leave_shop(run)
    choose_next_node(run, 0)
    assert {e.enemy_id for e in run.current_battle.enemies} == {'enemy.spire_shield', 'enemy.spire_spear'}
    assert all(e.statuses.get('artifact') == 1 for e in run.current_battle.enemies)
    run.current_battle.battle_over = True
    run.current_battle.victory = True
    finish_current_battle_if_needed(run)
    skip_reward(run)
    choose_next_node(run, 0)
    assert run.current_battle.enemies[0].enemy_id == 'enemy.corrupt_heart'


def test_act4_choice_waits_for_relic_selection_and_rejects_early_entry():
    run = boss_run()
    assert '没有待确认' in choose_act4_entry(run, True)
    skip_reward(run)
    run.pending_bottle_selections = [{'required_card_type': 'attack'}]
    assert '先完成遗物' in choose_act4_entry(run, False)
    assert run.pending_act4_choice and not run.run_over


def test_web_and_service_act4_choice():
    import json
    from web import bridge
    from app.game_service import GameService
    bridge.service = GameService()
    bridge.dispatch('/card new 0')
    run = bridge.service.get_run(bridge.SESSION)
    fixture = boss_run()
    run.route_nodes = fixture.route_nodes
    run.current_node_id = fixture.current_node_id
    run.pending_reward = fixture.pending_reward
    result = json.loads(bridge.dispatch('/card skip'))
    assert result['run']['actionTitle'] == '是否上楼？'
    assert {c['command'] for c in result['run']['choices']} == {'/card ascend yes', '/card ascend no'}
    result = json.loads(bridge.dispatch('/card ascend yes'))
    assert result['run']['node'] == '四层入口'
    assert not run.pending_act4_choice


def test_web_slow_count_and_service_decline_ends_run():
    import json
    from web import bridge
    from app.game_service import GameService
    bridge.service = GameService()
    bridge.dispatch('/card new 0')
    run = bridge.service.get_run(bridge.SESSION)
    run.current_battle, _ = battle()
    run.current_battle.enemies[0].statuses.set('slow', 1)
    run.current_battle.enemies[0]._slow_cards_played_this_turn = 4
    assert '缓慢（当前计数：4）' in bridge.snapshot()['run']['enemies'][0]['status']
    run.current_battle = None
    fixture = boss_run()
    run.route_nodes, run.current_node_id = fixture.route_nodes, fixture.current_node_id
    run.pending_reward = fixture.pending_reward
    bridge.dispatch('/card skip')
    result = json.loads(bridge.dispatch('/card ascend no'))
    assert result['run'] is None and '胜利' in result['reply']
