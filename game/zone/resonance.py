# -*- coding: utf-8 -*-

from game.constants import KEYWORD_EXHAUST, KEYWORD_RESONANCE


RESONANCE_ZONE_ELEMENTS = {
    "crystal",
    "shade",
}


def get_active_resonance_zone_element(game_state):
    from game.zone.zone_utils import get_active_zone, normalize_element

    zone = get_active_zone(game_state)
    if zone is None or zone.is_expired():
        return ""

    element = normalize_element(getattr(zone, "element", ""))

    if element in RESONANCE_ZONE_ELEMENTS:
        return element

    return ""


def card_has_resonance(card):
    return KEYWORD_RESONANCE in getattr(card, "keywords", [])


def collect_non_exhaust_pile_cards(player):
    options = []

    pile_specs = [
        ("hand", "手牌", getattr(player, "hand", []) or []),
        ("draw_pile", "抽牌堆", getattr(player, "draw_pile", []) or []),
        ("discard_pile", "弃牌堆", getattr(player, "discard_pile", []) or []),
    ]

    for pile_name, pile_label, pile_cards in pile_specs:
        for card in list(pile_cards):
            options.append({
                "pile_name": pile_name,
                "pile_label": pile_label,
                "card": card,
            })

    return options


def apply_synchronization_to_card(card, add_exhaust=True):
    logs = []

    if KEYWORD_RESONANCE not in getattr(card, "keywords", []):
        card.keywords.append(KEYWORD_RESONANCE)
        logs.append("【{}】获得词条：共鸣。".format(card.name))

    if add_exhaust and KEYWORD_EXHAUST not in getattr(card, "keywords", []):
        card.keywords.append(KEYWORD_EXHAUST)
        logs.append("【{}】获得词条：消耗。".format(card.name))

    return logs


def trigger_resonance_on_draw(game_state, card):
    logs = []

    if game_state is None or card is None:
        return logs

    if not card_has_resonance(card):
        return logs

    zone_element = get_active_resonance_zone_element(game_state)
    if not zone_element:
        return logs

    player = game_state.player

    if card not in getattr(player, "hand", []):
        return logs

    player.hand.remove(card)

    zone_name = {
        "crystal": "晶",
        "shade": "阴",
    }.get(zone_element, zone_element)

    logs.append("【{}】的共鸣触发：在{} Zone 下自动叠加{}属性打出，并在结算后消耗。".format(
        card.name,
        zone_name,
        zone_name
    ))

    from game.effects import play_card_from_effect_and_exhaust

    logs.extend(play_card_from_effect_and_exhaust(
        game_state=game_state,
        source_card=card,
        played_card=card,
        reason="resonance",
        force_exhaust=True,
        effect_context_extra={
            "zone_element_override": zone_element,
            "resonance_auto_play": True,
        },
        source_label="共鸣"
    ))

    return logs