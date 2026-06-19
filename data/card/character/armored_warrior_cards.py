# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE
)
#普通 攻击 common attack 
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
def create_clothesline():
    return CardTemplate(
        card_id="card.clothesline",
        name="金刚臂",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 12 点伤害。赋予 2t 虚弱。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 12,
            "weak": 2
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
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "weak",
                "amount": {
                    "var": "weak"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "金刚臂+",
            "description": "造成 14 点伤害。赋予 3t 虚弱。",
            "card_vars": {
                "damage": 14,
                "weak": 3
            },
        }
    )
def create_heavy_blade():
    return CardTemplate(
        card_id="card.heavy_blade",
        name="重刃",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 14 点伤害，力量在重刃上发挥 3 倍效果。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "base_damage": 14,
            "strength_multiplier": 2
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "base_damage",
                    "scaling": [
                        {
                            "stat": "strength",
                            "multiplier_var": "strength_multiplier"
                        }
                    ],
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "重刃+",
            "description": "造成 14 点伤害，力量在重刃上发挥 5 倍效果。",
            "card_vars": {
                "strength_multiplier": 4
            },
        }
    )
def create_anger():
    return CardTemplate(
        card_id="card.anger",
        name="愤怒",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 6 点伤害。在弃牌堆放入一张此牌的复制品。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 6,
            "copy_count": 1
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
                "op": "add_copy_to_discard",
                "amount": {
                    "var": "copy_count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "愤怒+",
            "description": "造成 8 点伤害。在弃牌堆放入一张此牌的复制品。",
            "card_vars": {
                "damage": 8
            },
        }
    )
def create_double_strike():
    return CardTemplate(
        card_id="card.double_strike",
        name="双重打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 5 点伤害 2 次。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5,
            "repeat": 2
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "times": {
                    "var": "repeat"
                },
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "双重打击+",
            "description": "造成 7 点伤害 2 次。",
            "card_vars": {
                "damage": 7
            },
        }
    )
def create_sword_boomerang():
    return CardTemplate(
        card_id="card.sword_boomerang",
        name="飞剑回旋镖",
        card_type="attack",
        cost=1,
        target="random_enemy",
        description="对随机敌人造成 3 点伤害 3 次。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 3,
            "repeat": 3
        },
        effects=[
            {
                "op": "deal_damage_random_enemies",
                "times": {
                    "var": "repeat"
                },
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "飞剑回旋镖+",
            "description": "对随机敌人造成 3 点伤害 4 次。",
            "card_vars": {
                "repeat": 4
            },
        }
    )
def create_thunderclap():
    return CardTemplate(
        card_id="card.thunderclap",
        name="闪电霹雳",
        card_type="attack",
        cost=1,
        target="all_enemies",
        description="对所有敌人造成 4 点伤害，赋予 1t 易伤。",
        quantity="common",
        attack_type="magic",
        attack_element="thunder",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 4,
            "vulnerable": 1
        },
        effects=[
            {
                "op":"deal_damage_all_enemies",
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
            "name":"闪电霹雳+",
            "description":"对所有敌人造成 7 点伤害，赋予 1t 易伤。",
            "card_vars":{
                "damage": 7
            },
        }
    )
def create_cleave():
    return CardTemplate(
        card_id="card.cleave",
        name="顺劈斩",
        card_type="attack",
        cost=1,
        target="all_enemies",
        description="对所有敌人造成 8 点伤害。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 8
        },
        effects=[
            {
                "op":"deal_damage_all_enemies",
                "amount":{
                    "base_var":"damage",
                    "modifier_profile":"attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"顺劈斩+",
            "description":"对所有敌人造成 11 点伤害。",
            "card_vars":{
                "damage": 11
            },
        }
    )
def create_iron_wave():
    return CardTemplate(
        card_id="card.iron_wave",
        name="铁斩波",
        card_type="attack",
        cost=1,
        target="enemy",
        description="获得 5 点格挡。造成 5 点伤害。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5,
            "block": 5
        },
        effects=[
            {
                "op":"gain_block",
                "target":"self",
                "amount":{
                    "var": "block",
                    "modifier_profile": "block"
                }
            },
            {
                "op":"deal_damage",
                "target":"selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"铁斩波+",
            "description":"获得 7 点格挡。造成 7 点伤害。",
            "card_vars":{
                "damage": 7,
                "block": 7
            },
        }
    )
def create_wild_strike():
    return CardTemplate(
        card_id="card.wild_strike",
        name="狂野打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 12 点伤害。在抽牌堆中加入 1 张【伤口】。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 12,
            "wound_count": 1
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
                "op": "add_card_to_draw_pile",
                "card_id": "card.status.wound",
                "amount": {
                    "var": "wound_count"
                },
                "shuffle": True
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "狂野打击+",
            "description": "造成 17 点伤害。在抽牌堆中加入 1 张【伤口】。",
            "card_vars": {
                "damage": 17
            },
        }
    )
def create_pommel_strike():
    return CardTemplate(
        card_id="card.pommel_strike",
        name="剑柄打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 9 点伤害。抽 1 张牌。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 9,
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
            "name": "剑柄打击+",
            "description": "造成 10 点伤害。抽 2 张牌。",
            "card_vars": {
                "damage": 10,
                "draw": 2
            },
        }
    )
