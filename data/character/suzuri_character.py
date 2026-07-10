# -*- coding: utf-8 -*-

from data.character.base_character import CharacterTemplate


class SuzuriCharacter(CharacterTemplate):
    """
    Suzuri

    初始 HP：76
    初始遗物：贯岩
    初始牌组：4 打击、4 格挡、地原统御、熔离作用
    """

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.suzuri",
            name="Suzuri",
            max_hp=76,
            max_cost=3,
            starting_relic_ids=[
                "relic.piercing_lance",
                "relic.hometown_clear_stone",
            ],
            max_potion_slots=3,
            starting_gold=99,
            starting_deck_ids=[
                "card.strike_suzuri",
                "card.strike_suzuri",
                "card.strike_suzuri",
                "card.strike_suzuri",
                "card.defend_suzuri",
                "card.defend_suzuri",
                "card.defend_suzuri",
                "card.defend_suzuri",
                "card.earth_origin_dominion",
                "card.anatexis_action",
            ]
        )