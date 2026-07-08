# -*- coding: utf-8 -*-

import math

from game.modifiers import get_status_value
from game.status.status_defs import get_status_name
from game.status.status_gain import format_status_gain_log


def gain_rock_layer(game_state, target, amount, source_name="岩层"):
    """
    统一获得岩层入口。

    会处理：
    - 重岩：每次获得岩层时，额外 +2，且多层重岩叠加。
    """
    logs = []

    amount = int(amount)
    if target is None or amount <= 0:
        return logs

    heavy_rock = int(get_status_value(target, "heavy_rock"))
    bonus = 0

    if heavy_rock > 0:
        bonus = heavy_rock * 2
        logs.append("【重岩】触发：本次获得岩层额外 +{}。".format(bonus))

    total = amount + bonus

    if hasattr(target, "gain_status_with_result"):
        result = target.gain_status_with_result("rock_layer", total)
        logs.append(format_status_gain_log(target, "rock_layer", total, result))
    else:
        current = target.gain_status("rock_layer", total)
        logs.append("{} 获得 {} 层{}。当前{}：{}。".format(
            target.name,
            total,
            get_status_name("rock_layer"),
            get_status_name("rock_layer"),
            current
        ))

    return logs


def trigger_rock_polishing_if_needed(game_state, target, consumed_amount, source_name="岩层消耗"):
    """
    岩石打磨：
    - rock_polishing_9：一次性消耗岩层 >= 9 时，每层获得 1 敏捷
    - rock_polishing_6：一次性消耗岩层 >= 6 时，每层获得 1 敏捷
    """
    logs = []

    consumed_amount = int(consumed_amount)
    if target is None or consumed_amount <= 0:
        return logs

    dexterity_gain = 0

    polishing_6 = int(get_status_value(target, "rock_polishing_6"))
    polishing_9 = int(get_status_value(target, "rock_polishing_9"))

    if consumed_amount >= 6 and polishing_6 > 0:
        dexterity_gain += polishing_6

    if consumed_amount >= 9 and polishing_9 > 0:
        dexterity_gain += polishing_9

    if dexterity_gain <= 0:
        return logs

    if hasattr(target, "gain_status_with_result"):
        result = target.gain_status_with_result("dexterity", dexterity_gain)
        logs.append("【岩石打磨】触发：一次性消耗 {} 层岩层，获得 {} 点敏捷。".format(
            consumed_amount,
            dexterity_gain
        ))
        logs.append(format_status_gain_log(target, "dexterity", dexterity_gain, result))
    else:
        current = target.gain_status("dexterity", dexterity_gain)
        logs.append("【岩石打磨】触发：一次性消耗 {} 层岩层，获得 {} 点敏捷。当前敏捷：{}。".format(
            consumed_amount,
            dexterity_gain,
            current
        ))

    return logs


def consume_rock_layer(game_state, target, amount=None, source_name="岩层消耗"):
    """
    统一消耗岩层入口。

    amount=None 表示消耗全部岩层。
    返回：(实际消耗层数, logs)
    """
    logs = []

    if target is None:
        return 0, logs

    current = int(get_status_value(target, "rock_layer"))

    if current <= 0:
        logs.append("【{}】没有可消耗的岩层。".format(source_name))
        return 0, logs

    if amount is None:
        consume_amount = current
    else:
        consume_amount = int(amount)

    consume_amount = max(0, min(current, consume_amount))

    if consume_amount <= 0:
        logs.append("【{}】没有消耗岩层。".format(source_name))
        return 0, logs

    remaining = target.statuses.add("rock_layer", -consume_amount)

    logs.append("【{}】消耗 {} 层岩层。当前岩层：{}。".format(
        source_name,
        consume_amount,
        remaining
    ))

    logs.extend(trigger_rock_polishing_if_needed(
        game_state=game_state,
        target=target,
        consumed_amount=consume_amount,
        source_name=source_name
    ))

    return consume_amount, logs


def calculate_ratio_rock_consume(current, ratio, rounding="ceil"):
    current = int(current)
    ratio = float(ratio)

    if current <= 0 or ratio <= 0:
        return 0

    raw = current * ratio

    if rounding == "floor":
        return int(math.floor(raw))

    if rounding == "round":
        return int(round(raw))

    return int(math.ceil(raw))
