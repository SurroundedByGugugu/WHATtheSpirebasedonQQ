# -*- coding: utf-8 -*-

from data.content_gate import is_content_enabled

def normalize_weighted_pool(pool, default_weight=1):
    """
    统一 encounter pool 格式。

    支持：
    1. 加权格式：
       [("encounter.xxx", 10)]

    2. 简写格式：
       ["encounter.xxx"]

    简写格式会自动补 default_weight。
    """
    result = []

    for item in pool or []:
        if isinstance(item, str):
            result.append((item, default_weight))
            continue

        if isinstance(item, tuple) and len(item) >= 2:
            result.append((item[0], item[1]))
            continue

        if isinstance(item, list) and len(item) >= 2:
            result.append((item[0], item[1]))
            continue

        raise ValueError("非法 encounter pool 项：{}".format(item))

    return result


def pick_weighted(pool, rng):
    pool = normalize_weighted_pool(pool)
    if not pool:
        raise ValueError("encounter pool 为空，无法随机遭遇。")

    encounter_ids = [item[0] for item in pool]
    weights = [item[1] for item in pool]
    return rng.choices(encounter_ids, weights=weights, k=1)[0]


def filter_encounter_pool(pool):
    normalized_pool = normalize_weighted_pool(pool)
    filtered = [
        item for item in normalized_pool
        if is_content_enabled("encounter", item[0])
    ]
    return filtered or normalized_pool


ENCOUNTER_SEEN_ALIAS_MAP = {
    # 冒险者尸体中睡醒的乐加维林，和精英池中开局睡觉的乐加维林视为同一个遭遇。
    "encounter.event.lagavulin_awake": "encounter.elite.lagavulin",
}


def get_encounter_seen_key(encounter_id):
    return ENCOUNTER_SEEN_ALIAS_MAP.get(encounter_id, encounter_id)


def get_unseen_weighted_pool(pool, seen_encounter_ids):
    seen = set([get_encounter_seen_key(encounter_id) for encounter_id in (seen_encounter_ids or [])])
    unseen_pool = [
        item for item in pool
        if get_encounter_seen_key(item[0]) not in seen
    ]
    return unseen_pool or pool


def pick_weighted_with_seen_priority(pool, rng, seen_encounter_ids=None):
    return pick_weighted(get_unseen_weighted_pool(pool, seen_encounter_ids), rng)

