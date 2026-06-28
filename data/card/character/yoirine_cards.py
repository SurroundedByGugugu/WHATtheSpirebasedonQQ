# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST

#starting
def create_crystal_piercing():
    return CardTemplate(
        card_id="card.crystal_piercing",
        name="晶刺",
        card_type="attack",
        cost=2,
        target="random_enemy",
        description="对随机敌人造成 2 点伤害 4 次。晶 Zone 条件下费用 -1。",
        quantity="starting",
        attack_type="piercing",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        cost_rules=[
            {
                "op": "reduce_if_active_zone",
                "element": "crystal",
                "amount": 1,
                "min_cost": 0
            }
        ],
        card_vars={
            "damage": 2,
            "repeat": 4
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
            "name": "晶刺+",
            "description": "对随机敌人造成 2 点伤害 6 次。晶 Zone 条件下费用 -1。",
            "card_vars": {
                "damage": 2,
                "repeat": 6
            },
        }
    )
def create_crystal_zone():
    return CardTemplate(
        card_id="card.crystal_zone",
        name="辉晶领域",
        card_type="skill",
        cost=2,
        target="none",
        description="场地效果变为辉晶。已有辉晶效果时，改为场地效果变为极·辉晶，持续3t。已在极·辉晶期间再次使用时，延长持续回合。",
        quantity="starting",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "set_zone"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "辉晶领域+",
            "description": "费用减少1。场地效果变为辉晶。已有辉晶效果时，改为场地效果变为极·辉晶，持续3t。已在极·辉晶期间再次使用时，延长持续回合。",
            "cost": 1
        }
    )

