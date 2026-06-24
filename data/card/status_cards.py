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

def create_regret():
    return CardTemplate(
        card_id="card.curse.regret",
        name="悔恨",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。在你的回合结束时，每有一张手牌就失去 1 点生命。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )



def create_injury():
    return CardTemplate(
        card_id="card.curse.injury",
        name="受伤",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_doubt():
    return CardTemplate(
        card_id="card.curse.doubt",
        name="疑虑",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。在你的回合结束时，获得 1 层虚弱。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_parasite():
    return CardTemplate(
        card_id="card.curse.parasite",
        name="寄生",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。如果这张牌在你的牌组中被转化或移除，你失去 3 点最大生命。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_pain():
    return CardTemplate(
        card_id="card.curse.pain",
        name="疼痛",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。当在手牌中时，每打出一张其他牌，失去 1 生命。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_decay():
    return CardTemplate(
        card_id="card.curse.decay",
        name="腐朽",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。若在手牌中，在你的回合结束时，受到 2 点伤害。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_curse_of_the_bell():
    return CardTemplate(
        card_id="card.curse.bell",
        name="铃铛的诅咒",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。无法从牌组中移除。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_normality():
    return CardTemplate(
        card_id="card.curse.normality",
        name="凡庸",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。在手牌中时，你在此回合无法打出 3 张以上牌。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )


def create_necronomicurse():
    card = CardTemplate(
        card_id="card.curse.necronomicurse",
        name="死灵诅咒",
        card_type="curse",
        cost=0,
        target="none",
        description="不能被打出。无法逃脱：不能被移除或变化；被消耗后会回到手牌。",
        quantity="curse",
        effects=[],
        keywords=[KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={}
    )
    setattr(card, "unremovable", True)
    setattr(card, "untransformable", True)
    setattr(card, "inescapable", True)
    return card
