# -*- coding: utf-8 -*-
"""Run 层遗物工具函数。

把“获得金币 / 加牌 / 最大生命变化”等长期行为集中在这里，
避免奖励、商店、事件各写一套后遗漏陶瓷小鱼、火龙果、御守等触发。
"""

import copy

STARTING_RELIC_MYTH_MAP = {
    "relic.burning_blood": "relic.black_blood",
}


def find_upgradeable_starting_relic(run_state):
    owned_ids = {
        getattr(relic, "relic_id", "")
        for relic in getattr(run_state, "relics", []) or []
    }
    for index, relic in enumerate(getattr(run_state, "relics", []) or []):
        source_id = getattr(relic, "relic_id", "")
        target_id = STARTING_RELIC_MYTH_MAP.get(source_id)
        if not target_id:
            continue
        if target_id in owned_ids:
            continue
        return index, relic, target_id

    return None

def can_upgrade_starting_relic(run_state):
    return find_upgradeable_starting_relic(run_state) is not None

def iter_run_relics(run_state):
    return list(getattr(run_state, "relics", []) or [])


def has_run_relic(run_state, relic_id):
    for relic in iter_run_relics(run_state):
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False




def has_no_heal_relic(run_state):
    return has_run_relic(run_state, "relic.mark_of_the_bloom")


def heal_run_hp_with_relics(run_state, amount, source="回复"):
    """长期流程回血统一入口：处理绽放印记。"""
    amount = int(amount)
    if amount <= 0:
        return ["{}：没有回复生命。".format(source)]
    if has_no_heal_relic(run_state):
        return ["【绽放印记】阻止了本次回复生命：{} 点。".format(amount)]
    old_hp = int(getattr(run_state, "hp", 0))
    max_hp = int(getattr(run_state, "max_hp", old_hp))
    run_state.hp = min(max_hp, old_hp + amount)
    real = run_state.hp - old_hp
    if real > 0:
        return ["{}：回复 {} 点生命。HP：{} -> {}。".format(source, real, old_hp, run_state.hp)]
    return ["{}：HP 已满，没有回复。".format(source)]

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

    if has_run_relic(run_state, "relic.ectoplasm"):
        logs.append("【灵体外质】阻止了本次获得金币：{} 金币。".format(amount))
        return logs

    old_gold = int(getattr(run_state, "gold", 0))
    run_state.gold = old_gold + amount
    logs.append("{}：获得 {} 金币。当前金币：{}。".format(source, amount, run_state.gold))

    if has_run_relic(run_state, "relic.bloody_idol"):
        logs.append("【鲜血神像】触发。")
        logs.extend(heal_run_hp_with_relics(run_state, 5, source="鲜血神像"))

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
    if has_no_heal_relic(run_state):
        run_state.hp = min(run_state.max_hp, old_hp)
    else:
        run_state.hp = min(run_state.max_hp, old_hp + amount)
    return ["【{}】生效：最大生命值 {} -> {}，HP {} -> {}。".format(
        source_name,
        old_max,
        run_state.max_hp,
        old_hp,
        run_state.hp
    )]


def add_card_to_master_deck_with_relics(run_state, card, source="获得卡牌", apply_gain_preview=True):
    """向长期牌组加入一张牌，并处理三蛋、御守、黑石护符、陶瓷小鱼。"""
    logs = []
    if card is None:
        return logs

    if apply_gain_preview:
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



def try_gain_potion_with_relics(run_state, potion, source="获得药水"):
    """获得药水统一入口：处理添水与药水栏。"""
    logs = []
    if potion is None:
        return logs
    if has_run_relic(run_state, "relic.sozu"):
        return ["【添水】阻止了获得药水【{}】。".format(getattr(potion, "name", "药水"))]
    max_slots = int(getattr(run_state, "max_potion_slots", 3))
    potions = getattr(run_state, "potions", [])
    if len(potions) >= max_slots:
        return ["{}：药水栏已满，无法获得【{}】。".format(source, getattr(potion, "name", "药水"))]
    potions.append(potion)
    logs.append("{}：获得药水【{}】。".format(source, getattr(potion, "name", "药水")))
    if getattr(potion, "potion_id", "") == "potion.fairy_in_a_bottle" and getattr(run_state, "character_id", "") == "character.yoirine":
        logs.append("Yoirine：“我没见过这个。但本能地……不太喜欢它。”")
    return logs


def has_pending_astrolabe_selection(run_state):
    return bool(getattr(run_state, "pending_astrolabe_selections", []) or [])


