# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate
from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE
)

def _gain_strength_effect():
    return {
        "op": "gain_status",
        "target": "self",
        "status": "strength",
        "amount": {
            "var": "strength"
        }
    }

def create_gain_status_strength():
    return CardTemplate(
        card_id="card.gain_status_strength",
        name="力量",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 1 点力量。",
        card_vars={
            "strength": 1
        },
        quantity="test",
        effects=[
            _gain_strength_effect()
        ]
    )

def _create_keyword_strength_card(card_id, name, keyword, keyword_name):
    return CardTemplate(
        card_id=card_id,
        name=name,
        card_type="skill",
        cost=1,
        target="self",
        description="获得 1 点力量。{}。".format(keyword_name),
        quantity="test",
        card_vars={
            "strength": 1
        },
        effects=[
            _gain_strength_effect()
        ],
        keywords=[keyword]
    )

def create_exhaust_strength():
    return _create_keyword_strength_card(
        card_id="card.exhaust_strength",
        name="消耗力量",
        keyword=KEYWORD_EXHAUST,
        keyword_name="消耗"
    )

def create_ethereal_strength():
    return _create_keyword_strength_card(
        card_id="card.ethereal_strength",
        name="虚无力量",
        keyword=KEYWORD_ETHEREAL,
        keyword_name="虚无"
    )

def create_retain_strength():
    return _create_keyword_strength_card(
        card_id="card.retain_strength",
        name="保留力量",
        keyword=KEYWORD_RETAIN,
        keyword_name="保留"
    )

def create_clever_strength():
    return _create_keyword_strength_card(
        card_id="card.clever_strength",
        name="奇巧力量",
        keyword=KEYWORD_CLEVER,
        keyword_name="奇巧"
    )

def create_innate_thorns():
    return CardTemplate(
        card_id="card.innate_thorns",
        name="固有荆棘",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 4 层荆棘。固有。",
        quantity="test",
        card_vars={
            "thorns": 4
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "thorns",
                "amount": {
                    "var": "thorns"
                }
            }
        ],
        keywords=[
            KEYWORD_INNATE
        ]
    )

def create_draw_discard_test():
    return CardTemplate(
        card_id="card.draw_discard_test",
        name="抽弃测试",
        card_type="skill",
        cost=1,
        target="self",
        description="抽牌直到手牌满，然后选择任意张数手牌丢弃。",
        quantity="test",
        card_vars={},
        effects=[
            {
                "op": "draw_to_full"
            },
            {
                "op": "request_discard_any"
            }
        ]
    )

def create_test_heavy_strike():
    """
    测试重击：造成 2 + 力量 × 8 点伤害。
    """
    return CardTemplate(
        card_id="card.test_heavy_strike",
        name="测试重击",
        card_type="attack",
        cost=2,
        target="enemy",
        description="造成 2 + 力量 × 8 点伤害。",
        quantity="test",
        card_vars={
            "base_damage": 2,
            "strength_multiplier": 7
        },
        effects=[
            {
                "op": "deal_damage",
                "target": "selected_enemy",
                "amount": {
                    "base_var": "base_damage",
                    "scaling": [
                        {
                            "stat": "strength",
                            "multiplier_var": "strength_multiplier"
                        }
                    ],
                    "modifier_profile": "attack_damage"
                }
            }
        ]
    )

def create_test_x_drill():
    """
    测试X钻头：

    结算顺序：
    1. X = 当前剩余费用
    2. 遗物修正 X，例如 X药：X + 2
    3. 本卡修正 X：若 X >= 3，则 X = 2X
    4. 若最终 X >= 3，每次造成 4 点伤害；否则每次造成 3 点伤害
    5. 重复 X 次
    """
    return CardTemplate(
        card_id="card.test_x_drill",
        name="测试X钻头",
        card_type="attack",
        cost="X",
        target="enemy",
        description="消耗所有费用。若最终 X >= 3，则 X 翻倍。造成 3 点伤害 X 次；若最终 X >= 3，改为造成 4 点伤害 X 次。",
        quantity="test",
        card_vars={
            "low_damage": 3,
            "high_damage": 4
        },
        x_rules=[
            {
                "op": "if_ge_mul",
                "threshold": 3,
                "multiplier": 2
            }
        ],
        effects=[
            {
                "op": "repeat_x",
                "effects": [
                    {
                        "op": "deal_damage",
                        "target": "selected_enemy",
                        "amount": {
                            "x_conditional_var": {
                                "x_gte": 3,
                                "then_var": "high_damage",
                                "else_var": "low_damage"
                            },
                            "modifier_profile": "attack_damage"
                        }
                    }
                ]
            }
        ],
        upgraded=False,
        upgrade_patch={
            "name": "测试X钻头+",
            "description": "消耗所有费用。若最终 X >= 2，则 X 翻倍。造成 4 点伤害 X 次；若最终 X >= 2，改为造成 5 点伤害 X 次。",
            "card_vars": {
                "low_damage": 4,
                "high_damage": 5
            },
            "x_rules": [
                {
                    "op": "if_ge_mul",
                    "threshold": 2,
                    "multiplier": 2
                }
            ],
            "patches": [
                {
                    "path": [
                        "effects",
                        0,
                        "effects",
                        0,
                        "amount",
                        "x_conditional_var",
                        "x_gte"
                    ],
                    "value": 2
                }
            ],
        }
    )