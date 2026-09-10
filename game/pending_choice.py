# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PendingChoice:
    """
    通用的“等待玩家选择”状态。
    先作为新机制入口使用，旧的 pending_* 字段可以逐步迁移过来。
    """

    kind: str
    source: str = ""
    prompt: str = ""
    command_hint: str = ""
    block_message: str = ""
    options: List[Any] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)


def get_pending_choice(game_state):
    return getattr(game_state, "pending_choice", None)


def set_pending_choice(game_state, choice):
    game_state.pending_choice = choice


def enqueue_pending_choice(game_state, choice):
    """多个选择同时触发时，保留当前选择并按顺序等待。"""
    if get_pending_choice(game_state) is None:
        set_pending_choice(game_state, choice)
    else:
        game_state.pending_choice_queue.append(choice)


def has_pending_choice(game_state):
    return get_pending_choice(game_state) is not None


def pending_choice_is(game_state, kind):
    choice = get_pending_choice(game_state)
    if choice is None:
        return False
    return getattr(choice, "kind", "") == kind


def clear_pending_choice(game_state, kind=None):
    if kind is not None and not pending_choice_is(game_state, kind):
        return
    if kind is None:
        # 不指定类型表示取消全部选择，例如回合结束时清理。
        game_state.pending_choice_queue.clear()
    game_state.pending_choice = (
        game_state.pending_choice_queue.pop(0)
        if game_state.pending_choice_queue else None
    )


def format_pending_choice_hint(game_state):
    choice = get_pending_choice(game_state)
    if choice is None:
        return ""
    if choice.block_message:
        return choice.block_message
    lines = []
    if choice.prompt:
        lines.append(choice.prompt)
    if choice.command_hint:
        lines.append(choice.command_hint)
    return "\n".join(lines)
