# -*- coding: utf-8 -*-
# 宝箱节点：现在支持先打开、再选择是否取走内容。

import random
from dataclasses import dataclass, field
from typing import Any, List

from data.relic.AAAregistry import create_relic
from data.card.AAAregistry import create_card, CARD_REGISTRY
from game.command_help import command_tip
from game.reward import get_available_relic_ids
from game.relic_logic.run_relic_utils import (
    gain_gold_with_relics,
    has_run_relic,
    add_card_to_master_deck_with_relics,
)


CHEST_TYPES = [
    {
        "name": "小型宝箱",
        "weight": 3,
        "relic_rarity_weights": {"common": 75, "uncommon": 25, "rare": 0},
        "old_gold_chance": 0.50,
        "gold_base": 25,
    },
    {
        "name": "中型宝箱",
        "weight": 2,
        "relic_rarity_weights": {"common": 35, "uncommon": 50, "rare": 15},
        "old_gold_chance": 0.35,
        "gold_base": 50,
    },
    {
        "name": "大型宝箱",
        "weight": 1,
        "relic_rarity_weights": {"common": 0, "uncommon": 75, "rare": 25},
        "old_gold_chance": 0.50,
        "gold_base": 75,
    },
]


@dataclass
class TreasureItem:
    item_type: str
    title: str
    payload: Any = None
    claimed: bool = False
    skipped: bool = False


@dataclass
class TreasureState:
    seed: int = 0
    chest: Any = None
    opened: bool = False
    curse_triggered: bool = False
    items: List[TreasureItem] = field(default_factory=list)
    source_node_type: str = "treasure"

    def all_done(self):
        if not self.opened:
            return False
        for item in self.items:
            if not item.claimed and not item.skipped:
                return False
        return True


def roll_chest_type(rng):
    return rng.choices(
        population=CHEST_TYPES,
        weights=[chest["weight"] for chest in CHEST_TYPES],
        k=1,
    )[0]


def roll_treasure_gold(chest, rng):
    expected = float(chest["gold_base"]) * float(chest["old_gold_chance"])
    low = int(round(expected * 0.90))
    high = int(round(expected * 1.10))
    if low < 1:
        low = 1
    if high < low:
        high = low
    return rng.randint(low, high)


def choose_relic_id_by_chest(run_state, chest, rng):
    available_relic_ids = get_available_relic_ids(run_state)
    if not available_relic_ids:
        return ""

    ids_by_rarity = {}
    for relic_id in available_relic_ids:
        relic = create_relic(relic_id)
        rarity = getattr(relic, "quantity", "")
        ids_by_rarity.setdefault(rarity, []).append(relic_id)

    rarity_weights = chest["relic_rarity_weights"]
    available_rarities = []
    available_weights = []
    for rarity, weight in rarity_weights.items():
        if weight <= 0:
            continue
        if ids_by_rarity.get(rarity):
            available_rarities.append(rarity)
            available_weights.append(weight)

    if not available_rarities:
        return rng.choice(available_relic_ids)

    rarity = rng.choices(population=available_rarities, weights=available_weights, k=1)[0]
    return rng.choice(ids_by_rarity[rarity])


def get_nloths_mask_relic(run_state):
    for relic in getattr(run_state, "relics", []) or []:
        if getattr(relic, "relic_id", "") == "relic.nloths_mask" and int(getattr(relic, "charges", 0) or 0) > 0:
            return relic
    return None


def get_matryoshka_relic(run_state):
    for relic in getattr(run_state, "relics", []) or []:
        if getattr(relic, "relic_id", "") == "relic.matryoshka" and int(getattr(relic, "charges", 0)) > 0:
            return relic
    return None


def choose_extra_relic_id_for_matryoshka(run_state, rng):
    available_relic_ids = get_available_relic_ids(run_state)
    if not available_relic_ids:
        return ""
    ids_by_rarity = {"common": [], "uncommon": []}
    for relic_id in available_relic_ids:
        relic = create_relic(relic_id)
        rarity = getattr(relic, "quantity", "")
        if rarity in ids_by_rarity:
            ids_by_rarity[rarity].append(relic_id)
    rarities = []
    weights = []
    if ids_by_rarity["common"]:
        rarities.append("common")
        weights.append(75)
    if ids_by_rarity["uncommon"]:
        rarities.append("uncommon")
        weights.append(25)
    if not rarities:
        return ""
    rarity = rng.choices(population=rarities, weights=weights, k=1)[0]
    return rng.choice(ids_by_rarity[rarity])


def create_treasure_state(run_state, seed=None, source_node_type="treasure"):
    rng = random.Random(seed)
    return TreasureState(
        seed=int(seed or 0),
        chest=roll_chest_type(rng),
        opened=False,
        items=[],
        source_node_type=source_node_type,
    )


def _roll_random_curse_id(rng):
    candidates = []
    for card_id in CARD_REGISTRY.keys():
        if card_id == "card.curse.bell":
            continue
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "card_type", "") == "curse":
            candidates.append(card_id)
    if not candidates:
        return "card.curse.injury"
    return rng.choice(candidates)


