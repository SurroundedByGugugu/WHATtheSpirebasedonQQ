# game/status/status_display.py
# -*- coding: utf-8 -*-

from game.status.status_defs import get_status_def, iter_status_defs


def format_status(key, value):
    status_def = get_status_def(key)

    if status_def is None:
        return "{}({})".format(key, value)

    name = status_def.name
    mode = status_def.display_mode

    if mode == "flag":
        return name

    if mode == "turns":
        return "{}({}回合)".format(name, value)

    if mode == "stack":
        return "{}({}层)".format(name, value)

    if mode == "percent":
        return "{}(+{}%)".format(name, value)

    return "{}({})".format(name, value)

    return "{}({})".format(name, value)


def get_status_display_text(status_container):
    active = status_container.all_active()

    if not active:
        return "无状态"

    parts = []

    for status_def in iter_status_defs():
        key = status_def.key
        value = active.get(key, 0)

        if value != 0:
            parts.append(format_status(key, value))

    for key, value in active.items():
        if get_status_def(key) is None:
            parts.append(format_status(key, value))

    return "，".join(parts)