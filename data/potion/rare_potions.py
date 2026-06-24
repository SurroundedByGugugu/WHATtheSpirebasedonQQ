# -*- coding: utf-8 -*-

from data.potion.base_potion import PotionTemplate


def create_fairy_in_a_bottle():
    return PotionTemplate(
        potion_id="potion.fairy_in_a_bottle",
        name="瓶中精灵",
        description="当你要被杀死时，免死并回复到最大生命值的 30%，丢弃这瓶药水。神圣树皮不会使该药水翻倍。",
        target="self",
        quantity="rare",
        effects=[],
    )


def create_chaos_potion():
    return PotionTemplate(
        potion_id="potion.chaos",
        name="混沌药水",
        description="在所有空药水栏位中获得随机药水。可以产出另一瓶混沌药水。神圣树皮不会使该药水翻倍。",
        target="self",
        quantity="rare",
        effects=[],
    )


def create_smoke_bomb():
    return PotionTemplate(
        potion_id="potion.smoke_bomb",
        name="烟雾弹",
        description="从一场非 Boss 战斗中逃离，不获得任何奖励。使用烟雾弹逃离会正常触发战斗结束时生效的遗物。神圣树皮不会使该药水翻倍。",
        target="self",
        quantity="rare",
        effects=[],
    )
