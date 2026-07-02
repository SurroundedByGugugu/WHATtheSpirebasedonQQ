# -*- coding: utf-8 -*-

import random

from data.enemy.base_enemy import Enemy, EnemyActionResult


class PatternEnemy(Enemy):
    """
    固定 / 半随机意图循环敌人。

    支持：
    1. EnemyIntent(...) 固定意图
    2. [EnemyIntent(...), EnemyIntent(...)] 等概率随机意图槽
    3. [(10, EnemyIntent(...)), (30, EnemyIntent(...))] 加权随机意图槽
    4. EnemyIntent(kind="multi", actions=[...]) 复合行动
    5. EnemyIntent(kind="attack", repeat=3) 多段攻击
    """

    def __init__(self, enemy_id, name, max_hp, intent_cycle, loop_start_index=0):
        Enemy.__init__(self, enemy_id, name, max_hp)

        self._intent_index = 0
        self._intent_cycle = intent_cycle
        self._locked_intent = None
        self._loop_start_index = int(loop_start_index)

        if not self._intent_cycle:
            raise ValueError("intent_cycle 不能为空")
        if self._loop_start_index < 0 or self._loop_start_index >= len(self._intent_cycle):
            raise ValueError("loop_start_index 超出 intent_cycle 范围")

    def _is_weighted_choice_list(self, slot):
        if not isinstance(slot, (list, tuple)):
            return False
        if not slot:
            return False

        for item in slot:
            if not isinstance(item, (list, tuple)):
                return False
            if len(item) != 2:
                return False
            if not isinstance(item[0], (int, float)):
                return False

        return True

    def _resolve_intent_slot(self, slot):
        """
        如果当前槽位是列表/元组，则随机抽取其中一个意图。
        为了保证显示意图和实际行动一致，抽到的意图会被锁定到本回合。
        """
        if self._is_weighted_choice_list(slot):
            choices = [item[1] for item in slot]
            weights = [item[0] for item in slot]
            return random.choices(choices, weights=weights, k=1)[0]

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
            self._intent_index = self._loop_start_index
        self._locked_intent = None

    def _intent_to_action(self, intent):
        if intent.kind == "attack":
            one_action = {
                "op": "enemy_attack",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "damage": intent.value,
                "target": intent.target,
                "attack_type": intent.attack_type,
                "attack_element": intent.attack_element,
                "message": intent.message,
                "heal_unblocked": bool(getattr(intent, "heal_unblocked", False)),
            }

            repeat = int(getattr(intent, "repeat", 1))
            if repeat <= 1:
                return one_action

            return {
                "op": "enemy_multi_action",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "actions": [
                    dict(one_action)
                    for _ in range(repeat)
                ]
            }

        if intent.kind == "block":
            return {
                "op": "enemy_gain_block",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "block": intent.value,
                "attack_type": intent.attack_type,
                "attack_element": intent.attack_element,
                "message": intent.message,
            }
        
        if intent.kind == "heal_all_allies":
            return {
                "op": "enemy_heal_all_allies",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "heal": intent.value,
                "message": intent.message,
            }

        if intent.kind == "status_all_allies":
            return {
                "op": "enemy_status_all_allies",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "status": intent.status,
                "amount": intent.value,
                "message": intent.message,
            }

        if intent.kind == "block_mystic_or_self":
            return {
                "op": "enemy_block_mystic_or_self",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "block": intent.value,
                "message": intent.message,
            }
        
        if intent.kind == "summon_gremlins":
            return {
                "op": "enemy_summon_gremlins",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "count": int(intent.count),
                "message": intent.message,
            }

        if intent.kind == "gremlin_leader_rally":
            return {
                "op": "enemy_gremlin_leader_rally",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "strength": int(intent.value),
                "minion_block": int(intent.count),
                "message": intent.message,
            }
        if intent.kind == "summon_fixed_enemies":
            return {
                "op": "enemy_summon_fixed_enemies",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "enemy_ids": list(getattr(intent, "actions", []) or []),
                "count": int(getattr(intent, "count", 0) or 0),
                "message": intent.message,
            }

        if intent.kind == "champ_burst":
            return {
                "op": "enemy_champ_burst",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "message": intent.message,
            }

        if intent.kind == "bronze_orb_capture_card":
            return {
                "op": "enemy_bronze_orb_capture_card",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "message": intent.message,
            }

        if intent.kind == "block_bronze_automaton":
            return {
                "op": "enemy_block_bronze_automaton",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "block": int(intent.value),
                "message": intent.message,
            }

        if intent.kind == "collector_buff":
            return {
                "op": "enemy_collector_buff",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "strength": 3,
                "block": 15,
                "message": intent.message,
            }

        if intent.kind == "collector_summon_torch_heads":
            return {
                "op": "enemy_collector_summon_torch_heads",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "target_count": 2,
                "message": intent.message,
            }
        
        if intent.kind == "split":
            return {
                "op": "enemy_split",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "message": intent.message,
            }

        if intent.kind == "status":
            return {
                "op": "enemy_gain_status",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "target": intent.target,
                "status": intent.status,
                "amount": intent.value,
                "attack_type": intent.attack_type,
                "attack_element": intent.attack_element,
                "message": intent.message,
            }

        if intent.kind == "multi":
            return {
                "op": "enemy_multi_action",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "actions": [
                    self._intent_to_action(child)
                    for child in getattr(intent, "actions", [])
                ],
                "message": intent.message,
            }
        
        if intent.kind in ("add_card_to_discard", "add_card_to_draw", "add_card_to_hand"):
            op_map = {
                "add_card_to_discard": "enemy_add_card_to_discard",
                "add_card_to_draw": "enemy_add_card_to_draw",
                "add_card_to_hand": "enemy_add_card_to_hand",
            }

            return {
                "op": op_map[intent.kind],
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "card_id": intent.card_id,
                "count": intent.count,
                "message": intent.message,
            }
        if intent.kind == "steal_gold":
            return {
                "op": "enemy_steal_gold",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "amount": intent.value,
                "message": intent.message,
            }

        if intent.kind == "escape":
            return {
                "op": "enemy_escape",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "message": intent.message,
            }
        
        if intent.kind == "wait":
            return {
                "op": "enemy_wait",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "message": intent.message,
            }
        
        if intent.kind == "smart_ally_block_or_attack":
            return {
                "op": "enemy_smart_ally_block_or_attack",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "block": intent.value,
                "damage": intent.count,
                "message": intent.message,
            }
        
        return {
            "op": "enemy_unknown_action",
            "source_enemy_id": self.enemy_id,
            "source_enemy_name": self.name,
            "message": intent.message,
        }

    def act(self):
        intent = self.get_current_intent()
        logs = []

        logs.append("{} 准备执行：{}。".format(
            self.name,
            intent.to_text()
        ))

        action = self._intent_to_action(intent)
        self.advance_intent()

        return EnemyActionResult(action=action, logs=logs)