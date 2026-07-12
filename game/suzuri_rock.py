# -*- coding: utf-8 -*-

import math

from game.modifiers import get_status_value
from game.status.status_defs import get_status_name
from game.status.status_gain import format_status_gain_log

def find_owned_relic(entity, relic_id):
    for relic in getattr(entity, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return relic
    return None

def gain_rock_layer(game_state, target, amount, source_name="岩层"):
    """
    统一获得岩层入口。

    会处理：
    - 重岩：每次获得岩层时，额外 +2，且多层重岩叠加。
    - 故乡的坚石：获得岩层时，额外获得本次实际获得岩层数一半的格挡。
    - 苍空鸣响之石：获得岩层时，额外获得等量格挡和隐蔽石砾。
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

    if game_state is None or total <= 0:
        return logs

    myth_relic = find_owned_relic(target, "relic.resonant_azure_sky_stone")
    starting_relic = find_owned_relic(target, "relic.hometown_clear_stone")

    if myth_relic is not None:
        from game.block import gain_block_without_modifiers

        logs.append("【{}】触发：获得等量格挡和隐蔽石砾。".format(myth_relic.name))

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=target,
            target=target,
            amount=total,
            block_source="relic",
            card=None
        ))

        if hasattr(target, "gain_status_with_result"):
            result = target.gain_status_with_result("hidden_gravel", total)
            logs.append(format_status_gain_log(target, "hidden_gravel", total, result))
        else:
            current = target.gain_status("hidden_gravel", total)
            logs.append("{} 获得 {} 层{}。当前{}：{}。".format(
                target.name,
                total,
                get_status_name("hidden_gravel"),
                get_status_name("hidden_gravel"),
                current
            ))

    elif starting_relic is not None:
        block_amount = total // 2

        if block_amount > 0:
            from game.block import gain_block_without_modifiers

            logs.append("【{}】触发：获得本次岩层数一半的格挡。".format(starting_relic.name))

            logs.extend(gain_block_without_modifiers(
                game_state=game_state,
                source=target,
                target=target,
                amount=block_amount,
                block_source="relic",
                card=None
            ))

    return logs

def get_rock_polishing_counters(target):
    counters = getattr(target, "rock_polishing_counters", None)

    if counters is None:
        counters = []
        setattr(target, "rock_polishing_counters", counters)

    return counters


def sync_rock_polishing_status(target):
    counters = get_rock_polishing_counters(target)

    normal_count = 0
    upgraded_count = 0

    for counter in counters:
        threshold = int(counter.get("threshold", 9) or 9)

        if threshold <= 6:
            upgraded_count += 1
        else:
            normal_count += 1

    if hasattr(target, "statuses"):
        target.statuses.set("rock_polishing_9", normal_count)
        target.statuses.set("rock_polishing_6", upgraded_count)


def add_rock_polishing_counter(game_state, target, threshold, source_name="岩石打磨"):
    logs = []

    if target is None:
        return logs

    threshold = int(threshold)
    if threshold <= 0:
        threshold = 9

    counters = get_rock_polishing_counters(target)
    counters.append({
        "threshold": threshold,
        "progress": 0,
    })

    sync_rock_polishing_status(target)

    logs.append("【{}】生效：新增 1 个独立计数器，当前进度 0/{}。".format(
        source_name,
        threshold
    ))

    return logs


def trigger_rock_polishing_if_needed(game_state, target, consumed_amount, source_name="岩层消耗"):
    """
    岩石打磨：
    每个计数器独立累计消耗岩层。
    达到阈值时获得 1 点敏捷，并扣除对应阈值进度。
    一次消耗大量岩层时，同一个计数器可以触发多次。
    """
    logs = []

    consumed_amount = int(consumed_amount)
    if target is None or consumed_amount <= 0:
        return logs

    counters = get_rock_polishing_counters(target)

    if not counters:
        return logs

    total_dexterity_gain = 0

    for counter_index, counter in enumerate(counters):
        threshold = int(counter.get("threshold", 9) or 9)
        progress = int(counter.get("progress", 0) or 0)

        if threshold <= 0:
            threshold = 9

        progress += consumed_amount
        trigger_count = 0

        while progress >= threshold:
            progress -= threshold
            trigger_count += 1

        counter["progress"] = progress

        if trigger_count > 0:
            total_dexterity_gain += trigger_count
            logs.append("【岩石打磨】计数器 {} 触发 {} 次，剩余进度 {}/{}。".format(
                counter_index + 1,
                trigger_count,
                progress,
                threshold
            ))
        else:
            logs.append("【岩石打磨】计数器 {} 进度：{}/{}。".format(
                counter_index + 1,
                progress,
                threshold
            ))

    if total_dexterity_gain <= 0:
        return logs

    if hasattr(target, "gain_status_with_result"):
        result = target.gain_status_with_result("dexterity", total_dexterity_gain)
        logs.append("【岩石打磨】获得 {} 点敏捷。".format(total_dexterity_gain))
        logs.append(format_status_gain_log(target, "dexterity", total_dexterity_gain, result))
    else:
        current = target.gain_status("dexterity", total_dexterity_gain)
        logs.append("【岩石打磨】获得 {} 点敏捷。当前敏捷：{}。".format(
            total_dexterity_gain,
            current
        ))

    return logs

def get_living_soil_counters(target):
    counters = getattr(target, "living_soil_counters", None)

    if counters is None:
        counters = []
        setattr(target, "living_soil_counters", counters)

    return counters


def sync_living_soil_status(target):
    counters = get_living_soil_counters(target)

    normal_count = 0
    upgraded_count = 0

    for counter in counters:
        threshold = int(counter.get("threshold", 9) or 9)

        if threshold <= 6:
            upgraded_count += 1
        else:
            normal_count += 1

    if hasattr(target, "statuses"):
        target.statuses.set("living_soil_9", normal_count)
        target.statuses.set("living_soil_6", upgraded_count)


def add_living_soil_counter(game_state, target, threshold, source_name="息壤"):
    logs = []

    if target is None:
        return logs

    threshold = int(threshold)
    if threshold <= 0:
        threshold = 9

    counters = get_living_soil_counters(target)
    counters.append({
        "threshold": threshold,
        "progress": 0,
    })

    sync_living_soil_status(target)

    logs.append("【{}】生效：新增 1 个独立计数器，当前进度 0/{}。".format(
        source_name,
        threshold
    ))

    return logs


def trigger_living_soil_if_needed(game_state, target, consumed_amount, source_name="岩层消耗"):
    """
    息壤：
    每个计数器独立累计消耗岩层。
    达到阈值时，获得 5 层岩层，并扣除对应阈值进度。
    一次消耗大量岩层时，同一个计数器可以触发多次。
    """
    logs = []

    consumed_amount = int(consumed_amount)
    if target is None or consumed_amount <= 0:
        return logs

    counters = get_living_soil_counters(target)

    if not counters:
        return logs

    total_rock_gain = 0

    for counter_index, counter in enumerate(counters):
        threshold = int(counter.get("threshold", 9) or 9)
        progress = int(counter.get("progress", 0) or 0)

        if threshold <= 0:
            threshold = 9

        progress += consumed_amount
        trigger_count = 0

        while progress >= threshold:
            progress -= threshold
            trigger_count += 1

        counter["progress"] = progress

        if trigger_count > 0:
            gain_amount = trigger_count * 5
            total_rock_gain += gain_amount
            logs.append("【息壤】计数器 {} 触发 {} 次，剩余进度 {}/{}。".format(
                counter_index + 1,
                trigger_count,
                progress,
                threshold
            ))
        else:
            logs.append("【息壤】计数器 {} 进度：{}/{}。".format(
                counter_index + 1,
                progress,
                threshold
            ))

    if total_rock_gain <= 0:
        return logs

    logs.append("【息壤】获得 {} 层岩层。".format(total_rock_gain))
    logs.extend(gain_rock_layer(
        game_state=game_state,
        target=target,
        amount=total_rock_gain,
        source_name="息壤"
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

    logs.extend(trigger_living_soil_if_needed(
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
