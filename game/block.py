# game/block.py
# -*- coding: utf-8 -*-

from game.modifiers import apply_block_modifiers
from game.battle_context import BattleContext
from game.event_bus import dispatch_event
from game.constants import EVENT_GAIN_BLOCK_AFTER


def gain_block_without_modifiers(
    game_state,
    source,
    target,
    amount,
    block_source="effect",
    card=None,
    message=None
):
    """
    直接获得格挡，不再额外经过敏捷 / 脆弱等修正。

    用于：
    - 已经在 effects.resolve_amount 中修正过的 gain_block
    - 愤怒、金属化、无惧疼痛等间接格挡
    - 巩固翻倍后的新增格挡
    """
    logs = []

    amount = int(amount)
    if amount < 0:
        amount = 0

    if amount <= 0:
        if message:
            logs.append(message)
        else:
            logs.append("{} 没有获得格挡。".format(target.name))
        return logs

    old_block = int(getattr(target, "block", 0))
    target.block = old_block + amount

    if message:
        logs.append(message)
    else:
        logs.append("{} 获得 {} 点格挡。当前格挡：{}。".format(
            target.name,
            amount,
            target.block
        ))

    context = BattleContext(
        game_state=game_state,
        player=game_state.player,
        source=source,
        target=target,
        card=card,
        extra={
            "amount": amount,
            "old_block": old_block,
            "new_block": target.block,
            "block_source": block_source
        }
    )

    logs.extend(dispatch_event(
        game_state,
        EVENT_GAIN_BLOCK_AFTER,
        context
    ))

    return logs

def gain_block(
    game_state,
    source,
    target,
    amount,
    block_source="effect",
    card=None
):
    logs = []

    amount = int(amount)

    amount = apply_block_modifiers(
        value=amount,
        game_state=game_state,
        source=source,
        target=target,
        card=card,
        block_source=block_source
    )

    if amount < 0:
        amount = 0

    logs.extend(gain_block_without_modifiers(
        game_state=game_state,
        source=source,
        target=target,
        amount=amount,
        block_source=block_source,
        card=card
    ))

    return logs