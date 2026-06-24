# -*- coding: utf-8 -*-

from data.potion.base_potion import PotionTemplate


def create_attack_potion():
    return PotionTemplate(
        potion_id="potion.attack",
        name="攻击药水",
        description="从 3 张随机攻击牌中选择 1 张加入你的手牌。这张牌在本回合耗能变为 0。",
        target="self",
        quantity="common",
        effects=[],
    )


def create_skill_potion():
    return PotionTemplate(
        potion_id="potion.skill",
        name="技能药水",
        description="从 3 张随机技能牌中选择 1 张加入你的手牌。这张牌在本回合耗能变为 0。",
        target="self",
        quantity="common",
        effects=[],
    )


def create_power_potion():
    return PotionTemplate(
        potion_id="potion.power",
        name="能力药水",
        description="从 3 张随机能力牌中选择 1 张加入你的手牌。这张牌在本回合耗能变为 0。",
        target="self",
        quantity="common",
        effects=[],
    )


def create_forges_blessing():
    return PotionTemplate(
        potion_id="potion.forges_blessing",
        name="熔炉的祝福",
        description="在本场战斗中升级手牌中的所有牌。神圣树皮不会使该药水翻倍。",
        target="self",
        quantity="common",
        effects=[
            {
                "op": "upgrade_cards",
                "scope": "hand",
                "mode": "all",
            }
        ],
    )
