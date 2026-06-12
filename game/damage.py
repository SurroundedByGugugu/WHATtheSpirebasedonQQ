# -*- coding: utf-8 -*-

from game.battle_context import BattleContext
from game.event_bus import dispatch_event
from game.constants import EVENT_DAMAGE_AFTER


def take_damage_with_wind_block_effect(target, amount, multiplier):
    """
    风 Zone：攻击对格挡效果提升。
    multiplier=1.3 时，13 点格挡约只能抵消 10 点伤害。
    """
    import math

    amount = int(amount)
    multiplier = float(multiplier)

    if amount <= 0:
        return "{} 没有受到伤害。".format(target.name)

    if multiplier <= 1.0 or getattr(target, "block", 0) <= 0:
        return target.take_damage(amount)

    old_block = int(target.block)

    blocked_damage = min(amount, int(old_block / multiplier))
    if blocked_damage <= 0:
        used_block = old_block
    else:
        used_block = int(math.ceil(blocked_damage * multiplier))
        if used_block > old_block:
            used_block = old_block

    target.block -= used_block
    if target.block < 0:
        target.block = 0

    real_damage = amount - blocked_damage
    if real_damage < 0:
        real_damage = 0

    target.hp -= real_damage
    if target.hp < 0:
        target.hp = 0

    return "{} 受到 {} 点伤害，剩余 HP：{}/{}, 格挡：{}。".format(
        target.name,
        real_damage,
        target.hp,
        target.max_hp,
        target.block
    )


def deal_damage(
    game_state,
    source,
    target,
    amount,
    damage_kind="attack",
    card=None,
    is_reaction_damage=False,
    ignore_block=False,
    attack_type="",
    attack_element="",
    zone_element=""
):
    """
    统一伤害入口。

    source: 伤害来源，例如玩家、敌人、状态拥有者
    target: 受伤目标
    amount: 结算前伤害
    damage_kind:
        attack   攻击伤害，可触发荆棘
        thorns   荆棘反伤
        poison   中毒伤害
        effect   其他效果伤害
    is_reaction_damage:
        用于避免荆棘反伤继续触发荆棘。
    ignore_block:
        是否无视格挡。中毒建议使用 True。
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

    if ignore_block:
        if amount <= 0:
            logs.append("{} 没有受到伤害。".format(target.name))
        else:
            target.hp -= amount

            if target.hp < 0:
                target.hp = 0

            real_damage = old_hp - target.hp

            logs.append("{} 失去 {} 点生命，剩余 HP：{}/{}，格挡：{}。".format(
                target.name,
                real_damage,
                target.hp,
                target.max_hp,
                target.block
            ))
    else:
        wind_block_multiplier = 1.0
        if damage_kind == "attack":
            from game.zone_utils import get_zone_wind_block_effect_multiplier
            wind_block_multiplier = get_zone_wind_block_effect_multiplier(
                game_state=game_state,
                zone_element=zone_element
            )
        if wind_block_multiplier > 1.0:
            logs.append(take_damage_with_wind_block_effect(
                target=target,
                amount=amount,
                multiplier=wind_block_multiplier
            ))
        else:
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
            "ignore_block": ignore_block,
            "attack_type": attack_type,
            "attack_element": attack_element,
            "zone_element": zone_element,
        }
    )

    logs.extend(dispatch_event(game_state, EVENT_DAMAGE_AFTER, context))

    if was_alive and not target.is_alive() and not context.extra.get("suppress_death_message", False):
        if hasattr(target, "enemy_id"):
            from data.enemy.death_messages import get_enemy_death_message
            logs.append(get_enemy_death_message(target))

    return logs