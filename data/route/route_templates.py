# -*- coding: utf-8 -*-
# 路线模板

ACT1_TEST_ROUTE = [
    {
        "node_id": "act1.ancient.start",
        "node_type": "ancient",
        "name": "先古之民",
        "next_node_ids": ["act1.node.01"]
    },

    {
        "node_id": "act1.node.01",
        "node_type": "starting",
        "name": "普通战斗",
        "next_node_ids": ["act1.node.02a", "act1.node.02b"]
    },

    {
        "node_id": "act1.node.02a",
        "node_type": "starting",
        "name": "普通战斗",
        "next_node_ids": ["act1.node.03a", "act1.node.03b"]
    },
    {
        "node_id": "act1.node.02b",
        "node_type": "mystery",
        "name": "右路？",
        "next_node_ids": ["act1.node.03b"]
    },

    {
        "node_id": "act1.node.03a",
        "node_type": "shop",
        "name": "临时商店",
        "next_node_ids": ["act1.node.04a"]
    },
    {
        "node_id": "act1.node.03b",
        "node_type": "mystery",
        "name": "岔路？",
        "next_node_ids": ["act1.node.04a", "act1.node.04b"]
    },

    {
        "node_id": "act1.node.04a",
        "node_type": "normal_enemy",
        "name": "普通战斗",
        "next_node_ids": ["act1.node.05"]
    },
    {
        "node_id": "act1.node.04b",
        "node_type": "elite",
        "name": "精英战斗",
        "next_node_ids": ["act1.node.05"]
    },

    {
        "node_id": "act1.node.05",
        "node_type": "event",
        "name": "异常房间",
        "next_node_ids": ["act1.node.06a", "act1.node.06b"]
    },

    {
        "node_id": "act1.node.06a",
        "node_type": "rest",
        "name": "小火堆",
        "next_node_ids": ["act1.node.07"]
    },
    {
        "node_id": "act1.node.06b",
        "node_type": "shop",
        "name": "商店",
        "next_node_ids": ["act1.node.07"]
    },

    {
        "node_id": "act1.node.07",
        "node_type": "normal_enemy",
        "name": "普通战斗",
        "next_node_ids": ["act1.node.08a", "act1.node.08b"]
    },

    {
        "node_id": "act1.node.08a",
        "node_type": "mystery",
        "name": "深处？",
        "next_node_ids": ["act1.node.09a","act1.node.09b"]
    },
    {
        "node_id": "act1.node.08b",
        "node_type": "treasure",
        "name": "旧宝箱",
        "next_node_ids": ["act1.node.09a","act1.node.09b"]
    },

    {
        "node_id": "act1.node.09a",
        "node_type": "elite",
        "name": "精英战斗",
        "next_node_ids": ["act1.node.10a", "act1.node.10b"]
    },
    {
        "node_id": "act1.node.09b",
        "node_type": "rest",
        "name": "小火堆",
        "next_node_ids": ["act1.node.10a", "act1.node.10b"]
    },
    {
        "node_id": "act1.node.10a",
        "node_type": "normal_enemy",
        "name": "普通战斗",
        "next_node_ids": ["act1.rest.before_boss"]
    },
    {
        "node_id": "act1.node.10b",
        "node_type": "shop",
        "name": "Boss 前商店",
        "next_node_ids": ["act1.rest.before_boss"]
    },

    {
        "node_id": "act1.rest.before_boss",
        "node_type": "rest",
        "name": "Boss 前火堆",
        "next_node_ids": ["act1.boss"]
    },

    {
        "node_id": "act1.boss",
        "node_type": "boss",
        "name": "一层 Boss",
        "next_node_ids": []
        # "next_node_ids": ["act2.ancient.start"]
    },
    # {
    #     "node_id": "act2.ancient.start",
    #     "node_type": "ancient",
    #     "name": "下一层的先古之民",
    #     "next_node_ids": []
    # },
]
ACT2_TEST_ROUTE=[
    {
        "node_id": "act1.ancient.start",
        "node_type": "ancient",
        "name": "先古之民",
        "next_node_ids": ["act1.node.01"]
    },
    {
        "node_id": "act1.node.01",
        "node_type": "normal_enemy",
        "name": "入口战斗",
        "next_node_ids": ["act1.node.02"]
    },
    {
        "node_id": "act1.node.02",
        "node_type": "event",
        "name": "异常房间",
        "next_node_ids": ["act1.node.04"]
    },
    {
        "node_id": "act1.node.04",
        "node_type": "shop",
        "name": "Boss 前商店",
        "next_node_ids": ["act1.rest.before_boss"]
    },

    {
        "node_id": "act1.rest.before_boss",
        "node_type": "rest",
        "name": "Boss 前火堆",
        "next_node_ids": ["act1.elite"]
    },
    {
        "node_id": "act1.elite",
        "node_type": "elite",
        "name": "伪装成boss的精英",
        "next_node_ids": ["act1.boss"]
    },
    {
        "node_id": "act1.boss",
        "node_type": "boss",
        "name": "珊瑚集群和正在进食的棘冠海星",
        "next_node_ids": []
    },
]
TEST_ROUTE = ACT1_TEST_ROUTE

# =========================
# 正式版：固定 5 列文本地图
# =========================

import random

