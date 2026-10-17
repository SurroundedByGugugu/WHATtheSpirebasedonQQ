import random
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from data.card.AAAregistry import CARD_REGISTRY, create_card
from data.content_gate import (private_content_session, set_private_content_enabled,
                               is_content_enabled, PRIVATE_CHARACTER_IDS)
from data.relic.AAAregistry import RELIC_REGISTRY, create_relic
from data.potion.AAAregistry import POTION_REGISTRY, create_potion
from data.route.encounters import filter_encounter_pool
from game.reward import get_card_reward_pool, get_available_relic_ids, get_available_potion_ids_by_quantity
from game.node.node_event_0 import get_event_builders_for_current_node, filter_event_builders
from game.node.software_shop import build_software_shop_event
from game.run_state import RunState
from test_py_save.test_orbs import battle


@pytest.fixture
def original_only():
    session = 'test:original-only'
    set_private_content_enabled(False, session)
    with private_content_session(session):
        yield
    set_private_content_enabled(True, session)


def test_custom_owner_content_is_automatically_filtered(original_only):
    for kind, registry, create in [('card', CARD_REGISTRY, create_card),
                                   ('relic', RELIC_REGISTRY, create_relic),
                                   ('potion', POTION_REGISTRY, create_potion)]:
        for cid in registry:
            if create(cid).owner_character_id in PRIVATE_CHARACTER_IDS:
                assert not is_content_enabled(kind, cid), cid
    assert is_content_enabled('card', 'card.molten_fist')
    assert is_content_enabled('card', 'card.curse.enthralled')
    assert not is_content_enabled('card', 'card.curse.region_lock')


def test_rewards_events_and_encounters_filter_private_content(original_only):
    run = RunState('test:original-only', 'character.defect')
    run.current_node_id = 'act3.floor05.col0'
    run.route_nodes = [SimpleNamespace(node_id=run.current_node_id)]
    run.relics = [create_relic('relic.prismatic_shard')]
    pool = get_card_reward_pool(run, include_colorless=True)
    assert 'card.molten_fist' in pool
    assert 'card.machine_rush' not in pool
    assert all(is_content_enabled('card', cid) for cid in pool)
    assert all(is_content_enabled('relic', rid) for rid in get_available_relic_ids(run))
    assert all(is_content_enabled('potion', pid)
               for ids in get_available_potion_ids_by_quantity(run).values() for pid in ids)
    builders = filter_event_builders(get_event_builders_for_current_node(run), run)
    assert build_software_shop_event not in builders
    assert filter_encounter_pool(['encounter.corsoal_single']) == []
    assert filter_encounter_pool(['encounter.corsoal_single', 'encounter.cultist_1']) == [('encounter.cultist_1', 1)]


def test_blue_generation_and_glass_orb_remain_usable(original_only):
    from game.defect import random_blue
    from game.orbs import channel, rack
    state, player = battle()
    choices = []
    def pick(pool):
        choices.extend(pool)
        return pool[0]
    with patch('game.defect.random.choice', side_effect=pick):
        random_blue(state, kind='power')
    assert choices and 'machine_rush' not in choices and 'transformer' not in choices
    channel(state, player, 'glass')
    assert rack(player).orbs[-1].kind == 'glass'


def test_confirmed_original_content_and_equivalents_are_retained(original_only):
    for key in ('dominate', 'breakthrough', 'setup_strike', 'cinder', 'tremble',
                'blood_wall', 'amplify', 'molten_fist', 'curse.enthralled'):
        assert 'card.' + key in CARD_REGISTRY
        assert is_content_enabled('card', 'card.' + key)
    for key in ('x_potion', 'dragon_fruit', 'miniature_tent', 'ssserpent_head',
                'xanthosis', 'white_star', 'homunculus_prototype'):
        assert 'relic.' + key in RELIC_REGISTRY
        assert is_content_enabled('relic', 'relic.' + key)
    assert is_content_enabled('event', 'event.holy_water')


def test_nectar_and_calcium_solution_are_excluded_only_when_disabled(original_only):
    from game.node.node_shop import get_normal_shop_relic_ids
    run = RunState('test:original-only', 'character.armored_warrior')
    assert not is_content_enabled('relic', 'relic.four_color_nectar')
    assert not is_content_enabled('potion', 'potion.saturated_calcium_carbonate_solution')
    assert 'relic.four_color_nectar' not in get_available_relic_ids(run)
    assert 'relic.four_color_nectar' not in get_normal_shop_relic_ids(run, random.Random(1), 1000)
    potion_ids = get_available_potion_ids_by_quantity(run)
    assert 'potion.saturated_calcium_carbonate_solution' not in potion_ids['rare']
    with private_content_session('test:private-enabled'):
        set_private_content_enabled(True, 'test:private-enabled')
        assert is_content_enabled('relic', 'relic.four_color_nectar')
        assert is_content_enabled('potion', 'potion.saturated_calcium_carbonate_solution')