#common
def create_brave_bird():
    return CardTemplate(
        card_id="card.brave_bird",
        name="勇鸟",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 13 点伤害。失去 2 点生命；若有飞行，改为消耗 1 层飞行并消去自伤。",
        quantity="common",
        owner_character_id="character.yoirine",
        card_vars={
            "damage": 13,
            "self_loss": 2
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
                "op": "brave_bird_self_cost",
                "status": "flying",
                "amount": {
                    "var": "self_loss"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "勇鸟+",
            "description": "造成 17 点伤害。失去 1 点生命；若有飞行，改为消耗 1 层飞行并消去自伤。",
            "card_vars": {
                "damage": 17,
                "self_loss": 1
            }
        }
    )
def create_trace_pursuit():
    return CardTemplate(
        card_id="card.trace_pursuit",
        name="追迹",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 5 点伤害。添加 5 层深渊凝视。",
        quantity="common",
        owner_character_id="character.yoirine",
        card_vars={
            "damage": 5,
            "abyss_gaze": 5
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
                "status": "abyss_gaze",
                "amount": {
                    "var": "abyss_gaze"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "追迹+",
            "description": "造成 8 点伤害。添加 8 层深渊凝视。",
            "card_vars": {
                "damage": 8,
                "abyss_gaze": 8
            }
        }
    )

def create_crystal_thorns():
    return CardTemplate(
        card_id="card.crystal_thorns",
        name="辉晶之棘",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 3 点格挡。获得等量临时荆棘。",
        quantity="common",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        card_vars={
            "block": 3
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
                    "var": "block",
                    "modifier_profile": "block"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "辉晶之棘+",
            "description": "获得 4 点格挡。获得等量临时荆棘。",
            "card_vars": {
                "block": 4
            },
        }
    )
def create_spreading_wing():
    return CardTemplate(
        card_id="card.spreading_wing",
        name="展翼",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 2 层飞行。",
        quantity="common",
        owner_character_id="character.yoirine",
        card_vars={"flying": 2},
        effects=[{
            "op": "apply_status",
            "target": "self",
            "status": "flying",
            "amount": {"base_var": "flying"}
        }],
        upgraded=False,
        upgrade_patch={
            "name": "展翼+",
            "description": "获得 3 层飞行。",
            "card_vars": {
                "flying": 3
            },
        }
    )

#uncommon
def create_abyssal_erosion():
    return CardTemplate(
        card_id="card.abyssal_erosion",
        name="渊蚀",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 3 点伤害。本场战斗中每因自身行动失去 1 点生命，本牌伤害 +3。",
        quantity="uncommon",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "damage": 3,
            "per_hp": 3
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "player_self_action_hp_loss_total_this_battle": True,
                    "multiplier_var": "per_hp",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "渊蚀+",
            "description": "造成 4 点伤害。本场战斗中每因自身行动失去 1 点生命，本牌伤害 +4。",
            "card_vars": {
                "damage": 4,
                "per_hp": 4
            }
        }
    )

def create_crystal_cocoon():
    return CardTemplate(
        card_id="card.crystal_cocoon",
        name="晶茧",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 3 点格挡。本回合结束时，在敌人攻击完后，若你有格挡，获得 1 点力量。",
        quantity="uncommon",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        card_vars={
            "block": 3,
            "cocoon": 1
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
                "status": "crystal_cocoon",
                "amount": {
                    "var": "cocoon"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "晶茧+",
            "description": "获得 4 点格挡。本回合结束时，在敌人攻击完后，若你有格挡，获得 2 点力量。",
            "card_vars": {
                "block": 4,
                "cocoon": 2
            },
        }
    )
def create_roost():
    return CardTemplate(
        card_id="card.roost",
        name="羽栖",
        card_type="skill",
        cost=1,
        target="self",
        description="只能在有飞行时打出。消耗。获得 1 层易伤。结束当前回合。恢复 10% 最大生命值。不失去飞行层数。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        card_vars={
            "vulnerable": 1,
            "heal_percent": 0.10
        },
        play_conditions=[
            {
                "op": "has_status_at_least",
                "status": "flying",
                "amount": 1
            }
        ],
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
                "op": "heal_player_by_max_hp_percent",
                "percent": 0.10
            },
            {
                "op": "force_end_turn"
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "羽栖+",
            "description": "只能在有飞行时打出。消耗。获得 1 层易伤。结束当前回合。恢复 15% 最大生命值。不失去飞行层数。",
            "card_vars": {
                "heal_percent": 0.15
            },
            "patches": [
                {
                    "path": ["effects", 1, "percent"],
                    "value": 0.15
                }
            ]
        }
    )
def create_call_of_the_abyss():
    return CardTemplate(
        card_id="card.call_of_the_abyss",
        name="唤渊",
        card_type="skill",
        cost=0,
        target="self",
        description="消耗。抽 1 张牌。若你本回合失去过生命，额外抽 1 张牌，并获得 1 点费用。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        card_vars={
            "base_draw": 1,
            "extra_draw": 1,
            "energy": 1
        },
        effects=[
            {
                "op": "draw_gain_energy_if_player_lost_hp_this_turn",
                "base_draw": {
                    "var": "base_draw"
                },
                "extra_draw": {
                    "var": "extra_draw"
                },
                "energy": {
                    "var": "energy"
                }
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "唤渊+",
            "description": "消耗。抽 1 张牌。若你本回合失去过生命，额外抽 2 张牌，并获得 2 点费用。",
            "card_vars": {
                "extra_draw": 2,
                "energy": 2
            }
        }
    )
