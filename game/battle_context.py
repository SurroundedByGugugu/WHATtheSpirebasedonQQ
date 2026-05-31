# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BattleContext:
    """
    战斗事件上下文。

    当前用途：
    - 遗物触发
    - 回合开始触发
    - 出牌后触发

    后续可继续给状态、Field、Zone、敌人被动复用。
    """

    game_state: Any

    # 当前主要行动者，通常是玩家
    player: Any = None

    # 当前打出的牌，可为空
    card: Any = None

    # 后续扩展用
    source: Any = None
    target: Any = None

    # 临时扩展数据
    extra: Dict[str, Any] = field(default_factory=dict)

    # 事件过程中追加的日志
    logs: List[str] = field(default_factory=list)

    def add_log(self, text):
        if text:
            self.logs.append(text)