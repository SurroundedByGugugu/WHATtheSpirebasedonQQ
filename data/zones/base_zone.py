# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass
class ZoneTemplate:
    """
    Zone：更像当前区域环境，一般同时只有一个。

    当前规则：
    - 普通 Zone 持续到战斗结束或被覆盖。
    - 再次展开同属性普通 Zone，会升级为极 Zone。
    - 极 Zone 持续若干回合，期间不可覆盖。
    """

    zone_id: str
    name: str
    description: str

    # 当前先做属性 Zone。空字符串表示非属性 Zone / 测试 Zone。
    element: str = ""

    # 极 Zone：持续回合内不可覆盖。
    is_extreme: bool = False
    duration: int = 0

    # damage_multiplier: float = 1.0

    # 旧字段名：同属性伤害倍率。
    # 现在保留兼容，同时作为同属性牌 deal_damage 的基础 Zone 乘区。
    damage_multiplier: float = 1.0

    # 同属性牌基础数值乘区。
    # 用于卡牌 deal_damage 和 gain_block，普通 Zone 默认 1.1，极 Zone 默认 1.3。
    base_amount_multiplier: float = 1.0


    def on_event(self, event_name, context):
        return []

    def tick_turn_end(self):
        if self.is_extreme and self.duration > 0:
            self.duration -= 1

    def is_expired(self):
        return self.is_extreme and self.duration <= 0

    def prompt_text(self):
        return self.summary_text()

    def summary_text(self):
        if self.is_extreme:
            return "{}({}回合)：{}".format(
                self.name,
                self.duration,
                self.description
            )
        return "{}：{}".format(self.name, self.description)

    def __str__(self):
        return self.summary_text()