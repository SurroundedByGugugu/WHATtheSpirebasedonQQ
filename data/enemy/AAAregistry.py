# -*- coding: utf-8 -*-

from data.enemy.chaos_fragment_enemy import ChaosFragmentEnemy
from data.enemy.test_dummy_enemy import TestDummyEnemy
from data.enemy.sea_enemy import CorsoalEnemy, MareanieEnemy, PlasticBagEnemy
from data.enemy.enemy_origin_1_1 import (
    create_cultist,
    create_spike_slime_large,
    create_spike_slime_middle,
    create_spike_slime_small,
    create_acid_slime_large,
    create_acid_slime_middle,
    create_acid_slime_small,
    create_jaw_worm_g1,
    create_jaw_worm_g2,
    create_green_louse,
    create_red_louse,
    create_random_louse,
    create_fungi_beast,
    create_red_slaver,
    create_blue_slaver,
    create_looter,
    create_mugger,
    create_fat_gremlin,
    create_mad_gremlin,
    create_shield_gremlin,
    create_sneaky_gremlin,
    create_gremlin_wizard,
    create_gremlin_nob,
    create_lagavulin,
    create_lagavulin_awake,
    create_sentry_a,
    create_sentry_b,
    create_hexaghost,
    create_guardian,
    create_slime_boss,
)
from data.enemy.enemy_origin_1_2 import (
    create_byrd,
    create_snecko,
    create_shelled_parasite,
    create_spheric_guardian,
    create_chosen,
    create_snake_plant,
    create_mystic,
    create_centurion,

    create_pointy,
    create_romeo,
    create_bear,

    create_book_of_stabbing,
    create_gremlin_leader,
    create_taskmaster,

    create_champ,
    create_bronze_automaton,
    create_bronze_orb,
    create_collector,
    create_torch_head,

)

from data.enemy.enemy_origin_1_3 import (
    create_orb_walker,
    create_the_maw,
    create_darkling_left,
    create_darkling_middle,
    create_darkling_right,
    create_transient,
    create_writhing_mass,
    create_spire_growth,
    create_spiker,
    create_exploder,
    create_repulsor,
    create_giant_head,
    create_reptomancer,
    create_dagger,
    create_nemesis,
    create_deca,
    create_donu,
    create_awakened_one,
    create_time_eater,
)

ENEMY_REGISTRY = {
    "enemy.test_dummy": TestDummyEnemy,
    "enemy.chaos_fragment":ChaosFragmentEnemy,
    "enemy.corsoal": CorsoalEnemy,
    "enemy.mareanie": MareanieEnemy,
    "enemy.plastic_bag": PlasticBagEnemy,
    #_1_1_common
    "enemy.cultist":create_cultist,
    "enemy.spike_slime_large": create_spike_slime_large,
    "enemy.spike_slime_middle": create_spike_slime_middle,
    "enemy.spike_slime_small": create_spike_slime_small,
    "enemy.acid_slime_large": create_acid_slime_large,
    "enemy.acid_slime_middle": create_acid_slime_middle,
    "enemy.acid_slime_small": create_acid_slime_small,
    "enemy.jaw_worm_g1": create_jaw_worm_g1,
    "enemy.jaw_worm_g2": create_jaw_worm_g2,
    "enemy.red_louse": create_red_louse,
    "enemy.green_louse": create_green_louse,
    "enemy.random_louse": create_random_louse,
    "enemy.fungi_beast": create_fungi_beast,
    "enemy.red_slaver": create_red_slaver,
    "enemy.blue_slaver": create_blue_slaver,
    "enemy.looter": create_looter,
    "enemy.mugger": create_mugger,
    "enemy.fat_gremlin": create_fat_gremlin,
    "enemy.mad_gremlin": create_mad_gremlin,
    "enemy.shield_gremlin": create_shield_gremlin,
    "enemy.sneaky_gremlin": create_sneaky_gremlin,
    "enemy.gremlin_wizard": create_gremlin_wizard,
    #_1_1_elite
    "enemy.gremlin_nob": create_gremlin_nob,
    "enemy.lagavulin": create_lagavulin,
    "enemy.lagavulin_awake": create_lagavulin_awake,
    "enemy.sentry_a": create_sentry_a,
    "enemy.sentry_b": create_sentry_b,
    #_1_1_boss
    "enemy.hexaghost": create_hexaghost,
    "enemy.guardian": create_guardian,
    "enemy.slime_boss": create_slime_boss,

    #_1_2_common
    "enemy.byrd": create_byrd,
    "enemy.snecko": create_snecko,
    "enemy.shelled_parasite":create_shelled_parasite,
    "enemy.spheric_guardian": create_spheric_guardian,
    "enemy.chosen":create_chosen,
    "enemy.snake_plant": create_snake_plant,
    "enemy.mystic": create_mystic,
    "enemy.centurion": create_centurion,
    #_1_2_event    
    "enemy.pointy": create_pointy,
    "enemy.romeo": create_romeo,
    "enemy.bear": create_bear,
    #_1_2_elite
    "enemy.book_of_stabbing": create_book_of_stabbing,
    "enemy.gremlin_leader": create_gremlin_leader,
    "enemy.taskmaster": create_taskmaster,
    #_1_2_boss
    "enemy.champ": create_champ,
    "enemy.bronze_automaton": create_bronze_automaton,
    "enemy.bronze_orb": create_bronze_orb,
    "enemy.collector": create_collector,
    "enemy.torch_head": create_torch_head,
    
    #_1_3_common
    "enemy.orb_walker": create_orb_walker,
    "enemy.the_maw": create_the_maw,
    "enemy.darkling_left": create_darkling_left,
    "enemy.darkling_middle": create_darkling_middle,
    "enemy.darkling_right": create_darkling_right,
    "enemy.transient": create_transient,
    "enemy.writhing_mass": create_writhing_mass,
    "enemy.spire_growth": create_spire_growth,
    "enemy.spiker": create_spiker,
    "enemy.exploder": create_exploder,
    "enemy.repulsor": create_repulsor,
    #_1_3_elite
    "enemy.giant_head": create_giant_head,
    "enemy.reptomancer": create_reptomancer,
    "enemy.dagger": create_dagger,
    "enemy.nemesis": create_nemesis,
    #_1_3_boss
    "enemy.deca": create_deca,
    "enemy.donu": create_donu,
    "enemy.awakened_one": create_awakened_one,
    "enemy.time_eater": create_time_eater,
}


def create_enemy(enemy_id):
    enemy_class = ENEMY_REGISTRY.get(enemy_id)

    if enemy_class is None:
        raise ValueError("未知敌人 ID：{}".format(enemy_id))

    return enemy_class()

