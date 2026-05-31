# -*- coding: utf-8 -*-
# 从 data/status 读取定义，供 game 层使用

from dataclasses import dataclass
# 导入后触发通用状态注册
import data.status.common_statuses  # noqa: F401

from data.status.AAAregistry import (
    get_status_def,
    get_status_name,
    iter_status_defs,
    has_status_def,
)

@dataclass(frozen=True)
class StatusDef:
    key: str
    name: str
    category: str = "neutral"   # buff / debuff / special / field / zone
    display_mode: str = "value" # value / turns / stack / flag
    order: int = 100


STATUS_DEFS = {
    "strength": StatusDef(
        key="strength",
        name="力量",
        category="buff",
        display_mode="value",
        order=10,
    ),
    "vulnerable": StatusDef(
        key="vulnerable",
        name="易伤",
        category="debuff",
        display_mode="turns",
        order=20,
    ),
    "weak": StatusDef(
        key="weak",
        name="虚弱",
        category="debuff",
        display_mode="turns",
        order=30,
    ),
    "poison": StatusDef(
        key="poison",
        name="中毒",
        category="debuff",
        display_mode="stack",
        order=40,
    ),
    "intangible": StatusDef(
        key="intangible",
        name="无实体",
        category="buff",
        display_mode="turns",
        order=50,
    ),
}