def open_pending_treasure(run_state):
    treasure = getattr(run_state, "pending_treasure", None)
    if treasure is None:
        return "当前不在宝箱房间。"
    if treasure.opened:
        return format_treasure(run_state)

    rng = random.Random(int(getattr(treasure, "seed", 0) or 0) + 17)
    chest = treasure.chest or roll_chest_type(rng)
    treasure.chest = chest
    treasure.opened = True
    logs = ["打开{}。".format(chest["name"])]

    if has_run_relic(run_state, "relic.cursed_key"):
        curse = create_card(_roll_random_curse_id(rng))
        logs.append("【诅咒钥匙】触发：打开非 Boss 宝箱，获得一张诅咒。")
        logs.extend(add_card_to_master_deck_with_relics(run_state, curse, source="诅咒钥匙"))
        treasure.curse_triggered = True

    nloths_mask = get_nloths_mask_relic(run_state)
    if nloths_mask is not None:
        nloths_mask.charges = max(0, int(getattr(nloths_mask, "charges", 0) or 0) - 1)
        logs.append("【恩洛斯的饥饿的脸】触发：这个宝箱是空的。")
        return "\n".join(logs + ["", format_treasure(run_state)])

    relic_id = choose_relic_id_by_chest(run_state, chest, rng)
    if relic_id:
        relic = create_relic(relic_id)
        treasure.items.append(TreasureItem(
            item_type="relic",
            title="遗物：【{}】".format(relic.name),
            payload={"relic": relic},
        ))
    else:
        logs.append("宝箱里没有新的遗物。")

    matryoshka = get_matryoshka_relic(run_state)
    if matryoshka is not None:
        matryoshka.charges = max(0, int(getattr(matryoshka, "charges", 0)) - 1)
        extra_relic_id = choose_extra_relic_id_for_matryoshka(run_state, rng)
        if extra_relic_id:
            extra_relic = create_relic(extra_relic_id)
            treasure.items.append(TreasureItem(
                item_type="relic",
                title="套娃：额外遗物：【{}】".format(extra_relic.name),
                payload={"relic": extra_relic, "source": "matryoshka"},
            ))
            logs.append("【套娃】触发：宝箱中额外出现 1 件遗物。剩余次数：{}。".format(int(getattr(matryoshka, "charges", 0))))
        else:
            logs.append("【套娃】触发，但当前没有可额外获得的普通/罕见遗物。")

    gold = roll_treasure_gold(chest, rng)
    if gold > 0:
        treasure.items.append(TreasureItem(
            item_type="gold",
            title="{}金币".format(gold),
            payload={"amount": gold},
        ))

    return "\n".join(logs + ["", format_treasure(run_state)])


def take_treasure_item(run_state, item_index):
    treasure = getattr(run_state, "pending_treasure", None)
    if treasure is None:
        return "当前不在宝箱房间。"
    if not treasure.opened:
        return "宝箱尚未打开。使用 /card open 打开宝箱，或 /card leave 离开。"
    if item_index < 0 or item_index >= len(treasure.items):
        return "宝箱内容编号无效。"
    item = treasure.items[item_index]
    if item.claimed:
        return "该内容已经取走。"
    if item.skipped:
        return "该内容已经放弃。"
    logs = []
    if item.item_type == "gold":
        amount = int((item.payload or {}).get("amount", 0))
        logs.extend(gain_gold_with_relics(run_state, amount, source="宝箱"))
    elif item.item_type == "relic":
        relic = (item.payload or {}).get("relic")
        if relic is None:
            logs.append("遗物内容异常，已跳过。")
        else:
            run_state.relics.append(relic)
            logs.append("获得遗物：【{}】。".format(relic.name))
            if hasattr(relic, "on_obtained"):
                logs.extend(relic.on_obtained(run_state))
    else:
        logs.append("未知宝箱内容：{}。".format(item.item_type))
    item.claimed = True
    if not logs:
        logs.append("没有获得任何东西。")
    return "\n".join(logs)


def skip_unclaimed_treasure(run_state):
    treasure = getattr(run_state, "pending_treasure", None)
    if treasure is None:
        return "当前不在宝箱房间。"
    for item in treasure.items:
        if not item.claimed and not item.skipped:
            item.skipped = True
    return "你离开了宝箱，未取走的内容被放弃。"


def format_treasure(run_state):
    treasure = getattr(run_state, "pending_treasure", None)
    if treasure is None:
        return "当前不在宝箱房间。"
    lines = ["=== 宝箱 ==="]
    chest_name = treasure.chest["name"] if treasure.chest else "宝箱"
    if not treasure.opened:
        lines.append("你发现了{}。".format(chest_name))
        lines.append(command_tip("open", "使用 /card open 打开宝箱。拥有【诅咒钥匙】时，打开会获得诅咒。"))
        lines.append(command_tip("leave", "使用 /card leave 直接离开。"))
        return "\n".join(lines)

    if not treasure.items:
        lines.append("{}已经打开，但里面没有可取走的内容。".format(chest_name))
        lines.append(command_tip("leave", "使用 /card leave 离开宝箱房间。"))
        return "\n".join(lines)

    lines.append("{}已打开。可以选择是否取走其中内容：".format(chest_name))
    for index, item in enumerate(treasure.items):
        status = ""
        if item.claimed:
            status = "（已取走）"
        elif item.skipped:
            status = "（已放弃）"
        lines.append("[{}] {}{}".format(index, item.title, status))
    lines.append("")
    lines.append(command_tip("take", "使用 /card take 0 取走宝箱内容。"))
    lines.append(command_tip("leave", "使用 /card leave 离开宝箱房间，未取走内容会放弃。"))
    return "\n".join(lines)


def open_treasure(run_state, seed=None):
    """兼容旧调用：直接打开并自动取走所有内容。"""
    run_state.pending_treasure = create_treasure_state(run_state, seed=seed)
    logs = [open_pending_treasure(run_state)]
    treasure = run_state.pending_treasure
    for index, item in enumerate(list(treasure.items)):
        if not item.claimed:
            logs.append(take_treasure_item(run_state, index))
    run_state.pending_treasure = None
    return "\n\n".join(logs)
