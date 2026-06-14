# -*- coding: utf-8 -*-

from game.card_cost import get_card_current_cost
from game.effects import resolve_amount
from game.x_value import is_x_cost_card, calculate_card_x_value


def _alive_enemy_parts(game_state, card, amount_spec, effect_context, attack_type="", attack_element=""):
    parts = []
    for index, enemy in enumerate(game_state.enemies):
        if not enemy.is_alive():
            continue

        value = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=amount_spec,
            source=game_state.player,
            target=enemy,
            damage_source="played_card",
            effect_context=effect_context,
            attack_type=attack_type,
            attack_element=attack_element
        )
        parts.append("[{}]{}".format(index, value))

    return parts


def _preview_effect(game_state, card, effect, effect_context):
    op = effect.get("op")
    attack_type = effect.get("attack_type", getattr(card, "attack_type", ""))
    attack_element = effect.get("attack_element", getattr(card, "attack_element", ""))

    if op == "deal_damage":
        target = effect.get("target", "selected_enemy")
        if target in ("selected_enemy", "enemy"):
            parts = _alive_enemy_parts(
                game_state,
                card,
                effect.get("amount"),
                effect_context,
                attack_type=attack_type,
                attack_element=attack_element
            )
            if parts:
                return "伤害 " + "/".join(parts)
        return ""

    if op in ("deal_damage_all_enemies", "deal_damage_random_enemies"):
        parts = _alive_enemy_parts(
            game_state,
            card,
            effect.get("amount"),
            effect_context,
            attack_type=attack_type,
            attack_element=attack_element
        )
        if parts:
            label = "全体伤害" if op == "deal_damage_all_enemies" else "随机伤害"
            return label + " " + "/".join(parts)
        return ""

    if op == "gain_block":
        target = effect.get("target", "self")
        if target in ("self", None):
            value = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("amount"),
                source=game_state.player,
                target=game_state.player,
                block_source="played_card",
                effect_context=effect_context
            )
            return "格挡 {}".format(value)
        return ""

    if op == "repeat_x":
        x = int(effect_context.get("x", 0))
        child_parts = []

        for child_effect in effect.get("effects", []):
            text = _preview_effect(game_state, card, child_effect, effect_context)
            if text:
                child_parts.append(text)

        if child_parts:
            return "；".join(child_parts) + " ×{}".format(x)

        return "X ×{}".format(x)

    return ""


def format_card_actual_preview(game_state, card):
    if game_state is None:
        return ""

    effect_context = {}

    if is_x_cost_card(card):
        x, _ = calculate_card_x_value(
            game_state=game_state,
            card=card,
            raw_x=game_state.player.cost
        )
        effect_context = {
            "raw_x": game_state.player.cost,
            "x": x,
            "spent_cost": game_state.player.cost,
        }

    parts = []
    if not is_x_cost_card(card):
        current_cost = get_card_current_cost(game_state, card)
        try:
            base_cost = int(card.cost)
        except (TypeError, ValueError):
            base_cost = card.cost

        if current_cost != base_cost:
            parts.append("费用 {}".format(current_cost))
            
    for effect in getattr(card, "effects", []):
        text = _preview_effect(game_state, card, effect, effect_context)
        if text:
            parts.append(text)

    if not parts:
        return ""

    return "实际：" + "；".join(parts)