def create_perfected_strike():
    return CardTemplate(
        card_id="card.perfected_strike",
        name="完美打击",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 6 点伤害。抽牌堆、手牌和弃牌堆中每有 1 张名称包含“打击”的牌，伤害 +2。此牌也会为自身增加伤害。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 6,
            "strike_bonus": 2
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "name_count_bonus": {
                        "name_contains": "打击",
                        "piles": [
                            "draw_pile",
                            "hand",
                            "discard_pile"
                        ],
                        "include_self": True,
                        "bonus_var": "strike_bonus"
                    },
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "完美打击+",
            "description": "造成 6 点伤害。抽牌堆、手牌和弃牌堆中每有 1 张名称包含“打击”的牌，伤害 +3。此牌也会为自身增加伤害。",
            "card_vars": {
                "strike_bonus": 3
            },
        }
    )
def create_headbutt():
    return CardTemplate(
        card_id="card.headbutt",
        name="头槌",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 9 点伤害。选择弃牌堆中的 1 张牌放到抽牌堆顶。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 9
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
                "op": "request_discard_to_draw_top"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "头槌+",
            "description": "造成 12 点伤害。选择弃牌堆中的 1 张牌放到抽牌堆顶。",
            "card_vars": {
                "damage": 12
            },
        }
    )
def create_body_slam():
    return CardTemplate(
        card_id="card.body_slam",
        name="全身撞击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成等同于当前格挡值的伤害。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "current_block": True,
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "全身撞击+",
            "cost": 0,
            "description": "造成等同于当前格挡值的伤害。"
        }
    )
def create_clash():
    return CardTemplate(
        card_id="card.clash",
        name="交锋",
        card_type="attack",
        cost=0,
        target="enemy",
        description="只能在手牌中的所有牌都是攻击牌时打出。造成 14 点伤害。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 14
        },
        play_conditions=[
            {
                "op": "hand_all_cards_are_type",
                "card_type": "attack"
            }
        ],
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
            "name": "交锋+",
            "description": "只能在手牌中的所有牌都是攻击牌时打出。造成 18 点伤害。",
            "card_vars": {
                "damage": 18
            },
        }
    )

#普通 技能 common skill
def create_havoc():
    return CardTemplate(
        card_id="card.havoc",
        name="破灭",
        card_type="skill",
        cost=1,
        target="none",
        description="打出抽牌堆顶部的牌，然后将其消耗。",
        quantity="common",
        owner_character_id="character.armored_warrior",
        card_vars={},
        effects=[
            {
                "op": "play_draw_pile_top_and_exhaust"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "破灭+",
            "cost": 0,
            "description": "打出抽牌堆顶部的牌，然后将其消耗。"
        }
    )
def create_shrug_it_off():
    return CardTemplate(
        card_id="card.shrug_it_off",
        name="耸肩无视",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 8 点格挡。抽 1 张牌。",
        quantity="common",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 8,
            "draw": 1
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block"
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
            "name": "耸肩无视+",
            "description": "获得 11 点格挡。抽 1 张牌。",
            "card_vars": {
                "block": 11
            },
        }
    )
def create_true_grit():
    return CardTemplate(
        card_id="card.true_grit",
        name="坚毅",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 7 点格挡。随机消耗 1 张手牌。",
        quantity="common",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 7
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block"
                }
            },
            {
                "op": "exhaust_random_hand_card"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "坚毅+",
            "description": "获得 9 点格挡。选择 1 张手牌消耗。",
            "card_vars": {
                "block": 9
            },
            "effects": [
                {
                    "op": "gain_block",
                    "target": "self",
                    "amount": {
                        "var": "block",
                        "modifier_profile": "block"
                    }
                },
                {
                    "op": "request_exhaust_hand_card"
                }
            ]
        }
    )
def create_warcry():
    return CardTemplate(
        card_id="card.warcry",
        name="战吼",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 1 张牌。选择 1 张手牌放到抽牌堆顶。消耗。",
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
            },
            {
                "op": "request_hand_to_draw_top"
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "战吼+",
            "description": "抽 2 张牌。选择 1 张手牌放到抽牌堆顶。消耗。",
            "card_vars": {
                "draw": 2
            },
        }
    )
def create_armaments():
    return CardTemplate(
        card_id="card.armaments",
        name="武装",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。在本场战斗中升级手牌中的 1 张牌。",
        quantity="common",
        owner_character_id="character.armored_warrior",
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
            },
            {
                "op": "request_upgrade_hand_card"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "武装+",
            "description": "获得 5 点格挡。在本场战斗中升级手牌中的所有牌。",
            "effects": [
                {
                    "op": "gain_block",
                    "target": "self",
                    "amount": {
                        "var": "block",
                        "modifier_profile": "block"
                    }
                },
                {
                    "op": "upgrade_cards",
                    "scope": "hand",
                    "mode": "all",
                    "temporary": True
                }
            ]
        }
    )
