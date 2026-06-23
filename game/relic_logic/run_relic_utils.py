# -*- coding: utf-8 -*-
"""Run 层遗物工具函数。

把“获得金币 / 加牌 / 最大生命变化”等长期行为集中在这里，
避免奖励、商店、事件各写一套后遗漏陶瓷小鱼、火龙果、御守等触发。
"""

import copy


def iter_run_relics(run_state):
    return list(getattr(run_state, "relics", []) or [])


def has_run_relic(run_state, relic_id):
    for relic in iter_run_relics(run_state):
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def get_run_relic(run_state, relic_id):
    for relic in iter_run_relics(run_state):
        if getattr(relic, "relic_id", "") == relic_id:
            return relic
    return None


def get_current_floor(run_state):
    node = None
    try:
        node = run_state.get_current_node()
    except Exception:
        node = None
    if node is not None:
        floor = getattr(node, "floor", None)
        if floor is not None:
            try:
                return int(floor)
            except (TypeError, ValueError):
                pass
    # 没有楼层元数据时，用已完成节点数量粗略兜底。
    return len(getattr(run_state, "completed_node_ids", []) or []) + 1


def is_relic_available_by_floor(run_state, relic):
    max_floor = getattr(relic, "max_reward_floor", None)
    if max_floor is None:
        return True
    try:
        return get_current_floor(run_state) <= int(max_floor)
    except (TypeError, ValueError):
        return True


def gain_gold_with_relics(run_state, amount, source="获得金币"):
    """获得金币，并处理火龙果。返回日志列表。"""
    logs = []
    amount = int(amount)
    if amount <= 0:
        return logs

    old_gold = int(getattr(run_state, "gold", 0))
    run_state.gold = old_gold + amount
    logs.append("{}：获得 {} 金币。当前金币：{}。".format(source, amount, run_state.gold))

    if has_run_relic(run_state, "relic.dragon_fruit"):
        old_max = int(getattr(run_state, "max_hp", 0))
        old_hp = int(getattr(run_state, "hp", 0))
        run_state.max_hp = old_max + 1
        run_state.hp = min(run_state.max_hp, old_hp + 1)
        logs.append("【火龙果】触发：最大生命值 {} -> {}，HP {} -> {}。".format(
            old_max,
            run_state.max_hp,
            old_hp,
            run_state.hp
        ))
    return logs


def increase_max_hp(run_state, amount, source_name="遗物"):
    amount = int(amount)
    if amount <= 0:
        return []
    old_max = int(getattr(run_state, "max_hp", 0))
    old_hp = int(getattr(run_state, "hp", 0))
    run_state.max_hp = old_max + amount
    run_state.hp = min(run_state.max_hp, old_hp + amount)
    return ["【{}】生效：最大生命值 {} -> {}，HP {} -> {}。".format(
        source_name,
        old_max,
        run_state.max_hp,
        old_hp,
        run_state.hp
    )]


def add_card_to_master_deck_with_relics(run_state, card, source="获得卡牌"):
    """向长期牌组加入一张牌，并处理三蛋、御守、黑石护符、陶瓷小鱼。"""
    logs = []
    if card is None:
        return logs

    card = apply_card_gain_preview_relics(run_state, card)

    if getattr(card, "card_type", "") == "curse":
        blocked, block_log = try_block_curse_with_omamori(run_state, getattr(card, "name", "诅咒"))
        if blocked:
            logs.append(block_log)
            return logs
        logs.extend(trigger_darkstone_periapt_for_curse(run_state, card))

    run_state.master_deck.append(card)
    logs.append("{}：【{}】加入牌组。".format(source, getattr(card, "name", "未知卡牌")))

    if has_run_relic(run_state, "relic.ceramic_fish"):
        logs.append("【陶瓷小鱼】触发。")
        logs.extend(gain_gold_with_relics(run_state, 9, source="陶瓷小鱼"))
    return logs


def try_block_curse_with_omamori(run_state, card_name="诅咒"):
    relic = get_run_relic(run_state, "relic.omamori")
    if relic is None:
        return False, ""
    charges = int(getattr(relic, "charges", 0))
    if charges <= 0:
        return False, ""
    relic.charges = charges - 1
    return True, "【御守】抵消了将要获得的诅咒【{}】。剩余次数：{}。".format(card_name, relic.charges)


def spend_gold_in_shop(run_state, amount):
    """商店花钱后的统一标记。当前用于巨口储蓄罐失效。"""
    amount = int(amount)
    if amount <= 0:
        return []
    logs = []
    if has_run_relic(run_state, "relic.maw_bank") and not getattr(run_state, "maw_bank_disabled", False):
        run_state.maw_bank_disabled = True
        logs.append("【巨口储蓄罐】因为你在商店中花费金币而失效。")
    return logs


def copy_card_for_deck(card):
    return copy.deepcopy(card)



def apply_card_gain_preview_relics(run_state, card):
    """在“看见/生成可获得卡牌”时应用三蛋，使奖励、商店、事件展示即为升级状态。"""
    if card is None:
        return card
    try:
        from data.card.upgrade_rules import has_upgrade, upgrade_card
        from game.relic_logic.bottle_utils import copy_bottled_flags
    except Exception:
        return card
    card_type = getattr(card, "card_type", "")
    egg_by_type = {
        "attack": "relic.molten_egg",
        "skill": "relic.toxic_egg",
        "power": "relic.frozen_egg",
    }
    relic_id = egg_by_type.get(card_type)
    if relic_id and has_run_relic(run_state, relic_id) and has_upgrade(card):
        upgraded = upgrade_card(card)
        upgraded = copy_bottled_flags(card, upgraded)
        return upgraded
    return card


def trigger_darkstone_periapt_for_curse(run_state, card):
    """获得诅咒时触发黑石护符。御守抵消后的诅咒不会走到这里。"""
    if card is None or getattr(card, "card_type", "") != "curse":
        return []
    if not has_run_relic(run_state, "relic.darkstone_periapt"):
        return []
    old_max = int(getattr(run_state, "max_hp", 0))
    old_hp = int(getattr(run_state, "hp", 0))
    run_state.max_hp = old_max + 6
    run_state.hp = min(run_state.max_hp, old_hp + 6)
    return ["【黑石护符】触发：获得诅咒【{}】，最大生命值 {} -> {}，HP {} -> {}。".format(
        getattr(card, "name", "诅咒"), old_max, run_state.max_hp, old_hp, run_state.hp
    )]
