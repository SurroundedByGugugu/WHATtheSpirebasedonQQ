# -*- coding: utf-8 -*-

import random

from data.enemy.base_enemy import Enemy, EnemyActionResult


class PatternEnemy(Enemy):
    """
    固定 / 半随机意图循环敌人。

    支持：
    1. EnemyIntent(...) 固定意图
    2. [EnemyIntent(...), EnemyIntent(...)] 随机意图槽
    """

    def __init__(self, enemy_id, name, max_hp, intent_cycle):
        Enemy.__init__(self, enemy_id, name, max_hp)

        self._intent_index = 0
        self._intent_cycle = intent_cycle
        self._locked_intent = None

        if not self._intent_cycle:
            raise ValueError("intent_cycle 不能为空")

    def _resolve_intent_slot(self, slot):
        """
        如果当前槽位是列表/元组，则随机抽取其中一个意图。
        为了保证显示意图和实际行动一致，抽到的意图会被锁定到本回合。
        """
        if isinstance(slot, (list, tuple)):
            if not slot:
                raise ValueError("随机意图槽不能为空")
            return random.choice(slot)

        return slot

    def get_current_intent(self):
        if self._locked_intent is None:
            slot = self._intent_cycle[self._intent_index]
            self._locked_intent = self._resolve_intent_slot(slot)

        return self._locked_intent

    def advance_intent(self):
        self._intent_index += 1

        if self._intent_index >= len(self._intent_cycle):
            self._intent_index = 0

        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = []

        if intent.kind == "attack":
            action = {
                "op": "enemy_attack",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "damage": intent.value
            }
            logs.append("{} 准备造成 {} 点伤害。".format(self.name, intent.value))

        elif intent.kind == "block":
            action = {
                "op": "enemy_gain_block",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "block": intent.value
            }
            logs.append("{} 准备获得 {} 点格挡。".format(self.name, intent.value))

        elif intent.kind == "status":
            action = {
                "op": "enemy_gain_status",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "target": intent.target,
                "status": intent.status,
                "amount": intent.value
            }
            logs.append("{} 准备使用状态效果：{}。".format(
                self.name,
                intent.to_text()
            ))

        else:
            action = {
                "op": "enemy_unknown_action",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name
            }
            logs.append("{} 执行了未知行动。".format(self.name))

        self.advance_intent()

        return EnemyActionResult(action=action, logs=logs)