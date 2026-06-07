# -*- coding: utf-8 -*-

from data.enemy.chaos_fragment_enemy import ChaosFragmentEnemy
from data.enemy.test_dummy_enemy import TestDummyEnemy
from data.enemy.sea_enemy import CorsoalEnemy, MareanieEnemy, PlasticBagEnemy

ENEMY_REGISTRY = {
    "enemy.test_dummy": TestDummyEnemy,
    "enemy.chaos_fragment":ChaosFragmentEnemy,
    "enemy.corsoal": CorsoalEnemy,
    "enemy.mareanie": MareanieEnemy,
    "enemy.plastic_bag": PlasticBagEnemy,
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