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