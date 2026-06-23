# -*- coding: utf-8 -*-
# 宝箱节点：必定获得遗物，并必定获得金币。

import random

from data.relic.AAAregistry import create_relic
from game.reward import get_available_relic_ids
from game.relic_logic.run_relic_utils import gain_gold_with_relics


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


def open_treasure(run_state, seed=None):
    rng = random.Random(seed)
    chest = roll_chest_type(rng)

    matryoshka_before_open = get_matryoshka_relic(run_state)
    relic_id = choose_relic_id_by_chest(run_state, chest, rng)

    gold = roll_treasure_gold(chest, rng)

    logs = []
    logs.append("打开{}。".format(chest["name"]))

    if relic_id:
        relic = create_relic(relic_id)
        run_state.relics.append(relic)
        logs.append("获得遗物：【{}】。".format(relic.name))

        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))

        matryoshka = matryoshka_before_open
        if matryoshka is not None:
            matryoshka.charges = max(0, int(getattr(matryoshka, "charges", 0)) - 1)
            extra_relic_id = choose_extra_relic_id_for_matryoshka(run_state, rng)
            if extra_relic_id:
                extra_relic = create_relic(extra_relic_id)
                run_state.relics.append(extra_relic)
                logs.append("【套娃】触发：额外获得遗物：【{}】。剩余次数：{}。".format(
                    extra_relic.name, int(getattr(matryoshka, "charges", 0))
                ))
                if hasattr(extra_relic, "on_obtained"):
                    logs.extend(extra_relic.on_obtained(run_state))
            else:
                logs.append("【套娃】触发，但当前没有可额外获得的普通/罕见遗物。")
    else:
        logs.append("宝箱里没有新的遗物。")

    logs.extend(gain_gold_with_relics(run_state, gold, source="宝箱"))

    return "\n".join(logs)