MAP_WIDTH = 5
ACT1_MAX_FLOOR = 15
ACT1_TREASURE_FLOOR = 9
ACT1_PRE_BOSS_REST_FLOOR = 14
ACT1_BOSS_FLOOR = 15

NODE_NAME_BY_TYPE = {
    "ancient": "先古之民",
    "starting": "起始战斗",
    "normal_enemy": "普通战斗",
    "elite": "精英战斗",
    "event": "事件",
    "mystery": "未知房间",
    "shop": "商店",
    "rest": "火堆",
    "treasure": "宝箱",
    "boss": "一层 Boss",
}


def make_grid_node_id(act, floor, col=None):
    if col is None:
        return "act{}.floor{:02d}".format(act, floor)
    return "act{}.floor{:02d}.col{}".format(act, floor, col)


def make_adjacent_next_ids(act, floor, col):
    next_floor = floor + 1
    if next_floor > ACT1_BOSS_FLOOR:
        return []

    result = []
    for next_col in (col - 1, col, col + 1):
        if 0 <= next_col < MAP_WIDTH:
            result.append(make_grid_node_id(act, next_floor, next_col))
    return result


def make_full_next_ids(act, floor):
    next_floor = floor + 1
    if next_floor > ACT1_BOSS_FLOOR:
        return []

    return [
        make_grid_node_id(act, next_floor, col)
        for col in range(MAP_WIDTH)
    ]


def choose_node_type_for_floor(floor, rng, current_counts):
    """
    普通随机层节点生成规则：
    - 前期偏向普通战斗和事件。
    - 第 4 层后允许精英。
    - 中后段允许火堆和商店。
    - 每层至少 2 个普通战斗。
    - 每层精英最多 2 个。
    - 每层商店最多 1 个。
    - 每层火堆最多 1 个。
    """
    remaining_slots = MAP_WIDTH - sum(current_counts.values())
    normal_count = current_counts.get("normal_enemy", 0)

    if normal_count + remaining_slots <= 2:
        return "normal_enemy"

    if floor in (2, 3):
        population = ["normal_enemy", "event"]
        weights = [75, 25]
    elif 4 <= floor <= 5:
        population = ["normal_enemy", "event", "elite", "shop"]
        weights = [60, 25, 12, 3]
    elif 6 <= floor <= 9:
        population = ["normal_enemy", "event", "elite", "shop", "rest"]
        weights = [48, 27, 15, 5, 5]
    elif 11 <= floor <= 13:
        population = ["normal_enemy", "event", "elite", "shop", "rest"]
        weights = [45, 25, 16, 7, 7]
    else:
        population = ["normal_enemy", "event"]
        weights = [70, 30]

    for _ in range(20):
        node_type = rng.choices(
            population=population,
            weights=weights,
            k=1
        )[0]

        if node_type == "elite" and current_counts.get("elite", 0) >= 2:
            continue
        if node_type == "shop" and current_counts.get("shop", 0) >= 1:
            continue
        if node_type == "rest" and current_counts.get("rest", 0) >= 1:
            continue

        return node_type

    return "normal_enemy"


def generate_random_floor_types(floor, rng):
    counts = {}
    result = []

    for _ in range(MAP_WIDTH):
        node_type = choose_node_type_for_floor(floor, rng, counts)
        result.append(node_type)
        counts[node_type] = counts.get(node_type, 0) + 1

    # 避免一整层全是普通战斗。
    if floor not in (
        1,
        ACT1_TREASURE_FLOOR,
        ACT1_PRE_BOSS_REST_FLOOR,
        ACT1_BOSS_FLOOR,
    ):
        if all(node_type == "normal_enemy" for node_type in result):
            replace_col = rng.randrange(MAP_WIDTH)
            result[replace_col] = "event"

    return result


def generate_act1_grid_route(seed=None):
    """
    生成固定 5 列、15 层的一层路线。

    第 0 层：先古之民，单节点。
    第 1 层：5 个 starting 战斗，允许任选，用于决定初始列。
    第 10 层：5 个宝箱。
    第 14 层：5 个火堆。
    第 15 层：5 个 Boss。
    """
    rng = random.Random(seed)
    route = []

    route.append({
        "node_id": make_grid_node_id(1, 0),
        "node_type": "ancient",
        "name": NODE_NAME_BY_TYPE["ancient"],
        "floor": 0,
        "col": -1,
        "next_node_ids": make_full_next_ids(1, 0),
    })

    for floor in range(1, ACT1_BOSS_FLOOR + 1):
        if floor == 1:
            floor_types = ["starting"] * MAP_WIDTH
        elif floor == ACT1_TREASURE_FLOOR:
            floor_types = ["treasure"] * MAP_WIDTH
        elif floor == ACT1_PRE_BOSS_REST_FLOOR:
            floor_types = ["rest"] * MAP_WIDTH
        elif floor == ACT1_BOSS_FLOOR:
            floor_types = ["boss"] * MAP_WIDTH
        else:
            floor_types = generate_random_floor_types(floor, rng)

        for col, node_type in enumerate(floor_types):
            route.append({
                "node_id": make_grid_node_id(1, floor, col),
                "node_type": node_type,
                "name": NODE_NAME_BY_TYPE.get(node_type, node_type),
                "floor": floor,
                "col": col,
                "next_node_ids": make_adjacent_next_ids(1, floor, col),
            })

    return route