# -*- coding: utf-8 -*-

ENCOUNTER_TABLE = {
    "encounter.test_dummy": {
        "enemy_ids": ["enemy.test_dummy"]
    },

    "encounter.elite.chaos_fragment": {
        "enemy_ids": ["enemy.chaos_fragment"]
    },

    "encounter.corsoal_single": {
        "enemy_ids": ["enemy.corsoal"]
    },

    "encounter.mareanie_single": {
        "enemy_ids": ["enemy.mareanie"]
    },

    "encounter.corsoal_mareanie_pack": {
        # 顺序故意让两个珊瑚先行动：
        # 它们当回合获得的格挡可以吃到海星的优先攻击。
        "enemy_ids": ["enemy.corsoal", "enemy.corsoal", "enemy.mareanie"]
    },

    # Boss 先占位
    "encounter.boss_dummy": {
        "enemy_ids": ["enemy.test_dummy"]
    },
}


NORMAL_ENCOUNTER_POOL = [
    "encounter.test_dummy",
    "encounter.corsoal_single",
    "encounter.mareanie_single",
]


ELITE_ENCOUNTER_POOL = [
    "encounter.elite.chaos_fragment",
    "encounter.corsoal_mareanie_pack"
]


BOSS_ENCOUNTER_POOL = [
    "encounter.corsoal_mareanie_pack",
]


def pick_encounter_id_by_node_type(node_type, rng):
    if node_type == "elite":
        return rng.choice(ELITE_ENCOUNTER_POOL)

    if node_type == "boss":
        return rng.choice(BOSS_ENCOUNTER_POOL)

    return rng.choice(NORMAL_ENCOUNTER_POOL)