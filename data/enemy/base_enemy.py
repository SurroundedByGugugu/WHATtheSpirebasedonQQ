# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List, Dict, Any
from game.status.status_container import StatusContainer
from game.status.status_display import get_status_display_text


@dataclass
class EnemyIntent:
    kind: str
    value: int = 0
    status: str = ""
    target: str = "player"
    def to_text(self):
        if self.kind == "attack":
            return "攻击 {}".format(self.value)
        if self.kind == "block":
            return "获得 {} 点格挡".format(self.value)
        if self.kind == "status":
            status_name_map = {
                "vulnerable": "易伤",
                "weak": "虚弱",
                "frail": "脆弱",
                "thorns": "荆棘",
                "strength": "力量",
                "dexterity": "敏捷",
                "poison": "中毒",
                "poison_thorns": "毒荆棘",
            }
            status_name = status_name_map.get(self.status, self.status)
            if self.target == "self":
                return "自身获得 {} 点{}".format(self.value, status_name)
            return "给予玩家 {} 点{}".format(self.value, status_name)
        return "未知意图"


@dataclass
class EnemyActionResult:
    action: Dict[str, Any]
    logs: List[str]


class Enemy(object):
    """
    敌人父类。

    约定：
    1. 敌人只管理自己的 hp、block、intent。
    2. 敌人 attack 时不直接扣玩家血，只返回 action。
    3. 具体伤害结算交给 engine.py。
    """

    def __init__(self, enemy_id, name, max_hp):
        self.enemy_id = enemy_id
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.block = 0
        self.statuses = StatusContainer()

    def is_alive(self):
        return self.hp > 0
    
    def clear_block(self):
        old_block = self.block
        self.block = 0
        return old_block

    def get_current_intent(self):
        raise NotImplementedError

    def get_intent_text(self):
        return self.get_current_intent().to_text()

    def act(self):
        raise NotImplementedError

    def take_damage(self, damage):
        if damage <= 0:
            return "{} 没有受到伤害。".format(self.name)

        blocked = min(self.block, damage)
        self.block -= blocked

        real_damage = damage - blocked
        self.hp -= real_damage

        if self.hp < 0:
            self.hp = 0

        return "{} 受到 {} 点伤害，剩余 HP：{}/{}，格挡：{}。".format(
            self.name,
            real_damage,
            self.hp,
            self.max_hp,
            self.block
        )

    def status_text(self):
        return "{} HP：{}/{}，格挡：{}，意图：{}，状态：{}".format(
            self.name,
            self.hp,
            self.max_hp,
            self.block,
            self.get_intent_text(),
            get_status_display_text(self.statuses)
        )
    
    def get_status_value(self, key):
        return self.statuses.get(key)

    def gain_status(self, key, amount):
        return self.statuses.add(key, amount)