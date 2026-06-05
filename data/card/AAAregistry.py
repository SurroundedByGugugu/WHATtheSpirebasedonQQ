# -*- coding: utf-8 -*-

from data.card.basic_cards import (
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

from data.card.character.lumine_card import (
    create_mirage_shadows,
    create_god_in_hand,
    create_transfer,
    create_inducing,
    create_cheap_intuition,
    create_energetic,
    create_factor_separate,
    create_fast_transfer,
    create_brain_shockwave,
    create_ok_next,
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
    "card.mirage_shadows": create_mirage_shadows,
    "card.god_in_hand": create_god_in_hand,
    "card.transfer": create_transfer,
    "card.inducing": create_inducing,
    "card.cheap_intuition": create_cheap_intuition,
    "card.energetic": create_energetic,
    "card.factor_separate": create_factor_separate,
    "card.fast_transfer": create_fast_transfer,
    "card.brain_shockwave": create_brain_shockwave,
    "card.ok_next": create_ok_next,
}

def create_card(card_id):
    create_func = CARD_REGISTRY.get(card_id)

    if create_func is None:
        raise ValueError("未知卡牌 ID：{}".format(card_id))

    return create_func()


def create_deck(card_ids):
    return [create_card(card_id) for card_id in card_ids]