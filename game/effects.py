# -*- coding: utf-8 -*-

from game.modifiers import apply_modifier_profile, get_status_value
from game.status.status_defs import get_status_name
from game.damage import deal_damage
import random

def resolve_amount(
    game_state,
    card,
    amount_spec,
    target=None,
    source=None,
    damage_source=None,
    block_source=None,
    effect_context=None,
    attack_type="",
    attack_element=""
):
    """
    解析卡牌效果中的数值。

    支持：
    1. 直接整数：
       "amount": 6

    2. 从 card_vars 取值：
       "amount": {"var": "block"}

    3. 基础值 + 修正：
       "amount": {
           "base_var": "damage",
           "modifier_profile": "attack_damage"
       }

    4. 根据状态缩放：
       "amount": {
           "base_var": "damage",
           "scaling": [
               {"stat": "strength", "multiplier_var": "strength_scale"}
           ]
       }
    """
    if isinstance(amount_spec, int):
        return amount_spec

    if amount_spec is None:
        return 0

    if source is None:
        source = game_state.player

    if effect_context is None:
        effect_context = {}

    if not isinstance(amount_spec, dict):
        return 0

    card_vars = getattr(card, "card_vars", None)

    if card_vars is None:
        card_vars = getattr(card, "effect_vars", {})

    value = 0

    base_var = amount_spec.get("base_var")
    if base_var:
        value += int(card_vars.get(base_var, 0))

    var_name = amount_spec.get("var")
    if var_name:
        value += int(card_vars.get(var_name, 0))

    scaling_list = amount_spec.get("scaling", [])
    for scaling in scaling_list:
        stat = scaling.get("stat")
        multiplier_var = scaling.get("multiplier_var")

        if not stat or not multiplier_var:
            continue
        stat_value = get_status_value(source, stat)
        multiplier = int(card_vars.get(multiplier_var, 0))
        value += stat_value * multiplier

    x_var_name = amount_spec.get("x_var")
    if x_var_name:
        value += int(effect_context.get(x_var_name, 0))

    x_conditional_var = amount_spec.get("x_conditional_var")
    if x_conditional_var:
        x_value = int(effect_context.get("x", 0))
        threshold = int(x_conditional_var.get("x_gte", 0))
        then_var = x_conditional_var.get("then_var")
        else_var = x_conditional_var.get("else_var")

        if x_value >= threshold:
            value += int(card_vars.get(then_var, 0))
        else:
            value += int(card_vars.get(else_var, 0))

    modifier_profile = amount_spec.get("modifier_profile")

    value = apply_modifier_profile(
        value=value,
        modifier_profile=modifier_profile,
        game_state=game_state,
        source=source,
        target=target,
        card=card,
        damage_source=damage_source,
        block_source=block_source,
        attack_type=attack_type,
        attack_element=attack_element
    )
    return int(value)


def get_target_enemy(game_state, target_index):
    enemies = game_state.enemies
    if target_index < 0 or target_index >= len(enemies):
        return None
    enemy = enemies[target_index]
    if not enemy.is_alive():
        return None
    return enemy

def get_alive_enemies(game_state):
    alive_enemies = []
    for enemy in game_state.enemies:
        if enemy.is_alive():
            alive_enemies.append(enemy)
    return alive_enemies

def get_effect_target_entity(game_state, target_key, target_index):
    if target_key in (None, "self"):
        return game_state.player
    if target_key in ("selected_enemy", "enemy"):
        return get_target_enemy(game_state, target_index)
    return None

def get_effect_attack_tags(card, effect):
    attack_type = effect.get("attack_type", getattr(card, "attack_type", ""))
    attack_element = effect.get("attack_element", getattr(card, "attack_element", ""))
    return attack_type, attack_element

