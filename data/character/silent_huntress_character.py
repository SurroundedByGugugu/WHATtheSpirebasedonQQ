# -*- coding: utf-8 -*-

from data.character.base_character import CharacterTemplate


class SilentHuntressCharacter(CharacterTemplate):
    """
    静默猎手。
    初始 HP：70
    初始遗物：蛇之戒指
    初始牌组：
        5 张打击
        5 张格挡
        1 张中和
        1 张生存者
    """

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.silent_huntress",
            name="静默猎手",
            max_hp=70,
            max_cost=3,
            starting_relic_ids=[
                "relic.ring_of_the_snake",
            ],
            max_potion_slots=3,
            starting_gold=99,
            starting_deck_ids=[
                "card.strike",
                "card.strike",
                "card.strike",
                "card.strike",
                "card.strike",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.neutralize",
                "card.survivor",
            ],
        )