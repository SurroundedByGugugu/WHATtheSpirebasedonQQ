# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import KEYWORD_EXHAUST

#staring
def create_transfer():
    return CardTemplate(
        card_id="card.transfer",
        name="转移",
        card_type="skill",
        cost=0,
        target="self",
        keywords=[
            KEYWORD_EXHAUST
        ],
        description="获得 8 点格挡。消耗。",
        quantity="starting",
        owner_character_id="character.lumine",
        card_vars={
            "block": 8
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
            "name": "转移+",
            "description": "获得 14 点格挡。消耗。",
            "card_vars": {
                "block": 14
            }
        }
    )

def create_inducing():
    return CardTemplate(
        card_id="card.inducing",
        name="感应",
        card_type="skill",
        cost=1,
        target="self",
        description="将你的消耗牌堆中名称中含有“转移”的牌放入你的抽牌堆，并重洗抽牌堆。",
        quantity="starting",
        owner_character_id="character.lumine",
        effects=[
            {
                "op": "move_exhaust_cards_by_name",
                "name_contains": "转移",
                "destination": "draw_pile_shuffle"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "感应+",
            "description": "将你的消耗牌堆中名称中含有“转移”的牌放入你的手牌。",
            "effects": [
                {
                    "op": "move_exhaust_cards_by_name",
                    "name_contains": "转移",
                    "destination": "hand"
                }
            ],
        }
    )

#rare
def create_god_in_hand():
    return CardTemplate(
        card_id="card.god_in_hand",
        name="手中上帝",
        card_type="power",
        cost=3,
        target="self",
        description="结束你的回合。获得 3 点力量、9 点敏捷。接下来 2 个回合开始时，失去 6 点生命、2 点能量；随后失去 20 点生命，并不再失去能量。",
        quantity="rare",
        owner_character_id="character.lumine",
        card_vars={
            "strength": 3,
            "dexterity": 9,
            "hp_loss": 6,
            "energy_loss": 2,
            "duration": 2,
            "final_hp_loss": 20,
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "strength",
                "amount": {
                    "var": "strength"
                }
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "dexterity",
                "amount": {
                    "var": "dexterity"
                }
            },
            {
                "op": "gain_god_in_hand",
                "target": "self",
                "hp_loss": {
                    "var": "hp_loss"
                },
                "energy_loss": {
                    "var": "energy_loss"
                },
                "duration": {
                    "var": "duration"
                },
                "final_hp_loss": {
                    "var": "final_hp_loss"
                }
            },
            {
                "op": "force_end_turn"
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "手中上帝+",
            "description": "结束你的回合。获得 6 点力量、6 点敏捷。接下来 3 个回合开始时，失去 3 点生命、1 点能量；随后失去 30 点生命，并不再失去能量。",
            "card_vars": {
                "strength": 6,
                "dexterity": 6,
                "hp_loss": 3,
                "energy_loss": 1,
                "duration": 3,
                "final_hp_loss": 30,
            }
        }
    )

def create_cheap_intuition():
    return CardTemplate(
        card_id="card.cheap_intuition",
        name="廉价直觉",
        card_type="skill",
        cost=1,
        target="self",
        description="将你手牌中所有技能牌变为转移。",
        quantity="rare",
        owner_character_id="character.lumine",
        effects=[
            {
                "op": "transform_hand_skills_to_card",
                "new_card_id": "card.transfer",
                "new_card_upgraded": False
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "廉价直觉+",
            "description": "将你手牌中所有技能牌变为转移+。",
            "effects": [
                {
                    "op": "transform_hand_skills_to_card",
                    "new_card_id": "card.transfer",
                    "new_card_upgraded": True
                }
            ],
        }
    )

#uncommon
def create_energetic():
    return CardTemplate(
        card_id="card.energetic",
        name="精力充沛",
        card_type="skill",
        cost=0,
        target="self",
        description="本回合失去 5 点敏捷。获得 2 点能量。抽 1 张牌。",
        quantity="uncommon",
        owner_character_id="character.lumine",
        card_vars={
            "dexterity_loss": 5,
            "energy": 2,
            "draw": 1,
        },
        effects=[
            {
                "op": "lose_dexterity_this_turn",
                "amount": {
                    "var": "dexterity_loss"
                }
            },
            {
                "op": "gain_energy",
                "amount": {
                    "var": "energy"
                }
            },
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "精力充沛+",
            "description": "本回合失去 5 点敏捷。获得 3 点能量。抽 2 张牌。",
            "card_vars": {
                "energy": 3,
                "draw": 2,
            },
        }
    )

def create_mirage_shadows():
    return CardTemplate(
        card_id="card.mirage_shadows",
        name="蜃楼复影",
        card_type="skill",
        cost="X",
        target="self",
        description="获得 12 点格挡。如果 X 的值为 3 及以上，接下来 X 回合开始时，获得 6 点格挡。消耗。",
        quantity="uncommon",
        owner_character_id="character.lumine",
        card_vars={
            "block_0": 12,
            "block_1": 6,
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block_0",
                    "modifier_profile": "block"
                }
            },
            {
                "op": "gain_mirage_shadows",
                "target": "self",
                "threshold": 3,
                "duration_add": 0,
                "amount": {
                    "var": "block_1"
                }
            }
        ],
        keywords=[
            KEYWORD_EXHAUST
        ],
        upgraded=False,
        upgrade_patch={
            "name": "蜃楼复影+",
            "description": "获得 16 点格挡。如果 X 的值为 2 及以上，接下来 X+1 回合开始时，获得 8 点格挡。",
            "card_vars": {
                "block_0": 16,
                "block_1": 8,
            },
            "remove_keywords": [
                KEYWORD_EXHAUST
            ],
            "patches": [
                {
                    "path": ["effects", 1, "threshold"],
                    "value": 2
                },
                {
                    "path": ["effects", 1, "duration_add"],
                    "value": 1
                }
            ],
        }
    )

#common
def create_factor_separate():
    return CardTemplate(
        card_id="card.factor_separate",
        name="因子切割",
        card_type="attack",
        cost=1,
        target="enemy",
        description="如果敌人有格挡，则给予 1 层易伤、虚弱。造成 6 点伤害。",
        quantity="common",
        owner_character_id="character.lumine",
        card_vars={
            "damage": 6,
            "status_amount": 1,
        },
        effects=[
            {
                "op": "gain_status_if_target_has_block",
                "target": "selected_enemy",
                "statuses": ["vulnerable", "weak"],
                "amount": {
                    "var": "status_amount"
                }
            },
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "var": "damage",
                    "modifier_profile": "attack_damage"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "因子切割+",
            "description": "如果敌人有格挡，则给予 1 层易伤、虚弱。造成 8 点伤害。",
            "card_vars": {
                "damage": 8
            }
        }
    )

def create_fast_transfer():
    return CardTemplate(
        card_id="card.fast_transfer",
        name="快速转移",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 10 点格挡。本场战斗中每次打出时，增加 1 点获得的格挡。",
        quantity="common",
        owner_character_id="character.lumine",
        card_vars={
            "block": 10,
            "increment": 1
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
                "op": "increase_card_var",
                "var": "block",
                "amount": {
                    "var": "increment"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "快速转移+",
            "description": "获得 10 点格挡。本场战斗中每次打出时，增加 2 点获得的格挡。",
            "card_vars": {
                "increment": 2
            }
        }
    )