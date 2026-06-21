# -*- coding: utf-8 -*-
# 牌组长期操作工具：事件、商店等都应通过这里移除 / 转化卡牌，便于触发寄生等长期副作用。

import random

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from game.reward import CARD_REWARD_POOL


PARASITE_CARD_ID = "card.curse.parasite"


def apply_card_removed_or_transformed_side_effects(run_state, card, reason=""):
    """
    处理长期牌组中的卡牌被移除 / 转化时的副作用。

    当前支持：
    - 寄生：如果这张牌在你的牌组中被转化或移除，你失去 3 点最大生命。

    战斗中的临时变化、消耗、弃牌等不调用本函数。
    """
    logs = []
    if card is None:
        return logs

    card_id = getattr(card, "card_id", "")
    if card_id != PARASITE_CARD_ID:
        return logs

    old_max_hp = int(getattr(run_state, "max_hp", 0))
    old_hp = int(getattr(run_state, "hp", 0))
    new_max_hp = max(1, old_max_hp - 3)
    run_state.max_hp = new_max_hp
    if run_state.hp > run_state.max_hp:
        run_state.hp = run_state.max_hp

    logs.append("【寄生】离开牌组时发作：最大生命值 {} -> {}，HP {} -> {}。".format(
        old_max_hp,
        run_state.max_hp,
        old_hp,
        run_state.hp
    ))
    return logs


def remove_card_from_master_deck(run_state, card_index, reason=""):
    deck = getattr(run_state, "master_deck", [])
    if card_index < 0 or card_index >= len(deck):
        return None, ["卡牌编号无效。"]

    removed_card = deck.pop(card_index)
    logs = ["移除卡牌：【{}】。".format(getattr(removed_card, "name", "未知卡牌"))]
    logs.extend(apply_card_removed_or_transformed_side_effects(
        run_state,
        removed_card,
        reason=reason or "remove"
    ))
    return removed_card, logs


def get_transform_candidate_ids(run_state=None):
    result = []
    for card_id in CARD_REWARD_POOL:
        try:
            card = create_card(card_id)
        except Exception:
            continue
        card_type = getattr(card, "card_type", "")
        if card_type in ("status", "curse"):
            continue
        result.append(card_id)
    return result


def transform_card_in_master_deck(run_state, card_index, rng=None):
    if rng is None:
        rng = random.Random()

    deck = getattr(run_state, "master_deck", [])
    if card_index < 0 or card_index >= len(deck):
        return None, None, ["卡牌编号无效。"]

    old_card = deck[card_index]
    pool = get_transform_candidate_ids(run_state)
    old_card_id = getattr(old_card, "card_id", "")
    pool = [card_id for card_id in pool if card_id != old_card_id] or pool

    if not pool:
        return None, None, ["当前没有可转化成的卡牌。"]

    new_card = create_card(rng.choice(pool))

    # 简化规则：已升级牌转化后尽量保持升级状态。
    if getattr(old_card, "upgraded", False):
        try:
            new_card = upgrade_card(new_card)
        except Exception:
            pass

    deck[card_index] = new_card

    logs = ["变化卡牌：【{}】 -> 【{}】。".format(
        getattr(old_card, "name", "未知卡牌"),
        getattr(new_card, "name", "未知卡牌")
    )]
    logs.extend(apply_card_removed_or_transformed_side_effects(
        run_state,
        old_card,
        reason="transform"
    ))
    return old_card, new_card, logs
