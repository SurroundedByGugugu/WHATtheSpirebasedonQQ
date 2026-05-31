# -*- coding: utf-8 -*-

from game.battle_context import BattleContext
from game.event_bus import dispatch_event
from game.constants import EVENT_DAMAGE_AFTER


def deal_damage(
    game_state,
    source,
    target,
    amount,
    damage_kind="attack",
    card=None,
    is_reaction_damage=False
):
    """
    统一伤害入口。

    source: 伤害来源，例如玩家、敌人
    target: 受伤目标
    amount: 结算前伤害
    damage_kind:
        attack   攻击伤害，可触发荆棘
        thorns   荆棘反伤
        poison   中毒伤害
        effect   其他效果伤害
    is_reaction_damage:
        用于避免荆棘反伤继续触发荆棘。
    """
    logs = []

    amount = int(amount)

    if amount < 0:
        amount = 0

    if target is None:
        return ["伤害目标无效。"]

    old_hp = target.hp
    old_block = target.block
    was_alive = target.is_alive()

    logs.append(target.take_damage(amount))

    real_damage = old_hp - target.hp
    blocked = old_block - target.block

    if real_damage < 0:
        real_damage = 0

    if blocked < 0:
        blocked = 0

    context = BattleContext(
        game_state=game_state,
        player=game_state.player,
        source=source,
        target=target,
        card=card,
        extra={
            "amount": amount,
            "real_damage": real_damage,
            "blocked": blocked,
            "damage_kind": damage_kind,
            "is_reaction_damage": is_reaction_damage,
        }
    )

    logs.extend(dispatch_event(game_state, EVENT_DAMAGE_AFTER, context))

    if was_alive and not target.is_alive():
        if hasattr(target, "enemy_id"):
            from data.enemy.death_messages import get_enemy_death_message
            logs.append(get_enemy_death_message(target))

    return logs