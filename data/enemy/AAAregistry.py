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
)

ENEMY_REGISTRY = {
    "enemy.test_dummy": TestDummyEnemy,
    "enemy.chaos_fragment":ChaosFragmentEnemy,
    "enemy.corsoal": CorsoalEnemy,
    "enemy.mareanie": MareanieEnemy,
    "enemy.plastic_bag": PlasticBagEnemy,
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
    "enemy.gremlin_nob": create_gremlin_nob,
    "enemy.lagavulin": create_lagavulin,
    "enemy.lagavulin_awake": create_lagavulin_awake,
    "enemy.sentry_a": create_sentry_a,
    "enemy.sentry_b": create_sentry_b,
    "enemy.hexaghost": create_hexaghost,
    "enemy.guardian": create_guardian,
    "enemy.slime_boss": create_slime_boss,
    
    "enemy.byrd": create_byrd,
    "enemy.snecko": create_snecko,
    "enemy.shelled_parasite":create_shelled_parasite,
    "enemy.spheric_guardian": create_spheric_guardian,
    "enemy.chosen":create_chosen,
    "enemy.snake_plant": create_snake_plant,
    "enemy.mystic": create_mystic,
    "enemy.centurion": create_centurion,
}


def create_enemy(enemy_id):
    enemy_class = ENEMY_REGISTRY.get(enemy_id)

    if enemy_class is None:
        raise ValueError("未知敌人 ID：{}".format(enemy_id))

    return enemy_class()


'''以后你新增敌人，只要加：

from enemy.xxx_enemy import XxxEnemy
ENEMY_REGISTRY = {
    "enemy.test_dummy": TestDummyEnemy,
    "enemy.xxx": XxxEnemy
}'''