def format_pending_astrolabe(run_state):
    queue = getattr(run_state, "pending_astrolabe_selections", []) or []
    if not queue:
        return "当前没有需要处理的星盘选择。"
    pending = queue[0]
    count = int(pending.get("count", 3))
    lines = ["=== 星盘：选择变化牌 ===", "需要选择 {} 张牌。".format(count), ""]
    for index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        lines.append("[{}] {}".format(index, card.summary_text()))
    lines.append("")
    lines.append("使用 /card astrolabe 0,1,2 选择。")
    return "\n".join(lines)


def choose_pending_astrolabe_cards(run_state, indices, rng=None):
    queue = getattr(run_state, "pending_astrolabe_selections", []) or []
    if not queue:
        return "当前没有需要处理的星盘选择。"
    pending = queue[0]
    count = int(pending.get("count", 3))
    unique = []
    for idx in indices:
        if idx not in unique:
            unique.append(idx)
    if len(unique) != count:
        return "【星盘】需要选择 {} 张互不重复的牌。".format(count)
    deck = getattr(run_state, "master_deck", []) or []
    for idx in unique:
        if idx < 0 or idx >= len(deck):
            return "卡牌编号无效：{}。".format(idx)
    import random
    from game.deck_utils import transform_card_in_master_deck
    from data.card.upgrade_rules import has_upgrade, upgrade_card
    from game.relic_logic.bottle_utils import copy_bottled_flags
    if rng is None:
        rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 33119)
    logs = ["【星盘】选择 {} 张牌变化并升级。".format(count)]
    for idx in sorted(unique, reverse=True):
        old, new, sub = transform_card_in_master_deck(run_state, idx, rng=rng)
        logs.extend(sub)
        if new is not None and has_upgrade(new) and not getattr(new, "upgraded", False):
            upgraded = upgrade_card(new)
            upgraded = copy_bottled_flags(new, upgraded)
            run_state.master_deck[idx] = upgraded
            logs.append("【星盘】升级变化结果：【{}】 -> 【{}】。".format(new.name, upgraded.name))
    queue.pop(0)
    return "\n".join(logs)


def has_pending_empty_cage_selection(run_state):
    return bool(getattr(run_state, "pending_empty_cage_selections", []) or [])


def format_pending_empty_cage(run_state):
    queue = getattr(run_state, "pending_empty_cage_selections", []) or []
    if not queue:
        return "当前没有需要处理的空鸟笼选择。"
    pending = queue[0]
    count = int(pending.get("count", 2))
    lines = ["=== 空鸟笼：选择移除牌 ===", "需要选择 {} 张牌。".format(count), ""]
    for index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        lines.append("[{}] {}".format(index, card.summary_text()))
    lines.append("")
    lines.append("使用 /card cage 0,1 选择。")
    return "\n".join(lines)


def choose_pending_empty_cage_cards(run_state, indices):
    queue = getattr(run_state, "pending_empty_cage_selections", []) or []
    if not queue:
        return "当前没有需要处理的空鸟笼选择。"
    pending = queue[0]
    count = int(pending.get("count", 2))
    unique = []
    for idx in indices:
        if idx not in unique:
            unique.append(idx)
    if len(unique) != count:
        return "【空鸟笼】需要选择 {} 张互不重复的牌。".format(count)
    deck = getattr(run_state, "master_deck", []) or []
    for idx in unique:
        if idx < 0 or idx >= len(deck):
            return "卡牌编号无效：{}。".format(idx)
        card = deck[idx]
        if getattr(card, "card_id", "") == "card.curse.bell":
            return "【铃铛的诅咒】无法从牌组中移除。"
    from game.deck_utils import remove_card_from_master_deck
    logs = ["【空鸟笼】移除 {} 张牌。".format(count)]
    for idx in sorted(unique, reverse=True):
        removed, sub = remove_card_from_master_deck(run_state, idx, reason="empty_cage")
        logs.extend(sub)
    queue.pop(0)
    return "\n".join(logs)




# =========================
# Shop relic pending choices
# =========================

def _make_orrery_card_group(run_state, rng):
    """星系仪固定三选一。棱镜碎片对这里生效。"""
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import has_upgrade, upgrade_card
    from game.reward import get_card_reward_pool, get_card_reward_upgrade_chance
    pool = get_card_reward_pool(run_state)
    if not pool:
        return []
    if len(pool) <= 3:
        ids = list(pool)
    else:
        ids = rng.sample(pool, 3)
    cards = []
    upgrade_chance = get_card_reward_upgrade_chance(run_state)
    for card_id in ids:
        card = create_card(card_id)
        card = apply_card_gain_preview_relics(run_state, card)
        if has_upgrade(card) and rng.random() < upgrade_chance:
            card = upgrade_card(card)
        cards.append(card)
    return cards


