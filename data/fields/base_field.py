# -*- coding: utf-8 -*-
# Field 父类

from dataclasses import dataclass


@dataclass
class FieldTemplate:
    """
    Field：更像临时场地效果，可以多个同时存在。

    例：
    - 本回合所有攻击 +2
    - 下三次抽牌额外抽一张
    - 所有敌人回合开始失去 1 HP
    """

    field_id: str
    name: str
    description: str
    duration: int = 1

    def on_event(self, event_name, context):
        return []

    def tick_turn_end(self):
        self.duration -= 1

    def is_expired(self):
        return self.duration <= 0

    def summary_text(self):
        return "{}({}回合)：{}".format(self.name, self.duration, self.description)