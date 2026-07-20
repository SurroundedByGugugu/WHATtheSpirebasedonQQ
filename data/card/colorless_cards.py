# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE
)

def _simple_attack(card_id, name, cost, description, quantity, damage, upgraded_damage, upgrade_description, keywords=None, attack_type="magic"):
    return CardTemplate(
        card_id=card_id,
        name=name,
        card_type="attack",
        cost=cost,
        target="enemy",
        description=description,
        quantity=quantity,
        attack_type=attack_type,
        owner_character_id="",
        card_vars={"damage": damage},
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        keywords=list(keywords or []),
        upgraded=False,
        upgrade_patch={
            "name": name + "+",
            "description": upgrade_description,
            "card_vars": {"damage": upgraded_damage}
        }
    )
def _simple_block(card_id, name, cost, description, quantity, block, upgraded_block, upgrade_description, keywords=None):
    return CardTemplate(
        card_id=card_id,
        name=name,
        card_type="skill",
        cost=cost,
        target="self",
        description=description,
        quantity=quantity,
        owner_character_id="",
        card_vars={"block": block},
        effects=[{
            "op": "gain_block",
            "target": "self",
            "amount": {"var": "block", "modifier_profile": "block"}
        }],
        keywords=list(keywords or []),
        upgraded=False,
        upgrade_patch={
            "name": name + "+",
            "description": upgrade_description,
            "card_vars": {"block": upgraded_block}
        }
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
        owner_character_id="",
        card_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "burst",
                "amount": {
                    "var": "count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "爆发+",
            "description": "本回合内，你打出的下 2 张技能牌会打出 2 次。",
            "card_vars": {
                "count": 2
            },
        }
    )
def create_amplify():
    return CardTemplate(
        card_id="card.amplify",
        name="增幅",
        card_type="skill",
        cost=1,
        target="self",
        description="本回合内，你打出的下一张能力牌会打出 2 次。",
        quantity="rare",
        owner_character_id="",
        card_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "amplify",
                "amount": {
                    "var": "count"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "增幅+",
            "description": "本回合内，你打出的下 2 张能力牌会打出 2 次。",
            "card_vars": {
                "count": 2
            },
        }
    )

def create_soul():
    return CardTemplate(
        card_id="card.soul",
        name="灵魂",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 2 张牌。消耗。",
        quantity="event",
        owner_character_id="",
        card_vars={
            "draw": 2
        },
        effects=[
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "灵魂+",
            "description": "抽 3 张牌。消耗。",
            "card_vars": {
                "draw": 3
            },
        }
    )

def create_shiv():
    return CardTemplate(
        card_id="card.shiv",
        name="小刀",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 4 点伤害。消耗。",
        quantity="event",
        attack_type="piercing",
        owner_character_id="",
        card_vars={"damage": 4},
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "小刀+",
            "description": "造成 6 点伤害。消耗。",
            "card_vars": {"damage": 6}
        }
    )

def create_jax():
    from game.constants import KEYWORD_EXHAUST
    return CardTemplate(
        card_id="card.jax",
        name="J.A.X.",
        card_type="skill",
        cost=0,
        target="self",
        description="失去 3 点生命。获得 2 点力量。消耗。",
        quantity="event",
        owner_character_id="",
        card_vars={"hp_loss": 3, "strength": 2},
        effects=[
            {"op": "lose_hp", "amount": {"var": "hp_loss"}},
            {"op": "gain_status", "target": "self", "status": "strength", "amount": {"var": "strength"}},
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "J.A.X.+",
            "description": "失去 3 点生命。获得 3 点力量。消耗。",
            "card_vars": {"strength": 3}
        }
    )

#uncommon attack
def create_swift_strike():
    return CardTemplate(
        card_id="card.swift_strike",
        name="迅捷打击",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 7 点伤害。",
        quantity="uncommon",
        attack_type="blunt",
        owner_character_id="",
        card_vars={"damage": 7},
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        upgraded=False,
        upgrade_patch={
            "name": "迅捷打击+",
            "description": "造成 10 点伤害。",
            "card_vars": {"damage": 10}
        }
    )