ENCOUNTER_TABLE = {
    "encounter.test_dummy": {"enemy_ids": ["enemy.test_dummy"]},
    "encounter.elite.chaos_fragment": {"enemy_ids": ["enemy.chaos_fragment"]},
    "encounter.elite.plastic_bag": {"enemy_ids":["enemy.plastic_bag"]},
    "encounter.corsoal_single": { "enemy_ids": ["enemy.corsoal"]},
    "encounter.mareanie_single": {"enemy_ids": ["enemy.mareanie"]},
    "encounter.corsoal_mareanie_pack": {"enemy_ids": ["enemy.corsoal", "enemy.corsoal", "enemy.mareanie"]},
    "encounter.cultist_1":{"enemy_ids":["enemy.cultist"]},
    "encounter.slimes_ms1":{"enemy_ids":["enemy.spike_slime_middle","enemy.acid_slime_small"]},
    "encounter.slimes_ms2":{"enemy_ids":["enemy.acid_slime_middle","enemy.spike_slime_small"]},
    "encounter.slimes_l1":{"enemy_ids":["enemy.acid_slime_large"]},
    "encounter.slimes_l2":{"enemy_ids":["enemy.spike_slime_large"]},
    "encounter.slimes_cluster":{"enemy_ids":["enemy.spike_slime_small","enemy.spike_slime_small","enemy.spike_slime_small","enemy.acid_slime_small","enemy.acid_slime_small"]},
    "encounter.jaw_worm_starting":{"enemy_ids":["enemy.jaw_worm_g1"]},
    "encounter.louses_2":{"enemy_ids":["enemy.random_louse","enemy.random_louse"]},
    "encounter.louses_3":{"enemy_ids":["enemy.random_louse","enemy.random_louse","enemy.random_louse"]},
    "encounter.fungi_beast_2":{"enemy_ids":["enemy.fungi_beast","enemy.fungi_beast"]},
    "encounter.fungi_beast_slime1":{"enemy_ids":["enemy.fungi_beast","enemy.spike_slime_small"]},
    "encounter.fungi_beast_slime2":{"enemy_ids":["enemy.fungi_beast","enemy.acid_slime_small"]},
    "encounter.fungi_beast_louse":{"enemy_ids":["enemy.fungi_beast","enemy.random_louse"]},
    "encounter.fungi_beast_3":{"enemy_ids":["enemy.fungi_beast","enemy.fungi_beast","enemy.fungi_beast"]},#event
    "encounter.red_slaver": {"enemy_ids": ["enemy.red_slaver"]},
    "encounter.blue_slaver": {"enemy_ids": ["enemy.blue_slaver"]},
    "encounter.thief_looter": {"enemy_ids": ["enemy.looter"]},
    "encounter.exordium_thugs": {"enemy_ids": [
            ["enemy.red_louse","enemy.green_louse","enemy.spike_slime_middle","enemy.acid_slime_middle",],
            ["enemy.looter","enemy.cultist","enemy.red_slaver","enemy.blue_slaver",],
        ]},
    "encounter.exordium_wildlife": {"enemy_ids": [
            ["enemy.fungi_beast","enemy.jaw_worm_g1",],
            ["enemy.red_louse","enemy.green_louse","enemy.spike_slime_middle","enemy.acid_slime_middle",],
        ]},
    "encounter.gremlin_gang": {"generator":"gremlin_gang"},
    "encounter.elite.gremlin_nob": {"enemy_ids": ["enemy.gremlin_nob"]},
    "encounter.elite.lagavulin": {"enemy_ids": ["enemy.lagavulin"]},
    "encounter.event.lagavulin_awake": {"enemy_ids": ["enemy.lagavulin_awake"]},
    "encounter.elite.sentries_bab": {"enemy_ids": ["enemy.sentry_b", "enemy.sentry_a", "enemy.sentry_b"]},
    "encounter.boss.hexaghost": {"enemy_ids": ["enemy.hexaghost"]},
    "encounter.boss.guardian": { "enemy_ids": ["enemy.guardian"]},
    "encounter.boss.slime_boss": {"enemy_ids": ["enemy.slime_boss"]},

    "encounter.byrd_3": {"enemy_ids": ["enemy.byrd","enemy.byrd","enemy.byrd"]},
    "encounter.shelled_parasite_single": {"enemy_ids": ["enemy.shelled_parasite"]},
    "encounter.thieves_2":{"enemy_ids": ["enemy.looter","enemy.mugger"]},
    "encounter.chosen_single":{"enemy_ids": ["enemy.chosen"]},
    "encounter.spheric_guardian_single":{"enemy_ids": ["enemy.spheric_guardian"]},

    "encounter.snecko_single": {"enemy_ids": ["enemy.snecko"]},
    "encounter.sentry_spheric_guardian":{"enemy_ids": ["enemy.sentry_b","enemy.spheric_guardian"]},
    "encounter.cultist_3":{"enemy_ids": ["enemy.cultist","enemy.cultist","enemy.cultist"]},
    "encounter.shelled_parasite_fungi_beast":{"enemy_ids": ["enemy.shelled_parasite","enemy.fungi_beast"]},
    "encounter.chosen_byrd":{"enemy_ids": ["enemy.chosen","enemy.byrd"]},
    "encounter.chosen_cultist":{"enemy_ids": ["enemy.chosen","enemy.cultist"]},
    "encounter.snake_plant_single": {"enemy_ids": ["enemy.snake_plant"]},
    "encounter.mystic_centurion": {"enemy_ids": ["enemy.centurion", "enemy.mystic"]},

    "encounter.elite.book_of_stabbing": {"enemy_ids": ["enemy.book_of_stabbing"]},
    "encounter.elite.gremlin_leader": {"enemy_ids": ["enemy.gremlin_leader"]},
    "encounter.elite.taskmaster_slavers": {"enemy_ids": ["enemy.red_slaver", "enemy.taskmaster", "enemy.blue_slaver"]},

    "encounter.boss.champ": {"enemy_ids": ["enemy.champ"]},
    "encounter.boss.bronze_automaton": {"enemy_ids": ["enemy.bronze_automaton"]},
    "encounter.boss.collector": {"enemy_ids": ["enemy.collector"]},
}


STARTING_ENCOUNTER_POOL_1_1 =[
    ("encounter.test_dummy", 5),
    ("encounter.cultist_1", 20),
    ("encounter.slimes_ms1", 10),
    ("encounter.slimes_ms2", 10),
    ("encounter.jaw_worm_starting", 20),
    ("encounter.louses_2", 20)
]

