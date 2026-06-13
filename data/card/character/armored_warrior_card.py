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


#罕见 技能 uncommon skill

#罕见 能力 uncommon power

#稀有 攻击 rare attack

#稀有 技能 rare skill

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
