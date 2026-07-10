# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST

# 一对私有打防
def create_strikeSuzuri():
    return CardTemplate(
        card_id="card.strike_suzuri",
        name="打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 6 点伤害。",
        quantity="starting",
        owner_character_id="character.suzuri",
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
def create_defendSuzuri():
    return CardTemplate(
        card_id="card.defend_suzuri",
        name="格挡",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。",
        quantity="starting",
        owner_character_id="character.suzuri",
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
        description="获得 6 点格挡和 4 层岩层。",
        quantity="starting",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "block": 6,
            "rock_layer": 4,
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
                "op": "gain_rock_layer",
                "target": "self",
                "amount": {
                    "var": "rock_layer",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "熔离作用+",
            "description": "获得 8 点格挡和 6 层岩层。",
            "card_vars": {
                "block": 8,
                "rock_layer": 6,
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
        description="造成 8 点伤害。每有 5 层岩层，本次伤害增加 0.5 倍。",
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
                    "status_step_multiplier": {
                        "target": "self",
                        "status": "rock_layer",
                        "step": 5,
                        "multiplier_per_step": 0.5,
                    },
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "石刃+",
            "description": "造成 10 点伤害。每有 5 层岩层，本次伤害增加 0.5 倍。",
            "card_vars": {
                "damage": 10,
            },
        }
    )
def create_rockslide():
    return CardTemplate(
        card_id="card.rockslide",
        name="岩崩",
        card_type="attack",
        cost=1,
        target="all_enemies",
        description="消耗所有岩层。对所有敌人造成岩层数 / 10 + 1 次 6 点伤害。",
        quantity="common",
        attack_type="blunt",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "damage": 6,
            "base_times": 1,
        },
        effects=[
            {
                "op": "consume_rock_layer_to_context",
                "mode": "all",
                "context_key": "consumed_rock",
            },
            {
                "op": "deal_damage_all_enemies",
                "times": {
                    "context_var": "consumed_rock",
                    "divisor": 10,
                    "add_var": "base_times",
                },
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "岩崩+",
            "description": "消耗所有岩层。对所有敌人造成岩层数 / 10 + 2 次 6 点伤害。",
            "card_vars": {
                "base_times": 2,
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
def create_solidification():
    return CardTemplate(
        card_id="card.solidification",
        name="固结作用",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗所有岩层，获得等量格挡。",
        quantity="common",
        attack_element="earth",
        owner_character_id="character.suzuri",
        play_conditions=[
            {
                "op": "has_status_at_least",
                "status": "rock_layer",
                "amount": 1,
            }
        ],
        effects=[
            {
                "op": "consume_rock_layer_to_context",
                "mode": "all",
                "context_key": "consumed_rock",
            },
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "context_var": "consumed_rock",
                    "multiplier": 1,
                    "modifier_profile": "block",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "固结作用+",
            "description": "消耗当前岩层 60%（向上取整），获得消耗层数 2 倍的格挡。",
            "effects": [
                {
                    "op": "consume_rock_layer_to_context",
                    "mode": "ratio",
                    "ratio": 0.6,
                    "rounding": "ceil",
                    "context_key": "consumed_rock",
                },
                {
                    "op": "gain_block",
                    "target": "self",
                    "amount": {
                        "context_var": "consumed_rock",
                        "multiplier": 2,
                        "modifier_profile": "block",
                    },
                },
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
            "remove_keywords": [KEYWORD_EXHAUST],
        }
    )
def create_fossil():
    return CardTemplate(
        card_id="card.fossil",
        name="化石",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗任意数量手牌，获得等量岩层。",
        quantity="uncommon",
        owner_character_id="character.suzuri",
        card_vars={
            "draw_after": 0,
        },
        effects=[
            {
                "op": "request_fossil_exhaust_hand_gain_rock_layer",
                "draw_after": {
                    "var": "draw_after",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "化石+",
            "description": "消耗任意数量手牌，获得等量岩层。抽 1 张牌。",
            "card_vars": {
                "draw_after": 1,
            },
        }
    )

def create_rock_polishing():
    return CardTemplate(
        card_id="card.rock_polishing",
        name="岩石打磨",
        card_type="power",
        cost=2,
        target="self",
        description="每累计消耗 9 层岩层，获得 1 点敏捷。每张【岩石打磨】独立计数。",
        quantity="uncommon",
        owner_character_id="character.suzuri",
        effects=[
            {
                "op": "gain_rock_polishing_counter",
                "threshold": 9,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "岩石打磨+",
            "description": "每累计消耗 6 层岩层，获得 1 点敏捷。每张【岩石打磨】独立计数。",
            "effects": [
                {
                    "op": "gain_rock_polishing_counter",
                    "threshold": 6,
                },
            ],
        }
    )
def create_heavy_rock():
    return CardTemplate(
        card_id="card.heavy_rock",
        name="重岩",
        card_type="power",
        cost=2,
        target="self",
        description="每次获得岩层时，额外获得 2 层岩层。",
        quantity="uncommon",
        owner_character_id="character.suzuri",
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "heavy_rock",
                "amount": 1,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "重岩+",
            "cost": 1,
            "description": "费用减少 1。每次获得岩层时，额外获得 2 层岩层。",
        }
    )


#rare
def create_sedimentation():
    return CardTemplate(
        card_id="card.sedimentation",
        name="沉积作用",
        card_type="power",
        cost=2,
        target="self",
        description="每回合结束时，获得 1 层岩层。",
        quantity="rare",
        owner_character_id="character.suzuri",
        card_vars={
            "rock_layer": 1,
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "sedimentation",
                "amount": {
                    "var": "rock_layer",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "沉积作用+",
            "description": "每回合结束时，获得 2 层岩层。",
            "card_vars": {
                "rock_layer": 2,
            },
        }
    )
def create_quartz_ritual():
    return CardTemplate(
        card_id="card.quartz_ritual",
        name="石英祭仪",
        card_type="power",
        cost=3,
        target="self",
        description="每回合开始时，本场战斗费用上限增加 1。地属性攻击牌伤害增加 0.5 倍。",
        quantity="rare",
        attack_element="earth",
        owner_character_id="character.suzuri",
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "quartz_ritual",
                "amount": 1,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "石英祭仪+",
            "cost": 2,
            "description": "费用减少 1。每回合开始时，本场战斗费用上限增加 1。地属性攻击牌伤害增加 0.5 倍。",
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