STARTING_ENCOUNTER_POOL_1_2 =[
    "encounter.byrd_3",
    "encounter.shelled_parasite_single",
    "encounter.thieves_2",
    "encounter.chosen_single",
    "encounter.spheric_guardian_single"
]

NORMAL_ENCOUNTER_POOL_1_1 = [
    # 6.25% -> 16
    ("encounter.corsoal_single", 4),
    ("encounter.mareanie_single", 4),
    ("encounter.slimes_l1", 32),
    ("encounter.slimes_l2", 32),
    ("encounter.slimes_cluster", 16), 
    ("encounter.louses_3", 32), 
    ("encounter.fungi_beast_2", 32),
    ("encounter.fungi_beast_slime1", 8),
    ("encounter.fungi_beast_slime2", 8),
    ("encounter.fungi_beast_louse", 16),
    ("encounter.red_slaver",16),
    ("encounter.blue_slaver",32),
    ("encounter.thief_looter",32),
    ("encounter.exordium_thugs",24),
    ("encounter.exordium_wildlife",24),
    ("encounter.gremlin_gang", 16),
]
NORMAL_ENCOUNTER_POOL_1_2 = [
    ("encounter.snecko_single", 14),
    ("encounter.cultist_3", 10),
    ("encounter.shelled_parasite_fungi_beast", 10),
    ("encounter.chosen_byrd", 7),
    ("encounter.chosen_cultist", 10),
    ("encounter.sentry_spheric_guardian", 7),
    ("encounter.snake_plant_single", 21),
    ("encounter.mystic_centurion", 21)
]

ELITE_ENCOUNTER_POOL_1_1 = [
    ("encounter.elite.gremlin_nob", 4),
    ("encounter.elite.lagavulin", 4),
    ("encounter.elite.sentries_bab", 4),
    ("encounter.elite.chaos_fragment", 1),
    ("encounter.elite.plastic_bag", 1)
]

ELITE_ENCOUNTER_POOL_1_2 = [
    ("encounter.elite.book_of_stabbing", 4),
    ("encounter.elite.gremlin_leader", 4),
    ("encounter.elite.taskmaster_slavers", 4),
]

BOSS_ENCOUNTER_POOL_1_1 = [
    ("encounter.corsoal_mareanie_pack", 1),
    ("encounter.boss.hexaghost", 4),
    ("encounter.boss.guardian", 4),
    ("encounter.boss.slime_boss", 4),
]
BOSS_ENCOUNTER_POOL_1_2 = [
    ("encounter.boss.champ", 4),
    ("encounter.boss.bronze_automaton", 4),
    ("encounter.boss.collector", 4),
]


ENCOUNTER_DISPLAY_NAMES = {
    "encounter.boss.hexaghost": "六火亡魂",
    "encounter.boss.guardian": "守护者",
    "encounter.boss.slime_boss": "史莱姆老大",
    # 旧测试 Boss，如果你还保留在 BOSS_ENCOUNTER_POOL 里，就也给一个显示名。
    "encounter.corsoal_mareanie_pack": "旧日的珊瑚群……",
    "encounter.boss.champ": "第一勇士",
    "encounter.boss.bronze_automaton": "铜制机械人偶",
    "encounter.boss.collector": "收藏家",
}


def get_encounter_display_name(encounter_id):
    return ENCOUNTER_DISPLAY_NAMES.get(encounter_id, encounter_id)

ENCOUNTER_POOL_BY_NODE_TYPE_AND_SUFFIX = {
    "starting": {
        "1_1": STARTING_ENCOUNTER_POOL_1_1,
        "1_2": STARTING_ENCOUNTER_POOL_1_2,
    },
    "normal_enemy": {
        "1_1": NORMAL_ENCOUNTER_POOL_1_1,
        "1_2": NORMAL_ENCOUNTER_POOL_1_2,
    },
    "elite": {
        "1_1": ELITE_ENCOUNTER_POOL_1_1,
        "1_2": ELITE_ENCOUNTER_POOL_1_2,
    },
    "boss": {
        "1_1": BOSS_ENCOUNTER_POOL_1_1,
        "1_2": BOSS_ENCOUNTER_POOL_1_2,
    },
}


DEFAULT_ENCOUNTER_POOL_SUFFIX_BY_NODE_TYPE = {
    "starting": "1_1",
    "normal_enemy": "1_1",
    "elite": "1_1",
    "boss": "1_1",
}


