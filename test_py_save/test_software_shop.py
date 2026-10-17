import pickle
import random
from types import SimpleNamespace

from data.card.AAAregistry import create_card
from data.card.keyword_rules import can_play_card
from data.relic.AAAregistry import create_relic
from data.relic.software_relics import SPECS
from data.zones.element_zones import ElementZone
from data.zones.star_zone import StarZone, deploy_star
from game.battle_context import BattleContext
from game.deck_utils import can_remove_card, transform_card_in_master_deck
from game.node.node_ancient import create_ancient_state, choose_ancient_option, _apply_cost
from game.node.node_event_0 import choose_event_option, get_event_builders_for_current_node
from game.node.software_shop import build_software_shop_event
from game.reward import get_available_relic_ids
from game.run_state import RunState
from game.zone.zone_utils import deploy_element_zone, format_zone_field_detail, tick_zone_turn_end
from test_py_save.test_orbs import battle


def run_state():
    run = RunState('software-test', 'character.defect')
    run.master_deck = [create_card('card.strike_defect') for _ in range(6)]
    run.max_hp = run.hp = 75
    run.gold = 200
    return run


def install(run, key):
    event = build_software_shop_event(run, seed=1)
    from game.node.node_event_0 import EventChoice
    event.choices = [EventChoice(key, 'software_install', payload={'key': key})]
    run.pending_event = event
    return choose_event_option(run, 0, seed=1)


def test_shop_pool_and_three_unique_options():
    run = run_state()
    for act in (1, 2, 3):
        run.current_node_id = 'act{}.f1.n0'.format(act)
        run.route_nodes = [SimpleNamespace(node_id=run.current_node_id)]
        builders = get_event_builders_for_current_node(run)
        assert (build_software_shop_event in builders) == (act == 3)
    run.character_id = 'character.watcher'
    assert build_software_shop_event not in get_event_builders_for_current_node(run)
    run.character_id = 'character.defect'
    event = build_software_shop_event(run, seed=4)
    assert len({c.payload['key'] for c in event.choices}) == 3
    normal_pool = get_available_relic_ids(run)
    assert all('relic.' + key not in normal_pool for key in SPECS)


def test_doubao_curses_priority_and_persistent_strength():
    run = run_state()
    assert install(run, 'doubao')[0]
    assert [c.card_id for c in run.master_deck[-2:]] == ['card.curse.enthralled', 'card.curse.clumsy']
    enthralled = run.master_deck[-2]
    assert enthralled.cost == 2 and not can_remove_card(enthralled)
    assert transform_card_in_master_deck(run, 6)[0] is None
    state, player = battle()
    player.hand = [enthralled, create_card('card.strike_defect')]
    assert can_play_card(state, enthralled)[0]
    assert not can_play_card(state, player.hand[1])[0]
    relic = run.relics[-1]
    context = BattleContext(game_state=state, player=player, extra={'victory': True})
    for _ in range(2):
        relic.on_event('battle_end', context)
    restored = pickle.loads(pickle.dumps(relic))
    restored.on_event('battle_start', context)
    assert player.statuses.get('strength') == 2


def test_afu_heals_and_respects_bloom():
    state, player = battle()
    player.hp = 50
    relic = create_relic('relic.ant_afu')
    context = BattleContext(game_state=state, player=player)
    relic.on_event('battle_start', context)
    assert player.hp == 52
    player.relics = [create_relic('relic.mark_of_the_bloom')]
    relic.on_event('battle_start', context)
    assert player.hp == 52


def test_claude_removes_three_before_adding_curse_and_survives_save():
    run = run_state()
    assert not install(run, 'claude')[0]
    assert run.pending_event is None and run.pending_ancient is not None
    for index in range(3):
        done, _ = choose_ancient_option(run, 0, seed=2)
        assert done == (index == 2)
        run = pickle.loads(pickle.dumps(run))
    assert len(run.master_deck) == 4
    assert run.master_deck[-1].card_id == 'card.curse.region_lock'


def test_lock_stops_mid_draw_and_unlocks_after_discard():
    state, player = battle()
    player.draw_pile = [create_card('card.strike_defect'), create_card('card.curse.region_lock')]
    player.draw_cards(5, game_state=state)
    assert len(player.hand) == 1 and len(player.draw_pile) == 1
    player.discard_pile.extend(player.hand)
    player.hand = []
    player.draw_cards(1, game_state=state)
    assert player.hand[0].card_id == 'card.strike_defect'


def test_gpt_and_gemini_rewards():
    run = run_state()
    install(run, 'gpt')
    assert run.master_deck[-1].card_id == 'card.creative_ai' and run.master_deck[-1].upgraded
    install(run, 'gemini')
    cards = run.pending_reward.options[0].payload['cards']
    assert len({c.card_id for c in cards}) == 3
    assert all(c.quantity == 'rare' and not c.upgraded for c in cards)


def test_deepseek_full_blessing_and_local_gold_cost():
    run = run_state()
    run.current_node_id = 'act3.f5.n0'
    install(run, 'deepseek')
    assert len(run.pending_ancient.choices) == 4
    found = False
    for seed in range(100):
        state = create_ancient_state(run, seed=seed, software_blessing=True)
        choice = state.choices[2]
        assert choice.payload['cost_key'] != 'lose_all_gold'
        if choice.payload['cost_key'] == 'lose_gold_99':
            found = True
            assert '99' in choice.title
    assert found
    _apply_cost(run, 'lose_gold_99', 6, random.Random(1))
    assert run.gold == 101
    _apply_cost(run, 'lose_all_gold', 6, random.Random(1))
    assert run.gold == 0


def test_star_is_special_zone_with_independent_field_slot():
    state, _ = battle()
    field = SimpleNamespace(name='test')
    state.active_fields = [field]
    deploy_star(state)
    assert state.active_zone.zone_kind == 'special'
    assert '非属性特殊' in format_zone_field_detail(state)
    deploy_star(state)
    assert state.active_zone.is_extreme
    deploy_element_zone(state, 'fire')
    assert isinstance(state.active_zone, StarZone)
    for _ in range(3):
        tick_zone_turn_end(state)
    assert state.active_zone is None and state.active_fields == [field]
    deploy_element_zone(state, 'fire')
    assert isinstance(state.active_zone, ElementZone) and state.active_zone.zone_kind == 'elemental'