def start_pending_orrery_selection(run_state):
    import random
    seed = int(getattr(run_state, "run_seed", 0) or 0) + 7927 + len(getattr(run_state, "relics", []) or [])
    rng = random.Random(seed)
    groups = []
    for _ in range(5):
        groups.append(_make_orrery_card_group(run_state, rng))
    run_state.pending_orrery_selection = True
    run_state.pending_orrery_groups = groups
    run_state.pending_orrery_index = 0


def has_pending_orrery_selection(run_state):
    return bool(getattr(run_state, "pending_orrery_selection", False))


def format_pending_orrery(run_state):
    if not has_pending_orrery_selection(run_state):
        return "当前没有需要处理的【星系仪】选择。"
    groups = getattr(run_state, "pending_orrery_groups", []) or []
    index = int(getattr(run_state, "pending_orrery_index", 0) or 0)
    if index >= len(groups):
        return "【星系仪】选择已完成。"
    cards = groups[index]
    lines = ["=== 星系仪：第 {}/{} 组 ===".format(index + 1, len(groups)), "选择 1 张牌加入牌组。", ""]
    from game.reward import format_card_reward_summary
    for i, card in enumerate(cards):
        lines.append("[{}] {}".format(i, format_card_reward_summary(card)))
    lines.append("")
    lines.append("使用 /card orrery 0 选择。")
    return "\n".join(lines)


def choose_pending_orrery_card(run_state, choice_index):
    import copy
    if not has_pending_orrery_selection(run_state):
        return "当前没有需要处理的【星系仪】选择。"
    groups = getattr(run_state, "pending_orrery_groups", []) or []
    index = int(getattr(run_state, "pending_orrery_index", 0) or 0)
    if index < 0 or index >= len(groups):
        run_state.pending_orrery_selection = False
        return "【星系仪】选择状态异常，已取消。"
    cards = groups[index]
    if choice_index < 0 or choice_index >= len(cards):
        return "卡牌编号无效。"
    card = copy.deepcopy(cards[choice_index])
    logs = []
    logs.append("【星系仪】第 {}/{} 组选择【{}】。".format(index + 1, len(groups), getattr(card, "name", "未知卡牌")))
    logs.extend(add_card_to_master_deck_with_relics(run_state, card, source="星系仪"))
    index += 1
    run_state.pending_orrery_index = index
    if index >= len(groups):
        run_state.pending_orrery_selection = False
        run_state.pending_orrery_groups = []
        run_state.pending_orrery_index = 0
        logs.append("【星系仪】选择完成。")
    else:
        logs.append("")
        logs.append(format_pending_orrery(run_state))
    return "\n".join(logs)


def start_pending_dollys_mirror_selection(run_state):
    run_state.pending_dollys_mirror_selection = True


def has_pending_dollys_mirror_selection(run_state):
    return bool(getattr(run_state, "pending_dollys_mirror_selection", False))


def format_pending_dollys_mirror(run_state):
    if not has_pending_dollys_mirror_selection(run_state):
        return "当前没有需要处理的【多利之镜】选择。"
    deck = getattr(run_state, "master_deck", []) or []
    lines = ["=== 多利之镜：选择要复制的牌 ===", ""]
    for index, card in enumerate(deck):
        try:
            text = card.summary_text()
        except Exception:
            text = "【{}】".format(getattr(card, "name", "未知卡牌"))
        lines.append("[{}] {}".format(index, text))
    lines.append("")
    lines.append("使用 /card mirror 0 复制对应牌。")
    return "\n".join(lines)


def choose_pending_dollys_mirror_card(run_state, card_index):
    import copy
    if not has_pending_dollys_mirror_selection(run_state):
        return "当前没有需要处理的【多利之镜】选择。"
    deck = getattr(run_state, "master_deck", []) or []
    if card_index < 0 or card_index >= len(deck):
        return "牌组编号无效。"
    card = copy.deepcopy(deck[card_index])
    run_state.pending_dollys_mirror_selection = False
    logs = ["【多利之镜】复制【{}】。".format(getattr(card, "name", "未知卡牌"))]
    logs.extend(add_card_to_master_deck_with_relics(run_state, card, source="多利之镜", apply_gain_preview=False))
    return "\n".join(logs)
