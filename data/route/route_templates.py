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
    "boss_empty": "Boss（未实现）",
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


def get_floor_type_counts(route, floor):
    counts = {}

    for item in route:
        if int(item.get("floor", -1)) != int(floor):
            continue

        node_type = item.get("node_type", "")
        counts[node_type] = counts.get(node_type, 0) + 1

    return counts


def replace_random_route_node_type(route, rng, candidate_floors, new_type):
    """
    给随机地图做保底补点。

    优先替换事件；其次替换普通战斗，但保留每层至少 2 个普通战斗。
    不替换 starting / treasure / boss / shop / rest。
    """
    fixed_types = {"starting", "treasure", "boss", "shop", "rest"}
    candidate_floors = set(candidate_floors)

    def collect(prefer_event):
        result = []

        for item in route:
            floor = int(item.get("floor", -1))
            if floor not in candidate_floors:
                continue
            if int(item.get("col", -1)) < 0:
                continue

            node_type = item.get("node_type", "")
            if node_type in fixed_types:
                continue
            if prefer_event and node_type != "event":
                continue

            if node_type == "normal_enemy":
                counts = get_floor_type_counts(route, floor)
                if counts.get("normal_enemy", 0) <= 2:
                    continue

            result.append(item)

        return result

    candidates = collect(prefer_event=True)
    if not candidates:
        candidates = collect(prefer_event=False)

    if not candidates:
        return False

    item = rng.choice(candidates)
    item["node_type"] = new_type
    item["name"] = NODE_NAME_BY_TYPE.get(new_type, new_type)

    return True


def floor_has_support_room(route, floor):
    """判断某一整层是否已经有商店或火堆。"""
    return any(
        int(item.get("floor", -1)) == int(floor)
        and item.get("node_type") in ("shop", "rest")
        for item in route
    )


def is_mutable_support_floor(floor):
    """可被保底逻辑替换成商店/火堆的普通楼层。"""
    if floor <= 1:
        return False
    if floor in (ACT1_TREASURE_FLOOR, ACT1_PRE_BOSS_REST_FLOOR, ACT1_BOSS_FLOOR):
        return False
    return True


def enforce_sliding_shop_rest_guarantee(route, rng, start_floor=2, end_floor=13, lookback=3):
    """
    滑动窗口保底商店/火堆密度。

    规则近似：若前 lookback 层整层都没有商店或火堆，
    则在当前层强行刷出 1~2 个商店/火堆。
    例如玩家站在第 2 层时，如果第 3、4、5 层都没有补给，
    第 6 层会被保底刷出补给点。玩家最终走不走得到由路线连接决定。
    """
    for floor in range(int(start_floor), int(end_floor) + 1):
        if not is_mutable_support_floor(floor):
            continue
        if floor_has_support_room(route, floor):
            continue

        previous_floors = [f for f in range(floor - int(lookback), floor) if f >= 1]
        if len(previous_floors) < int(lookback):
            continue
        if any(floor_has_support_room(route, f) for f in previous_floors):
            continue

        inject_count = 2 if rng.random() < 0.35 else 1
        used_types = set()
        for _ in range(inject_count):
            allowed_types = ["shop"]
            if floor >= 6:
                allowed_types.append("rest")
            if len(used_types) < len(allowed_types):
                candidates = [t for t in allowed_types if t not in used_types]
            else:
                candidates = allowed_types
            new_type = rng.choice(candidates)
            if replace_random_route_node_type(route, rng, [floor], new_type):
                used_types.add(new_type)

    return route


def enforce_act1_route_guarantees(route, rng):
    """
    避免随机结果在可变楼层完全没有商店或火堆。

    第 14 层已经固定为 Boss 前火堆；
    这里额外保证：
    - 4~13 层至少有 1 个商店；
    - 6~13 层至少有 1 个随机火堆。
    """
    shop_floors = [
        floor for floor in range(4, 14)
        if floor != ACT1_TREASURE_FLOOR
    ]
    rest_floors = [
        floor for floor in range(6, 14)
        if floor != ACT1_TREASURE_FLOOR
    ]

    has_shop = any(
        item.get("node_type") == "shop"
        and int(item.get("floor", -1)) in shop_floors
        for item in route
    )

    has_rest = any(
        item.get("node_type") == "rest"
        and int(item.get("floor", -1)) in rest_floors
        for item in route
    )

    if not has_shop:
        replace_random_route_node_type(route, rng, shop_floors, "shop")

    if not has_rest:
        replace_random_route_node_type(route, rng, rest_floors, "rest")

    enforce_sliding_shop_rest_guarantee(route, rng, start_floor=2, end_floor=13, lookback=3)

    return route

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
    enforce_act1_route_guarantees(route, rng)
    return route


def generate_act2_grid_route(seed=None):
    """
    生成固定 5 列、15 层的二层路线。

    二层普通/精英遭遇已通过 run_engine 中的 pool_suffix 选择接到 1_2 池；
    二层 Boss 使用 boss 节点，并由 run_engine.prepare_visible_boss_for_route
    提前写入二层 Boss encounter，保证地图预告与实际战斗一致。
    """
    rng = random.Random(seed)
    route = []

    route.append({
        "node_id": make_grid_node_id(2, 0),
        "node_type": "ancient",
        "name": NODE_NAME_BY_TYPE["ancient"],
        "floor": 0,
        "col": -1,
        "next_node_ids": make_full_next_ids(2, 0),
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
                "node_id": make_grid_node_id(2, floor, col),
                "node_type": node_type,
                "name": NODE_NAME_BY_TYPE.get(node_type, node_type),
                "floor": floor,
                "col": col,
                "next_node_ids": make_adjacent_next_ids(2, floor, col),
            })

    enforce_act1_route_guarantees(route, rng)
    return route

def generate_act3_grid_route(seed=None):
    """
    生成固定 5 列、15 层的三层路线。

    三层事件池由 node_event_1_3.py 提供。
    当前普通/精英/Boss 遭遇暂沿用 1_2 池；后续补三层怪物池时再接 1_3 后缀。
    """
    rng = random.Random(seed)
    route = []

    route.append({
        "node_id": make_grid_node_id(3, 0),
        "node_type": "ancient",
        "name": NODE_NAME_BY_TYPE["ancient"],
        "floor": 0,
        "col": -1,
        "next_node_ids": make_full_next_ids(3, 0),
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
            name = NODE_NAME_BY_TYPE.get(node_type, node_type)
            if node_type == "boss":
                name = "三层 Boss"

            route.append({
                "node_id": make_grid_node_id(3, floor, col),
                "node_type": node_type,
                "name": name,
                "floor": floor,
                "col": col,
                "next_node_ids": make_adjacent_next_ids(3, floor, col),
            })

    enforce_act1_route_guarantees(route, rng)
    return route