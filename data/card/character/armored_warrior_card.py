# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE
)

def create_hard_blow():
    return CardTemplate(
        card_id="card.hard_blow",
        name="痛击",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 8 点伤害。赋予 2t 易伤",
        quantity="common",
        card_vars={
            "damage": 8,
            "vulnerable": 2
        },
        effects=[
            {
                "op":"deal_damage",
                "target":"selected_enemy",
                "amount":{
                    "base_var":"damage",
                    "modifier_profile":"attack_damage"
                }
            },
            {
                "op":"gain_status",
                "target":"selected_enemy",
                "status":"vulnerable",
                "amount":{
                    "var":"vulnerable"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"痛击+",
            "description":"造成 10 点伤害。赋予 3t 易伤",
            "card_vars":{
                "damage": 10,
                "vulnerable": 3
            },
        }
    )

def create_():
    return CardTemplate(
        card_id="card.",
        name="",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 8 点伤害。赋予 2t 易伤",
        quantity="common",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 8,
            "vulnerable": 2
        },
        effects=[
            {
                "op":"deal_damage",
                "target":"selected_enemy",
                "amount":{
                    "base_var":"damage",
                    "modifier_profile":"attack_damage"
                }
            },
            {
                "op":"gain_status",
                "target":"selected_enemy",
                "status":"vulnerable",
                "amount":{
                    "var":"vulnerable"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"痛击+",
            "description":"造成 10 点伤害。赋予 3t 易伤",
            "card_vars":{
                "damage": 10,
                "vulnerable": 3
            },
        }
    )