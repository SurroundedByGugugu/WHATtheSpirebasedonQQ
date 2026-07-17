# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST

# 一对私有打防
def create_strikeYoirine():
    return CardTemplate(
        card_id="card.strike_yoirine",
        name="打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 6 点伤害。",
        quantity="starting",
        owner_character_id="character.yoirine",
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
def create_defendYoirine():
    return CardTemplate(
        card_id="card.defend_yoirine",
        name="格挡",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。",
        quantity="starting",
        owner_character_id="character.yoirine",
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

#starting
def create_crystal_zone():
    return CardTemplate(
        card_id="card.crystal_zone",
        name="辉晶领域",
        card_type="skill",
        cost=2,
        target="none",
        description="场地效果变为晶。已有晶效果时，改为场地效果变为极·晶，持续3t。已在极·晶期间再次使用时，延长持续回合2t。",
        quantity="starting",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "set_zone",
                "element": "crystal"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "辉晶领域+",
            "description": "费用减少1。场地效果变为晶。已有晶效果时，改为场地效果变为极·晶，持续3t。已在极·晶期间再次使用时，延长持续回合2t。",
            "cost": 1
        }
    )
def create_crystal_plating():
    return CardTemplate(
        card_id="card.crystal_plating",
        name="结晶镀层",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 4 点格挡。消耗。选择一张没有属性的攻击或技能手牌，添加晶属性标签，持续本场战斗。",
        quantity="starting",
        owner_character_id="character.yoirine",
        card_vars={
            "block": 4
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
                "op": "choose_hand_attack_without_element_apply_plating",
                "element": "crystal",
                "suffix": "·晶",
                "allowed_card_types": ["attack", "skill"]
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "结晶镀层+",
            "description": "获得 7 点格挡。消耗。选择一张没有属性的攻击或技能手牌，添加晶属性标签，持续本场战斗。",
            "card_vars": {
                "block": 7
            }
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
        description="造成 13 点伤害。失去 2 点生命；若有飞行，消去自伤。",
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
            "description": "造成 17 点伤害。失去 1 点生命；若有飞行，消去自伤。",
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
def create_crystal_piercing():
    return CardTemplate(
        card_id="card.crystal_piercing",
        name="晶刺",
        card_type="attack",
        cost=2,
        target="random_enemy",
        description="对随机敌人造成 2 点伤害 4 次。晶 Zone 条件下费用 -1。",
        quantity="common",
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
            "description": "对随机敌人造成 3 点伤害 4 次。晶 Zone 条件下费用 -1。",
            "card_vars": {
                "damage": 3,
                "repeat": 4
            },
        }
    )
def create_crystal_thorns():
    return CardTemplate(
        card_id="card.crystal_thorns",
        name="辉晶之棘",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 6 点格挡。获得一半临时荆棘。",
        quantity="common",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        card_vars={
            "block": 6,
            "thorns": 3
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
                    "var": "thorns",
                    "modifier_profile": "block"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "辉晶之棘+",
            "description": "获得 8 点格挡。获得等量临时荆棘。",
            "card_vars": {
                "block": 8,
                "thorns": 8
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
            "op": "gain_status",
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
def create_abyss_plating():
    return CardTemplate(
        card_id="card.abyss_plating",
        name="深渊镀层",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 4 点格挡。消耗。选择一张没有属性的攻击牌手牌，添加阴属性标签，持续本场战斗。",
        quantity="common",
        owner_character_id="character.yoirine",
        card_vars={
            "block": 4
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
                "op": "choose_hand_attack_without_element_apply_plating",
                "element": "shade",
                "suffix": "·阴"
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "深渊镀层+",
            "description": "获得 7 点格挡。消耗。选择一张没有属性的攻击牌手牌，添加阴属性标签，持续本场战斗。",
            "card_vars": {
                "block": 7
            }
        }
    )
def create_lightless_prayer():
    return CardTemplate(
        card_id="card.lightless_prayer",
        name="无光祷言",
        card_type="skill",
        cost=0,
        target="none",
        description="消耗。对全场敌人添加 4 层深渊凝视。阴/极阴环境下层数变为 1.5/2 倍。（等效触发阴zone效果）",
        quantity="common",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "abyss_gaze": 4
        },
        effects=[
            {
                "op": "gain_status",
                "target": "all_enemies",
                "status": "abyss_gaze",
                "amount": {
                    "var": "abyss_gaze"
                }
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "无光祷言+",
            "description": "消耗。对全场敌人添加 6 层深渊凝视。阴/极阴环境下层数变为 1.5/2 倍。（等效触发阴zone效果）",
            "card_vars": {
                "abyss_gaze": 6
            }
        }
    )
def create_precipitate():
    return CardTemplate(
        card_id="card.precipitate",
        name="析出",
        card_type="skill",
        cost=1,
        target="self",
        description="破坏已展开的晶或阴 Zone，在抽牌堆中加入 1 张对应镀层；若破坏的是极 Zone，改为加入对应镀层+。",
        quantity="common",
        owner_character_id="character.yoirine",
        play_conditions=[
            {
                "op": "active_zone_in",
                "elements": ["crystal", "shade"]
            }
        ],
        effects=[
            {
                "op": "precipitate_zone_to_plating"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "析出+",
            "description": "费用减少 1。破坏已展开的晶或阴 Zone，在抽牌堆中加入 1 张对应镀层；若破坏的是极 Zone，改为加入对应镀层+。",
            "cost": 0
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
def create_divine_bird():
    return CardTemplate(
        card_id="card.divine_bird",
        name="神鸟",
        card_type="attack",
        cost=2,
        target="enemy",
        description="获得 2 层飞行。造成 16 点伤害。若飞行层数大于 9，额外赋予 1 层畏缩。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        card_vars={
            "damage": 16,
            "flying": 2,
            "flinch": 1,
            "threshold": 9
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "flying",
                "amount": {
                    "var": "flying"
                }
            },
            {
                "op": "apply_flinch_if_flying_gt",
                "target": "selected_enemy",
                "threshold": {
                    "var": "threshold"
                },
                "amount": {
                    "var": "flinch"
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
            "name": "神鸟+",
            "description": "获得 2 层飞行。造成 22 点伤害。若飞行层数大于 6，额外赋予 1 层畏缩。",
            "card_vars": {
                "threshold": 6,
                "damage": 22
            }
        }
    )
def create_crystal_dust_explosion():
    return CardTemplate(
        card_id="card.crystal_dust_explosion",
        name="晶尘爆炸",
        card_type="attack",
        cost=2,
        target="none",
        description="只能在当前真实 Zone 为晶或极晶时打出。破坏当前晶/极晶 Zone：普通晶时，对全体敌人造成 1 次 8 点伤害；极晶时，对全体敌人造成 2 次 10 点伤害。该伤害来源不视为自身。",
        quantity="uncommon",
        attack_element="crystal",
        ignore_zone_replay=True,
        owner_character_id="character.yoirine",
        play_conditions=[
            {
                "op": "active_zone_is",
                "element": "crystal"
            }
        ],
        effects=[
            {
                "op": "crystal_dust_explosion",
                "normal_times": 1,
                "normal_damage": 8,
                "extreme_times": 2,
                "extreme_damage": 10
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "晶尘爆炸+",
            "description": "只能在当前真实 Zone 为晶或极晶时打出。破坏当前晶/极晶 Zone：普通晶时，对全体敌人造成 2 次 10 点伤害；极晶时，对全体敌人造成 3 次 12 点伤害。无论【辉晶领域】在何处，将其升级并放回抽牌堆顶。该伤害来源不视为自身。",
            "patches": [
                {
                    "path": ["effects", 0, "normal_times"],
                    "value": 2
                },
                {
                    "path": ["effects", 0, "normal_damage"],
                    "value": 10
                },
                {
                    "path": ["effects", 0, "extreme_times"],
                    "value": 3
                },
                {
                    "path": ["effects", 0, "extreme_damage"],
                    "value": 12
                }
            ]
        }
    )

def create_crystal_cocoon():
    return CardTemplate(
        card_id="card.crystal_cocoon",
        name="晶茧",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 3 点格挡。本回合结束时，在敌人行动完后，若你有格挡，获得 1 点力量。",
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
            "description": "获得 4 点格挡。本回合结束时，在敌人行动完后，若你有格挡，获得 2 点力量。",
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
        description="消耗。获得 1 层易伤。结束当前回合。若有飞行，恢复 10% 最大生命值；否则恢复 5% 最大生命值。不失去飞行层数。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        card_vars={
            "vulnerable": 1,
            "heal_with_flying_percent": 0.10,
            "heal_without_flying_percent": 0.05
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
                "op": "roost_heal_by_flying_state",
                "with_flying_percent": 0.10,
                "without_flying_percent": 0.05
            },
            {
                "op": "force_end_turn"
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "羽栖+",
            "description": "消耗。获得 1 层易伤。结束当前回合。若有飞行，恢复 15% 最大生命值；否则恢复 7% 最大生命值。不失去飞行层数。",
            "card_vars": {
                "heal_with_flying_percent": 0.15,
                "heal_without_flying_percent": 0.07
            },
            "patches": [
                {
                    "path": ["effects", 1, "with_flying_percent"],
                    "value": 0.15
                },
                {
                    "path": ["effects", 1, "without_flying_percent"],
                    "value": 0.07
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
        cost=1,
        target="self",
        description="触发一次阴 Zone 自伤效果，然后抽 3 张牌。",
        quantity="uncommon",
        attack_element="shade",
        skip_auto_zone_hp_loss=True,
        owner_character_id="character.yoirine",
        card_vars={
            "draw": 3
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
            "description": "触发一次阴 Zone 自伤效果，然后抽 4 张牌。",
            "card_vars": {
                "draw": 4
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
def create_crystal_mist():
    return CardTemplate(
        card_id="card.crystal_mist",
        name="结晶薄雾",
        card_type="skill",
        cost=0,
        target="self",
        description="下 1 张打出的牌视为在晶 Zone 下。无属性牌也会占用次数。真实场地 Zone 存在时不触发。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        card_vars={
            "mist": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "crystal_mist",
                "amount": {
                    "var": "mist"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "结晶薄雾+",
            "description": "下 2 张打出的牌视为在晶 Zone 下。无属性牌也会占用次数。真实场地 Zone 存在时不触发。",
            "card_vars": {
                "mist": 2
            }
        }
    )
def create_abyss_mist():
    return CardTemplate(
        card_id="card.abyss_mist",
        name="深渊薄雾",
        card_type="skill",
        cost=0,
        target="self",
        description="下 1 张打出的攻击牌视为在阴 Zone 下。真实场地 Zone 存在时不触发。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        card_vars={
            "mist": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "abyss_mist",
                "amount": {
                    "var": "mist"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "深渊薄雾+",
            "description": "下 1 张打出的攻击牌视为在极阴 Zone 下。真实场地 Zone 存在时不触发。",
            "patches": [
                {
                    "path": ["effects", 0, "status"],
                    "value": "abyss_mist_extreme"
                }
            ]
        }
    )
def create_abyss_index():
    return CardTemplate(
        card_id="card.abyss_index",
        name="深渊索引",
        card_type="skill",
        cost=1,
        target="self",
        description="消耗。选择抽牌堆中一张牌，添加战斗内附魔【索引·阴】。每次打出阴属性牌后，将带【索引·阴】的牌从抽牌堆、弃牌堆或消耗堆加入手牌。",
        quantity="uncommon",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "request_abyss_index_choice",
                "enchantment": "index_shade"
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "深渊索引+",
            "description": "消耗。选择抽牌堆中一张牌，添加战斗内附魔【索引·阴+】。每次打出阴属性牌后，将带【索引·阴+】的牌从抽牌堆、弃牌堆或消耗堆加入手牌；以正常抽牌方式从抽牌堆抽到时，额外获得 1 点费用。",
            "patches": [
                {
                    "path": ["effects", 0, "enchantment"],
                    "value": "index_shade_plus"
                }
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
def create_phantom_form():
    return CardTemplate(
        card_id="card.phantom_form",
        name="虚影形态",
        card_type="power",
        cost=2,
        target="self",
        description="攻击牌无视格挡。",
        quantity="uncommon",
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
            "cost": 1,
            "description": "攻击牌无视格挡。",
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
        description="造成 28 点伤害。如果使一名生命满的敌人死亡，恢复 3 点生命。",
        quantity="rare",
        attack_element="shade",
        owner_character_id="character.yoirine",
        card_vars={
            "damage": 28,
            "heal": 3
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
            "description": "造成 38 点伤害。如果使一名生命满的敌人死亡，恢复 4 点生命。",
            "card_vars": {
                "damage": 38,
                "heal": 4
            }
        }
    )
def create_abyss_mire():
    return CardTemplate(
        card_id="card.abyss_mire",
        name="渊淖",
        card_type="attack",
        cost=2,
        target="none",
        description="依据深渊凝视层数，对全场敌人分别造成一次阴属性等值伤害。被阴属性攻击后，深渊凝视会清空。若没有造成实际生命伤害，获得 2 点费用，并在抽牌堆中加入 1 张【无光祷言】。",
        quantity="rare",
        attack_element="shade",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "abyss_mire_damage_by_gaze",
                "energy_if_no_damage": 2
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "渊淖+",
            "cost": 1,
            "description": "依据深渊凝视层数，对全场敌人分别造成一次阴属性等值伤害。被阴属性攻击后，深渊凝视会清空。若没有造成实际生命伤害，获得 2 点费用，并在抽牌堆中加入 1 张【无光祷言+】。"
        }
    )

def create_rockbound_wish():
    return CardTemplate(
        card_id="card.rockbound_wish",
        name="磐愿",
        card_type="skill",
        cost=1,
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
def create_abyss_manifestation():
    return CardTemplate(
        card_id="card.abyss_manifestation",
        name="深渊具现",
        card_type="skill",
        cost=1,
        target="none",
        description="对深渊凝视层数最高的敌人造成一次等量无来源环境伤害。次优先级：当前 HP 最低；全部相等则按序取第一个存活敌人。",
        quantity="rare",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "abyss_manifestation_damage",
                "use_shade_zone_when_upgraded": False
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "深渊具现+",
            "description": "对深渊凝视层数最高的敌人造成一次等量无来源环境伤害。若当前为阴/极阴 Zone，该环境伤害被阴 Zone 修正，并触发自伤。",
            "patches": [
                {
                    "path": ["effects", 0, "use_shade_zone_when_upgraded"],
                    "value": True
                }
            ]
        }
    )
def create_shade_zone():
    return CardTemplate(
        card_id="card.shade_zone",
        name="刻阴领域",
        card_type="skill",
        cost=2,
        target="none",
        description="场地效果变为阴。已有阴效果时，改为场地效果变为极·阴，持续3t。已在极·阴期间再次使用时，延长持续回合2t。",
        quantity="rare",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "set_zone",
                "element": "shade"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "刻阴领域+",
            "description": "费用减少1。场地效果变为阴。已有阴效果时，改为场地效果变为极·阴，持续3t。已在极·阴期间再次使用时，延长持续回合2t。",
            "cost": 1
        }
    )
def create_synchronization():
    return CardTemplate(
        card_id="card.synchronization",
        name="同调",
        card_type="skill",
        cost=2,
        target="self",
        description="消耗。对自己造成 1 点伤害。选择消耗堆以外任意 1 张牌，添加共鸣和消耗。共鸣牌在晶/阴 Zone 下抽到时自动叠加 Zone 属性打出。",
        quantity="rare",
        owner_character_id="character.yoirine",
        keywords=[KEYWORD_EXHAUST],
        card_vars={
            "self_damage": 1,
        },
        effects=[
            {
                "op": "lose_hp",
                "target": "self",
                "amount":{
                    "base_var": "self_damage"
                    },
            },
            {
                "op": "request_synchronization_choice",
                "add_exhaust": True,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "同调+",
            "description": "消耗。对自己造成 1 点伤害。选择消耗堆以外任意 1 张牌，添加共鸣。共鸣牌在晶/阴 Zone 下抽到时自动叠加 Zone 属性打出。",
            "effects": [
                {
                "op": "lose_hp",
                "target": "self",
                "amount":{
                    "base_var": "self_damage"
                    },
                },
                {
                    "op": "request_synchronization_choice",
                    "add_exhaust": False,
                },
            ],
        }
    )

def create_abyssal_form():
    return CardTemplate(
        card_id="card.abyssal_form",
        name="深渊形态",
        card_type="power",
        cost=3,
        target="self",
        description="阴属性攻击牌额外视为有极阴 Zone 效果。不会新开或覆盖 Zone。",
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
            "description": "阴属性攻击牌额外视为有极阴 Zone 效果。不会新开或覆盖 Zone。",
        }
    )
def create_tailwind():
    return CardTemplate(
        card_id="card.tailwind",
        name="顺风",
        card_type="power",
        cost=3,
        target="self",
        description="有飞行状态时，受到的攻击伤害变为 30%。",
        quantity="rare",
        owner_character_id="character.yoirine",
        card_vars={
            "tailwind": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "tailwind",
                "amount": {
                    "var": "tailwind"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "顺风+",
            "description": "费用减少 1。有飞行状态时，受到的攻击伤害变为 30%。",
            "cost": 2
        }
    )
def create_insatiable_abyss():
    return CardTemplate(
        card_id="card.insatiable_abyss",
        name="无厌之渊",
        card_type="power",
        cost=2,
        target="self",
        description="对敌人造成阴属性伤害并清除深渊凝视后，若敌人没有死亡，再赋予清除层数一半的深渊凝视。该比例在打出时确定。",
        quantity="rare",
        attack_element="shade",
        owner_character_id="character.yoirine",
        effects=[
            {
                "op": "gain_insatiable_abyss",
                "base_percent": 50,
                "upgraded_percent": 80
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "无厌之渊+",
            "description": "对敌人造成阴属性伤害并清除深渊凝视后，若敌人没有死亡，再赋予清除层数 80% 的深渊凝视。该比例在打出时确定。"
        }
    )

