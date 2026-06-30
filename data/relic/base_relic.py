# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class RelicTemplate:
    """
    遗物模板。

    目前只做占位。
    后面遗物可以通过 on_event 接入 battle_start、turn_start、card_played 等事件。
    """

    relic_id: str
    name: str
    description: str
    story: str
    quantity:str  # starting, common, uncommon, rare, event, myth, shop

    # 空字符串表示通用遗物。
    # 非空表示角色专属遗物。
    owner_character_id: str = ""
    
    # 是否允许重复获得
    allow_duplicate: bool = False

    def on_event(self, event_name, context):
        """
        暂时默认无效果。
        event_name: 事件名，例如 battle_start / turn_start / card_played
        context: 战斗上下文，后面再设计
        """
        return []
    
    def on_obtained(self, run_state):
        """
        获得遗物时触发。

        当前默认无效果。
        后续可以用于：
        - 获得多个造物原型后触发隐藏事件
        - 获得遗物时修改金币 / HP / 卡组
        - 获得遗物时写入 run_state 的特殊标记
        """
        return []
    
    def summary_text(self):
        from game.display_names import format_relic_display_name

        return "{}：{}".format(format_relic_display_name(self), self.description)