def create_dramatic_entrance():
    return CardTemplate(
        card_id="card.dramatic_entrance",
        name="闪亮登场",
        card_type="attack",
        cost=0,
        target="all_enemies",
        description="固有。对所有敌人造成 8 点伤害。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"damage": 8},
        effects=[{
            "op": "deal_damage_all_enemies",
            "target": "all_enemies",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
        }],
        keywords=[KEYWORD_EXHAUST,KEYWORD_INNATE],
        upgraded=False,
        upgrade_patch={
            "name": "闪亮登场+",
            "description": "固有。对所有敌人造成 12 点伤害。消耗。",
            "card_vars": {"damage": 12}
        }
    )
def create_flash_of_steel():
    return CardTemplate(
        card_id="card.flash_of_steel",
        name="亮剑",
        card_type="attack",
        cost=0,
        target="enemy",
        description="造成 3 点伤害。抽 1 张牌。",
        quantity="uncommon",
        attack_type="slash",
        card_vars={
            "damage": 3,
            "draw": 1
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
                "op": "draw_cards",
                "amount": {
                    "var": "draw"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "亮剑+",
            "description": "造成 6 点伤害。抽 1 张牌。",
            "card_vars": {
                "damage": 6
            },
        }
    )
def create_mind_blast():
    return CardTemplate(
        card_id="card.mind_blast",
        name="心灵震慑",
        card_type="attack",
        cost=2,
        target="enemy",
        description="固有。造成你抽牌堆中剩余牌数的伤害。",
        quantity="uncommon",
        attack_type="magic",
        owner_character_id="",
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {
                "draw_pile_count": True,
                "modifier_profile": "attack_damage"
            }
        }],
        keywords=[KEYWORD_INNATE],
        upgraded=False,
        upgrade_patch={
            "name": "心灵震慑+",
            "cost": 1,
            "description": "固有。造成你抽牌堆中剩余牌数的伤害。"
        }
    )

#rare attack
def create_hand_of_greed():
    return CardTemplate(
        card_id="card.hand_of_greed",
        name="贪婪之手",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 20 点伤害。斩杀时，获得 20 金币。",
        quantity="rare",
        attack_type="magic",
        owner_character_id="",
        card_vars={
            "damage": 20,
            "gold_gain": 20
        },
        effects=[
            {
                "op": "deal_damage_gain_gold_on_non_minion_kill",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "damage",
                    "modifier_profile": "attack_damage"
                },
                "gold_gain": {
                    "var": "gold_gain"
                }
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "贪婪之手+",
            "cost": 1,
            "description": "造成 25 点伤害。斩杀时，获得 25 金币。",
            "card_vars": {
                "damage": 25,
                "gold_gain": 25
            }
        }
    )


