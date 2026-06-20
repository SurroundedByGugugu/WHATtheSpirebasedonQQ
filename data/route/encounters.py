# -*- coding: utf-8 -*-

def pick_weighted(pool, rng):
    encounter_ids = [item[0] for item in pool]
    weights = [item[1] for item in pool]
    return rng.choices(encounter_ids, weights=weights, k=1)[0]

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
}


STARTING_ENCOUNTER_POOL =[
    ("encounter.test_dummy", 5),
    ("encounter.cultist_1", 20),
    ("encounter.slimes_ms1", 10),
    ("encounter.slimes_ms2", 10),
    ("encounter.jaw_worm_starting", 20),
    ("encounter.louses_2", 20)
]

NORMAL_ENCOUNTER_POOL = [
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

ELITE_ENCOUNTER_POOL = [
    ("encounter.elite.gremlin_nob", 4),
    ("encounter.elite.lagavulin", 4),
    ("encounter.elite.sentries_bab", 4),
    ("encounter.elite.chaos_fragment", 1),
    ("encounter.elite.plastic_bag", 1)
]

BOSS_ENCOUNTER_POOL = [
    ("encounter.corsoal_mareanie_pack", 1),
    ("encounter.boss.hexaghost", 4),
    ("encounter.boss.guardian", 4),
    ("encounter.boss.slime_boss", 4),
]
ENCOUNTER_DISPLAY_NAMES = {
    "encounter.boss.hexaghost": "六火亡魂",
    "encounter.boss.guardian": "守护者",
    "encounter.boss.slime_boss": "史莱姆老大",
    # 旧测试 Boss，如果你还保留在 BOSS_ENCOUNTER_POOL 里，就也给一个显示名。
    "encounter.corsoal_mareanie_pack": "旧日的珊瑚群……",
}


def get_encounter_display_name(encounter_id):
    return ENCOUNTER_DISPLAY_NAMES.get(encounter_id, encounter_id)

def pick_encounter_id_by_node_type(node_type, rng):
    if node_type == "starting":
        return pick_weighted(STARTING_ENCOUNTER_POOL, rng)
    if node_type == "elite":
        return pick_weighted(ELITE_ENCOUNTER_POOL, rng)
    if node_type == "boss":
        return pick_weighted(BOSS_ENCOUNTER_POOL, rng)

    return pick_weighted(NORMAL_ENCOUNTER_POOL, rng)

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

def build_gremlin_gang(rng):
    pool = [
        "enemy.mad_gremlin",
        "enemy.mad_gremlin",
        "enemy.sneaky_gremlin",
        "enemy.sneaky_gremlin",
        "enemy.fat_gremlin",
        "enemy.fat_gremlin",
        "enemy.gremlin_wizard",
        "enemy.shield_gremlin",
    ]
    return rng.sample(pool, 4)

ENCOUNTER_GENERATORS = {
    "gremlin_gang": build_gremlin_gang,
}