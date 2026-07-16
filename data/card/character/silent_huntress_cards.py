# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE,
    KEYWORD_UNPLAYABLE
)

# 一对私有打防
def create_strikeSH():
    return CardTemplate(
        card_id="card.strike_silent_huntress",
        name="打击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 6 点伤害。",
        quantity="starting",
        owner_character_id="character.silent_huntress",
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


def create_defendSH():
    return CardTemplate(
        card_id="card.defend_silent_huntress",
        name="格挡",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。",
        quantity="starting",
        owner_character_id="character.silent_huntress",
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
def create_neutralize():
    return CardTemplate(
        card_id="card.neutralize",
        name="中和",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 3 点伤害。赋予 1t 虚弱",
        quantity="starting",
        attack_type="magic",
        owner_character_id="character.silent_huntress",
        card_vars={
            "damage": 3,
            "weak": 1
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
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name":"中和+",
            "description":"造成 4 点伤害。赋予 2t 虚弱",
            "card_vars":{
                "damage": 4,
                "weak": 2
            },
        }
    )
def create_survivor():
    return CardTemplate(
        card_id="card.survivor",
        name="生存者",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 8 点格挡。丢弃 1 张牌。",
        quantity="starting",
        owner_character_id="character.silent_huntress",
        card_vars={
            "block": 8,
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
                "op": "request_discard_any",
                "min_count": 1,
                "max_count": 1,
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "生存者+",
            "description": "获得 11 点格挡。丢弃 1 张牌。",
            "card_vars": {
                "block": 11,
            },
        },
    )

# common attack
def create_bane():
    return CardTemplate(
        card_id="card.bane",
        name="灾祸",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 7 点伤害。如果敌人有中毒状态，则再次造成 7 点伤害。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 7},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {
                "op": "if_target_has_status",
                "target": "selected_enemy",
                "status": "poison",
                "effects": [
                    {
                        "op": "deal_damage",
                        "target": "selected_enemy",
                        "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
                    }
                ],
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "灾祸+",
            "description": "造成 10 点伤害。如果敌人有中毒状态，则再次造成 10 点伤害。",
            "card_vars": {"damage": 10},
        },
    )
def create_dagger_spray():
    return CardTemplate(
        card_id="card.dagger_spray",
        name="匕首雨",
        card_type="attack",
        cost=1,
        target="all_enemies",
        description="对所有敌人造成 4 点伤害 2 次。",
        quantity="common",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 4, "repeat": 2},
        effects=[
            {
                "op": "deal_damage_all_enemies",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
                "times": {"var": "repeat"},
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "匕首雨+",
            "description": "对所有敌人造成 6 点伤害 2 次。",
            "card_vars": {"damage": 6},
        },
    )
def create_dagger_throw():
    return CardTemplate(
        card_id="card.dagger_throw",
        name="投掷匕首",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 9 点伤害。抽 1 张牌。丢弃 1 张牌。",
        quantity="common",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 9, "draw": 1},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {"op": "draw_cards", "amount": {"var": "draw"}},
            {"op": "request_discard_any", "min_count": 1, "max_count": 1},
        ],
        upgraded=False,
        upgrade_patch={
            "name": "投掷匕首+",
            "description": "造成 12 点伤害。抽 1 张牌。丢弃 1 张牌。",
            "card_vars": {"damage": 12},
        },
    )
def create_flying_knee():
    return CardTemplate(
        card_id="card.flying_knee",
        name="飞膝",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 8 点伤害。在下一回合获得 1 点费用。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 8, "next_energy": 1},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "next_turn_energy",
                "amount": {"var": "next_energy"},
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "飞膝+",
            "description": "造成 11 点伤害。在下一回合获得 1 点费用。",
            "card_vars": {"damage": 11},
        },
    )
def create_poisoned_stab():
    return CardTemplate(
        card_id="card.poisoned_stab",
        name="带毒刺击",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 6 点伤害。给予 3 层中毒。",
        quantity="common",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 6, "poison": 3},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "poison",
                "amount": {"var": "poison"},
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "带毒刺击+",
            "description": "造成 8 点伤害。给予 4 层中毒。",
            "card_vars": {"damage": 8, "poison": 4},
        },
    )
def create_quick_slash():
    return CardTemplate(
        card_id="card.quick_slash",
        name="快斩",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 8 点伤害。抽 1 张牌。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 8, "draw": 1},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {"op": "draw_cards", "amount": {"var": "draw"}},
        ],
        upgraded=False,
        upgrade_patch={
            "name": "快斩+",
            "description": "造成 12 点伤害。抽 1 张牌。",
            "card_vars": {"damage": 12},
        },
    )
def create_slice():
    return CardTemplate(
        card_id="card.slice",
        name="切割",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 6 点伤害。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 6},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "切割+",
            "description": "造成 9 点伤害。",
            "card_vars": {"damage": 9},
        },
    )
def create_sucker_punch():
    return CardTemplate(
        card_id="card.sucker_punch",
        name="突然一拳",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 7 点伤害。给予 1 层虚弱。",
        quantity="common",
        attack_type="blunt",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 7, "weak": 1},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "weak",
                "amount": {"var": "weak"},
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "突然一拳+",
            "description": "造成 9 点伤害。给予 2 层虚弱。",
            "card_vars": {"damage": 9, "weak": 2},
        },
    )
