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
    ("encounter.corsoal_single", 4),
    ("encounter.mareanie_single", 4),
    ("encounter.slimes_l1", 32),
    ("encounter.slimes_l2", 32),
    ("encounter.slimes_cluster", 16), 
    ("encounter.louses_3", 32), 
    ("encounter.fungi_beast_2", 32),
    ("encounter.fungi_beast_slime1", 8),
    ("encounter.fungi_beast_slime2", 8),
    ("encounter.fungi_beast_louse", 16)
]

ELITE_ENCOUNTER_POOL = [
    ("encounter.elite.chaos_fragment", 5),
    ("encounter.elite.plastic_bag", 5)
]

BOSS_ENCOUNTER_POOL = [
    ("encounter.corsoal_mareanie_pack", 5),
]


def pick_encounter_id_by_node_type(node_type, rng):
    if node_type == "starting":
        return pick_weighted(STARTING_ENCOUNTER_POOL, rng)
    if node_type == "elite":
        return pick_weighted(ELITE_ENCOUNTER_POOL, rng)
    if node_type == "boss":
        return pick_weighted(BOSS_ENCOUNTER_POOL, rng)

    return pick_weighted(NORMAL_ENCOUNTER_POOL, rng)