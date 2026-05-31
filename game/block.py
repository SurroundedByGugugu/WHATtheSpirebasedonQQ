# game/block.py
# -*- coding: utf-8 -*-

from game.modifiers import apply_block_modifiers


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

    target.block += amount

    logs.append("{} 获得 {} 点格挡。".format(
        target.name,
        amount
    ))

    return logs