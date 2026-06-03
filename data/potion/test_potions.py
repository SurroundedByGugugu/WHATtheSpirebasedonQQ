# -*- coding: utf-8 -*-

from data.potion.base_potion import PotionTemplate


def create_test_strength_potion():
    return PotionTemplate(
        potion_id="potion.test_strength",
        name="测试力量药水",
        description="获得 2 点力量。",
        target="self",
        effect_vars={
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
        ]
    )

def create_test_fire_potion():
    return PotionTemplate(
        potion_id="potion.test_fire",
        name="测试火焰药水",
        description="对目标敌人造成 20 点攻击伤害。",
        target="enemy",
        effect_vars={
            "damage": 20
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "var": "damage",
                    "modifier_profile": None
                }
            }
        ]
    )

def create_test_dexterity_potion():
    return PotionTemplate(
        potion_id="potion.test_dexterity",
        name="测试敏捷药水",
        description="获得 2 点敏捷。",
        target="self",
        quantity="common",
        effect_vars={
            "dexterity": 2
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "dexterity",
                "amount": {
                    "var": "dexterity"
                }
            }
        ]
    )