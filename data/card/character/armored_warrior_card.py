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
        attack_type="blunt",
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

def create_whirlwind():
    return CardTemplate(
        card_id="card.whirlwind",
        name="旋风斩",
        card_type="attack",
        cost="X",
        target="all_enemies",
        description="消耗所有费用。对所有敌人造成 5 点伤害 X 次。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5,
        },
        x_rules=[],
        effects=[
            {
                "op": "repeat_x",
                "effects": [
                    {
                        "op": "deal_damage_all_enemies",
                        "amount": {
                            "base_var": "damage",
                            "modifier_profile": "attack_damage"
                        }
                    }
                ]
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "旋风斩+",
            "description": "消耗所有费用。对所有敌人造成 8 点伤害 X+1 次。",
            "card_vars": {
                "damage": 8,
            },
            "x_rules": [
                {
                    "op": "add",
                    "amount": 1
                }
            ],
        }
    )

def create_demon_form():
    return CardTemplate(
        card_id="card.demon_form",
        name="恶魔形态",
        card_type="power",
        cost=3,
        target="self",
        description="每回合开始时获得 2 点力量。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "strength_per_turn": 2
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "demon_form",
                "amount": {
                    "var": "strength_per_turn"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "恶魔形态+",
            "description": "每回合开始时获得 3 点力量。",
            "card_vars": {
                "strength_per_turn": 3
            },
        }
    )

def create_armored_placeholder_skill():
    return CardTemplate(
        card_id="card.armored_placeholder_skill",
        name="占位技能牌",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 1 张牌。",
        quantity="common",
        owner_character_id="character.armored_warrior",
        card_vars={
            "draw": 1
        },
        effects=[
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={}
    )
