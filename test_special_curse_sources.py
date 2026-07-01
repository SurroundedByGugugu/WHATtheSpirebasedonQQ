# -*- coding: utf-8 -*-

from data.card.AAAregistry import create_card
from data.card.special_curses import NECRONOMICURSE_CARD_ID
from data.relic.AAAregistry import create_relic
from game.deck_utils import get_curse_transform_candidate_ids
from game.node.node_treasure import _roll_random_curse_id
from game.run_state import RunState


class CaptureChoiceRandom:
    def __init__(self):
        self.candidates = None

    def choice(self, candidates):
        self.candidates = list(candidates)
        return self.candidates[0]


def test_random_curse_pool_excludes_necronomicurse():
    rng = CaptureChoiceRandom()

    _roll_random_curse_id(rng)

    assert NECRONOMICURSE_CARD_ID not in rng.candidates


def test_curse_transform_pool_excludes_necronomicurse():
    candidates = get_curse_transform_candidate_ids(create_card("card.curse.injury"))

    assert NECRONOMICURSE_CARD_ID not in candidates


def test_necronomicon_obtained_grants_necronomicurse():
    run_state = RunState(
        session_id="test:necronomicurse-source",
        character_id="character.armored_warrior",
    )
    relic = create_relic("relic.necronomicon")

    relic.on_obtained(run_state)

    assert [card.card_id for card in run_state.master_deck] == [NECRONOMICURSE_CARD_ID]
