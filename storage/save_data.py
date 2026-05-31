# -*- coding: utf-8 -*-
# 存档数据结构
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class SaveData:
    user_id: str
    session_id: str
    data: Dict[str, Any] = field(default_factory=dict)