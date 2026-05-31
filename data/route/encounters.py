# -*- coding: utf-8 -*-

ENCOUNTER_TABLE = {
    "encounter.test_dummy": {
        "enemy_ids": ["enemy.test_dummy"]
    },

    "encounter.elite.chaos_fragment": {
        "enemy_ids": ["enemy.chaos_fragment"]
    },

    # Boss 先占位
    "encounter.boss_dummy": {
        "enemy_ids": ["enemy.test_dummy"]
    },
}


NORMAL_ENCOUNTER_POOL = [
    "encounter.test_dummy",
]


ELITE_ENCOUNTER_POOL = [
    "encounter.elite.chaos_fragment",
]


BOSS_ENCOUNTER_POOL = [
    "encounter.boss_dummy",
]


def pick_encounter_id_by_node_type(node_type, rng):
    if node_type == "elite":
        return rng.choice(ELITE_ENCOUNTER_POOL)

    if node_type == "boss":
        return rng.choice(BOSS_ENCOUNTER_POOL)

    return rng.choice(NORMAL_ENCOUNTER_POOL)