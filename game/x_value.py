# -*- coding: utf-8 -*-

from game.battle_context import BattleContext


def is_x_cost_card(card):
    return str(getattr(card, "cost", "")).upper() == "X"


def calculate_card_x_value(game_state, card, raw_x):
    """
    计算 X 费用牌的最终 X。

    顺序：
    1. raw_x = 当前剩余费用
    2. 遗物等外部效果修正 X
    3. 卡牌自身 x_rules 修正 X
    4. 最终 X 只作为 X，不直接污染 card_vars
    """
    logs = []

    x = int(raw_x)

    if x < 0:
        x = 0

    player = game_state.player

    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        card=card,
        extra={
            "raw_x": raw_x,
            "x": x
        }
    )

    # 遗物修正 X。
    # 例如 X药：x = x + 2。
    for relic in getattr(player, "relics", []):
        modifier = getattr(relic, "modify_x_value", None)

        if modifier is None:
            continue

        old_x = x
        result = modifier(x, context)

        if isinstance(result, tuple):
            x = int(result[0])
            relic_logs = result[1]

            if relic_logs:
                logs.extend(relic_logs)
        else:
            x = int(result)

        context.extra["x"] = x

        if x != old_x:
            logs.append("X：{} -> {}。".format(old_x, x))

    # 卡牌自身修正 X。
    old_x = x
    x = apply_card_x_rules(card, x)

    if x != old_x:
        logs.append("【{}】修正 X：{} -> {}。".format(
            card.name,
            old_x,
            x
        ))

    if x < 0:
        x = 0

    return x, logs


def apply_card_x_rules(card, x):
    """
    当前先支持一种规则：

    {"op": "if_ge_mul", "threshold": 3, "multiplier": 2}

    含义：
    如果 x >= 3，则 x = x * 2。
    """
    rules = getattr(card, "x_rules", [])

    for rule in rules:
        op = rule.get("op")

        if op == "if_ge_mul":
            threshold = int(rule.get("threshold", 0))
            multiplier = int(rule.get("multiplier", 1))

            if x >= threshold:
                x = x * multiplier

        elif op == "add":
            x += int(rule.get("amount", 0))

        elif op == "mul":
            x = x * int(rule.get("multiplier", 1))

        elif op == "set_min":
            value = int(rule.get("value", 0))

            if x < value:
                x = value

        elif op == "set_max":
            value = int(rule.get("value", 0))

            if x > value:
                x = value

    return int(x)