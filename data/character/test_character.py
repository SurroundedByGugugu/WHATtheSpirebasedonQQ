# -*- coding: utf-8 -*-

from data.character.base_character import CharacterTemplate


class TestCharacter(CharacterTemplate):
    """
    测试角色。

    初始 HP：70
    初始遗物：占位符石头
    初始牌组：
        2 张打击：打 6
        2 张格挡：防 5
        1 张力量：力量 +1
        1 张测试重击：打 2 + 力量 * 8
    """

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.test",
            name="测试角色",
            max_hp=70,
            max_cost=3,
            starting_relic_ids=[
                "relic.placeholder_stone"
            ],
            starting_deck_ids=[
                "card.strike",
                "card.strike",
                "card.strike",
                "card.strike",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.defend",
                "card.gain_status_strength",
                "card.exhaust_strength",
                "card.ethereal_strength",
                "card.retain_strength",
                "card.clever_strength",
                "card.innate_thorns",
                "card.draw_discard_test",
                "card.test_heavy_strike"
            ],
            starting_potion_ids=[
                "potion.test_strength",
                "potion.test_fire",
            ]
        )