def create_sneaky_strike():
    return CardTemplate(
        card_id="card.sneaky_strike",
        name="隐秘打击",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 12 点伤害。如果你在这回合丢弃过牌，获得 2 点费用。",
        quantity="common",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 12, "energy": 2},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            },
            {
                "op": "gain_energy_if_discarded_this_turn",
                "amount": {"var": "energy"},
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "隐秘打击+",
            "description": "造成 16 点伤害。如果你在这回合丢弃过牌，获得 2 点费用。",
            "card_vars": {"damage": 16},
        },
    )

# common skill
def create_acrobatics():
    return CardTemplate(
        card_id="card.acrobatics",
        name="杂技",
        card_type="skill",
        cost=1,
        target="self",
        description="抽 3 张牌。丢弃 1 张牌。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"draw": 3},
        effects=[
            {"op": "draw_cards", "amount": {"var": "draw"}},
            {"op": "request_discard_any", "min_count": 1, "max_count": 1},
        ],
        upgraded=False,
        upgrade_patch={
            "name": "杂技+",
            "description": "抽 4 张牌。丢弃 1 张牌。",
            "card_vars": {"draw": 4},
        },
    )
def create_backflip():
    return CardTemplate(
        card_id="card.backflip",
        name="后空翻",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。抽 2 张牌。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 5, "draw": 2},
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {"var": "block", "modifier_profile": "block"},
            },
            {"op": "draw_cards", "amount": {"var": "draw"}},
        ],
        upgraded=False,
        upgrade_patch={
            "name": "后空翻+",
            "description": "获得 8 点格挡。抽 2 张牌。",
            "card_vars": {"block": 8},
        },
    )
def create_blade_dance():
    return CardTemplate(
        card_id="card.blade_dance",
        name="刀刃之舞",
        card_type="skill",
        cost=1,
        target="self",
        description="增加 3 张小刀到你的手牌。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"shiv": 3},
        effects=[
            {
                "op": "add_card_to_hand",
                "card_id": "card.shiv",
                "amount": {"var": "shiv"},
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "刀刃之舞+",
            "description": "增加 4 张小刀到你的手牌。",
            "card_vars": {"shiv": 4},
        },
    )
def create_cloak_and_dagger():
    return CardTemplate(
        card_id="card.cloak_and_dagger",
        name="斗篷与匕首",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 6 点格挡。增加 1 张小刀到你的手牌。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 6, "shiv": 1},
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {"var": "block", "modifier_profile": "block"},
            },
            {
                "op": "add_card_to_hand",
                "card_id": "card.shiv",
                "amount": {"var": "shiv"},
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "斗篷与匕首+",
            "description": "获得 6 点格挡。增加 2 张小刀到你的手牌。",
            "card_vars": {"shiv": 2},
        },
    )
def create_deadly_poison():
    return CardTemplate(
        card_id="card.deadly_poison",
        name="致命毒药",
        card_type="skill",
        cost=1,
        target="enemy",
        description="给予 5 层中毒。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"poison": 5},
        effects=[
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "poison",
                "amount": {"var": "poison"},
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "致命毒药+",
            "description": "给予 7 层中毒。",
            "card_vars": {"poison": 7},
        },
    )
def create_deflect():
    return CardTemplate(
        card_id="card.deflect",
        name="偏折",
        card_type="skill",
        cost=0,
        target="self",
        description="获得 4 点格挡。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 4},
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {"var": "block", "modifier_profile": "block"},
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "偏折+",
            "description": "获得 7 点格挡。",
            "card_vars": {"block": 7},
        },
    )
def create_dodge_and_roll():
    return CardTemplate(
        card_id="card.dodge_and_roll",
        name="闪躲翻滚",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 4 点格挡。在下一回合获得 4 点格挡。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 4, "next_block": 4},
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {"var": "block", "modifier_profile": "block"},
            },
            {
                "op": "gain_next_turn_block",
                "amount": {"var": "next_block", "modifier_profile": "block"},
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "闪躲翻滚+",
            "description": "获得 6 点格挡。在下一回合获得 6 点格挡。",
            "card_vars": {"block": 6, "next_block": 6},
        },
    )
def create_outmaneuver():
    return CardTemplate(
        card_id="card.outmaneuver",
        name="抢占先机",
        card_type="skill",
        cost=1,
        target="self",
        description="下一回合获得 2 点费用。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"next_energy": 2},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "next_turn_energy",
                "amount": {"var": "next_energy"},
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "抢占先机+",
            "description": "下一回合获得 3 点费用。",
            "card_vars": {"next_energy": 3},
        },
    )
