# -*- coding: utf-8 -*-
# buff/debuff 父类
# StatusDef 数据结构

from dataclasses import dataclass


@dataclass(frozen=True)
class StatusDef:
    """
    状态定义。

    注意：
    这里只描述状态本身，不保存运行时层数/回合数。
    具体数值由 game/status/status_container.py 管理。
    """

    key: str
    name: str
    description: str = ""

    category: str = "neutral"      # buff / debuff / neutral / special
    display_mode: str = "value"    # value / turns / stack / flag
    order: int = 100

    can_be_negative: bool = False
    remove_at_zero: bool = True

    # 预留：后续状态自然衰减用
    decay_timing: str = "none"     # none / turn_start / turn_end
    decay_amount: int = 0