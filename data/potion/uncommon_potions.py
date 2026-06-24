# -*- coding: utf-8 -*-

from data.potion.base_potion import PotionTemplate


def create_duplication_potion():
    return PotionTemplate(
        potion_id="potion.duplication",
        name="复制药水",
        description="本回合你的下一张牌将被打出两次。",
        target="self",
        quantity="uncommon",
        effect_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "duplication_potion_next_card",
                "amount": {
                    "var": "count"
                }
            }
        ]
    )


def create_liquid_memories():
    return PotionTemplate(
        potion_id="potion.liquid_memories",
        name="液态记忆",
        description="选择弃牌堆中的一张牌放入你的手牌。这张牌在本回合耗能变为 0。神圣树皮：将选中的牌加入手牌两次。",
        target="self",
        quantity="uncommon",
        effects=[],
    )


def create_cunning_potion():
    return PotionTemplate(
        potion_id="potion.cunning",
        name="狡诈药水",
        description="增加 3 张小刀+ 到你的手牌。神圣树皮：改为 6 张。",
        target="self",
        quantity="uncommon",
        effects=[],
    )


def create_elixir():
    return PotionTemplate(
        potion_id="potion.elixir",
        name="万灵药水",
        description="消耗任意张手牌。神圣树皮不会使该药水翻倍。",
        target="self",
        quantity="uncommon",
        owner_character_id="character.armored_warrior",
        effects=[],
    )
