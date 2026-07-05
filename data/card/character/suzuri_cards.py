# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST

# starting
def create_earth_origin_dominion():
    return CardTemplate(
        card_id="card.earth_origin_dominion",
        name="地原统御",
        card_type="skill",
        cost=3,
        target="self",
        description="消耗。展开地 Zone。获得 10 点格挡。将 1 张【成岩作用】加入抽牌堆。",
        quantity="starting",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "block": 10,
        },
        keywords=[KEYWORD_EXHAUST],
        effects=[
            {
                "op": "set_zone",
                "element": "earth",
            },
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block",
                },
            },
            {
                "op": "add_card_to_draw_pile",
                "card_id": "card.rock_forming_action",
                "amount": 1,
                "shuffle": True,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "地原统御+",
            "cost": 2,
            "description": "消耗。展开地 Zone。获得 10 点格挡。将 1 张【成岩作用+】加入抽牌堆。",
            "effects": [
                {
                    "op": "set_zone",
                    "element": "earth",
                },
                {
                    "op": "gain_block",
                    "target": "self",
                    "amount": {
                        "var": "block",
                        "modifier_profile": "block",
                    },
                },
                {
                    "op": "add_card_to_draw_pile",
                    "card_id": "card.rock_forming_action",
                    "amount": 1,
                    "shuffle": True,
                    "upgraded": True,
                },
            ],
        }
    )
def create_anatexis_action():
    return CardTemplate(
        card_id="card.anatexis_action",
        name="熔离作用",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 4 点格挡和 3 层岩层。",
        quantity="starting",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "block": 4,
            "rock_layer": 3,
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block",
                },
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "rock_layer",
                "amount": {
                    "var": "rock_layer",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "熔离作用+",
            "description": "获得 6 点格挡和 4 层岩层。",
            "card_vars": {
                "block": 6,
                "rock_layer": 4,
            },
        }
    )

def create_rock_forming_action():
    return CardTemplate(
        card_id="card.rock_forming_action",
        name="成岩作用",
        card_type="skill",
        cost=0,
        target="self",
        description="选择手牌中 1 张能产生格挡的无属性技能牌，添加地词条。消耗。",
        quantity="event",
        owner_character_id="",
        keywords=[KEYWORD_EXHAUST],
        effects=[
            {
                "op": "choose_hand_attack_without_element_apply_plating",
                "element": "earth",
                "suffix": "·地",
                "allowed_card_types": ["skill"],
                "require_gain_block": True,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "成岩作用+",
            "description": "选择手牌中 1 张能产生格挡的无属性技能牌，添加地词条。",
            "remove_keywords": [KEYWORD_EXHAUST],
        }
    )


# common
def create_stone_blade():
    return CardTemplate(
        card_id="card.stone_blade",
        name="石刃",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 8 点伤害。若岩层大于 5，本次伤害 ×1.5。",
        quantity="common",
        attack_type="slash",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "damage": 8,
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage",
                    "status_conditional_multiplier": {
                        "target": "self",
                        "status": "rock_layer",
                        "gt": 5,
                        "multiplier": 1.5,
                    },
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "石刃+",
            "description": "造成 10 点伤害。若岩层大于 5，本次伤害 ×1.5。",
            "card_vars": {
                "damage": 10,
            },
        }
    )

def create_anatexis():
    return CardTemplate(
        card_id="card.anatexis",
        name="深熔作用",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗 2 层岩层。获得 1 层岩浆层。",
        quantity="common",
        owner_character_id="character.suzuri",
        card_vars={
            "magma_layer": 1,
            "rock_cost": 2,
        },
        play_conditions=[
            {
                "op": "has_status_at_least",
                "status": "rock_layer",
                "amount": 2,
            }
        ],
        effects=[
            {
                "op": "consume_status_amount",
                "target": "self",
                "status": "rock_layer",
                "amount": {
                    "var": "rock_cost",
                },
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "magma_layer",
                "amount": {
                    "var": "magma_layer",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "深熔作用+",
            "description": "消耗 1 层岩层。获得 1 层岩浆层。",
            "card_vars": {
                "rock_cost": 1,
            },
            "patches": [
                {
                    "path": ["play_conditions"],
                    "value": [
                        {
                            "op": "has_status_at_least",
                            "status": "rock_layer",
                            "amount": 1,
                        }
                    ],
                }
            ],
        }
    )


# uncommon
def create_eruption_action():
    return CardTemplate(
        card_id="card.eruption_action",
        name="喷出作用",
        card_type="skill",
        cost=1,
        target="self",
        description="抽 2 张牌。在手牌中选择至多 1 张牌添加保留。",
        quantity="uncommon",
        owner_character_id="character.suzuri",
        card_vars={
            "draw": 2,
            "retain_count": 1,
        },
        effects=[
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw",
                },
            },
            {
                "op": "choose_hand_add_retain",
                "count": {
                    "var": "retain_count",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "喷出作用+",
            "description": "抽 3 张牌。在手牌中选择至多 2 张牌添加保留。",
            "card_vars": {
                "draw": 3,
                "retain_count": 2,
            },
        }
    )
def create_hidden_gravel():
    return CardTemplate(
        card_id="card.hidden_gravel",
        name="隐蔽石砾",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗。获得 2 层隐蔽石砾。地 Zone 下额外获得 1 层。",
        quantity="uncommon",
        attack_element="earth",
        owner_character_id="character.suzuri",
        keywords=[KEYWORD_EXHAUST],
        card_vars={
            "hidden_gravel": 2,
            "zone_bonus": 1,
        },
        effects=[
            {
                "op": "gain_status_with_zone_bonus",
                "target": "self",
                "status": "hidden_gravel",
                "amount": {
                    "var": "hidden_gravel",
                },
                "zone_element": "earth",
                "zone_bonus": {
                    "var": "zone_bonus",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "隐蔽石砾+",
            "description": "消耗。获得 3 层隐蔽石砾。地 Zone 下额外获得 1 层。",
            "card_vars": {
                "hidden_gravel": 3,
            },
        }
    )

# event
def create_radiant_crystal_reflection():
    return CardTemplate(
        card_id="card.radiant_crystal_reflection",
        name="辉晶映照",
        card_type="skill",
        cost=1,
        target="self",
        description="选择 1 张消耗堆以外的牌，添加重放 1。消耗。",
        quantity="event",
        attack_element="crystal",
        owner_character_id="",
        keywords=[KEYWORD_EXHAUST],
        card_vars={
            "count": 1,
        },
        effects=[
            {
                "op": "choose_non_exhaust_pile_card_add_replay",
                "count": {
                    "var": "count",
                },
            }
        ],
        upgraded=False,
        upgrade_patch={}
    )