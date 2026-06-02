# -*- coding: utf-8 -*-

from data.character.base_character import CharacterTemplate


class ArmoredWarriorTestCharacter(CharacterTemplate):

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.armored_warrior_test",
            name="铁甲战士（拿到了不得了的东西版）",
            max_hp=80,
            max_cost=3,
            starting_relic_ids=[
                "relic.burning_blood",
                "relic.x_potion"
            ],
            max_potion_slots = 3,
            starting_gold = 99,

            starting_deck_ids=[
                "card.strike",
                "card.strike",
                "card.strike",
                "card.strike",
                "card.whirlwind",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.hard_blow", 
            ]
        )