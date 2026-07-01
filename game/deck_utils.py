# -*- coding: utf-8 -*-
# 牌组长期操作工具：事件、商店等都应通过这里移除 / 转化卡牌，便于触发寄生等长期副作用。

import random

from data.card.AAAregistry import create_card
from data.card.special_curses import is_source_only_curse_card_id
from data.card.upgrade_rules import upgrade_card
from data.content_gate import filter_card_ids, is_content_enabled
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

    target_card = deck[card_index]
    if getattr(target_card, "card_id", "") == "card.curse.bell":
        return None, ["【铃铛的诅咒】无法从牌组中移除。"]
    if getattr(target_card, "card_id", "") == "card.curse.necronomicurse":
        return None, ["【死灵诅咒】无法从牌组中移除。"]

    removed_card = deck.pop(card_index)
    logs = ["移除卡牌：【{}】。".format(getattr(removed_card, "name", "未知卡牌"))]
    logs.extend(apply_card_removed_or_transformed_side_effects(
        run_state,
        removed_card,
        reason=reason or "remove"
    ))
    return removed_card, logs


def _iter_enabled_registry_card_ids():
    from data.card.AAAregistry import CARD_REGISTRY
    for card_id in CARD_REGISTRY.keys():
        if not is_content_enabled("card", card_id):
            continue
        yield card_id


def _same_owner_card_ids(source_card, candidate_ids, allowed_types=None):
    result = []
    source_owner = str(getattr(source_card, "owner_character_id", "") or "")
    if allowed_types is not None:
        allowed_types = set(allowed_types)

    for card_id in filter_card_ids(list(candidate_ids)):
        try:
            card = create_card(card_id)
        except Exception:
            continue

        if allowed_types is not None and getattr(card, "card_type", "") not in allowed_types:
            continue

        candidate_owner = str(getattr(card, "owner_character_id", "") or "")
        if candidate_owner != source_owner:
            continue

        result.append(card_id)

    return result


def get_transform_candidate_ids(run_state=None, source_card=None):
    """
    普通变化池：只在同 owner_character_id 的非状态/非诅咒牌中变化。
    owner_character_id 为空的无所属牌只会变化成无所属牌。
    """
    allowed_types = ("attack", "skill", "power")
    if source_card is None:
        result = []
        for card_id in filter_card_ids(CARD_REWARD_POOL):
            try:
                card = create_card(card_id)
            except Exception:
                continue
            if getattr(card, "card_type", "") in allowed_types:
                result.append(card_id)
        return result

    return _same_owner_card_ids(
        source_card=source_card,
        candidate_ids=CARD_REWARD_POOL,
        allowed_types=allowed_types
    )


def get_typed_transform_candidate_ids(source_card, card_type):
    """
    诅咒/状态等特殊类型变化池：同类型 + 同 owner。
    这些通常不在奖励池里，因此优先从全注册表收集。
    """
    return _same_owner_card_ids(
        source_card=source_card,
        candidate_ids=list(_iter_enabled_registry_card_ids()),
        allowed_types=(card_type,)
    )


def get_curse_transform_candidate_ids(source_card=None):
    if source_card is not None:
        return [
            card_id
            for card_id in get_typed_transform_candidate_ids(source_card, "curse")
            if not is_source_only_curse_card_id(card_id)
        ]

    result = []
    for card_id in filter_card_ids(CARD_REWARD_POOL):
        if is_source_only_curse_card_id(card_id):
            continue
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "card_type", "") == "curse":
            result.append(card_id)
    if not result:
        for card_id in _iter_enabled_registry_card_ids():
            if is_source_only_curse_card_id(card_id):
                continue
            try:
                card = create_card(card_id)
            except Exception:
                continue
            if getattr(card, "card_type", "") == "curse":
                result.append(card_id)
    return result


def transform_card_in_master_deck(run_state, card_index, rng=None):
    if rng is None:
        rng = random.Random()

    deck = getattr(run_state, "master_deck", [])
    if card_index < 0 or card_index >= len(deck):
        return None, None, ["卡牌编号无效。"]

    old_card = deck[card_index]
    if getattr(old_card, "card_id", "") == "card.curse.necronomicurse":
        return None, None, ["【死灵诅咒】无法被变化。"]
    old_card_type = getattr(old_card, "card_type", "")
    if old_card_type == "curse":
        pool = get_curse_transform_candidate_ids(old_card)
    elif old_card_type == "status":
        pool = get_typed_transform_candidate_ids(old_card, "status")
    else:
        pool = get_transform_candidate_ids(run_state, source_card=old_card)
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
    if getattr(old_card, "card_type", "") == "curse" and getattr(new_card, "card_type", "") == "curse":
        from game.relic_logic.run_relic_utils import trigger_darkstone_periapt_for_curse
        logs.extend(trigger_darkstone_periapt_for_curse(run_state, new_card))
    return old_card, new_card, logs
