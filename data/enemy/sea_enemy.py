# -*- coding: utf-8 -*-

from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy

class CorsoalEnemy(PatternEnemy):
    def __init__(self):
        intent_cycle = [
            EnemyIntent(kind="block", value=8),
            EnemyIntent(kind="attack", value=8),
            EnemyIntent(kind="status", target="self", status="dexterity", value=1),
        ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.corsoal",
            name="粉色的珊瑚",
            max_hp=32,
            intent_cycle=intent_cycle
        )

class MareanieEnemy(PatternEnemy):
    """
    海星：
    1. 首次行动：荆棘4 / 毒荆棘1，概率 1:1，只触发一次。
    2. 后续循环：毒2+打4 -> 防8 -> 毒2+打4 -> 防8 ...
    3. 攻击/施毒目标：若场上存在存活珊瑚，优先选择珊瑚；否则选择玩家。
    """

    def __init__(self):
        opening_intents = [
            EnemyIntent(kind="status", target="self", status="thorns", value=4),
            EnemyIntent(kind="status", target="self", status="poison_thorns", value=1),
        ]

        poison_and_attack = EnemyIntent(
            kind="multi",
            actions=[
                EnemyIntent(kind="status", target="corsoal_or_player", status="poison", value=2),
                EnemyIntent(kind="attack", target="corsoal_or_player", value=4),
            ]
        )

        intent_cycle = [
            opening_intents,
            poison_and_attack,
            EnemyIntent(kind="block", value=8),
        ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.mareanie",
            name="紫色的棘冠海星",
            max_hp=36,
            intent_cycle=intent_cycle,
            loop_start_index=1
        )

class PlasticBagEnemy(PatternEnemy):
    def __init__(self):
        intent_a = EnemyIntent(
            kind="attack",
            value=2,
            repeat=3
        )
        intent_b = EnemyIntent(
            kind="multi",
            actions=[
                EnemyIntent(kind="block", value=6),
                EnemyIntent(kind="attack", value=6),
            ]
        )
        intent_c = EnemyIntent(
            kind="attack",
            value=12
        )
        intent_d = EnemyIntent(
            kind="status",
            target="self",
            status="strength",
            value=3
        )
        intent_cycle = [
            # 1. 固定 a
            intent_a,
            # 2. 加权随机：10% a，30% b，30% c，30% d
            [
                (10, intent_a),
                (30, intent_b),
                (30, intent_c),
                (30, intent_d),
            ],
        ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.plastic_bag",
            name="飞翔塑料袋",
            max_hp=80,
            intent_cycle=intent_cycle
        )

