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