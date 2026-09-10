# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST


def create_dragon_dance():
    return CardTemplate(
        card_id="card.dance.dragon_dance",
        name="龙舞",
        card_type="skill",
        cost=1,
        target="self",
        description="当前力量和敏捷变为原来的 1.5 倍。消耗。",
        quantity="dance",
        owner_character_id="",
        card_vars={"multiplier": 1.5},
        effects=[
            {
                "op": "scale_status",
                "target": "self",
                "status": "strength",
                "multiplier_var": "multiplier"
            },
            {
                "op": "scale_status",
                "target": "self",
                "status": "dexterity",
                "multiplier_var": "multiplier"
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "龙舞+",
            "description": "当前力量和敏捷变为原来的 1.5 倍。",
            "remove_keywords": [KEYWORD_EXHAUST],
        },
    )


def create_swords_dance():
    return CardTemplate(
        card_id="card.dance.swords_dance",
        name="剑舞",
        card_type="skill",
        cost=1,
        target="self",
        description="当前力量变为原来的 2 倍。消耗。",
        quantity="dance",
        owner_character_id="",
        card_vars={"multiplier": 2.0},
        effects=[
            {
                "op": "scale_status",
                "target": "self",
                "status": "strength",
                "multiplier_var": "multiplier"
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "剑舞+",
            "description": "当前力量变为原来的 2 倍。",
            "remove_keywords": [KEYWORD_EXHAUST],
        },
    )


def create_petal_dance():
    return CardTemplate(
        card_id="card.dance.petal_dance",
        name="花瓣舞",
        card_type="attack",
        cost=2,
        target="random_enemy",
        description=(
            "接下来 2 回合结束时（包含当前回合），"
            "对随机敌人造成 12 点伤害。"
            "效果结束时获得 1 回合混乱。消耗。"
        ),
        quantity="dance",
        attack_element="wind",
        owner_character_id="",
        card_vars={
            "damage": 12,
            "duration": 2
        },
        effects=[
            {
                "op": "start_petal_dance",
                "damage": {"var": "damage"},
                "duration": {"var": "duration"}
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "花瓣舞+",
            "description": (
                "接下来 3 回合结束时（包含当前回合），"
                "对随机敌人造成 16 点伤害。"
                "效果结束时获得 1 回合混乱。消耗。"
            ),
            "card_vars": {
                "damage": 16,
                "duration": 3
            },
        },
    )


def create_feather_dance():
    return CardTemplate(
        card_id="card.dance.feather_dance",
        name="羽毛舞",
        card_type="skill",
        cost=1,
        target="enemy",
        description="敌人失去一半力量，至少失去 3 点力量。消耗。",
        quantity="dance",
        owner_character_id="",
        card_vars={"minimum_loss": 3},
        effects=[
            {
                "op": "reduce_enemy_strength_half",
                "target": "selected_enemy",
                "minimum_var": "minimum_loss"
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "羽毛舞+",
            "description":"敌人失去一半力量，至少失去 4 点力量。消耗。",
            "card_vars": {"minimum_loss": 4},
        },
    )


def create_quiver_dance():
    return CardTemplate(
        card_id="card.dance.quiver_dance",
        name="蝶舞",
        card_type="skill",
        cost=1,
        target="self",
        description=(
            "获得 1 点力量和 1 点敏捷，"
            "然后当前敏捷变为原来的 1.5 倍。消耗。"
        ),
        quantity="dance",
        owner_character_id="",
        card_vars={
            "gain": 1,
            "dex_multiplier": 1.5
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "strength",
                "amount": {"var": "gain"}
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "dexterity",
                "amount": {"var": "gain"}
            },
            {
                "op": "scale_status",
                "target": "self",
                "status": "dexterity",
                "multiplier_var": "dex_multiplier"
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "蝶舞+",
            "description":"获得 1 点力量和 1 点敏捷，然后当前敏捷变为原来的 2 倍。消耗。",
            "card_vars": {
                "dex_multiplier": 2.0
            },
        },
    )


def create_fiery_dance():
    return CardTemplate(
        card_id="card.dance.fiery_dance",
        name="火之舞",
        card_type="attack",
        cost=1,
        target="enemy",
        description="获得 1 点力量。造成 7 点伤害。消耗。",
        quantity="dance",
        attack_element="fire",
        owner_character_id="",
        card_vars={
            "strength": 1,
            "damage": 7
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "strength",
                "amount": {"var": "strength"}
            },
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "var": "damage",
                    "modifier_profile": "attack_damage"
                }
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "火之舞+",
            "description": "获得 1 点力量。造成 11 点伤害。消耗。",
            "card_vars": {"damage": 11},
        },
    )


def create_aqua_step():
    return CardTemplate(
        card_id="card.dance.aqua_step",
        name="流水旋舞",
        card_type="attack",
        cost=1,
        target="enemy",
        description="获得 1 点敏捷。造成 7 点伤害。消耗。",
        quantity="dance",
        attack_element="water",
        owner_character_id="",
        card_vars={
            "dexterity": 1,
            "damage": 7
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "dexterity",
                "amount": {"var": "dexterity"}
            },
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "var": "damage",
                    "modifier_profile": "attack_damage"
                }
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "流水旋舞+",
            "description": "获得 1 点敏捷。造成 11 点伤害。消耗。",
            "card_vars": {"damage": 11},
        },
    )


def create_dragon_sound_inspiration():
    return CardTemplate(
        card_id="card.dance.dragon_sound_inspiration",
        name="龙声鼓舞",
        card_type="skill",
        cost=1,
        target="self",
        description="下一次造成的伤害翻倍。消耗。",
        quantity="dance",
        owner_character_id="",
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "dragon_sound_inspiration",
                "amount": 1
            },
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "龙声鼓舞+",
            "cost": 0,
            "description": "下一次造成的伤害翻倍。消耗。",
        },
    )


DANCE_CARD_IDS = [
    "card.dance.dragon_dance",
    "card.dance.swords_dance",
    "card.dance.petal_dance",
    "card.dance.feather_dance",
    "card.dance.quiver_dance",
    "card.dance.fiery_dance",
    "card.dance.aqua_step",
    "card.dance.dragon_sound_inspiration",
]