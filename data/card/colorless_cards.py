# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE
)

def create_burst():
    return CardTemplate(
        card_id="card.burst",
        name="爆发",
        card_type="skill",
        cost=1,
        target="self",
        description="本回合内，你打出的下一张技能牌会打出 2 次。",
        quantity="rare",
        owner_character_id="",
        card_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "burst",
                "amount": {
                    "var": "count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "爆发+",
            "description": "本回合内，你打出的下 2 张技能牌会打出 2 次。",
            "card_vars": {
                "count": 2
            },
        }
    )
def create_amplify():
    return CardTemplate(
        card_id="card.amplify",
        name="增幅",
        card_type="skill",
        cost=1,
        target="self",
        description="本回合内，你打出的下一张能力牌会打出 2 次。",
        quantity="rare",
        owner_character_id="",
        card_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "amplify",
                "amount": {
                    "var": "count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "增幅+",
            "description": "本回合内，你打出的下 2 张能力牌会打出 2 次。",
            "card_vars": {
                "count": 2
            },
        }
    )

def create_soul():
    return CardTemplate(
        card_id="card.soul",
        name="灵魂",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 2 张牌。消耗。",
        quantity="event",
        owner_character_id="",
        card_vars={
            "draw": 2
        },
        effects=[
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "灵魂+",
            "description": "抽 3 张牌。消耗。",
            "card_vars": {
                "draw": 3
            },
        }
    )