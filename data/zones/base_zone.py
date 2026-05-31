# -*- coding: utf-8 -*-

from dataclasses import dataclass


@dataclass
class ZoneTemplate:
    """
    Zone：更像当前区域环境，一般同时只有一个。

    例：
    - 火山区域：所有燃烧相关牌增强
    - 雨地区域：雷电、冰冻相关效果变化
    - 某个整活区域：敌人死亡时追加特殊文本
    """

    zone_id: str
    name: str
    description: str

    def on_event(self, event_name, context):
        return []

    def summary_text(self):
        return "{}：{}".format(self.name, self.description)

    def __str__(self):
        return self.summary_text()