# -*- coding: utf-8 -*-

from data.character.base_character import CharacterTemplate


class ArmoredWarriorCharacter(CharacterTemplate):
    """
    战士哥，何时来的？更新于版本260526
    初始 HP：70
    初始遗物：燃烧之血
    初始牌组：
        5 张打击：打 6
        4 张格挡：防 5
        1 张痛击：打8 易伤2
    """

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.armored_warrior",
            name="铁甲战士",
            max_hp=80,
            max_cost=3,
            starting_relic_ids=[
                "relic.burning_blood"
            ],
            max_potion_slots = 3,
            starting_gold = 99,

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
                "card.hard_blow", 
            ]
        )