# -*- coding: utf-8 -*-

from game.x_value import is_x_cost_card


def get_card_current_cost(game_state, card):
    """
    返回卡牌当前实际费用。

    当前支持：
    - 以血还血：本场战斗中玩家每失去生命一次，费用 -1
    """
    if is_x_cost_card(card):
        return card.cost

    try:
        current_cost = int(card.cost)
    except (TypeError, ValueError):
        return card.cost

    temporary_cost_override = getattr(card, "temporary_cost_override", None)
    if temporary_cost_override is not None:
        try:
            current_cost = int(temporary_cost_override)
        except (TypeError, ValueError):
            pass
    else:
        for rule in getattr(card, "cost_rules", []):
            op = rule.get("op")

            if op == "reduce_by_player_life_loss_count":
                count = int(getattr(game_state, "player_life_loss_count_this_battle", 0))
                amount_per_loss = int(rule.get("amount_per_loss", 1))
                current_cost -= count * amount_per_loss

    min_cost = 0
    for rule in getattr(card, "cost_rules", []):
        if "min_cost" in rule:
            min_cost = int(rule.get("min_cost", 0))

    if current_cost < min_cost:
        current_cost = min_cost

    return current_cost