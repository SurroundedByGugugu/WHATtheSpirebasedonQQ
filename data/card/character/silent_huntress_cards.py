# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE
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


# uncommon attack
# uncommon skill
# uncommon power

# rare attack
# rare skill
# rare power