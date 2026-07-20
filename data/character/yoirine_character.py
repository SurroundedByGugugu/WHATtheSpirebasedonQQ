# -*- coding: utf-8 -*-
from data.character.base_character import CharacterTemplate
class YoirineCharacter(CharacterTemplate):
    """
    yoi酱（喂

    初始 HP：70
    初始遗物：饱和裂隙（展开zone效果时自动重复展开极zone
    初始牌组：4打4防 1晶zone，1晶茧

    """

    def __init__(self):
        CharacterTemplate.__init__(
            self,
            character_id="character.yoirine",
            name="Yoirine",
            max_hp=70,
            max_cost=3,
            starting_relic_ids=[
                "relic.saturated_fissure"
            ],
            max_potion_slots = 3,
            starting_gold = 67, #我说yoi没有编制没有工资没钱很合理
            #为什么是67？问就是617！
            starting_deck_ids=[
                "card.strike_yoirine",
                "card.strike_yoirine",
                "card.strike_yoirine",
                "card.defend_yoirine",
                "card.defend_yoirine",
                "card.defend_yoirine",
                "card.spreading_wing",
                "card.spreading_wing",
                "card.crystal_plating",
                "card.crystal_zone",
            ]
        )

        # "card.shade_zone",
        # "card.crystal_cocoon"