#uncommon skill
def create_bandage_up():
    return CardTemplate(
        card_id="card.bandage_up",
        name="包扎",
        card_type="skill",
        cost=0,
        target="self",
        description="回复 4 点生命。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"heal": 4},
        effects=[{"op": "heal_player", "amount": {"var": "heal"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "包扎+",
            "description": "回复 6 点生命。消耗。",
            "card_vars": {"heal": 6}
        }
    )
def create_blind():
    return CardTemplate(
        card_id="card.blind",
        name="致盲",
        card_type="skill",
        cost=0,
        target="enemy",
        description="给予 2 层虚弱。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"weak": 2},
        effects=[{"op": "gain_status", "target": "selected_enemy", "status": "weak", "amount": {"var": "weak"}}],
        upgraded=False,
        upgrade_patch={
            "name": "致盲+",
            "target": "all_enemies",
            "description": "给予所有敌人 2 层虚弱。",
            "effects": [{"op": "gain_status", "target": "all_enemies", "status": "weak", "amount": {"var": "weak"}}]
        }
    )
def create_dark_shackles():
    return CardTemplate(
        card_id="card.dark_shackles",
        name="黑暗镣铐",
        card_type="skill",
        cost=0,
        target="enemy",
        description="让一名敌人在本回合内失去 9 点力量。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"strength_loss": -9},
        effects=[{"op": "gain_status", "target": "selected_enemy", "status": "strength", "amount": {"var": "strength_loss"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "黑暗镣铐+",
            "description": "让一名敌人在本回合内失去 15 点力量。消耗。",
            "card_vars": {"strength_loss": -15}
        }
    )
def create_deep_breath():
    return CardTemplate(
        card_id="card.deep_breath",
        name="深呼吸",
        card_type="skill",
        cost=0,
        target="self",
        description="将你的弃牌堆洗牌后放入你的抽牌堆。抽 1 张牌。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"draw": 1},
        effects=[
            {"op": "shuffle_discard_into_draw"},
            {"op": "draw_cards", "amount": {"var": "draw"}}
        ],
        upgraded=False,
        upgrade_patch={
            "name": "深呼吸+",
            "description": "将你的弃牌堆洗牌后放入你的抽牌堆。抽 2 张牌。",
            "card_vars": {"draw": 2}
        }
    )
def create_discovery():
    return CardTemplate(
        card_id="card.discovery",
        name="发现",
        card_type="skill",
        cost=1,
        target="self",
        description="从 3 张随机牌中选择 1 张加入你的手牌。这张牌在本回合耗能变为 0。消耗。",
        quantity="uncommon",
        owner_character_id="",
        effects=[{"op": "request_discovery_card", "option_count": 3}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "发现+",
            "description": "从 3 张随机牌中选择 1 张加入你的手牌。这张牌在本回合耗能变为 0。",
            "remove_keywords": [KEYWORD_EXHAUST]
        }
    )
def create_enlightenment():
    return CardTemplate(
        card_id="card.enlightenment",
        name="开悟",
        card_type="skill",
        cost=0,
        target="self",
        description="在这个回合，你当前手牌中所有牌的耗能降低到 1。",
        quantity="uncommon",
        owner_character_id="",
        effects=[{"op": "reduce_hand_costs_to", "cost": 1, "duration": "turn"}],
        upgraded=False,
        upgrade_patch={
            "name": "开悟+",
            "description": "在本场战斗，你当前手牌中所有牌的耗能降低到 1。",
            "effects": [{"op": "reduce_hand_costs_to", "cost": 1, "duration": "combat"}]
        }
    )
def create_finesse():
    return CardTemplate(
        card_id="card.finesse",
        name="妙计",
        card_type="skill",
        cost=0,
        target="self",
        description="获得 2 点格挡。抽 1 张牌。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"block": 2, "draw": 1},
        effects=[
            {"op": "gain_block", "target": "self", "amount": {"var": "block", "modifier_profile": "block"}},
            {"op": "draw_cards", "amount": {"var": "draw"}}
        ],
        upgraded=False,
        upgrade_patch={
            "name": "妙计+",
            "description": "获得 4 点格挡。抽 1 张牌。",
            "card_vars": {"block": 4}
        }
    )
def create_forethought():
    return CardTemplate(
        card_id="card.forethought",
        name="预谋",
        card_type="skill",
        cost=0,
        target="self",
        description="将手牌中的一张牌放到抽牌堆的底部。并且这张牌在被打出之前，耗能变为 0。",
        quantity="uncommon",
        owner_character_id="",
        effects=[{"op": "request_hand_to_draw_bottom_temp_cost_zero"}],
        upgraded=False,
        upgrade_patch={
            "name": "预谋+",
            "description": "将手牌中的任意张牌放到抽牌堆的底部。并且它们被打出之前，耗能变为 0。"
        }
    )
def create_impatience():
    return CardTemplate(
        card_id="card.impatience",
        name="急躁",
        card_type="skill",
        cost=0,
        target="self",
        description="如果你的手牌中没有攻击牌，抽 2 张牌。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"draw": 2},
        effects=[{"op": "draw_if_no_attack_in_hand", "amount": {"var": "draw"}}],
        upgraded=False,
        upgrade_patch={
            "name": "急躁+",
            "description": "如果你的手牌中没有攻击牌，抽 3 张牌。",
            "card_vars": {"draw": 3}
        }
    )
def create_jack_of_all_trades():
    return CardTemplate(
        card_id="card.jack_of_all_trades",
        name="花样百出",
        card_type="skill",
        cost=0,
        target="self",
        description="增加 1 张随机无色牌到你的手牌。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"count": 1},
        effects=[{"op": "add_random_colorless_to_hand_temp_cost_zero", "amount": {"var": "count"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "花样百出+",
            "description": "增加 2 张随机无色牌到你的手牌。消耗。",
            "card_vars": {"count": 2}
        }
    )
def create_madness():
    return CardTemplate(
        card_id="card.madness",
        name="疯狂",
        card_type="skill",
        cost=1,
        target="self",
        description="你手牌中一张随机牌在本场战斗中耗能变为 0。消耗。",
        quantity="uncommon",
        owner_character_id="",
        effects=[{"op": "random_hand_card_cost_zero"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "疯狂+",
            "cost": 0,
            "description": "你手牌中一张随机牌在本场战斗中耗能变为 0。消耗。"
        }
    )
def create_panacea():
    return CardTemplate(
        card_id="card.panacea",
        name="万能药",
        card_type="skill",
        cost=0,
        target="self",
        description="获得 1 层人工制品。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"artifact": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "artifact", "amount": {"var": "artifact"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "万能药+",
            "description": "获得 2 层人工制品。消耗。",
            "card_vars": {"artifact": 2}
        }
    )
def create_panic_button():
    return CardTemplate(
        card_id="card.panic_button",
        name="应急按钮",
        card_type="skill",
        cost=0,
        target="self",
        description="获得 30 点格挡。你在接下来 2 回合内无法再从卡牌中获得格挡。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"block": 30, "no_card_block": 2},
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {"var": "block", "modifier_profile": "block"}
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "no_card_block",
                "amount": {"var": "no_card_block"}
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "应急按钮+",
            "description": "获得 40 点格挡。你在接下来 2 回合内无法再从卡牌中获得格挡。消耗。",
            "card_vars": {"block": 40}
        }
    )
def create_purity():
    return CardTemplate(
        card_id="card.purity",
        name="净化",
        card_type="skill",
        cost=0,
        target="self",
        description="从手牌中选择最多 3 张牌消耗。消耗。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"max_count": 3},
        effects=[{"op": "request_exhaust_multiple_hand_cards", "max_count": {"var": "max_count"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "净化+",
            "description": "从手牌中选择最多 5 张牌消耗。消耗。",
            "card_vars": {"max_count": 5}
        }
    )
def create_trip():
    return CardTemplate(
        card_id="card.trip",
        name="绊倒",
        card_type="skill",
        cost=0,
        target="enemy",
        description="给予 2 层易伤。",
        quantity="uncommon",
        owner_character_id="",
        card_vars={"vulnerable": 2},
        effects=[{"op": "gain_status", "target": "selected_enemy", "status": "vulnerable", "amount": {"var": "vulnerable"}}],
        upgraded=False,
        upgrade_patch={
            "name": "绊倒+",
            "target": "all_enemies",
            "description": "给予所有敌人 2 层易伤。",
            "effects": [{"op": "gain_status", "target": "all_enemies", "status": "vulnerable", "amount": {"var": "vulnerable"}}]
        }
    )
def create_good_instincts():
    return _simple_block(
        "card.good_instincts", "优秀直觉", 0,
        "获得 6 点格挡。", "uncommon", 6, 9, "获得 9 点格挡。"
    )

#rare skill
def create_apotheosis():
    return CardTemplate(
        card_id="card.apotheosis",
        name="神化",
        card_type="skill",
        cost=2,
        target="self",
        description="在本场战斗中升级你的所有牌。消耗。",
        quantity="rare",
        owner_character_id="",
        effects=[{"op": "upgrade_cards", "scope": "combat", "mode": "all"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "神化+",
            "cost": 1,
            "description": "在本场战斗中升级你的所有牌。消耗。"
        }
    )
def create_chrysalis():
    return CardTemplate(
        card_id="card.chrysalis",
        name="结茧",
        card_type="skill",
        cost=2,
        target="self",
        description="在你的抽牌堆中加入 3 张随机技能牌。它们在本场战斗中耗能为 0。消耗。",
        quantity="rare",
        owner_character_id="",
        card_vars={"count": 3},
        effects=[{"op": "add_random_cards_to_draw_pile_temp_cost_zero", "card_type": "skill", "amount": {"var": "count"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "结茧+",
            "description": "在你的抽牌堆中加入 5 张随机技能牌。它们在本场战斗中耗能为 0。消耗。",
            "card_vars": {"count": 5}
        }
    )
def create_master_of_strategy():
    return CardTemplate(
        card_id="card.master_of_strategy",
        name="战略大师",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 3 张牌。消耗。",
        quantity="rare",
        owner_character_id="",
        card_vars={"draw": 3},
        effects=[{"op": "draw_cards", "amount": {"var": "draw"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "战略大师+",
            "description": "抽 4 张牌。消耗。",
            "card_vars": {"draw": 4}
        }
    )
def create_metamorphosis():
    return CardTemplate(
        card_id="card.metamorphosis",
        name="羽化",
        card_type="skill",
        cost=2,
        target="self",
        description="在你的抽牌堆中加入 3 张随机攻击牌。它们在本场战斗中耗能为 0。消耗。",
        quantity="rare",
        owner_character_id="",
        card_vars={"count": 3},
        effects=[{"op": "add_random_cards_to_draw_pile_temp_cost_zero", "card_type": "attack", "amount": {"var": "count"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "羽化+",
            "description": "在你的抽牌堆中加入 5 张随机攻击牌。它们在本场战斗中耗能为 0。消耗。",
            "card_vars": {"count": 5}
        }
    )
def create_secret_technique():
    return CardTemplate(
        card_id="card.secret_technique",
        name="秘密技法",
        card_type="skill",
        cost=0,
        target="self",
        description="从抽牌堆中选择一张技能牌放入你的手牌。消耗。",
        quantity="rare",
        owner_character_id="",
        effects=[{"op": "request_draw_pile_card_to_hand", "card_type": "skill"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "秘密技法+",
            "description": "从抽牌堆中选择一张技能牌放入你的手牌。",
            "remove_keywords": [KEYWORD_EXHAUST]
        }
    )
def create_secret_weapon():
    return CardTemplate(
        card_id="card.secret_weapon",
        name="秘密武器",
        card_type="skill",
        cost=0,
        target="self",
        description="从抽牌堆中选择一张攻击牌放入你的手牌。消耗。",
        quantity="rare",
        owner_character_id="",
        effects=[{"op": "request_draw_pile_card_to_hand", "card_type": "attack"}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "秘密武器+",
            "description": "从抽牌堆中选择一张攻击牌放入你的手牌。",
            "remove_keywords": [KEYWORD_EXHAUST]
        }
    )
def create_the_bomb():
    return CardTemplate(
        card_id="card.the_bomb",
        name="炸弹",
        card_type="skill",
        cost=2,
        target="self",
        description="在 3 回合结束后，对所有敌人造成 40 点伤害。",
        quantity="rare",
        owner_character_id="",
        card_vars={"damage": 40},
        effects=[{"op": "gain_bomb", "damage": {"var": "damage"}, "turns": 3}],
        upgraded=False,
        upgrade_patch={
            "name": "炸弹+",
            "description": "在 3 回合结束后，对所有敌人造成 50 点伤害。",
            "card_vars": {"damage": 50}
        }
    )
def create_thinking_ahead():
    return CardTemplate(
        card_id="card.thinking_ahead",
        name="深谋远虑",
        card_type="skill",
        cost=0,
        target="self",
        description="抽 2 张牌，然后将手牌中的一张牌放到你抽牌堆的顶端。消耗。",
        quantity="rare",
        owner_character_id="",
        card_vars={"draw": 2},
        effects=[
            {"op": "draw_cards", "amount": {"var": "draw"}},
            {"op": "request_hand_to_draw_top"}
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "深谋远虑+",
            "description": "抽 2 张牌，然后将手牌中的一张牌放到你抽牌堆的顶端。",
            "remove_keywords": [KEYWORD_EXHAUST]
        }
    )
def create_transmutation():
    return CardTemplate(
        card_id="card.transmutation",
        name="转化",
        card_type="skill",
        cost="X",
        target="self",
        description="在你的手牌中加入 X 张随机无色牌。它们在本回合的耗能变为 0。消耗。",
        quantity="rare",
        owner_character_id="",
        effects=[{"op": "add_random_colorless_to_hand_temp_cost_zero", "amount": {"x_var": "x"}, "temp_cost_zero": True}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "转化+",
            "description": "在你的手牌中放入 X 张升级过的随机无色牌。它们在本回合的耗能变为 0。消耗。",
            "effects": [{"op": "add_random_colorless_to_hand_temp_cost_zero", "amount": {"x_var": "x"}, "temp_cost_zero": True, "upgrade": True}]
        }
    )
def create_violence():
    return CardTemplate(
        card_id="card.violence",
        name="暴力",
        card_type="skill",
        cost=0,
        target="self",
        description="随机将你抽牌堆中 3 张攻击牌加入你的手牌。消耗。",
        quantity="rare",
        owner_character_id="",
        card_vars={"count": 3},
        effects=[{"op": "move_random_draw_pile_cards_to_hand", "card_type": "attack", "amount": {"var": "count"}}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "暴力+",
            "description": "随机将你抽牌堆中 4 张攻击牌加入你的手牌。消耗。",
            "card_vars": {"count": 4}
        }
    )
def create_mirror_reflection():
    return CardTemplate(
        card_id="card.mirror_reflection",
        name="映镜",
        card_type="skill",
        cost=2,
        target="enemy",
        description="消耗。获得和目标同样的正面增益。",
        quantity="rare",
        owner_character_id="",
        effects=[
            {
                "op": "mirror_target_positive_buffs",
                "target": "selected_enemy",
                "exclude_statuses": [
                    # 四层 / Boss 机制
                    "beat_of_death",      # 死亡律动
                    "pain_stab",          # 疼痛戳刺
                    "time_warp",          # 时间扭曲
                    "invincible",         # 坚不可摧

                    # 敌人机制状态
                    "fading",             # 消逝
                    "self_destruct",      # 自爆
                    "life_link",          # 生命链接
                    "shape_shift",        # 形态转换
                    "shifting",           # 变幻
                    "writhing",           # 扭动
                    "spore_cloud",        # 孢子云

                ]
            }
        ],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "映镜+",
            "cost": 1,
            "description": "费用减少 1。消耗。获得和目标同样的正面增益。"
        }
    )


#rare power
def create_magnetism():
    return CardTemplate(
        card_id="card.magnetism",
        name="磁力",
        card_type="power",
        cost=2,
        target="self",
        description="在每回合开始时，增加一张随机无色牌到你的手牌。",
        quantity="rare",
        owner_character_id="",
        card_vars={"amount": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "magnetism", "amount": {"var": "amount"}}],
        upgraded=False,
        upgrade_patch={
            "name": "磁力+",
            "cost": 1,
            "description": "在每回合开始时，增加一张随机无色牌到你的手牌。"
        }
    )
def create_mayhem():
    return CardTemplate(
        card_id="card.mayhem",
        name="乱战",
        card_type="power",
        cost=2,
        target="self",
        description="在你的回合开始时，打出你抽牌堆顶部的牌。",
        quantity="rare",
        owner_character_id="",
        card_vars={"amount": 1},
        effects=[{"op": "gain_status", "target": "self", "status": "mayhem", "amount": {"var": "amount"}}],
        upgraded=False,
        upgrade_patch={
            "name": "乱战+",
            "cost": 1,
            "description": "在你的回合开始时，打出你抽牌堆顶部的牌。"
        }
    )
def create_panache():
    return CardTemplate(
        card_id="card.panache",
        name="神气制胜",
        card_type="power",
        cost=0,
        target="self",
        description="你每在同个回合内打出 5 张牌，就对所有敌人造成 10 点伤害。",
        quantity="rare",
        owner_character_id="",
        card_vars={"damage": 10},
        effects=[{"op": "gain_status", "target": "self", "status": "panache", "amount": {"var": "damage"}}],
        upgraded=False,
        upgrade_patch={
            "name": "神气制胜+",
            "description": "你每在同个回合内打出 5 张牌，就对所有敌人造成 14 点伤害。",
            "card_vars": {"damage": 14}
        }
    )
def create_sadistic_nature():
    return CardTemplate(
        card_id="card.sadistic_nature",
        name="残虐天性",
        card_type="power",
        cost=0,
        target="self",
        description="每当你对一名敌人造成负面状态，使对方受到 5 点伤害。",
        quantity="rare",
        owner_character_id="",
        card_vars={"damage": 5},
        effects=[{"op": "gain_status", "target": "self", "status": "sadistic_nature", "amount": {"var": "damage"}}],
        upgraded=False,
        upgrade_patch={
            "name": "残虐天性+",
            "description": "每当你对一名敌人造成负面状态，使对方受到 7 点伤害。",
            "card_vars": {"damage": 7}
        }
    )

#event attack
def create_bite():
    return CardTemplate(
        card_id="card.bite",
        name="噬咬",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 7 点伤害。回复 2 点生命。",
        quantity="event",
        attack_type="piercing",
        owner_character_id="",
        card_vars={"damage": 7, "heal": 2},
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {"base_var": "damage", "modifier_profile": "attack_damage"}
            },
            {"op": "heal_player", "amount": {"var": "heal"}}
        ],
        upgraded=False,
        upgrade_patch={
            "name": "噬咬+",
            "description": "造成 8 点伤害。回复 3 点生命。",
            "card_vars": {"damage": 8, "heal": 3}
        }
    )
def create_expunger():
    return CardTemplate(
        card_id="card.expunger",
        name="灭除之刃",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 9 点伤害 X 次。",
        quantity="event",
        attack_type="slash",
        owner_character_id="",
        card_vars={"damage": 9},
        effects=[{
            "op": "deal_damage",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            "times": {"x_var": "x"}
        }],
        upgraded=False,
        upgrade_patch={
            "name": "灭除之刃+",
            "description": "造成 15 点伤害 X 次。",
            "card_vars": {"damage": 15}
        }
    )
def create_ritual_dagger():
    return CardTemplate(
        card_id="card.ritual_dagger",
        name="仪式匕首",
        card_type="attack",
        cost=1,
        target="enemy",
        description="造成 15 点伤害。斩杀时，它在本局游戏中的伤害永久性增加 3。消耗。",
        quantity="event",
        attack_type="piercing",
        owner_character_id="",
        card_vars={"damage": 15, "growth": 3},
        effects=[{
            "op": "deal_damage_increase_card_var_on_non_minion_kill",
            "target": "selected_enemy",
            "amount": {"base_var": "damage", "modifier_profile": "attack_damage"},
            "var": "damage",
            "increase": {"var": "growth"}
        }],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "仪式匕首+",
            "description": "造成 15 点伤害。斩杀时，它在本局游戏中的伤害永久性增加 5。消耗。",
            "card_vars": {"growth": 5}
        }
    )
def create_smite():
    return _simple_attack(
        "card.smite", "惩恶", 1,
        "保留。造成 12 点伤害。消耗。", "event", 12, 16,
        "保留。造成 16 点伤害。消耗。",
        keywords=[KEYWORD_RETAIN, KEYWORD_EXHAUST],
        attack_type="blunt"
    )
def create_through_violence():
    return _simple_attack(
        "card.through_violence", "以暴易暴", 0,
        "保留。造成 20 点伤害。消耗。", "event", 20, 30,
        "保留。造成 30 点伤害。消耗。",
        keywords=[KEYWORD_RETAIN, KEYWORD_EXHAUST],
        attack_type="slash"
    )

#event skill
def create_beta():
    return CardTemplate(
        card_id="card.beta",
        name="贝塔",
        card_type="skill",
        cost=2,
        target="self",
        description="将一张欧米伽放入你的抽牌堆中。消耗。",
        quantity="event",
        owner_character_id="",
        effects=[{"op": "add_card_to_draw_pile", "card_id": "card.omega", "amount": 1}],
        keywords=[KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "贝塔+",
            "cost": 1,
            "description": "将一张欧米伽放入你的抽牌堆中。消耗。"
        }
    )
def create_ghostly():
    return CardTemplate(
        card_id="card.ghostly",
        name="灵体",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 1 层无实体。消耗。虚无。",
        quantity="event",
        owner_character_id="",
        card_vars={"intangible": 1},
        effects=[
            {
            "op": "gain_status", 
            "target": "self", 
            "status": "intangible", 
            "amount": {
                "var": "intangible"
                }}],
        keywords=[KEYWORD_EXHAUST, KEYWORD_ETHEREAL],
        upgraded=False,
        upgrade_patch={
            "name": "灵体+",
            "description": "获得 1 层无实体。消耗。",
            "remove_keywords": [KEYWORD_ETHEREAL]
        }
    )
def create_insight():
    return CardTemplate(
        card_id="card.insight",
        name="洞见",
        card_type="skill",
        cost=0,
        target="self",
        description="保留。抽 2 张牌。消耗。",
        quantity="event",
        owner_character_id="",
        card_vars={"draw": 2},
        effects=[{"op": "draw_cards", "amount": {"var": "draw"}}],
        keywords=[KEYWORD_RETAIN, KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "洞见+",
            "description": "保留。抽 3 张牌。消耗。",
            "card_vars": {"draw": 3}
        }
    )
def create_miracle():
    return CardTemplate(
        card_id="card.miracle",
        name="奇迹",
        card_type="skill",
        cost=0,
        target="self",
        description="保留。获得 1 点能量。消耗。",
        quantity="event",
        owner_character_id="",
        card_vars={"energy": 1},
        effects=[{"op": "gain_energy", "amount": {"var": "energy"}}],
        keywords=[KEYWORD_RETAIN, KEYWORD_EXHAUST],
        upgraded=False,
        upgrade_patch={
            "name": "奇迹+",
            "description": "保留。获得 2 点能量。消耗。",
            "card_vars": {"energy": 2}
        }
    )
def create_safety():
    return _simple_block(
        "card.safety", "平安", 1,
        "保留。获得 12 点格挡。消耗。", "event", 12, 16,
        "保留。获得 16 点格挡。消耗。",
        keywords=[KEYWORD_RETAIN, KEYWORD_EXHAUST]
    )

#event power
def create_omega():
    return CardTemplate(
        card_id="card.omega",
        name="欧米伽",
        card_type="power",
        cost=3,
        target="self",
        description="在你的回合结束时，对所有敌人造成 50 点伤害。",
        quantity="event",
        owner_character_id="",
        card_vars={"damage": 50},
        effects=[{"op": "gain_status", "target": "self", "status": "omega", "amount": {"var": "damage"}}],
        upgraded=False,
        upgrade_patch={
            "name": "欧米伽+",
            "description": "在你的回合结束时，对所有敌人造成 60 点伤害。",
            "card_vars": {"damage": 60}
        }
    )

