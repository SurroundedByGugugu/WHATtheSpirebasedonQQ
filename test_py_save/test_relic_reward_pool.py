# -*- coding: utf-8 -*-

import random
import pytest

from data.relic.AAAregistry import create_relic
from game.relic_logic.run_relic_utils import STARTING_RELIC_MYTH_MAP
from game.reward import get_available_boss_relic_ids, roll_boss_relic_choices

from game.reward import get_available_relic_ids
from game.run_engine import process_post_battle_effects
from game.run_state import RunState


def test_event_relics_are_not_in_normal_reward_pool():
    run_state = RunState(
        session_id="test:red-mask-pool",
        character_id="character.armored_warrior",
    )

    assert "relic.red_mask" not in get_available_relic_ids(run_state)


def test_event_post_battle_effect_can_grant_red_mask():
    run_state = RunState(
        session_id="test:red-mask-event",
        character_id="character.armored_warrior",
        pending_post_battle_effects=[
            {"type": "gain_relic", "relic_id": "relic.red_mask"},
        ],
    )

    process_post_battle_effects(run_state, rng=random.Random(0))

    assert [relic.relic_id for relic in run_state.relics] == ["relic.red_mask"]


@pytest.mark.parametrize('source_id,target_id', STARTING_RELIC_MYTH_MAP.items())
def test_myth_starters_require_xanthosis_even_if_added_to_boss_pool(monkeypatch, source_id, target_id):
    import game.reward as reward
    source = create_relic(source_id)
    run = RunState('test:myth-boss-pool', source.owner_character_id, relics=[source])
    targets = set(STARTING_RELIC_MYTH_MAP.values())
    assert not targets.intersection(reward.BOSS_RELIC_POOL)
    monkeypatch.setattr(reward, 'BOSS_RELIC_POOL', reward.BOSS_RELIC_POOL + list(targets))
    available = get_available_boss_relic_ids(run)
    assert 'relic.xanthosis' in available
    assert not targets.intersection(available)
    offered = roll_boss_relic_choices(run, random.Random(1), count=1000)
    assert offered and all(r.quantity != 'myth' and r.relic_id not in targets for r in offered)

    # The intended acquisition route still replaces the starter successfully.
    yellow = create_relic('relic.xanthosis')
    run.relics.append(yellow)
    yellow.on_obtained(run)
    assert target_id in {r.relic_id for r in run.relics}
    assert source_id not in {r.relic_id for r in run.relics}
    assert 'relic.xanthosis' not in get_available_boss_relic_ids(run)


def test_xanthosis_not_offered_without_upgradable_starter():
    run = RunState('test:no-starter', 'character.defect')
    assert 'relic.xanthosis' not in get_available_boss_relic_ids(run)
    assert 'relic.frozen_core' not in get_available_boss_relic_ids(run)
