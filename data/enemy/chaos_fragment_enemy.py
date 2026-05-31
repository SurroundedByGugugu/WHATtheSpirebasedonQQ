# -*- coding: utf-8 -*-

from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy


class ChaosFragmentEnemy(PatternEnemy):
    def __init__(self):
        intent_cycle = [
            # 第 1 个槽位：固定攻击
            EnemyIntent(kind="attack", value=7),
            # 第 2 个槽位：从三个动作里随机一个
            [
                EnemyIntent(kind="attack", value=11),
                EnemyIntent(kind="block", value=10),
                EnemyIntent(kind="status", target="player", status="weak", value=2),
            ],
            # 第 3 个槽位：从三个动作里随机一个
            [
                EnemyIntent(kind="status", target="player", status="vulnerable", value=2),
                EnemyIntent(kind="status", target="player", status="frail", value=2),
                EnemyIntent(kind="status", target="self", status="thorns", value=3),
            ],
        ]
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.chaos_fragment",
            name="混沌的碎片",
            max_hp=55,
            intent_cycle=intent_cycle
        )