def create_piercing_wail():
    return CardTemplate(
        card_id="card.piercing_wail",
        name="尖啸",
        card_type="skill",
        cost=1,
        target="all_enemies",
        description="所有敌人失去 6 点力量 1 回合。消耗。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"strength_loss": 6},
        effects=[
            {
                "op": "gain_temporary_strength_loss_all_enemies",
                "amount": {"var": "strength_loss"},
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "尖啸+",
            "description": "所有敌人失去 8 点力量 1 回合。消耗。",
            "card_vars": {"strength_loss": 8},
        },
    )
def create_prepared():
    return CardTemplate(
        card_id="card.prepared",
        name="早有准备",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 1 张牌。丢弃 1 张牌。",
        quantity="common",
        owner_character_id="character.silent_huntress",
        card_vars={"draw": 1},
        effects=[
            {"op": "draw_cards", "amount": {"var": "draw"}},
            {"op": "request_discard_any", "min_count": 1, "max_count": 1},
        ],
        upgraded=False,
        upgrade_patch={
            "name": "早有准备+",
            "description": "抽 2 张牌。丢弃 1 张牌。",
            "card_vars": {"draw": 2},
        },
    )


# uncommon power
def create_accuracy():
    return CardTemplate(
        card_id="card.accuracy",
        name="精准",
        card_type="power",
        cost=1,
        target="self",
        description="小刀造成的伤害增加 4 点。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"accuracy": 4},
        effects=[{"op": "gain_status", "target": "self", "status": "accuracy", "amount": {"var": "accuracy"}}],
        upgraded=False,
        upgrade_patch={"name": "精准+", "description": "小刀造成的伤害增加 6 点。", "card_vars": {"accuracy": 6}},
    )
def create_caltrops():
    return CardTemplate(
        card_id="card.caltrops",
        name="铁蒺藜",
        card_type="power",
        cost=1,
        target="self",
        description="获得 3 点荆棘。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"thorns": 3},
        effects=[{"op": "gain_status", "target": "self", "status": "thorns", "amount": {"var": "thorns"}}],
        upgraded=False,
        upgrade_patch={"name": "铁蒺藜+", "description": "获得 5 点荆棘。", "card_vars": {"thorns": 5}},
    )
def create_footwork():
    return CardTemplate(
        card_id="card.footwork",
        name="灵动步法",
        card_type="power",
        cost=1,
        target="self",
        description="获得 2 点敏捷。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"dexterity": 2},
        effects=[{"op": "gain_status", "target": "self", "status": "dexterity", "amount": {"var": "dexterity"}}],
        upgraded=False,
        upgrade_patch={"name": "灵动步法+", "description": "获得 3 点敏捷。", "card_vars": {"dexterity": 3}},
    )
def create_infinite_blades():
    return CardTemplate(
        card_id="card.infinite_blades",
        name="无限刀刃",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合开始时，增加 1 张小刀到你的手牌。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"count": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "infinite_blades", "amount": {"var": "count"}}],
        upgraded=False,
        upgrade_patch={"name": "无限刀刃+", "description": "固有。在你的回合开始时，增加 1 张小刀到你的手牌。", "add_keywords": [KEYWORD_INNATE]},
    )
def create_noxious_fumes():
    return CardTemplate(
        card_id="card.noxious_fumes",
        name="毒雾",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合开始时，给予所有敌人 2 层中毒。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"poison": 2},
        effects=[{"op": "gain_status", "target": "self", "status": "noxious_fumes", "amount": {"var": "poison"}}],
        upgraded=False,
        upgrade_patch={"name": "毒雾+", "description": "在你的回合开始时，给予所有敌人 3 层中毒。", "card_vars": {"poison": 3}},
    )
def create_well_laid_plans():
    return CardTemplate(
        card_id="card.well_laid_plans",
        name="计划妥当",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合结束时，保留最多 1 张牌。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"retain": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "well_laid_plans", "amount": {"var": "retain"}}],
        upgraded=False,
        upgrade_patch={"name": "计划妥当+", "description": "在你的回合结束时，保留最多 2 张牌。", "card_vars": {"retain": 2}},
    )

