# -*- coding: utf-8 -*-

from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy


class TestDummyEnemy(PatternEnemy):
    def __init__(self):
        intent_cycle = [
            EnemyIntent(kind="attack", value=4),
            EnemyIntent(kind="block", value=4)
        ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.test_dummy",
            name="测试假人",
            max_hp=20, #300
            intent_cycle=intent_cycle
        )