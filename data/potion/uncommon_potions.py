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

def create_ancient_potion():
    return PotionTemplate(
        potion_id="potion.ancient",
        name="先古药水",
        description="获得 1 层人工制品。",
        target="self",
        quantity="uncommon",
        effect_vars={"artifact": 1},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "artifact",
                "amount": {"var": "artifact"}
            }
        ],
    )


def create_distilled_chaos():
    return PotionTemplate(
        potion_id="potion.distilled_chaos",
        name="精炼混沌",
        description="打出你抽牌堆顶部的 3 张牌。",
        target="self",
        quantity="uncommon",
        effect_vars={"count": 3},
        effects=[
            {
                "op": "play_draw_pile_top_count",
                "times": {"var": "count"}
            }
        ],
    )


def create_liquid_bronze():
    return PotionTemplate(
        potion_id="potion.liquid_bronze",
        name="流动铜液",
        description="获得 3 点荆棘。",
        target="self",
        quantity="uncommon",
        effect_vars={"thorns": 3},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "thorns",
                "amount": {"var": "thorns"}
            }
        ],
    )


def create_regen_potion():
    return PotionTemplate(
        potion_id="potion.regen",
        name="再生药水",
        description="获得 5 层再生。",
        target="self",
        quantity="uncommon",
        effect_vars={"regeneration": 5},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "regeneration",
                "amount": {"var": "regeneration"}
            }
        ],
    )


def create_gamblers_brew():
    return PotionTemplate(
        potion_id="potion.gamblers_brew",
        name="赌徒特酿",
        description="丢弃任意张牌，然后抽相同数量的牌。神圣树皮对此无效。",
        target="self",
        quantity="uncommon",
        effects=[],
    )


def create_essence_of_steel():
    return PotionTemplate(
        potion_id="potion.essence_of_steel",
        name="钢之精华",
        description="获得 4 层多层护甲。",
        target="self",
        quantity="uncommon",
        effect_vars={"plated_armor": 4},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "plated_armor",
                "amount": {"var": "plated_armor"}
            }
        ],
    )