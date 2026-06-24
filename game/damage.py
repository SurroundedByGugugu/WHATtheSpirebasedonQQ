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

def should_ignore_block_by_phantom_form(game_state, source, card, damage_kind):
    if game_state is None:
        return False
    if damage_kind != "attack":
        return False
    if source is not getattr(game_state, "player", None):
        return False
    if getattr(card, "card_type", "") != "attack":
        return False

    from game.modifiers import get_status_value
    return get_status_value(source, "phantom_form") > 0


def _entity_has_relic(entity, relic_id):
    for relic in getattr(entity, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def _get_status_value(entity, key):
    statuses = getattr(entity, "statuses", None)
    if statuses is None:
        return 0
    try:
        return int(statuses.get(key))
    except Exception:
        return 0


def _apply_unblocked_damage_relics_and_statuses(game_state, source, target, raw_unblocked, damage_kind, card, logs):
    final_damage = int(raw_unblocked)
    if final_damage <= 0:
        return 0

    hp_loss_kinds = {
        "poison", "hp_loss", "life_loss", "card_hp_loss",
        "power_hp_loss_from_card", "curse", "burn"
    }
    if damage_kind not in hp_loss_kinds and _get_status_value(target, "intangible") > 0 and final_damage > 1:
        logs.append("{} 的无实体使本次未被格挡的伤害降为 1。".format(target.name))
        final_damage = 1

    if (
        damage_kind == "attack"
        and source is getattr(game_state, "player", None)
        and hasattr(target, "enemy_id")
        and getattr(card, "card_type", "") == "attack"
        and _entity_has_relic(source, "relic.the_boot")
        and final_damage > 0
        and final_damage <= 5
    ):
        if final_damage < 5:
            logs.append("【发条靴】触发：未被格挡的攻击伤害 {} -> 5。".format(final_damage))
        final_damage = 5

    player = getattr(game_state, "player", None)
    if target is player and final_damage > 0:
        if (
            damage_kind == "attack"
            and source is not None
            and hasattr(source, "enemy_id")
            and _entity_has_relic(target, "relic.torii")
            and final_damage <= 5
        ):
            if final_damage != 1:
                logs.append("【鸟居】触发：未被格挡的攻击伤害 {} -> 1。".format(final_damage))
            final_damage = 1

        if _entity_has_relic(target, "relic.tungsten_rod"):
            old_damage = final_damage
            final_damage = max(0, final_damage - 1)
            logs.append("【钨合金棍】触发：生命损失 {} -> {}。".format(old_damage, final_damage))

        if final_damage > 0 and _get_status_value(target, "buffer") > 0:
            target.statuses.add("buffer", -1)
            logs.append("{} 的缓冲阻止了本次生命值损伤。剩余缓冲：{}。".format(target.name, _get_status_value(target, "buffer")))
            final_damage = 0

    return final_damage

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

    phantom_ignore_block = False
    if (
        not ignore_block
        and should_ignore_block_by_phantom_form(game_state, source, card, damage_kind)
    ):
        ignore_block = True
        phantom_ignore_block = True

    if ignore_block:
        if phantom_ignore_block and old_block > 0:
            logs.append("虚影形态：本次攻击无视格挡。")

        if amount <= 0:
            logs.append("{} 没有受到伤害。".format(target.name))
        else:
            final_damage = _apply_unblocked_damage_relics_and_statuses(
                game_state=game_state,
                source=source,
                target=target,
                raw_unblocked=amount,
                damage_kind=damage_kind,
                card=card,
                logs=logs
            )
            target.hp -= final_damage
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
            # 风 Zone 的格挡倍率仍沿用旧函数；这里保留原行为，不在风格挡路径额外套发条靴。
            logs.append(take_damage_with_wind_block_effect(
                target=target,
                amount=amount,
                multiplier=wind_block_multiplier
            ))
        else:
            if amount <= 0:
                logs.append("{} 没有受到伤害。".format(target.name))
            else:
                blocked_now = min(int(getattr(target, "block", 0)), amount)
                target.block -= blocked_now
                if target.block < 0:
                    target.block = 0
                raw_unblocked = amount - blocked_now
                final_damage = _apply_unblocked_damage_relics_and_statuses(
                    game_state=game_state,
                    source=source,
                    target=target,
                    raw_unblocked=raw_unblocked,
                    damage_kind=damage_kind,
                    card=card,
                    logs=logs
                )
                target.hp -= final_damage
                if target.hp < 0:
                    target.hp = 0
                logs.append("{} 受到 {} 点伤害，剩余 HP：{}/{}，格挡：{}。".format(
                    target.name,
                    old_hp - target.hp,
                    target.hp,
                    target.max_hp,
                    target.block
                ))

    real_damage = old_hp - target.hp
    blocked = old_block - target.block

    if real_damage < 0:
        real_damage = 0

    if blocked < 0:
        blocked = 0

    if (
        damage_kind == "attack"
        and source is getattr(game_state, "player", None)
        and hasattr(target, "enemy_id")
        and _entity_has_relic(source, "relic.hand_drill")
        and int(old_block) > 0
        and int(getattr(target, "block", 0)) <= 0
        and int(blocked) > 0
    ):
        logs.append("【手钻】触发：突破了{}的格挡，给予 2 层易伤。".format(getattr(target, "name", "敌人")))
        try:
            from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
            logs.extend(apply_status_with_player_relics(
                game_state=game_state,
                source=source,
                target=target,
                status_key="vulnerable",
                amount=2
            ))
        except Exception:
            current = target.gain_status("vulnerable", 2)
            logs.append("{} 获得 2 点易伤。当前易伤：{}。".format(getattr(target, "name", "敌人"), current))

    if target is game_state.player and real_damage > 0:
        game_state.player_life_loss_count_this_battle = int(
            getattr(game_state, "player_life_loss_count_this_battle", 0)
        ) + 1
        
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
            "target_was_alive": was_alive,
            "target_is_dead_after": (was_alive and not target.is_alive()),
        }
    )

    logs.extend(dispatch_event(game_state, EVENT_DAMAGE_AFTER, context))

    if was_alive and not target.is_alive() and not context.extra.get("suppress_death_message", False):
        if hasattr(target, "enemy_id"):
            from data.enemy.death_messages import get_enemy_death_message
            logs.append(get_enemy_death_message(target))

    return logs