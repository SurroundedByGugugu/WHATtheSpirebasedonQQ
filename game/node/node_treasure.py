# -*- coding: utf-8 -*-
# 宝箱节点：必定获得遗物，并必定获得金币。

import random

from data.relic.AAAregistry import create_relic
from game.reward import get_available_relic_ids


CHEST_TYPES = [
    {
        "name": "小型宝箱",
        "weight": 3,
        "relic_rarity_weights": {
            "common": 75,
            "uncommon": 25,
            "rare": 0,
        },
        "old_gold_chance": 0.50,
        "gold_base": 25,
    },
    {
        "name": "中型宝箱",
        "weight": 2,
        "relic_rarity_weights": {
            "common": 35,
            "uncommon": 50,
            "rare": 15,
        },
        "old_gold_chance": 0.35,
        "gold_base": 50,
    },
    {
        "name": "大型宝箱",
        "weight": 1,
        "relic_rarity_weights": {
            "common": 0,
            "uncommon": 75,
            "rare": 25,
        },
        "old_gold_chance": 0.50,
        "gold_base": 75,
    },
]


def roll_chest_type(rng):
    return rng.choices(
        population=CHEST_TYPES,
        weights=[chest["weight"] for chest in CHEST_TYPES],
        k=1,
    )[0]


def roll_treasure_gold(chest, rng):
    """
    原作式宝箱是“有概率出金币”。
    这里改为必定有金币，并把原金币出现概率折算进金币数量期望：
    amount = gold_base * old_gold_chance * 90%~110%
    """
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

    # 如果当前实现的遗物池暂时缺少对应稀有度，就退回到全部可用遗物。
    if not available_rarities:
        return rng.choice(available_relic_ids)

    rarity = rng.choices(
        population=available_rarities,
        weights=available_weights,
        k=1,
    )[0]

    return rng.choice(ids_by_rarity[rarity])


def open_treasure(run_state, seed=None):
    rng = random.Random(seed)
    chest = roll_chest_type(rng)

    relic_id = choose_relic_id_by_chest(run_state, chest, rng)

    gold = roll_treasure_gold(chest, rng)
    run_state.gold += gold

    logs = []
    logs.append("打开{}。".format(chest["name"]))

    if relic_id:
        relic = create_relic(relic_id)
        run_state.relics.append(relic)
        logs.append("获得遗物：【{}】。".format(relic.name))

        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))
    else:
        logs.append("宝箱里没有新的遗物。")

    logs.append("获得 {} 金币。当前金币：{}。".format(
        gold,
        run_state.gold
    ))

    return "\n".join(logs)