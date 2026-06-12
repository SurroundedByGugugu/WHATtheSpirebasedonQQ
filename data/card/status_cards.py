# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST


def create_slime_i():
    return CardTemplate(
        card_id="card.status.slime_i",
        name="黏液I",
        card_type="status",
        cost=1,
        target="none",
        description="无效果。消耗。",
        quantity="status",
        effects=[],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={}
    )