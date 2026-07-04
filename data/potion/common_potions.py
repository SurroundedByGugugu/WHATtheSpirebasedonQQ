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

def create_block_potion():
    return PotionTemplate(
        potion_id="potion.block",
        name="格挡药水",
        description="获得 12 点格挡。",
        target="self",
        quantity="common",
        effect_vars={"block": 12},
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {"var": "block", "modifier_profile": None}
            }
        ],
    )


def create_blood_potion():
    return PotionTemplate(
        potion_id="potion.blood",
        name="鲜血药水",
        description="回复最大生命值的 20%。",
        target="self",
        quantity="common",
        owner_character_id="character.armored_warrior",
        effects=[
            {
                "op": "heal_player_by_max_hp_percent",
                "percent": 0.20
            }
        ],
    )


def create_energy_potion():
    return PotionTemplate(
        potion_id="potion.energy",
        name="能量药水",
        description="获得 2 点能量。",
        target="self",
        quantity="common",
        effect_vars={"energy": 2},
        effects=[
            {
                "op": "gain_energy",
                "amount": {"var": "energy"}
            }
        ],
    )


def create_explosive_potion():
    return PotionTemplate(
        potion_id="potion.explosive",
        name="爆炸药水",
        description="对所有敌人造成 10 点伤害。",
        target="none",
        quantity="common",
        effect_vars={"damage": 10},
        effects=[
            {
                "op": "deal_damage_all_enemies",
                "amount": {"var": "damage", "modifier_profile": None}
            }
        ],
    )


def create_fear_potion():
    return PotionTemplate(
        potion_id="potion.fear",
        name="恐惧药水",
        description="给予 3 层易伤。",
        target="enemy",
        quantity="common",
        effect_vars={"vulnerable": 3},
        effects=[
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "vulnerable",
                "amount": {"var": "vulnerable"}
            }
        ],
    )


def create_poison_potion():
    return PotionTemplate(
        potion_id="potion.poison",
        name="毒药水",
        description="给予 6 层中毒。",
        target="enemy",
        quantity="common",
        effect_vars={"poison": 6},
        effects=[
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "poison",
                "amount": {"var": "poison"}
            }
        ],
    )


def create_speed_potion():
    return PotionTemplate(
        potion_id="potion.speed",
        name="速度药水",
        description="获得 5 点敏捷。在你的回合结束时，失去 5 点敏捷。",
        target="self",
        quantity="common",
        effect_vars={"dexterity": 5},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "dexterity",
                "amount": {"var": "dexterity"}
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "temporary_dexterity_gain",
                "amount": {"var": "dexterity"}
            },
        ],
    )


def create_steroid_potion():
    return PotionTemplate(
        potion_id="potion.steroid",
        name="类固醇药水",
        description="获得 5 点力量。在你的回合结束时，失去 5 点力量。",
        target="self",
        quantity="common",
        effect_vars={"strength": 5},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "strength",
                "amount": {"var": "strength"}
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "flex",
                "amount": {"var": "strength"}
            },
        ],
    )


def create_weak_potion():
    return PotionTemplate(
        potion_id="potion.weak",
        name="虚弱药水",
        description="给予 3 层虚弱。",
        target="enemy",
        quantity="common",
        effect_vars={"weak": 3},
        effects=[
            {
                "op": "gain_status",
                "target": "selected_enemy",
                "status": "weak",
                "amount": {"var": "weak"}
            }
        ],
    )


def create_swift_potion():
    return PotionTemplate(
        potion_id="potion.swift",
        name="迅捷药水",
        description="抽 3 张牌。",
        target="self",
        quantity="common",
        effect_vars={"draw": 3},
        effects=[
            {
                "op": "draw_cards",
                "amount": {"var": "draw"}
            }
        ],
    )


def create_colorless_potion():
    return PotionTemplate(
        potion_id="potion.colorless",
        name="无色药水",
        description="从 3 张随机无色牌中选择 1 张加入你的手牌。这张牌在本回合耗能变为 0。神圣树皮：进行一次选择，将被选择的牌加入两次。",
        target="self",
        quantity="common",
        effects=[],
    )