# -*- coding: utf-8 -*-

from game.status.status_defs import get_status_def, get_status_name


def is_debuff_status(status_key):
    status_def = get_status_def(status_key)
    if status_def is None:
        return False
    return getattr(status_def, "category", "") == "debuff"


def add_status_with_artifact(owner, key, amount):
    """
    统一状态获得入口。

    规则：
    - amount > 0 且目标状态是 debuff 时，人工制品抵挡一次。
    - strength/dexterity 的负数变化不算施加 debuff，不被人工制品抵挡。
    """
    amount = int(amount)
    statuses = getattr(owner, "statuses", None)
    status_name = get_status_name(key)

    if statuses is None:
        return {
            "current": 0,
            "applied": False,
            "blocked": False,
            "artifact_left": 0,
            "status_name": status_name,
        }

    if amount > 0 and key != "artifact" and is_debuff_status(key):
        artifact = statuses.get("artifact")
        if artifact > 0:
            artifact_left = statuses.add("artifact", -1)
            return {
                "current": statuses.get(key),
                "applied": False,
                "blocked": True,
                "artifact_left": artifact_left,
                "status_name": status_name,
            }

    current = statuses.add(key, amount)
    return {
        "current": current,
        "applied": True,
        "blocked": False,
        "artifact_left": statuses.get("artifact"),
        "status_name": status_name,
    }


def format_status_gain_log(entity, key, amount, result):
    status_name = result.get("status_name", get_status_name(key))
    amount = int(amount)

    if result.get("blocked"):
        return "{} 的人工制品抵挡了 {}。剩余人工制品：{}。".format(
            entity.name,
            status_name,
            result.get("artifact_left", 0)
        )

    if amount < 0:
        return "{} 失去 {} 点{}。当前{}：{}。".format(
            entity.name,
            abs(amount),
            status_name,
            status_name,
            result.get("current", 0)
        )

    return "{} 获得 {} 点{}。当前{}：{}。".format(
        entity.name,
        amount,
        status_name,
        status_name,
        result.get("current", 0)
    )