# -*- coding: utf-8 -*-
from data.character.base_character import CharacterTemplate
class LumineCharacter(CharacterTemplate):
    """
    昼

    初始 HP：70
    初始遗物：十字架耳饰
    初始牌组：4打4防，？？

    """

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.lumine",
            name="昼·里辛塔法",
            max_hp=70,
            max_cost=3,
            starting_relic_ids=[
                "relic.cross_earring"
            ],
            max_potion_slots = 3,
            starting_gold = 99,
            starting_deck_ids=[
                "card.strike_lumine",
                "card.strike_lumine",
                "card.strike_lumine",
                "card.strike_lumine",
                "card.defend_lumine",
                "card.defend_lumine",
                "card.defend_lumine",
                "card.defend_lumine",
                "card.transfer",
                "card.inducing",
            ]
        )