def apply_card_effect(game_state, card, effect, target_index, effect_context=None):
    """
    执行单个卡牌效果。
    返回 logs。
    """
    if effect_context is None:
        effect_context = {}
    logs = []

    op = effect.get("op")

    if op == "deal_damage":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs
        damage = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            damage_source="played_card",
            effect_context=effect_context,
            attack_type=attack_type,
            attack_element=attack_element
        )
        logs.append("【{}】造成 {} 点攻击伤害。".format(card.name, damage))
        logs.extend(deal_damage(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            amount=damage,
            damage_kind="attack",
            card=card,
            attack_type=attack_type,
            attack_element=attack_element
        ))
        return logs
    
    if op == "deal_damage_random_enemies":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        times_spec = effect.get("times", None)
        if times_spec is None:
            times_spec = effect.get("count", 1)
        times = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=times_spec,
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        times = int(times)
        if times <= 0:
            logs.append("随机伤害次数为 0，【{}】没有造成伤害。".format(card.name))
            return logs
        unique_targets = bool(effect.get("unique_targets", False))
        if unique_targets:
            candidate_pool = get_alive_enemies(game_state)
        else:
            candidate_pool = None
        for hit_index in range(times):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续随机伤害不再结算。")
                break
            if game_state.is_all_enemies_dead():
                logs.append("所有敌人已被击败，后续随机伤害不再结算。")
                break
            if unique_targets:
                candidate_pool = [enemy for enemy in candidate_pool if enemy.is_alive()]
                if not candidate_pool:
                    logs.append("没有更多可随机命中的敌人。")
                    break
                target_entity = random.choice(candidate_pool)
                candidate_pool.remove(target_entity)
            else:
                alive_enemies = get_alive_enemies(game_state)
                if not alive_enemies:
                    logs.append("没有可攻击的敌人。")
                    break
                target_entity = random.choice(alive_enemies)
            damage = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("amount"),
                source=game_state.player,
                target=target_entity,
                damage_source="played_card",
                effect_context=effect_context,
                attack_type=attack_type,
                attack_element=attack_element
            )
            logs.append("【{}】随机命中 {}，造成 {} 点攻击伤害。第 {}/{} 次。".format(
                card.name,
                target_entity.name,
                damage,
                hit_index + 1,
                times
            ))
            logs.extend(deal_damage(
                game_state=game_state,
                source=game_state.player,
                target=target_entity,
                amount=damage,
                damage_kind="attack",
                card=card,
                attack_type=attack_type,
                attack_element=attack_element
            ))
        return logs

    if op == "deal_damage_all_enemies":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        alive_enemies = []
        for enemy in game_state.enemies:
            if enemy.is_alive():
                alive_enemies.append(enemy)
        if not alive_enemies:
            logs.append("没有可攻击的敌人。")
            return logs
        for target_entity in alive_enemies:
            if game_state.battle_over:
                logs.append("战斗已经结束，后续全体伤害不再结算。")
                break
            if not target_entity.is_alive():
                continue
            damage = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("amount"),
                source=game_state.player,
                target=target_entity,
                damage_source="played_card",
                effect_context=effect_context,
                attack_type=attack_type,
                attack_element=attack_element
            )
            logs.append("【{}】对 {} 造成 {} 点攻击伤害。".format(
                card.name,
                target_entity.name,
                damage
            ))
            logs.extend(deal_damage(
                game_state=game_state,
                source=game_state.player,
                target=target_entity,
                amount=damage,
                damage_kind="attack",
                card=card,
                attack_type=attack_type,
                attack_element=attack_element
            ))
            if game_state.battle_over:
                break
        return logs

    if op == "gain_block":
        target_key = effect.get("target", "self")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("格挡目标无效。")
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            block_source="played_card",
            effect_context=effect_context
        )

        if amount < 0:
            amount = 0

        target_entity.block += amount

        logs.append("{} 获得 {} 点格挡。".format(
            target_entity.name,
            amount
        ))

        return logs

    if op == "gain_status":
        status_key = effect.get("status")
        target_key = effect.get("target", "self")

        if not status_key:
            logs.append("gain_status 缺少 status。")
            return logs

        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("状态目标无效。")
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )

        current = target_entity.gain_status(status_key, amount)
        status_name = get_status_name(status_key)

        logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
            target_entity.name,
            amount,
            status_name,
            status_name,
            current
        ))

        return logs

    if op == "draw_cards":
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )

        logs.extend(game_state.player.draw_cards(amount))
        return logs

    if op == "draw_to_full":
        logs.extend(game_state.player.draw_to_full())
        return logs

    if op == "request_discard_any":
        game_state.pending_discard_selection = True
        game_state.pending_discard_source = card.name
        logs.append("请选择任意张手牌丢弃：/card drop 0 2 3。若不丢弃，使用 /card drop none。")
        return logs
    
    if op == "repeat_x":
        x = int(effect_context.get("x", 0))

        if x <= 0:
            logs.append("X 为 0，【{}】没有触发重复效果。".format(card.name))
            return logs

        child_effects = effect.get("effects", [])

        if not child_effects:
            logs.append("repeat_x 缺少 effects。")
            return logs

        for index in range(x):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续 X 次数不再结算。")
                break

            logs.append("X 效果第 {}/{} 次：".format(index + 1, x))

            for child_effect in child_effects:
                logs.extend(apply_card_effect(
                    game_state=game_state,
                    card=card,
                    effect=child_effect,
                    target_index=target_index,
                    effect_context=effect_context
                ))

                if game_state.battle_over:
                    break

        return logs

    if op in ("set_zone", "deploy_zone"):
        from game.zone_utils import deploy_element_zone
        element = effect.get("element", getattr(card, "attack_element", ""))
        force_extreme = bool(effect.get("force_extreme", False))
        logs.extend(deploy_element_zone(
            game_state=game_state,
            element=element,
            source=game_state.player,
            card=card,
            force_extreme=force_extreme
        ))
        return logs

    if op == "gain_energy":
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context,
        )

        game_state.player.cost += amount

        logs.append("{} 获得 {} 点费用。当前费用：{}。".format(
            game_state.player.name,
            amount,
            game_state.player.cost
        ))

        return logs

    logs.append("未知效果：{}".format(op))
    return logs


def apply_card_effects(game_state, card, target_index, effect_context=None):
    logs = []

    if effect_context is None:
        effect_context = {}

    for effect in card.effects:
        logs.extend(apply_card_effect(
            game_state,
            card,
            effect,
            target_index,
            effect_context=effect_context
        ))

    return logs