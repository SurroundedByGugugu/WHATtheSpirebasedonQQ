# -*- coding: utf-8 -*-

"""
卡牌附魔字段的通用读写与显示。

附魔与 keywords 平行：
- keywords 继续负责固有、保留、消耗等普通词条；
- enchanted 只保存附魔 ID；
- 允许多种附魔；
- 允许同名附魔重复出现；
- 同名附魔的实际数值由“层数 × 单层数值”计算。
"""


ENCHANTMENT_DISPLAY_NAMES = {
    "index_shade": "索引·阴",
    "index_shade_plus": "索引·阴+",
}


def normalize_enchantment_id(enchantment_id):
    return str(enchantment_id or "").strip().lower()


def get_card_enchantments(card):
    """
    返回卡牌的 enchanted 列表。

    getattr 兼容热更新前创建、尚未拥有 enchanted 属性的旧卡牌实例。
    """
    enchanted = getattr(card, "enchanted", None)

    if enchanted is None:
        enchanted = []
        setattr(card, "enchanted", enchanted)

    return enchanted


def add_card_enchantment(card, enchantment_id, stacks=1):
    """
    为卡牌追加附魔层数。

    不去重；同名 ID 重复保存即代表重复附魔。
    返回实际添加的层数。
    """
    enchantment_id = normalize_enchantment_id(enchantment_id)

    try:
        stacks = int(stacks)
    except (TypeError, ValueError):
        stacks = 0

    if not enchantment_id or stacks <= 0:
        return 0

    get_card_enchantments(card).extend([
        enchantment_id
    ] * stacks)

    return stacks


def remove_card_enchantment(
    card,
    enchantment_id,
    stacks=1,
    remove_all=False
):
    """
    移除指定附魔。

    remove_all=True：
        移除全部同名附魔。

    remove_all=False：
        至多移除 stacks 层。

    返回实际移除层数。
    """
    enchantment_id = normalize_enchantment_id(enchantment_id)
    enchanted = get_card_enchantments(card)

    if not enchantment_id or not enchanted:
        return 0

    if remove_all:
        old_count = len(enchanted)

        enchanted[:] = [
            current
            for current in enchanted
            if normalize_enchantment_id(current) != enchantment_id
        ]

        return old_count - len(enchanted)

    try:
        stacks = int(stacks)
    except (TypeError, ValueError):
        stacks = 0

    if stacks <= 0:
        return 0

    removed = 0
    index = len(enchanted) - 1

    while index >= 0 and removed < stacks:
        current = normalize_enchantment_id(enchanted[index])

        if current == enchantment_id:
            enchanted.pop(index)
            removed += 1

        index -= 1

    return removed


def is_card_enchanted(card):
    """
    卡牌只要拥有至少一层附魔，就属于附魔牌。

    打火机之类只关心“是否附魔”的遗物使用此函数。
    """
    return bool(get_card_enchantments(card))


def has_card_enchantment(card, enchantment_id):
    return get_card_enchantment_stacks(
        card,
        enchantment_id
    ) > 0


def get_card_enchantment_stacks(card, enchantment_id):
    """
    返回指定附魔的层数。
    """
    enchantment_id = normalize_enchantment_id(enchantment_id)

    if not enchantment_id:
        return 0

    return sum(
        1
        for current in get_card_enchantments(card)
        if normalize_enchantment_id(current) == enchantment_id
    )


def get_card_total_enchantment_stacks(card):
    """
    返回附魔总层数。

    同名附魔重复出现时分别计数。
    """
    return len(get_card_enchantments(card))


def get_card_distinct_enchantment_count(card):
    """
    返回不同附魔 ID 的数量。
    """
    return len({
        normalize_enchantment_id(enchantment_id)
        for enchantment_id in get_card_enchantments(card)
        if normalize_enchantment_id(enchantment_id)
    })


def get_enchantment_display_name(enchantment_id):
    enchantment_id = normalize_enchantment_id(enchantment_id)

    return ENCHANTMENT_DISPLAY_NAMES.get(
        enchantment_id,
        enchantment_id
    )


def get_card_enchantment_counts(card):
    """
    按首次出现顺序聚合同名附魔。

    返回：
        [
            ("sharp", 2),
            ("steady", 1),
        ]
    """
    counts = {}

    for raw_id in get_card_enchantments(card):
        enchantment_id = normalize_enchantment_id(raw_id)

        if not enchantment_id:
            continue

        counts[enchantment_id] = (
            counts.get(enchantment_id, 0) + 1
        )

    return list(counts.items())


def get_card_enchantment_display_text(card):
    """
    返回：
        附魔：锋利×2，沉稳
    """
    counts = get_card_enchantment_counts(card)

    if not counts:
        return ""

    parts = []

    for enchantment_id, stacks in counts:
        display_name = get_enchantment_display_name(
            enchantment_id
        )

        if stacks > 1:
            parts.append("{}×{}".format(
                display_name,
                stacks
            ))
        else:
            parts.append(display_name)

    return "附魔：{}".format("，".join(parts))