# uncommon attack
def create_all_out_attack():
    return CardTemplate(
        card_id="card.all_out_attack",
        name="全力攻击",
        card_type="attack",
        cost=1,
        target="all_enemies",
        description="对所有敌人造成 10 点伤害。丢弃 1 张随机手牌。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 10, "discard": 1},
        effects=[
            {"op": "deal_damage_all_enemies", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
            {"op": "discard_random_hand_cards", "amount": {"var": "discard"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "全力攻击+", "description": "对所有敌人造成 14 点伤害。丢弃 1 张随机手牌。", "card_vars": {"damage": 14}},
    )
def create_backstab():
    return CardTemplate(
        card_id="card.backstab",
        name="背刺",
        card_type="attack",
        cost=0,
        target="enemy",
        description="固有。造成 11 点伤害。消耗。",
        quantity="uncommon",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 11},
        effects=[{"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        keywords=[KEYWORD_INNATE, KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "背刺+", "description": "固有。造成 15 点伤害。消耗。", "card_vars": {"damage": 15}},
    )
def create_choke():
    return CardTemplate(
        card_id="card.choke",
        name="勒脖",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 12 点伤害。你在这个回合内每打出一张牌，该名敌人都会失去 3 点生命。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 12, "choke": 3},
        effects=[
            {"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
            {"op": "gain_status", "target": "selected_enemy", "status": "choked", "amount": {"var": "choke"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "勒脖+", "description": "造成 12 点伤害。你在这个回合内每打出一张牌，该名敌人都会失去 5 点生命。", "card_vars": {"choke": 5}},
    )
def create_dash():
    return CardTemplate(
        card_id="card.dash",
        name="冲刺",
        card_type="attack",
        cost=2,
        target="enemy",
        description="获得 10 点格挡。造成 10 点伤害。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 10, "damage": 10},
        effects=[
            {"op": "gain_block", "target": "self", "amount": {"var": "block", "modifier_profile": "block"}},
            {"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "冲刺+", "description": "获得 13 点格挡。造成 13 点伤害。", "card_vars": {"block": 13, "damage": 13}},
    )
def create_endless_agony():
    return CardTemplate(
        card_id="card.endless_agony",
        name="无尽苦痛",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 4 点伤害。每当你抽到这张牌，都增加一张其复制品到你的手牌。消耗。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 4},
        effects=[{"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "无尽苦痛+", "description": "造成 6 点伤害。每当你抽到这张牌，都增加一张其复制品到你的手牌。消耗。", "card_vars": {"damage": 6}},
    )
def create_eviscerate():
    return CardTemplate(
        card_id="card.eviscerate",
        name="内脏切除",
        card_type="attack",
        cost=3,
        target="enemy",
        description="你在这个回合内每丢弃一张牌，耗能就减少 1。造成 7 点伤害 3 次。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 7, "repeat": 3},
        cost_rules=[{"op": "reduce_by_player_discarded_this_turn", "amount_per_discard": 1, "min_cost": 0}],
        effects=[{"op": "deal_damage", "target": "selected_enemy", "times": {"var": "repeat"}, "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        upgraded=False,
        upgrade_patch={"name": "内脏切除+", "description": "你在这个回合内每丢弃一张牌，耗能就减少 1。造成 9 点伤害 3 次。", "card_vars": {"damage": 9}},
    )
def create_finisher():
    return CardTemplate(
        card_id="card.finisher",
        name="终结技",
        card_type="attack",
        cost=1,
        target="enemy",
        description="你在这个回合内每打出过一张攻击牌，就造成 1 次 6 点伤害。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 6},
        effects=[{"op": "deal_damage_times_by_attack_played_this_turn", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        upgraded=False,
        upgrade_patch={"name": "终结技+", "description": "你在这个回合内每打出过一张攻击牌，就造成 1 次 8 点伤害。", "card_vars": {"damage": 8}},
    )
def create_flechettes():
    return CardTemplate(
        card_id="card.flechettes",
        name="飞镖",
        card_type="attack",
        cost=1,
        target="enemy",
        description="手牌中每有一张技能牌，造成 4 点伤害。",
        quantity="uncommon",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 4},
        effects=[{"op": "deal_damage_times_by_hand_type", "card_type": "skill", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        upgraded=False,
        upgrade_patch={"name": "飞镖+", "description": "手牌中每有一张技能牌，造成 6 点伤害。", "card_vars": {"damage": 6}},
    )
def create_heel_hook():
    return CardTemplate(
        card_id="card.heel_hook",
        name="足跟勾",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 5 点伤害。如果敌人有虚弱状态，获得 1 点费用并且抽 1 张牌。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 5, "energy": 1, "draw": 1},
        effects=[
            {"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
            {"op": "if_target_has_status", "target": "selected_enemy", "status": "weak", "effects": [
                {"op": "gain_energy", "amount": {"var": "energy"}},
                {"op": "draw_cards", "amount": {"var": "draw"}},
            ]},
        ],
        upgraded=False,
        upgrade_patch={"name": "足跟勾+", "description": "造成 8 点伤害。如果敌人有虚弱状态，获得 1 点费用并且抽 1 张牌。", "card_vars": {"damage": 8}},
    )
def create_masterful_stab():
    return CardTemplate(
        card_id="card.masterful_stab",
        name="精巧刺击",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 12 点伤害。你每次受到伤害，这张牌的耗能增加 1。",
        quantity="uncommon",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 12},
        cost_rules=[{"op": "increase_by_player_life_loss_count", "amount_per_loss": 1}],
        effects=[{"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        upgraded=False,
        upgrade_patch={"name": "精巧刺击+", "description": "造成 16 点伤害。你每次受到伤害，这张牌的耗能增加 1。", "card_vars": {"damage": 16}},
    )
def create_predator():
    return CardTemplate(
        card_id="card.predator",
        name="猎杀者",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 15 点伤害。在下一回合多抽 2 张牌。",
        quantity="uncommon",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 15, "draw": 2},
        effects=[
            {"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
            {"op": "gain_status", "target": "self", "status": "next_turn_draw", "amount": {"var": "draw"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "猎杀者+", "description": "造成 20 点伤害。在下一回合多抽 2 张牌。", "card_vars": {"damage": 20}},
    )
def create_riddle_with_holes():
    return CardTemplate(
        card_id="card.riddle_with_holes",
        name="千穿百刺",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 3 点伤害 5 次。",
        quantity="uncommon",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 3, "repeat": 5},
        effects=[{"op": "deal_damage", "target": "selected_enemy", "times": {"var": "repeat"}, "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        upgraded=False,
        upgrade_patch={"name": "千穿百刺+", "description": "造成 4 点伤害 5 次。", "card_vars": {"damage": 4}},
    )
def create_skewer():
    return CardTemplate(
        card_id="card.skewer",
        name="串刺",
        card_type="attack",
        cost="X",
        target="enemy",
        description="造成 7 点伤害 X 次。",
        quantity="uncommon",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 7},
        effects=[{"op": "repeat_x", "effects": [{"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}]}],
        upgraded=False,
        upgrade_patch={"name": "串刺+", "description": "造成 10 点伤害 X 次。", "card_vars": {"damage": 10}},
    )

# uncommon skill
def create_blur():
    return CardTemplate(
        card_id="card.blur",
        name="残影",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 5 点格挡。你的下一回合开始时格挡不会消失。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 5, "blur": 1},
        effects=[
            {"op": "gain_block", "target": "self", "amount": {"var": "block", "modifier_profile": "block"}},
            {"op": "gain_status", "target": "self", "status": "blur", "amount": {"var": "blur"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "残影+", "description": "获得 8 点格挡。你的下一回合开始时格挡不会消失。", "card_vars": {"block": 8}},
    )
def create_bouncing_flask():
    return CardTemplate(
        card_id="card.bouncing_flask",
        name="弹跳药瓶",
        card_type="skill",
        cost=2,
        target="random_enemy",
        description="随机给予敌人 3 层中毒 3 次。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"poison": 3, "repeat": 3},
        effects=[{"op": "gain_status_random_enemies", "status": "poison", "amount": {"var": "poison"}, "times": {"var": "repeat"}}],
        upgraded=False,
        upgrade_patch={"name": "弹跳药瓶+", "description": "随机给予敌人 3 层中毒 4 次。", "card_vars": {"repeat": 4}},
    )
def create_calculated_gamble():
    return CardTemplate(
        card_id="card.calculated_gamble",
        name="计算下注",
        card_type="skill",
        cost=0,
        target="self",
        description="丢弃所有手牌。然后抽相同数量张牌。消耗。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        effects=[{"op": "discard_all_hand_then_draw_same"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "计算下注+", "description": "丢弃所有手牌。然后抽相同数量张牌。", "remove_keywords": [KEYWORD_EXHAUST]},
    )
def create_catalyst():
    return CardTemplate(
        card_id="card.catalyst",
        name="催化剂",
        card_type="skill",
        cost=1,
        target="enemy",
        description="将一名敌人的中毒层数变为 2 倍。消耗。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"multiplier": 2},
        effects=[{"op": "multiply_status", "target": "selected_enemy", "status": "poison", "multiplier": {"var": "multiplier"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "催化剂+", "description": "将一名敌人的中毒层数变为 3 倍。消耗。", "card_vars": {"multiplier": 3}},
    )
def create_concentrate():
    return CardTemplate(
        card_id="card.concentrate",
        name="全神贯注",
        card_type="skill",
        cost=0,
        target="self",
        description="选择丢弃 3 张牌。获得 2 点费用。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"discard": 3, "energy": 2},
        effects=[{"op": "request_discard_any", "min_count": {"var": "discard"}, "max_count": {"var": "discard"}, "after_effects": [{"op": "gain_energy", "amount": {"var": "energy"}}]}],
        upgraded=False,
        upgrade_patch={"name": "全神贯注+", "description": "选择丢弃 2 张牌。获得 2 点费用。", "card_vars": {"discard": 2}},
    )
def create_crippling_poison():
    return CardTemplate(
        card_id="card.crippling_poison",
        name="致残毒云",
        card_type="skill",
        cost=2,
        target="all_enemies",
        description="给予所有敌人 4 层中毒和 2 层虚弱。消耗。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"poison": 4, "weak": 2},
        effects=[
            {"op": "gain_status_all_enemies", "status": "poison", "amount": {"var": "poison"}},
            {"op": "gain_status_all_enemies", "status": "weak", "amount": {"var": "weak"}},
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "致残毒云+", "description": "给予所有敌人 7 层中毒和 2 层虚弱。消耗。", "card_vars": {"poison": 7}},
    )
def create_distraction():
    return CardTemplate(
        card_id="card.distraction_silent_huntress",
        name="声东击西",
        card_type="skill",
        cost=1,
        target="self",
        description="增加一张随机本角色的技能牌到你的手牌。这张牌在本回合耗能变为 0。消耗。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        effects=[{"op": "add_random_skill_to_hand_temp_cost_zero", "owner_character_id": "character.silent_huntress", "exclude_card_ids": ["card.distraction_silent_huntress"]}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "声东击西+", "cost": 0, "description": "增加一张随机本角色的技能牌到你的手牌。这张牌在本回合耗能变为 0。消耗。"},
    )
def create_escape_plan():
    return CardTemplate(
        card_id="card.escape_plan",
        name="逃脱计划",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 1 张牌。如果抽到的是技能牌，获得 3 点格挡。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 3},
        effects=[{"op": "draw_one_if_skill_gain_block", "amount": {"var": "block", "modifier_profile": "block"}}],
        upgraded=False,
        upgrade_patch={"name": "逃脱计划+", "description": "抽 1 张牌。如果抽到的是技能牌，获得 5 点格挡。", "card_vars": {"block": 5}},
    )
def create_expertise():
    return CardTemplate(
        card_id="card.expertise",
        name="独门技术",
        card_type="skill",
        cost=1,
        target="self",
        description="抽牌直到你的手牌有 6 张牌。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"target_size": 6},
        effects=[{"op": "draw_until_hand_size", "amount": {"var": "target_size"}}],
        upgraded=False,
        upgrade_patch={"name": "独门技术+", "description": "抽牌直到你的手牌有 7 张牌。", "card_vars": {"target_size": 7}},
    )
def create_leg_sweep():
    return CardTemplate(
        card_id="card.leg_sweep",
        name="扫腿",
        card_type="skill",
        cost=2,
        target="enemy",
        description="给予 2 层虚弱。获得 11 点格挡。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"weak": 2, "block": 11},
        effects=[
            {"op": "gain_status", "target": "selected_enemy", "status": "weak", "amount": {"var": "weak"}},
            {"op": "gain_block", "target": "self", "amount": {"var": "block", "modifier_profile": "block"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "扫腿+", "description": "给予 3 层虚弱。获得 14 点格挡。", "card_vars": {"weak": 3, "block": 14}},
    )
def create_reflex():
    return CardTemplate(
        card_id="card.reflex",
        name="本能反应",
        card_type="skill",
        cost="-",
        target="self",
        description="抽 2 张牌。奇巧。不能打出。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"draw": 2},
        effects=[{"op": "draw_cards", "amount": {"var": "draw"}}],
        keywords=[KEYWORD_CLEVER, KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={"name": "本能反应+", "description": "抽 3 张牌。奇巧。不能打出。", "card_vars": {"draw": 3}},
    )
def create_setup():
    return CardTemplate(
        card_id="card.setup_silent_huntress",
        name="部署",
        card_type="skill",
        cost=1,
        target="self",
        description="将手牌中的一张牌放到抽牌堆的顶部。并且在其被打出之前，其耗能变为 0。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        effects=[{"op": "request_hand_to_draw_top_temp_cost_zero"}],
        upgraded=False,
        upgrade_patch={"name": "部署+", "cost": 0, "description": "将手牌中的一张牌放到抽牌堆的顶部。并且在其被打出之前，其耗能变为 0。"},
    )
def create_tactician():
    return CardTemplate(
        card_id="card.tactician",
        name="战术大师",
        card_type="skill",
        cost="-",
        target="self",
        description="获得 1 点费用。奇巧。不能打出。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"energy": 1},
        effects=[{"op": "gain_energy", "amount": {"var": "energy"}}],
        keywords=[KEYWORD_CLEVER, KEYWORD_UNPLAYABLE],
        upgraded=False,
        upgrade_patch={"name": "战术大师+", "description": "获得 2 点费用。奇巧。不能打出。", "card_vars": {"energy": 2}},
    )
def create_terror():
    return CardTemplate(
        card_id="card.terror",
        name="恐怖",
        card_type="skill",
        cost=1,
        target="enemy",
        description="给予 99 层易伤。消耗。",
        quantity="uncommon",
        owner_character_id="character.silent_huntress",
        card_vars={"vulnerable": 99},
        effects=[{"op": "gain_status", "target": "selected_enemy", "status": "vulnerable", "amount": {"var": "vulnerable"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "恐怖+", "cost": 0, "description": "给予 99 层易伤。消耗。"},
    )


# rare power
def create_a_thousand_cuts():
    return CardTemplate(
        card_id="card.a_thousand_cuts",
        name="凌迟",
        card_type="power",
        cost=2,
        target="self",
        description="每打出一张牌，就对所有敌人造成 1 点伤害。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "a_thousand_cuts", "amount": {"var": "damage"}}],
        upgraded=False,
        upgrade_patch={"name": "凌迟+", "description": "每打出一张牌，就对所有敌人造成 2 点伤害。", "card_vars": {"damage": 2}},
    )
def create_after_image():
    return CardTemplate(
        card_id="card.after_image",
        name="余像",
        card_type="power",
        cost=1,
        target="self",
        description="你每打出一张牌，都获得 1 点格挡。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"block": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "after_image", "amount": {"var": "block"}}],
        upgraded=False,
        upgrade_patch={"name": "余像+", "description": "固有。你每打出一张牌，都获得 1 点格挡。", "add_keywords": [KEYWORD_INNATE]},
    )
def create_envenom():
    return CardTemplate(
        card_id="card.envenom",
        name="涂毒",
        card_type="power",
        cost=2,
        target="self",
        description="每有一次攻击造成未被格挡的伤害，就给予 1 层中毒。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"poison": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "envenom", "amount": {"var": "poison"}}],
        upgraded=False,
        upgrade_patch={"name": "涂毒+", "cost": 1, "description": "每有一次攻击造成未被格挡的伤害，就给予 1 层中毒。"},
    )
def create_tools_of_the_trade():
    return CardTemplate(
        card_id="card.tools_of_the_trade",
        name="必备工具",
        card_type="power",
        cost=1,
        target="self",
        description="在你的回合开始时，抽 1 张牌，选择丢弃 1 张牌。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"count": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "tools_of_the_trade", "amount": {"var": "count"}}],
        upgraded=False,
        upgrade_patch={"name": "必备工具+", "cost": 0, "description": "在你的回合开始时，抽 1 张牌，选择丢弃 1 张牌。"},
    )
def create_wraith_form():
    return CardTemplate(
        card_id="card.wraith_form",
        name="幽魂形态",
        card_type="power",
        cost=3,
        target="self",
        description="获得 2 层无实体。在每回合结束时失去 1 点敏捷。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"intangible": 2, "dex_loss": 1},
        effects=[
            {"op": "gain_status", "target": "self", "status": "intangible", "amount": {"var": "intangible"}},
            {"op": "gain_status", "target": "self", "status": "wraith_form", "amount": {"var": "dex_loss"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "幽魂形态+", "description": "获得 3 层无实体。在每回合结束时失去 1 点敏捷。", "card_vars": {"intangible": 3}},
    )


# rare attack
def create_die_die_die():
    return CardTemplate(
        card_id="card.die_die_die",
        name="死吧死吧死吧",
        card_type="attack",
        cost=1,
        target="all_enemies",
        description="对所有敌人造成 13 点伤害。消耗。",
        quantity="rare",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 13},
        effects=[{"op": "deal_damage_all_enemies", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "死吧死吧死吧+", "description": "对所有敌人造成 17 点伤害。消耗。", "card_vars": {"damage": 17}},
    )
def create_glass_knife():
    return CardTemplate(
        card_id="card.glass_knife",
        name="玻璃刀刃",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 8 点伤害 2 次。这张牌每被打出一次，在本场战斗中其基础伤害减少 2。",
        quantity="rare",
        attack_type="slash",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 8, "repeat": 2, "loss": 2},
        effects=[
            {"op": "deal_damage", "target": "selected_enemy", "times": {"var": "repeat"}, "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
            {"op": "decrease_self_card_var", "var": "damage", "amount": {"var": "loss"}, "min_value": 0},
        ],
        upgraded=False,
        upgrade_patch={"name": "玻璃刀刃+", "description": "造成 12 点伤害 2 次。这张牌每被打出一次，在本场战斗中其基础伤害减少 2。", "card_vars": {"damage": 12}},
    )
def create_grand_finale():
    return CardTemplate(
        card_id="card.grand_finale",
        name="华丽收场",
        card_type="attack",
        cost=0,
        target="all_enemies",
        description="只有当抽牌堆中没有牌时才能打出。对所有敌人造成 50 点伤害。",
        quantity="rare",
        attack_type="magic",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 50},
        play_conditions=[{"op": "draw_pile_empty"}],
        effects=[{"op": "deal_damage_all_enemies", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}}],
        upgraded=False,
        upgrade_patch={"name": "华丽收场+", "description": "只有当抽牌堆中没有牌时才能打出。对所有敌人造成 60 点伤害。", "card_vars": {"damage": 60}},
    )
def create_unload():
    return CardTemplate(
        card_id="card.unload",
        name="乾坤一掷",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 14 点伤害。丢弃所有非攻击牌。",
        quantity="rare",
        attack_type="piercing",
        owner_character_id="character.silent_huntress",
        card_vars={"damage": 14},
        effects=[
            {"op": "deal_damage", "target": "selected_enemy", "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}},
            {"op": "discard_all_non_attack_hand_cards"},
        ],
        upgraded=False,
        upgrade_patch={"name": "乾坤一掷+", "description": "造成 18 点伤害。丢弃所有非攻击牌。", "card_vars": {"damage": 18}},
    )

# rare skill
def create_adrenaline():
    return CardTemplate(
        card_id="card.adrenaline",
        name="肾上腺素",
        card_type="skill",
        cost=0,
        target="self",
        description="获得 1 点费用，抽 2 张牌。消耗。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"energy": 1, "draw": 2},
        effects=[{"op": "gain_energy", "amount": {"var": "energy"}}, {"op": "draw_cards", "amount": {"var": "draw"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "肾上腺素+", "description": "获得 2 点费用，抽 2 张牌。消耗。", "card_vars": {"energy": 2}},
    )
def create_bullet_time():
    return CardTemplate(
        card_id="card.bullet_time",
        name="子弹时间",
        card_type="skill",
        cost=3,
        target="self",
        description="你在本回合内不能再抽牌。你手牌中的所有牌在本回合的耗能变为 0 点。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"no_draw": 1},
        effects=[
            {"op": "gain_status", "target": "self", "status": "no_draw", "amount": {"var": "no_draw"}},
            {"op": "set_all_hand_cost_zero_this_turn"},
        ],
        upgraded=False,
        upgrade_patch={"name": "子弹时间+", "cost": 2, "description": "你在本回合内不能再抽牌。你手牌中的所有牌在本回合的耗能变为 0 点。"},
    )
def create_corpse_explosion():
    return CardTemplate(
        card_id="card.corpse_explosion",
        name="尸爆术",
        card_type="skill",
        cost=2,
        target="enemy",
        description="给予 6 层中毒。当这名敌人死亡时，对所有敌人造成等于其最大生命值的伤害。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"poison": 6, "corpse": 1},
        effects=[
            {"op": "gain_status", "target": "selected_enemy", "status": "poison", "amount": {"var": "poison"}},
            {"op": "gain_status", "target": "selected_enemy", "status": "corpse_explosion", "amount": {"var": "corpse"}},
        ],
        upgraded=False,
        upgrade_patch={"name": "尸爆术+", "description": "给予 9 层中毒。当这名敌人死亡时，对所有敌人造成等于其最大生命值的伤害。", "card_vars": {"poison": 9}},
    )
def create_doppelganger():
    return CardTemplate(
        card_id="card.doppelganger",
        name="双重存在",
        card_type="skill",
        cost="X",
        target="self",
        description="下一回合，抽 X 张牌，获得 X 点费用。消耗。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        effects=[
            {"op": "gain_status", "target": "self", "status": "next_turn_draw", "amount": {"x_var": "x"}},
            {"op": "gain_status", "target": "self", "status": "next_turn_energy", "amount": {"x_var": "x"}},
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "双重存在+", "description": "下一回合，抽 X+1 张牌，获得 X+1 点费用。消耗。", "effects": [
            {"op": "gain_status", "target": "self", "status": "next_turn_draw", "amount": {"x_var": "x", "add": 1}},
            {"op": "gain_status", "target": "self", "status": "next_turn_energy", "amount": {"x_var": "x", "add": 1}},
        ]},
    )
def create_malaise():
    return CardTemplate(
        card_id="card.malaise",
        name="萎靡",
        card_type="skill",
        cost="X",
        target="enemy",
        description="敌人失去 X 点力量，给予 X 层虚弱。消耗。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        effects=[
            {"op": "gain_status", "target": "selected_enemy", "status": "strength", "amount": {"x_var": "x", "multiplier": -1}},
            {"op": "gain_status", "target": "selected_enemy", "status": "weak", "amount": {"x_var": "x"}},
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "萎靡+", "description": "敌人失去 X+1 点力量，给予 X+1 层虚弱。消耗。", "effects": [
            {"op": "gain_status", "target": "selected_enemy", "status": "strength", "amount": {"x_var": "x", "add": 1, "multiplier": -1}},
            {"op": "gain_status", "target": "selected_enemy", "status": "weak", "amount": {"x_var": "x", "add": 1}},
        ]},
    )
def create_night_terror():
    return CardTemplate(
        card_id="card.night_terror",
        name="夜魇",
        card_type="skill",
        cost=3,
        target="self",
        description="选择一张牌，在下一回合，将 3 份这张牌的复制品放入你的手牌中。消耗。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        effects=[{"op": "request_night_terror_card"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "夜魇+", "cost": 2, "description": "选择一张牌，在下一回合，将 3 份这张牌的复制品放入你的手牌中。消耗。"},
    )
def create_phantasmal_killer():
    return CardTemplate(
        card_id="card.phantasmal_killer",
        name="幻影杀手",
        card_type="skill",
        cost=1,
        target="self",
        description="在你的下个回合，你所有的攻击伤害翻倍。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        card_vars={"count": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "phantasmal_killer_next", "amount": {"var": "count"}}],
        upgraded=False,
        upgrade_patch={"name": "幻影杀手+", "cost": 0, "description": "在你的下个回合，你所有的攻击伤害翻倍。"},
    )
def create_storm_of_steel():
    return CardTemplate(
        card_id="card.storm_of_steel",
        name="钢铁风暴",
        card_type="skill",
        cost=1,
        target="self",
        description="丢弃所有手牌。每丢弃一张牌，在你的手牌中增加一张小刀。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        effects=[{"op": "discard_all_hand_add_shivs", "upgrade_shiv": False}],
        upgraded=False,
        upgrade_patch={"name": "钢铁风暴+", "description": "丢弃所有手牌。每丢弃一张牌，在你的手牌中增加一张小刀+。", "effects": [{"op": "discard_all_hand_add_shivs", "upgrade_shiv": True}]},
    )
def create_venomology():
    return CardTemplate(
        card_id="card.venomology",
        name="炼制药水",
        card_type="skill",
        cost=1,
        target="self",
        description="获得一瓶随机药水。消耗。",
        quantity="rare",
        owner_character_id="character.silent_huntress",
        effects=[{"op": "gain_random_potion"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={"name": "炼制药水+", "cost": 0, "description": "获得一瓶随机药水。消耗。"},
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
        owner_character_id="character.silent_huntress",
        card_vars={"count": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "burst", "amount": {"var": "count"}}],
        upgraded=False,
        upgrade_patch={"name": "爆发+", "description": "本回合内，你打出的下 2 张技能牌会打出 2 次。", "card_vars": {"count": 2}},
    )