def create_flex():
    return CardTemplate(
        card_id="card.flex",
        name="活动肌肉",
        card_type="skill",
        cost=0,
        target="self",
        description="获得 2 点力量。回合结束时，失去 2 点力量。",
        quantity="common",
        owner_character_id="character.armored_warrior",
        card_vars={
            "strength": 2
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "strength",
                "amount": {
                    "var": "strength"
                }
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "flex",
                "amount": {
                    "var": "strength"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "活动肌肉+",
            "description": "获得 4 点力量。回合结束时，失去 4 点力量。",
            "card_vars": {
                "strength": 4
            },
        }
    )

#罕见 攻击 uncommon attack
def create_whirlwind():
    return CardTemplate(
        card_id="card.whirlwind",
        name="旋风斩",
        card_type="attack",
        cost="X",
        target="all_enemies",
        description="消耗所有费用。对所有敌人造成 5 点伤害 X 次。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5
        },
        effects=[
            {
                "op": "deal_damage_all_enemies",
                "times": {
                    "x_var": "x"
                },
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "旋风斩+",
            "description": "消耗所有费用。对所有敌人造成 8 点伤害 X+1 次。",
            "card_vars": {
                "damage": 8
            },
            "x_rules": [
                {
                    "op": "add",
                    "amount": 1
                }
            ],
        }
    )
def create_uppercut():
    return CardTemplate(
        card_id="card.uppercut",
        name="上勾拳",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成13点伤害。赋予 1t 虚弱。赋予 1t 易伤。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 13,
            "weak": 1,
            "vulnerable": 1
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
                "status":"weak",
                "amount":{
                    "var":"weak"
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
            "name":"上勾拳+",
            "description":"造成 13 点伤害。赋予 2t 虚弱。赋予 2t 易伤。",
            "card_vars":{
                "weak": 2,
                "vulnerable": 2
            },
        }
    )
def create_pummel():
    return CardTemplate(
        card_id="card.pummel",
        name="连续拳",
        card_type="attack",
        cost=1,
        target="enemy",
        description="消耗。造成 2 点伤害 4 次。",
        keywords=[KEYWORD_EXHAUST],
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 2,
            "repeat": 4
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "times": {
                    "var": "repeat"
                },
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "连续拳+",
            "description": "消耗。造成 2 点伤害 5 次。",
            "card_vars": {
                "repeat": 5
            },
        }
    )
def create_carnage():
    return CardTemplate(
        card_id="card.carnage",
        name="残杀",
        card_type="attack",
        cost=2,
        target="enemy",
        description="虚无。造成 20 点伤害。",
        keywords=[KEYWORD_ETHEREAL],
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 20
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
            "name": "残杀+",
            "description": "虚无。造成 28 点伤害。",
            "card_vars": {
                "damage": 28
            },
        }
    )
def create_reckless_charge():
    return CardTemplate(
        card_id="card.reckless_charge",
        name="无谋冲锋",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 7 点伤害。在抽牌堆中加入 1 张【眩晕】。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 7,
            "dazed_count": 1
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
                "op": "add_card_to_draw_pile",
                "card_id": "card.status.dazed",
                "amount": {
                    "var": "dazed_count"
                },
                "shuffle": True
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "无谋冲锋+",
            "description": "造成 10 点伤害。在抽牌堆中加入 1 张【眩晕】。",
            "card_vars": {
                "damage": 10
            },
        }
    )
def create_blood_for_blood():
    return CardTemplate(
        card_id="card.blood_for_blood",
        name="以血还血",
        card_type="attack",
        cost=4,
        target="enemy",
        description="本场战斗中你每失去生命一次，本牌耗能减少 1。造成 18 点伤害。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 18
        },
        cost_rules=[
            {
                "op": "reduce_by_player_life_loss_count",
                "amount_per_loss": 1,
                "min_cost": 0
            }
        ],
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
            "name": "以血还血+",
            "cost": 3,
            "description": "本场战斗中你每失去生命一次，本牌耗能减少 1。造成 22 点伤害。",
            "card_vars": {
                "damage": 22
            },
        }
    )
def create_dropkick():
    return CardTemplate(
        card_id="card.dropkick",
        name="飞身踢",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 5 点伤害。如果敌人有易伤，获得 1 点费用并抽 1 张牌。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5,
            "energy": 1,
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
                "op": "if_target_has_status",
                "target": "selected_enemy",
                "status": "vulnerable",
                "effects": [
                    {
                        "op": "gain_energy",
                        "amount": {
                            "var": "energy"
                        }
                    },
                    {
                        "op": "draw_cards",
                        "amount": {
                            "var": "draw"
                        }
                    }
                ]
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "飞身踢+",
            "description": "造成 8 点伤害。如果敌人有易伤，获得 1 点费用并抽 1 张牌。",
            "card_vars": {
                "damage": 8
            },
        }
    )
def create_hemokinesis():
    return CardTemplate(
        card_id="card.hemokinesis",
        name="御血术",
        card_type="attack",
        cost=1,
        target="enemy",
        description="失去 2 点生命。造成 15 点伤害。",
        quantity="uncommon",
        attack_type="magic",
        owner_character_id="character.armored_warrior",
        card_vars={
            "hp_loss": 2,
            "damage": 15
        },
        effects=[
            {
                "op": "lose_hp",
                "target": "self",
                "amount": {
                    "var": "hp_loss"
                }
            },
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
            "name": "御血术+",
            "description": "失去 2 点生命。造成 20 点伤害。",
            "card_vars": {
                "damage": 20
            },
        }
    )
