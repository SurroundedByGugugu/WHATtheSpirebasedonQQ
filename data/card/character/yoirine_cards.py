# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate


def create_crystal_piercing():
    return CardTemplate(
        card_id="card.crystal_piercing",
        name="晶刺",
        card_type="attack",
        cost=2,
        target="random_enemy",
        description="对随机敌人造成 2 点伤害 4 次。",
        quantity="starting",
        attack_type="piercing",
        attack_element="crystal",
        owner_character_id="character.yoirine",
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
            "description": "对随机敌人造成 2 点伤害 6 次。",
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
        description="场地效果变为辉晶。已有辉晶效果时，改为场地效果变为极·辉晶，持续3t。",
        quantity="rare",
        attack_element = "crystal",
        owner_character_id= "character.yoirine",
        effects=[
            {
                "op": "set_zone"
            }
        ],
        upgraded = False, #升级降1费
        upgrade_patch={
            "name":"辉晶领域+",
            "description":"费用减少1。场地效果变为辉晶。已有辉晶效果时，改为场地效果变为极·辉晶，持续3t。",
            "cost":1
        }
    )
