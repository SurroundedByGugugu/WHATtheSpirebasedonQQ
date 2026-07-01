# -*- coding: utf-8 -*-

NECRONOMICURSE_CARD_ID = "card.curse.necronomicurse"

# Curses in this set are tied to a specific obtain source and must not be
# produced by generic random-curse or curse-transform pools.
SOURCE_ONLY_CURSE_CARD_IDS = {
    NECRONOMICURSE_CARD_ID,
}


def is_source_only_curse_card_id(card_id):
    return str(card_id or "") in SOURCE_ONLY_CURSE_CARD_IDS
