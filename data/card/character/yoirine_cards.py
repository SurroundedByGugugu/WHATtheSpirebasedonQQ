# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate


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
        quantity="rare",
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


def create_crystal_cocoon():
    return CardTemplate(
        card_id="card.crystal_cocoon",
        name="晶茧",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 3 点格挡。本回合结束时，在敌人攻击完后，获得与当前格挡层数相同的力量。",
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
            "description": "获得 4 点格挡。本回合结束时，在敌人攻击完后，获得与当前格挡层数相同的力量。",
            "card_vars": {
                "block": 4
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
        description="获得 6 点格挡。获得等量临时荆棘。",
        quantity="common",
        attack_element="crystal",
        owner_character_id="character.yoirine",
        card_vars={
            "block": 6
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
            "description": "获得 8 点格挡。获得等量临时荆棘。",
            "card_vars": {
                "block": 8
            },
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