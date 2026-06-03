# -*- coding: utf-8 -*-

from data.card.global_cards.basic_cards import (
    create_strike,
    create_defend
)

from data.card.character.test_character_cards import (
    create_gain_status_strength,
    create_exhaust_strength,
    create_ethereal_strength,
    create_retain_strength,
    create_clever_strength,
    create_innate_thorns,
    create_draw_discard_test,
    create_test_heavy_strike,
    create_test_x_drill,
)

from data.card.character.armored_warrior_card import(
    create_hard_blow,
    create_whirlwind,
    create_armored_placeholder_skill,
    create_demon_form
)

from data.card.character.yoirine_card import (
    create_crystal_piercing,
    create_crystal_zone
)

CARD_REGISTRY = {
    "card.strike": create_strike,
    "card.defend": create_defend,
    "card.gain_status_strength": create_gain_status_strength,
    "card.exhaust_strength": create_exhaust_strength,
    "card.ethereal_strength": create_ethereal_strength,
    "card.retain_strength": create_retain_strength,
    "card.clever_strength": create_clever_strength,
    "card.innate_thorns": create_innate_thorns,
    "card.draw_discard_test": create_draw_discard_test,
    "card.test_heavy_strike": create_test_heavy_strike,
    "card.hard_blow": create_hard_blow,
    "card.test_x_drill": create_test_x_drill,
    "card.whirlwind": create_whirlwind,
    "card.crystal_piercing": create_crystal_piercing,
    "card.crystal_zone":create_crystal_zone,
    "card.demon_form":create_demon_form,
    "card.armored_placeholder_skill": create_armored_placeholder_skill,
}

# CARD_REGISTRY = {
#     "card.strike": create_strike,
#     "card.defend": create_defend,
#     "card.hard_blow": create_hard_blow,
# }

def create_card(card_id):
    create_func = CARD_REGISTRY.get(card_id)

    if create_func is None:
        raise ValueError("未知卡牌 ID：{}".format(card_id))

    return create_func()


def create_deck(card_ids):
    return [create_card(card_id) for card_id in card_ids]