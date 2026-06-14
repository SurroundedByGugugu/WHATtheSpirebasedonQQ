# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST, KEYWORD_UNPLAYABLE, KEYWORD_ETHEREAL

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

def create_wound():
    return CardTemplate(
        card_id="card.status.wound",
        name="伤口",
        card_type="status",
        cost=0,
        target="none",
        description="不能被打出。",
        quantity="status",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )

def create_dazed():
    return CardTemplate(
        card_id="card.status.dazed",
        name="眩晕",
        card_type="status",
        cost=0,
        target="none",
        description="不能被打出。虚无。",
        quantity="status",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE,KEYWORD_ETHEREAL],
        upgraded=False,
        upgrade_patch={}
    )

def create_burn_i():
    return CardTemplate(
        card_id="card.status.burn_i",
        name="灼伤I",
        card_type="status",
        cost=0,
        target="none",
        description="不能被打出。在你的回合结束时，你受到 2 点伤害。",
        quantity="status",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )

def create_burn_ii():
    return CardTemplate(
        card_id="card.status.burn_ii",
        name="灼伤II",
        card_type="status",
        cost=0,
        target="none",
        description="不能被打出。在你的回合结束时，你受到 4 点伤害。",
        quantity="status",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )