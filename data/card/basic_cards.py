# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate

def create_strike():
    return CardTemplate(
        card_id="card.global.strike",
        name="打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 6 点伤害。",
        quantity="starting",
        card_vars={
            "damage": 6
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"打击+",
            "description":"造成 9 点伤害。",
            "card_vars":{
                "damage": 9
            }
        }
    )


def create_defend():
    return CardTemplate(
        card_id="card.global.defend",
        name="格挡",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。",
        quantity="starting",
        card_vars={
            "block": 5
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"格挡+",
            "description":"获得 8 点格挡。",
            "card_vars":{
                "block": 8
            }
        }
    )

