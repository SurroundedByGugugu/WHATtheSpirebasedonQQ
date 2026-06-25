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

def create_shiv():
    return CardTemplate(
        card_id="card.shiv",
        name="小刀",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 4 点伤害。消耗。",
        quantity="event",
        attack_type="piercing",
        owner_character_id="",
        card_vars={"damage": 4},
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "小刀+",
            "description": "造成 6 点伤害。消耗。",
            "card_vars": {"damage": 6}
        }
    )

def create_jax():
    from game.constants import KEYWORD_EXHAUST
    return CardTemplate(
        card_id="card.jax",
        name="J.A.X.",
        card_type="skill",
        cost=0,
        target="self",
        description="失去 3 点生命。获得 2 点力量。消耗。",
        quantity="event",
        owner_character_id="",
        card_vars={"hp_loss": 3, "strength": 2},
        effects=[
            {"op": "lose_hp", "amount": {"var": "hp_loss"}},
            {"op": "gain_status", "target": "self", "status": "strength", "amount": {"var": "strength"}},
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "J.A.X.+",
            "description": "失去 3 点生命。获得 3 点力量。消耗。",
            "card_vars": {"strength": 3}
        }
    )

#uncommon attack
def create_swift_strike():
    return CardTemplate(
        card_id="card.swift_strike",
        name="迅捷打击",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 7 点伤害。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="",
        card_vars={"damage": 7},
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        upgraded=False,
        upgrade_patch={
            "name": "迅捷打击+",
            "description": "造成 10 点伤害。",
            "card_vars": {"damage": 10}
        }
    )
def create_dramatic_entrance():
    return CardTemplate(
        card_id="card.dramatic_entrance",
        name="闪亮登场",
        card_type="attack",
        cost=0,
        target="all_enemies",
        description="固有。对所有敌人造成 8 点伤害。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"damage": 8},
        effects=[{
            "op": "deal_damage_all_enemies",
            "target": "all_enemies",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        keywords=[KEYWORD_EXHAUST,KEYWORD_INNATE],
        upgraded=False,
        upgrade_patch={
            "name": "闪亮登场+",
            "description": "固有。对所有敌人造成 12 点伤害。消耗。",
            "card_vars": {"damage": 12}
        }
    )
def create_flash_of_steel():
    return CardTemplate(
        card_id="card.flash_of_steel",
        name="亮剑",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 3 点伤害。抽 1 张牌。",
        quantity="uncommon",
        attack_type="slash",
        card_vars={
            "damage": 3,
            "draw": 1
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            },
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "亮剑+",
            "description": "造成 6 点伤害。抽 1 张牌。",
            "card_vars": {
                "damage": 6
            },
        }
    )
def create_mind_blast():
    return CardTemplate(
        card_id="card.mind_blast",
        name="心灵震慑",
        card_type="attack",
        cost=2,
        target="enemy",
        description="固有。造成你抽牌堆中剩余牌数的伤害。",
        quantity="uncommon",
        attack_type="magic",
        owner_character_id="",
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {
                "draw_pile_count": True,
                "modifier_profile": "attack_damage"
            }
        }],
        keywords=[KEYWORD_INNATE],
        upgraded=False,
        upgrade_patch={
            "name": "心灵震慑+",
            "cost": 1,
            "description": "固有。造成你抽牌堆中剩余牌数的伤害。"
        }
    )

#rare attack
def create_hand_of_greed():
    return CardTemplate(
        card_id="card.hand_of_greed",
        name="贪婪之手",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 20 点伤害。斩杀时，获得 20 金币。",
        quantity="rare",
        attack_type="magic",
        owner_character_id="",
        card_vars={
            "damage": 20,
            "gold_gain": 20
        },
        effects=[
            {
                "op": "deal_damage_gain_gold_on_non_minion_kill",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                },
                "gold_gain": {
                    "var": "gold_gain"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "贪婪之手+",
            "cost": 1,
            "description": "造成 25 点伤害。斩杀时，获得 25 金币。",
            "card_vars": {
                "damage": 25,
                "gold_gain": 25
            }
        }
    )

#uncommon skill
#rare skill
#rare power