def create_rampage():
    return CardTemplate(
        card_id="card.rampage",
        name="暴走",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 8 点伤害。本场战斗中，每打出一次，本牌伤害增加 5。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 8,
            "increase": 5
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
                "op": "increase_card_var",
                "var": "damage",
                "amount": {
                    "var": "increase"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "暴走+",
            "description": "造成 8 点伤害。本场战斗中，每打出一次，本牌伤害增加 8。",
            "card_vars": {
                "increase": 8
            },
        }
    )
def create_searing_blow():
    return CardTemplate(
        card_id="card.searing_blow",
        name="灼热攻击",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 12 点伤害。能被多次升级。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 12
        },
        multi_upgrade=True,
        upgrade_count=0,
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
            "multi_upgrade": True,
            "damage_var": "damage",
            "damage_bonus_offset": 3,
            "description_template": "造成 {} 点伤害。能被多次升级。"
        }
    )
def create_sever_soul():
    return CardTemplate(
        card_id="card.sever_soul",
        name="断魂斩",
        card_type="attack",
        cost=2,
        target="enemy",
        description="消耗手牌中所有非攻击牌。造成 16 点伤害。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 16
        },
        effects=[
            {
                "op": "exhaust_non_attack_hand_cards"
            },
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
            "name": "断魂斩+",
            "description": "消耗手牌中所有非攻击牌。造成 22 点伤害。",
            "card_vars": {
                "damage": 22
            },
        }
    )

#罕见 技能 uncommon skill
def create_immolate_history():
    return CardTemplate(
        card_id="card.immolate_history",
        name="燔祭·旧",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗 1 张手牌。如果这张牌是诅咒牌或状态牌，对所有敌人造成 10 点伤害。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 10
        },
        effects=[
            {
                "op": "request_exhaust_hand_card_then_if_type",
                "card_types": [
                    "curse",
                    "status"
                ],
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
            "name": "燔祭·旧+",
            "description": "消耗 1 张手牌。如果这张牌是诅咒牌或状态牌，对所有敌人造成 15 点伤害。",
            "card_vars": {
                "damage": 15
            },
        }
    )
