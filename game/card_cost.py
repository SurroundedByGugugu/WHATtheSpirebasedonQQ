# -*- coding: utf-8 -*-

from game.x_value import is_x_cost_card
from game.modifiers import get_status_value

def get_card_current_cost(game_state, card):
    """
    返回卡牌当前实际费用。

    当前支持：
    - 以血还血：本场战斗中玩家每失去生命一次，费用 -1
    """
    if is_x_cost_card(card):
        return card.cost

    # 蓝蜡烛 / 医药箱允许打出的诅咒、状态牌，费用按 0 处理。
    if game_state is not None:
        player = getattr(game_state, "player", None)
        relic_ids = {getattr(relic, "relic_id", "") for relic in getattr(player, "relics", []) or []}
        card_type = getattr(card, "card_type", "")
        if card_type == "curse" and "relic.blue_candle" in relic_ids:
            return 0
        if card_type == "status" and "relic.medical_kit" in relic_ids:
            return 0

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

            elif op == "reduce_if_active_zone":
                from game.zone_utils import normalize_element

                zone = getattr(game_state, "active_zone", None)
                wanted_element = normalize_element(rule.get("element", ""))
                current_element = normalize_element(getattr(zone, "element", ""))

                if zone is not None and wanted_element and current_element == wanted_element:
                    current_cost -= int(rule.get("amount", 1))

    if (
        game_state is not None
        and getattr(card, "card_type", "") == "skill"
        and get_status_value(game_state.player, "corruption") > 0
    ):
        current_cost = 0
    min_cost = 0
    for rule in getattr(card, "cost_rules", []):
        if "min_cost" in rule:
            min_cost = int(rule.get("min_cost", 0))

    if current_cost < min_cost:
        current_cost = min_cost

    return current_cost