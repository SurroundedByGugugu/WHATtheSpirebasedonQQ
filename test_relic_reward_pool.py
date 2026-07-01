# -*- coding: utf-8 -*-

import random

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