def create_shockwave():
    return CardTemplate(
        card_id="card.shockwave",
        name="震荡波",
        card_type="skill",
        cost=2,
        target="all_enemies",
        description="消耗。给予所有敌人 3 层虚弱和易伤。",
        quantity="uncommon",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={
            "weak": 3,
            "vulnerable": 3,
        },
        effects=[
            {
                "op":"gain_status",
                "target":"all_enemies",
                "status":"weak",
                "amount":{
                    "var":"weak"
                }
            },
            {
                "op":"gain_status",
                "target":"all_enemies",
                "status":"vulnerable",
                "amount":{
                    "var":"vulnerable"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "震荡波+",
            "description": "消耗。给予所有敌人 5 层虚弱和易伤。",
            "card_vars": {
                "weak": 5,
                "vulnerable": 5,
            },
        }
    )
def create_intimidate():
    return CardTemplate(
        card_id="card.intimidate",
        name="威吓",
        card_type="skill",
        cost=0,
        target="all_enemies",
        description="消耗。给予所有敌人 1 层虚弱.",
        quantity="uncommon",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={
            "weak": 1,
        },
        effects=[
            {
                "op":"gain_status",
                "target":"all_enemies",
                "status":"weak",
                "amount":{
                    "var":"weak"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "威吓+",
            "description": "消耗。给予所有敌人 2 层虚弱和易伤。",
            "card_vars": {
                "weak": 2,
            },
        }
    )
def create_battle_trance():
    return CardTemplate(
        card_id="card.battle_trance",
        name="战斗专注",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 3 张牌。本回合内不能再抽任何牌。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "draw": 3,
            "no_draw": 1
        },
        effects=[
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "no_draw",
                "amount": {
                    "var": "no_draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "战斗专注+",
            "description": "抽 4 张牌。本回合内不能再抽任何牌。",
            "card_vars": {
                "draw": 4
            },
        }
    )
def create_bloodletting():
    return CardTemplate(
        card_id="card.bloodletting",
        name="放血",
        card_type="skill",
        cost=0,
        target="self",
        description="失去 3 点生命。获得 2 点能量。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "hp_loss": 3,
            "energy": 2
        },
        effects=[
            {
                "op": "lose_hp",
                "target": "self",
                "amount": {
                    "var": "hp_loss"
                }
            },
            {
                "op": "gain_energy",
                "amount": {
                    "var": "energy"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "放血+",
            "description": "失去 3 点生命。获得 3 点能量。",
            "card_vars": {
                "energy": 3
            },
        }
    )
def create_burning_pact():
    return CardTemplate(
        card_id="card.burning_pact",
        name="燃烧契约",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗 1 张手牌。抽 2 张牌。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "draw": 2
        },
        effects=[
            {
                "op": "request_exhaust_hand_card_then_effects",
                "effects": [
                    {
                        "op": "draw_cards",
                        "amount": {
                            "var": "draw"
                        }
                    }
                ]
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "燃烧契约+",
            "description": "消耗 1 张手牌。抽 3 张牌。",
            "card_vars": {
                "draw": 3
            },
        }
    )
def create_disarm():
    return CardTemplate(
        card_id="card.disarm",
        name="缴械",
        card_type="skill",
        cost=1,
        target="enemy",
        description="消耗。使敌人降低 2 点力量。",
        quantity="uncommon",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={
            "strength_down": -2
        },
        effects=[
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "strength",
                "amount": {
                    "var": "strength_down"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "缴械+",
            "description": "消耗。使敌人降低 3 点力量。",
            "card_vars": {
                "strength_down": -3
            },
        }
    )
def create_dual_wield():
    return CardTemplate(
        card_id="card.dual_wield",
        name="双持",
        card_type="skill",
        cost=1,
        target="self",
        description="选择 1 张攻击牌或能力牌，添加 1 张此牌的复制品到手牌。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "copy_count": 1
        },
        effects=[
            {
                "op": "request_duplicate_hand_card",
                "card_types": [
                    "attack",
                    "power"
                ],
                "amount": {
                    "var": "copy_count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "双持+",
            "description": "选择 1 张攻击牌或能力牌，添加 2 张此牌的复制品到手牌。",
            "card_vars": {
                "copy_count": 2
            },
        }
    )
def create_entrench():
    return CardTemplate(
        card_id="card.entrench",
        name="巩固",
        card_type="skill",
        cost=2,
        target="self",
        description="使你的格挡翻倍。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={},
        effects=[
            {
                "op": "double_block"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "巩固+",
            "cost": 1,
            "description": "使你的格挡翻倍。",
        }
    )
def create_flame_barrier():
    return CardTemplate(
        card_id="card.flame_barrier",
        name="火焰屏障",
        card_type="skill",
        cost=2,
        target="self",
        description="获得 12 点格挡。本回合每受到一次攻击，对攻击者造成 4 点伤害。",
        quantity="uncommon",
        attack_element="fire",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 12,
            "temporary_thorns": 4
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block"
                }
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "temporary_thorns",
                "amount": {
                    "var": "temporary_thorns"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "火焰屏障+",
            "description": "获得 16 点格挡。本回合每受到一次攻击，对攻击者造成 6 点伤害。",
            "card_vars": {
                "block": 16,
                "temporary_thorns": 6
            },
        }
    )
def create_ghostly_armor():
    return CardTemplate(
        card_id="card.ghostly_armor",
        name="幽灵铠甲",
        card_type="skill",
        cost=1,
        target="self",
        description="虚无。获得 10 点格挡。",
        quantity="uncommon",
        keywords=[KEYWORD_ETHEREAL],
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 10
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
            "name": "幽灵铠甲+",
            "description": "虚无。获得 13 点格挡。",
            "card_vars": {
                "block": 13
            },
        }
    )
def create_infernal_blade():
    return CardTemplate(
        card_id="card.infernal_blade",
        name="地狱之刃",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗。增加 1 张随机攻击牌到你的手牌。这张牌在本回合耗能变为 0。",
        quantity="uncommon",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={},
        effects=[
            {
                "op": "add_random_attack_to_hand_temp_cost_zero",
                "owner_character_id": "character.armored_warrior",
                "exclude_card_ids": [
                    "card.feed",
                    "card.death_reaper",
                    "card.reaper"
                ]
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "地狱之刃+",
            "cost": 0,
            "description": "消耗。增加 1 张随机攻击牌到你的手牌。这张牌在本回合耗能变为 0。",
        }
    )
def create_power_through():
    return CardTemplate(
        card_id="card.power_through",
        name="硬撑",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 15 点格挡。在手牌中添加 2 张【伤口】。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 15,
            "wound_count": 2
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block"
                }
            },
            {
                "op": "add_card_to_hand",
                "card_id": "card.status.wound",
                "amount": {
                    "var": "wound_count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "硬撑+",
            "description": "获得 20 点格挡。在手牌中添加 2 张【伤口】。",
            "card_vars": {
                "block": 20
            },
        }
    )
def create_rage():
    return CardTemplate(
        card_id="card.rage",
        name="狂怒",
        card_type="skill",
        cost=0,
        target="self",
        description="本回合每打出一张攻击牌，获得 3 点格挡。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "rage": 3
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "rage",
                "amount": {
                    "var": "rage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "狂怒+",
            "description": "本回合每打出一张攻击牌，获得 5 点格挡。",
            "card_vars": {
                "rage": 5
            },
        }
    )
def create_second_wind():
    return CardTemplate(
        card_id="card.second_wind",
        name="重振精神",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗手牌中所有非攻击牌。每消耗 1 张，获得 5 点格挡。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block_per_card": 5
        },
        effects=[
            {
                "op": "exhaust_non_attack_hand_cards_gain_block_per_card",
                "block_per_card": {
                    "var": "block_per_card",
                    "modifier_profile": "block"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "重振精神+",
            "description": "消耗手牌中所有非攻击牌。每消耗 1 张，获得 7 点格挡。",
            "card_vars": {
                "block_per_card": 7
            },
        }
    )
def create_seeing_red():
    return CardTemplate(
        card_id="card.seeing_red",
        name="盛怒",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗。获得 2 点能量。",
        quantity="uncommon",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={
            "energy": 2
        },
        effects=[
            {
                "op": "gain_energy",
                "amount": {
                    "var": "energy"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "盛怒+",
            "cost": 0,
            "description": "消耗。获得 2 点能量。",
        }
    )
def create_sentinel():
    return CardTemplate(
        card_id="card.sentinel",
        name="哨卫",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。如果这张牌被消耗，获得 2 点能量。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 5,
            "energy": 2
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
        exhaust_effects=[
            {
                "op": "gain_energy",
                "amount": {
                    "var": "energy"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "哨卫+",
            "description": "获得 8 点格挡。如果这张牌被消耗，获得 3 点能量。",
            "card_vars": {
                "block": 8,
                "energy": 3
            },
        }
    )
def create_spot_weakness():
    return CardTemplate(
        card_id="card.spot_weakness",
        name="观察弱点",
        card_type="skill",
        cost=1,
        target="enemy",
        description="如果敌人的意图是攻击，获得 3 点力量。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "strength": 3
        },
        effects=[
            {
                "op": "gain_status_if_enemy_intent_attack",
                "target": "selected_enemy",
                "status": "strength",
                "amount": {
                    "var": "strength"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "观察弱点+",
            "description": "如果敌人的意图是攻击，获得 4 点力量。",
            "card_vars": {
                "strength": 4
            },
        }
    )

#罕见 能力 uncommon power
def create_combust():
    return CardTemplate(
        card_id="card.combust",
        name="自燃",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合结束时，你失去 1 点生命，对所有敌人造成 5 点伤害。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "combust",
                "amount": {
                    "var": "damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "自燃+",
            "description": "在你的回合结束时，你失去 1 点生命，对所有敌人造成 7 点伤害。",
            "card_vars": {
                "damage": 7
            },
        }
    )
def create_dark_embrace():
    return CardTemplate(
        card_id="card.dark_embrace",
        name="黑暗之拥",
        card_type="power",
        cost=2,
        target="self",
        description="每当有一张牌被消耗时，抽 1 张牌。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "draw": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "dark_embrace",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "黑暗之拥+",
            "cost": 1,
            "description": "每当有一张牌被消耗时，抽 1 张牌。",
        }
    )
def create_feel_no_pain():
    return CardTemplate(
        card_id="card.feel_no_pain",
        name="无惧疼痛",
        card_type="power",
        cost=1,
        target="self",
        description="每当有一张牌被消耗，获得 3 点格挡。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 3
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "feel_no_pain",
                "amount": {
                    "var": "block"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "无惧疼痛+",
            "description": "每当有一张牌被消耗，获得 4 点格挡。",
            "card_vars": {
                "block": 4
            },
        }
    )
def create_fire_breathing():
    return CardTemplate(
        card_id="card.fire_breathing",
        name="火焰吐息",
        card_type="power",
        cost=1,
        target="self",
        description="每当你抽到一张状态牌或诅咒牌时，对所有敌人造成 6 点伤害。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 6
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "fire_breathing",
                "amount": {
                    "var": "damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "火焰吐息+",
            "description": "每当你抽到一张状态牌或诅咒牌时，对所有敌人造成 10 点伤害。",
            "card_vars": {
                "damage": 10
            },
        }
    )
def create_fire_breathing_history():
    return CardTemplate(
        card_id="card.fire_breathing_history",
        name="火焰吐息·旧",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合结束时，你这一回合内每出过一张攻击牌，就对所有敌人造成 1 点伤害。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage_per_attack": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "fire_breathing_history",
                "amount": {
                    "var": "damage_per_attack"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "火焰吐息·旧+",
            "cost": 0,
            "description": "在你的回合结束时，你这一回合内每出过一张攻击牌，就对所有敌人造成 1 点伤害。",
        }
    )
def create_inflame():
    return CardTemplate(
        card_id="card.inflame",
        name="燃烧",
        card_type="power",
        cost=1,
        target="self",
        description="获得 2 点力量。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "strength": 2
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "strength",
                "amount": {
                    "var": "strength"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "燃烧+",
            "description": "获得 3 点力量。",
            "card_vars": {
                "strength": 3
            },
        }
    )
def create_metallicize():
    return CardTemplate(
        card_id="card.metallicize",
        name="金属化",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合结束时，获得 3 点格挡。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 3
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "metallicize",
                "amount": {
                    "var": "block"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "金属化+",
            "description": "在你的回合结束时，获得 4 点格挡。",
            "card_vars": {
                "block": 4
            },
        }
    )
def create_rupture():
    return CardTemplate(
        card_id="card.rupture",
        name="撕裂",
        card_type="power",
        cost=1,
        target="self",
        description="每当你从一张牌中失去生命时，获得 1 点力量。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "strength": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "rupture",
                "amount": {
                    "var": "strength"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "撕裂+",
            "description": "每当你从一张牌中失去生命时，获得 2 点力量。",
            "card_vars": {
                "strength": 2
            },
        }
    )
def create_evolve():
    return CardTemplate(
        card_id="card.evolve",
        name="进化",
        card_type="power",
        cost=1,
        target="self",
        description="每当你抽到一张状态牌时，抽 1 张牌。",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        card_vars={
            "draw": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "evolve",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "进化+",
            "description": "每当你抽到一张状态牌时，抽 2 张牌。",
            "card_vars": {
                "draw": 2
            },
        }
    )

#稀有 攻击 rare attack
def create_bludgeon():
    return CardTemplate(
        card_id="card.bludgeon",
        name="重锤",
        card_type="attack",
        cost=3,
        target="enemy",
        description="造成 32 点伤害。",
        quantity="rare",
        attack_type="blunt",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 32
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
            "name":"重锤+",
            "description":"造成 42 点伤害。",
            "card_vars":{
                "damage": 42
            }
        }
    )
def create_feed():
    return CardTemplate(
        card_id="card.feed",
        name="狂宴",
        card_type="attack",
        cost=1,
        target="enemy",
        description="消耗。造成 10 点伤害。若杀死了不为爪牙的敌人，获得 3 点最大生命。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 10,
            "max_hp_gain": 3
        },
        effects=[
            {
                "op": "deal_damage_gain_max_hp_on_non_minion_kill",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                },
                "max_hp_gain": {
                    "var": "max_hp_gain"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "狂宴+",
            "description": "消耗。造成 12 点伤害。若杀死了不为爪牙的敌人，获得 4 点最大生命。",
            "card_vars": {
                "damage": 12,
                "max_hp_gain": 4
            },
        }
    )
def create_fiend_fire():
    return CardTemplate(
        card_id="card.fiend_fire",
        name="恶魔之焰",
        card_type="attack",
        cost=2,
        target="enemy",
        description="消耗。消耗所有手牌。每消耗 1 张牌，对目标敌人造成 7 点伤害。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        attack_type="magic",
        attack_element="fire",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 7
        },
        effects=[
            {
                "op": "exhaust_all_hand_cards_then_attack_per_card",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "恶魔之焰+",
            "description": "消耗。消耗所有手牌。每消耗 1 张牌，对目标敌人造成 10 点伤害。",
            "card_vars": {
                "damage": 10
            },
        }
    )
def create_immolate():
    return CardTemplate(
        card_id="card.immolate",
        name="燔祭",
        card_type="attack",
        cost=2,
        target="all_enemies",
        description="对所有敌人造成 21 点伤害。将 1 张【灼伤】放入弃牌堆。",
        quantity="rare",
        attack_type="magic",
        attack_element="fire",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 21,
            "burn_count": 1
        },
        effects=[
            {
                "op": "deal_damage_all_enemies",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            },
            {
                "op": "add_card_to_discard_pile",
                "card_id": "card.status.burn",
                "amount": {
                    "var": "burn_count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "燔祭+",
            "description": "对所有敌人造成 28 点伤害。将 1 张【灼伤】放入弃牌堆。",
            "card_vars": {
                "damage": 28
            },
        }
    )
def create_death_reaper():
    return CardTemplate(
        card_id="card.death_reaper",
        name="死亡收割",
        card_type="attack",
        cost=2,
        target="all_enemies",
        description="消耗。对所有敌人造成 4 点伤害。未被格挡的伤害将回复你的生命。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        attack_type="slash",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 4
        },
        effects=[
            {
                "op": "deal_damage_all_enemies_heal_unblocked",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "死亡收割+",
            "description": "消耗。对所有敌人造成 5 点伤害。未被格挡的伤害将回复你的生命。",
            "card_vars": {
                "damage": 5
            },
        }
    )

#稀有 技能 rare skill
def create_impervious():
    return CardTemplate(
        card_id="card.impervious",
        name="岿然不动",
        card_type="skill",
        cost=2,
        target="self",
        description="消耗。获得 30 点格挡。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={
            "block": 30
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block"
                }
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "岿然不动+",
            "description": "消耗。获得 40 点格挡。",
            "card_vars": {
                "block": 40
            },
        }
    )
def create_double_tap():
    return CardTemplate(
        card_id="card.double_tap",
        name="双发",
        card_type="skill",
        cost=1,
        target="self",
        description="本回合内，你打出的下一张攻击牌会打出 2 次。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "double_tap",
                "amount": {
                    "var": "count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "双发+",
            "description": "本回合内，你打出的下 2 张攻击牌会打出 2 次。",
            "card_vars": {
                "count": 2
            },
        }
    )
def create_exhume():
    return CardTemplate(
        card_id="card.exhume",
        name="发掘",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗。选择 1 张已消耗的牌，将其放入你的手牌。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={},
        effects=[
            {
                "op": "request_exhume_card"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "发掘+",
            "cost": 0,
            "description": "消耗。选择 1 张已消耗的牌，将其放入你的手牌。",
        }
    )
def create_limit_break():
    return CardTemplate(
        card_id="card.limit_break",
        name="突破极限",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗。将你的力量翻倍。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={},
        effects=[
            {
                "op": "double_status",
                "target": "self",
                "status": "strength"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "突破极限+",
            "description": "将你的力量翻倍。",
            "remove_keywords": [
                KEYWORD_EXHAUST
            ],
        }
    )
def create_offering():
    return CardTemplate(
        card_id="card.offering",
        name="祭品",
        card_type="skill",
        cost=0,
        target="self",
        description="消耗。失去 6 点生命。获得 2 点能量。抽 3 张牌。",
        quantity="rare",
        keywords=[KEYWORD_EXHAUST],
        owner_character_id="character.armored_warrior",
        card_vars={
            "hp_loss": 6,
            "energy": 2,
            "draw": 3
        },
        effects=[
            {
                "op": "lose_hp",
                "target": "self",
                "amount": {
                    "var": "hp_loss"
                }
            },
            {
                "op": "gain_energy",
                "amount": {
                    "var": "energy"
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
            "name": "祭品+",
            "description": "消耗。失去 6 点生命。获得 2 点能量。抽 5 张牌。",
            "card_vars": {
                "draw": 5
            },
        }
    )

#稀有 能力 rare power
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
def create_barricade():
    return CardTemplate(
        card_id="card.barricade",
        name="壁垒",
        card_type="power",
        cost=3,
        target="self",
        description="格挡不再在你的回合开始时消失。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "barricade": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "barricade",
                "amount": {
                    "var": "barricade"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "壁垒+",
            "cost": 2,
            "description": "格挡不再在你的回合开始时消失。",
        }
    )
def create_berserk():
    return CardTemplate(
        card_id="card.berserk",
        name="狂暴",
        card_type="power",
        cost=0,
        target="self",
        description="获得 2 层易伤。每回合开始时，费用上限增加 1。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "vulnerable": 2,
            "berserk": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "vulnerable",
                "amount": {
                    "var": "vulnerable"
                }
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "berserk",
                "amount": {
                    "var": "berserk"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "狂暴+",
            "description": "获得 1 层易伤。每回合开始时，费用上限增加 1。",
            "card_vars": {
                "vulnerable": 1
            },
        }
    )
def create_brutality():
    return CardTemplate(
        card_id="card.brutality",
        name="残暴",
        card_type="power",
        cost=0,
        target="self",
        description="在你的回合开始时，你失去 1 点生命，抽 1 张牌。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "brutality": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "brutality",
                "amount": {
                    "var": "brutality"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "残暴+",
            "description": "固有。在你的回合开始时，你失去 1 点生命，抽 1 张牌。",
            "add_keywords": [
                KEYWORD_INNATE
            ],
        }
    )
def create_corruption():
    return CardTemplate(
        card_id="card.corruption",
        name="腐化",
        card_type="power",
        cost=3,
        target="self",
        description="所有技能牌耗能变为 0。所有技能牌在被打出时消耗。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "corruption": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "corruption",
                "amount": {
                    "var": "corruption"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "腐化+",
            "cost": 2,
            "description": "所有技能牌耗能变为 0。所有技能牌在被打出时消耗。",
        }
    )
def create_juggernaut():
    return CardTemplate(
        card_id="card.juggernaut",
        name="势不可当",
        card_type="power",
        cost=2,
        target="self",
        description="每当你获得格挡时，对随机一名敌人造成 5 点伤害。",
        quantity="rare",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 5
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "juggernaut",
                "amount": {
                    "var": "damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "势不可当+",
            "description": "每当你获得格挡时，对随机一名敌人造成 7 点伤害。",
            "card_vars": {
                "damage": 7
            },
        }
    )

#！特别私货
def create_fire_strike():
    return CardTemplate(
        card_id="card.fire_strike",
        name="猛火打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 6 点 火属性 伤害 2 次。",
        quantity="uncommon",
        attack_type="blunt",
        attack_element="fire",
        owner_character_id="character.armored_warrior",
        card_vars={
            "damage": 6,
            "repeat": 2
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "times": {
                    "var": "repeat"
                },
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "猛火打击+",
            "description": "造成 8 点 火属性 伤害 2 次。",
            "card_vars": {
                "damage": 8
            },
        }
    )
def create_fire_zone():
    return CardTemplate(
        card_id="card.crystal_zone",
        name="烈火领域",
        card_type="skill",
        cost=2,
        target="none",
        description="场地效果变为烈火。已有烈火效果时，改为场地效果变为极·烈火，持续3t。（私货版本说明：没有遗物以太介质或者火打不要抓，我说这是2费大伤口（喂）",
        quantity="rare",
        attack_element = "fire",
        owner_character_id="character.armored_warrior",
        effects=[
            {
                "op": "set_zone"
            }
        ],
        upgraded = False, #升级降1费
        upgrade_patch={
            "name":"烈火领域+",
            "description":"费用减少1。场地效果变为烈火。已有烈火效果时，改为场地效果变为极·烈火，持续3t。",
            "cost":1
        }
    )
# 我说要不再塞个私货遗物拾起时为3张攻击牌添加火词条