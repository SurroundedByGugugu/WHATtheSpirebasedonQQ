# -*- coding: utf-8 -*-
# 瓶装遗物选择逻辑。

from game.command_help import command_tip


BOTTLE_RELIC_CONFIG = {
    "relic.bottled_lightning": {
        "required_card_type": "skill",
        "required_card_type_name": "技能牌",
    },
    "relic.bottled_flame": {
        "required_card_type": "attack",
        "required_card_type_name": "攻击牌",
    },
    "relic.bottled_tornado": {
        "required_card_type": "power",
        "required_card_type_name": "能力牌",
    },
}


BOTTLE_ATTRS = ("bottled_by", "bottled_relic_id", "bottled_card_type")


def get_pending_bottle_queue(run_state):
    queue = getattr(run_state, "pending_bottle_selections", None)
    if queue is None:
        queue = []
        setattr(run_state, "pending_bottle_selections", queue)
    return queue


def has_pending_bottle_selection(run_state):
    return bool(get_pending_bottle_queue(run_state))


def is_card_bottled(card):
    return bool(
        getattr(card, "bottled_by", "")
        or getattr(card, "bottled_relic_id", "")
    )


def get_bottle_candidates(run_state, required_card_type):
    result = []
    for deck_index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if getattr(card, "card_type", "") != required_card_type:
            continue
        if is_card_bottled(card):
            continue
        result.append((deck_index, card))
    return result


def start_pending_bottle_selection(run_state, relic_id, relic_name, required_card_type=None):
    config = BOTTLE_RELIC_CONFIG.get(relic_id, {})
    required_card_type = required_card_type or config.get("required_card_type", "")
    required_card_type_name = config.get("required_card_type_name", required_card_type)

    if not required_card_type:
        return ["【{}】没有配置可瓶装的卡牌类型。".format(relic_name)]

    candidates = get_bottle_candidates(run_state, required_card_type)
    if not candidates:
        return ["【{}】没有找到可瓶装的{}。".format(relic_name, required_card_type_name)]

    queue = get_pending_bottle_queue(run_state)
    queue.append({
        "relic_id": relic_id,
        "relic_name": relic_name,
        "required_card_type": required_card_type,
        "required_card_type_name": required_card_type_name,
    })

    return [
        "【{}】等待选择一张{}进行瓶装。".format(relic_name, required_card_type_name),
        command_tip("bottle", "使用 /card bottle 0 选择。"),
    ]


def format_pending_bottle(run_state):
    queue = get_pending_bottle_queue(run_state)
    if not queue:
        return "当前没有需要处理的瓶装选择。"

    pending = queue[0]
    relic_name = pending.get("relic_name", "瓶装遗物")
    required_card_type = pending.get("required_card_type", "")
    required_card_type_name = pending.get("required_card_type_name", required_card_type)

    candidates = get_bottle_candidates(run_state, required_card_type)

    lines = []
    lines.append("=== 瓶装选择 ===")
    lines.append("【{}】：选择一张{}。".format(relic_name, required_card_type_name))

    if len(queue) > 1:
        lines.append("当前还有 {} 个瓶装选择等待处理。".format(len(queue) - 1))

    lines.append("")

    if not candidates:
        lines.append("当前没有可瓶装的{}。".format(required_card_type_name))
        lines.append("可以使用 /card bottle -1 跳过这个瓶装选择。")
        return "\n".join(lines)

    for display_index, item in enumerate(candidates):
        deck_index, card = item
        lines.append("[{}] 牌组编号 {}：{}".format(
            display_index,
            deck_index,
            card.summary_text()
        ))

    lines.append("")
    lines.append(command_tip("bottle", "使用 /card bottle 0 选择。"))
    return "\n".join(lines)


def choose_pending_bottle_card(run_state, choice_index):
    queue = get_pending_bottle_queue(run_state)
    if not queue:
        return "当前没有需要处理的瓶装选择。"

    pending = queue[0]
    relic_id = pending.get("relic_id", "")
    relic_name = pending.get("relic_name", "瓶装遗物")
    required_card_type = pending.get("required_card_type", "")
    required_card_type_name = pending.get("required_card_type_name", required_card_type)

    candidates = get_bottle_candidates(run_state, required_card_type)

    if choice_index == -1:
        queue.pop(0)
        lines = ["已跳过【{}】的瓶装选择。".format(relic_name)]
        if queue:
            lines.append("")
            lines.append(format_pending_bottle(run_state))
        return "\n".join(lines)

    if choice_index < 0 or choice_index >= len(candidates):
        return "瓶装选择编号无效。"

    deck_index, card = candidates[choice_index]

    setattr(card, "bottled_by", relic_id)
    setattr(card, "bottled_relic_id", relic_id)
    setattr(card, "bottled_card_type", required_card_type)

    queue.pop(0)

    lines = []
    lines.append("【{}】瓶装了【{}】。".format(relic_name, card.name))
    lines.append("这张牌会在每场战斗开始时出现在手牌中。")

    if queue:
        lines.append("")
        lines.append(format_pending_bottle(run_state))

    return "\n".join(lines)


def strip_bottled_flags(card):
    for attr in BOTTLE_ATTRS:
        if hasattr(card, attr):
            try:
                delattr(card, attr)
            except Exception:
                setattr(card, attr, "")
    return card


def copy_bottled_flags(old_card, new_card):
    """
    长期牌组升级时保留瓶装标记。
    复制祭坛不要用这个；复制祭坛应继续清除瓶装标记。
    """
    for attr in BOTTLE_ATTRS:
        value = getattr(old_card, attr, "")
        if value:
            setattr(new_card, attr, value)
    return new_card