# -*- coding: utf-8 -*-

import random

from data.enemy.base_enemy import Enemy, EnemyIntent, EnemyActionResult
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


class MareanieEnemy(Enemy):
    """
    海星：
    1. 首次行动：荆棘4 / 毒荆棘1，概率 1:1，只触发一次。
    2. 后续循环：毒4+打4 -> 防8 -> 毒4+打4 -> 防8 ...
    3. 攻击/施毒目标：若场上存在存活珊瑚，优先选择珊瑚；否则选择玩家。
    """

    def __init__(self):
        Enemy.__init__(
            self,
            enemy_id="enemy.mareanie",
            name="紫色的棘冠海星",
            max_hp=36
        )

        self._intent_index = 0
        self._locked_opening_intent = None

    def _get_opening_intent(self):
        if self._locked_opening_intent is None:
            self._locked_opening_intent = random.choice([
                EnemyIntent(kind="status", target="self", status="thorns", value=4),
                EnemyIntent(kind="status", target="self", status="poison_thorns", value=1),
            ])
        return self._locked_opening_intent

    def get_current_intent(self):
        if self._intent_index == 0:
            return self._get_opening_intent()

        if self._intent_index == 1:
            return EnemyIntent(kind="attack", value=2, target="corsoal_or_player")

        return EnemyIntent(kind="block", value=8)

    def get_intent_text(self):
        if self._intent_index == 0:
            return self._get_opening_intent().to_text()
        if self._intent_index == 1:
            return "优先对珊瑚施加 2 层中毒，并攻击 4"
        return "获得 8 点格挡"

    def advance_intent(self):
        if self._intent_index == 0:
            self._intent_index = 1
            return

        if self._intent_index == 1:
            self._intent_index = 2
            return

        self._intent_index = 1

    def act(self):
        logs = []

        if self._intent_index == 0:
            intent = self._get_opening_intent()
            action = {
                "op": "enemy_gain_status",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "target": "self",
                "status": intent.status,
                "amount": intent.value
            }
            logs.append("{} 准备使用状态效果：{}。".format(
                self.name,
                intent.to_text()
            ))
            self.advance_intent()
            return EnemyActionResult(action=action, logs=logs)

        if self._intent_index == 1:
            action = {
                "op": "enemy_multi_action",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "actions": [
                    {
                        "op": "enemy_gain_status",
                        "source_enemy_id": self.enemy_id,
                        "source_enemy_name": self.name,
                        "target": "corsoal_or_player",
                        "status": "poison",
                        "amount": 2
                    },
                    {
                        "op": "enemy_attack",
                        "source_enemy_id": self.enemy_id,
                        "source_enemy_name": self.name,
                        "target": "corsoal_or_player",
                        "damage": 4
                    },
                ]
            }
            logs.append("{} 准备优先对珊瑚施加 2 层中毒，并造成 4 点伤害。".format(self.name))
            self.advance_intent()
            return EnemyActionResult(action=action, logs=logs)

        action = {
            "op": "enemy_gain_block",
            "source_enemy_id": self.enemy_id,
            "source_enemy_name": self.name,
            "block": 8
        }
        logs.append("{} 准备获得 8 点格挡。".format(self.name))
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)