def get_encounter_pool(node_type, pool_suffix=None):
    """
    根据节点类型和池后缀获取 encounter pool。

    pool_suffix 示例：
    - "1_1"：一层前半 / 基础池
    - "1_2"：一层后半 / 扩展池

    这里保留 pool_suffix=None 的兼容行为，
    所以旧调用 pick_encounter_id_by_node_type("normal_enemy", rng) 不会崩。
    """
    node_type = str(node_type or "normal_enemy")

    if node_type not in ENCOUNTER_POOL_BY_NODE_TYPE_AND_SUFFIX:
        node_type = "normal_enemy"

    suffix_map = ENCOUNTER_POOL_BY_NODE_TYPE_AND_SUFFIX[node_type]

    if pool_suffix is None:
        pool_suffix = DEFAULT_ENCOUNTER_POOL_SUFFIX_BY_NODE_TYPE.get(node_type, "1_1")

    pool_suffix = str(pool_suffix)

    if pool_suffix in suffix_map:
        return suffix_map[pool_suffix]

    if "1_1" in suffix_map:
        return suffix_map["1_1"]

    for pool in suffix_map.values():
        return pool

    raise ValueError("没有可用 encounter pool：node_type={}，pool_suffix={}".format(
        node_type,
        pool_suffix
    ))


def pick_encounter_id_by_node_type(node_type, rng, seen_encounter_ids=None, pool_suffix=None):
    pool = get_encounter_pool(
        node_type=node_type,
        pool_suffix=pool_suffix,
    )

    if node_type == "boss":
        return pick_weighted(filter_encounter_pool(pool), rng)

    return pick_weighted_with_seen_priority(
        filter_encounter_pool(pool),
        rng,
        seen_encounter_ids
    )

def pick_enemy_spec(enemy_spec, rng):
    """
    解析单个敌人槽位。

    支持：
    1. 固定敌人：
       "enemy.cultist"

    2. 等概率随机：
       ["enemy.red_louse", "enemy.green_louse"]

    3. 带权随机：
       [("enemy.red_louse", 1), ("enemy.green_louse", 1)]
    """
    if isinstance(enemy_spec, str):
        return enemy_spec

    if isinstance(enemy_spec, list):
        if not enemy_spec:
            return ""

        # 带权格式：[("enemy.a", 3), ("enemy.b", 1)]
        if isinstance(enemy_spec[0], tuple):
            enemy_ids = [item[0] for item in enemy_spec]
            weights = [item[1] for item in enemy_spec]
            return rng.choices(enemy_ids, weights=weights, k=1)[0]

        # 等概率格式：["enemy.a", "enemy.b"]
        return rng.choice(enemy_spec)
    return str(enemy_spec)

def resolve_encounter_enemy_ids(encounter_id, rng):
    encounter = ENCOUNTER_TABLE.get(encounter_id)
    if encounter is None:
        raise ValueError("遭遇配置不存在：{}".format(encounter_id))

    generator_name = encounter.get("generator")
    if generator_name:
        generator = ENCOUNTER_GENERATORS.get(generator_name)
        if generator is None:
            raise ValueError("未知 encounter generator：{}".format(generator_name))
        return generator(rng)

    enemy_specs = encounter.get("enemy_ids", [])
    return [
        pick_enemy_spec(enemy_spec, rng)
        for enemy_spec in enemy_specs
    ]

GREMLIN_GANG_RANDOM_POOL = [
    "enemy.mad_gremlin",
    "enemy.mad_gremlin",
    "enemy.sneaky_gremlin",
    "enemy.sneaky_gremlin",
    "enemy.fat_gremlin",
    "enemy.fat_gremlin",
    "enemy.gremlin_wizard",
    "enemy.shield_gremlin",
]


def build_random_gremlin_ids(rng, count=4):
    """
    复用地精组的抽取权重。
    pool 中重复出现的敌人等价于更高权重。

    encounter generator 会以 generator(rng) 调用，
    所以 count 需要有默认值；地精群默认生成 4 只。
    """
    count = int(count)
    if count <= 0:
        return []

    if count >= len(GREMLIN_GANG_RANDOM_POOL):
        return list(GREMLIN_GANG_RANDOM_POOL)

    return rng.sample(GREMLIN_GANG_RANDOM_POOL, count)


ENCOUNTER_GENERATORS = {
    "gremlin_gang": build_random_gremlin_ids,
}