def create_fleeting_shadow():
    return CardTemplate(
        card_id="card.fleeting_shadow",
        name="掠影",
        card_type="skill",
        cost=0,
        target="self",
        description="触发一次阴 Zone 自伤效果，然后抽 2 张牌。",
        quantity="uncommon",
        attack_element="shade",
        skip_auto_zone_hp_loss=True,
        owner_character_id="character.yoirine",
        card_vars={
            "draw": 2
        },
        effects=[
            {
                "op": "trigger_shade_hp_loss_then_draw",
                "draw": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "掠影+",
            "description": "触发一次阴 Zone 自伤效果，然后抽 3 张牌。",
            "card_vars": {
                "draw": 3
            }
        }
    )
def create_abyss_gaze():
    return CardTemplate(
        card_id="card.abyss_gaze",
        name="深渊凝视",
        card_type="skill",
        cost=1,
        target="enemy",
        description="消耗。对目标添加 10 层深渊凝视。",
        quantity="uncommon",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "abyss_gaze": 10
        },
        effects=[
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "abyss_gaze",
                "amount": {
                    "var": "abyss_gaze"
                }
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "深渊凝视+",
            "description": "对目标添加 15 层深渊凝视。",
            "card_vars": {
                "abyss_gaze": 15
            },
            "remove_keywords": [
                KEYWORD_EXHAUST
            ]
        }
    )

def create_reminiscence():
    return CardTemplate(
        card_id="card.reminiscence",
        name="追思",
        card_type="power",
        cost=2,
        target="self",
        description="晶 Zone 下，每回合开始时额外抽 1 张牌。",
        quantity="uncommon",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        card_vars={
            "draw": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "reminiscence",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "追思+",
            "description": "晶 Zone 下，每回合开始时额外抽 2 张牌。",
            "card_vars": {
                "draw": 2
            }
        }
    )

#rare
def create_to_your_tranquility():
    return CardTemplate(
        card_id="card.to_your_tranquility",
        name="献给你的安宁",
        card_type="attack",
        cost=3,
        target="enemy",
        description="造成 28 点伤害。如果使一名生命满的敌人死亡，恢复 2 点生命。",
        quantity="rare",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "damage": 28,
            "heal": 2
        },
        effects=[
            {
                "op": "deal_damage_heal_on_full_hp_kill",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                },
                "heal": {
                    "var": "heal"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "献给你的安宁+",
            "description": "造成 38 点伤害。如果使一名生命满的敌人死亡，恢复 3 点生命。",
            "card_vars": {
                "damage": 38,
                "heal": 3
            }
        }
    )

def create_rockbound_wish():
    return CardTemplate(
        card_id="card.rockbound_wish",
        name="磐愿",
        card_type="skill",
        cost=0,
        target="self",
        description="消耗。消耗所有状态牌和诅咒牌。失去等于消耗牌数量 1/2 的生命，获得等于消耗牌数量 1/4 的力量和敏捷（保底 1）。",
        quantity="rare",
        attack_element="",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "exhaust_status_and_curse_hand_gain_stats",
                "hp_divisor": 2,
                "stat_divisor": 4
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "磐愿+",
            "description": "消耗。消耗所有状态牌和诅咒牌。失去等于消耗牌数量 1/3 的生命，获得等于消耗牌数量 1/4 的力量和敏捷（保底 1）。",
            "patches": [
                {
                    "path": ["effects", 0, "hp_divisor"],
                    "value": 3
                }
            ]
        }
    )

def create_abyssal_form():
    return CardTemplate(
        card_id="card.abyssal_form",
        name="深渊形态",
        card_type="power",
        cost=3,
        target="self",
        description="攻击牌额外视为有极阴 Zone 效果。不会新开或覆盖 Zone。",
        quantity="rare",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "abyssal_form": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "abyssal_form",
                "amount": {
                    "var": "abyssal_form"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "深渊形态+",
            "cost": 2,
            "description": "攻击牌额外视为有极阴 Zone 效果。不会新开或覆盖 Zone。",
        }
    )
def create_phantom_form():
    return CardTemplate(
        card_id="card.phantom_form",
        name="虚影形态",
        card_type="power",
        cost=3,
        target="self",
        description="攻击牌无视格挡。",
        quantity="rare",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "phantom_form": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "phantom_form",
                "amount": {
                    "var": "phantom_form"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "虚影形态+",
            "cost": 2,
            "description": "攻击牌无视格挡。",
        }
    )







