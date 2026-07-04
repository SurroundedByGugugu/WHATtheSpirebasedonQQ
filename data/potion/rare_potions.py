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

def create_cultist_potion():
    return PotionTemplate(
        potion_id="potion.cultist",
        name="邪教徒药水",
        description="获得 1 层仪式。",
        target="self",
        quantity="rare",
        effect_vars={"ritual": 1},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "ritual",
                "amount": {"var": "ritual"}
            }
        ],
    )


def create_fruit_juice():
    return PotionTemplate(
        potion_id="potion.fruit_juice",
        name="果汁",
        description="获得 5 点最大生命。药水栏已满时，可在奖励列表中直接喝掉。",
        target="self",
        quantity="rare",
        effect_vars={"max_hp": 5},
        effects=[
            {
                "op": "increase_player_max_hp",
                "amount": {"var": "max_hp"}
            }
        ],
    )


def create_ghost_in_a_jar():
    return PotionTemplate(
        potion_id="potion.ghost_in_a_jar",
        name="罐装幽灵",
        description="获得 1 层无实体。",
        target="self",
        quantity="rare",
        effect_vars={"intangible": 1},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "intangible",
                "amount": {"var": "intangible"}
            }
        ],
    )


def create_heart_of_iron():
    return PotionTemplate(
        potion_id="potion.heart_of_iron",
        name="铁之心",
        description="获得 6 层金属化。",
        target="self",
        quantity="rare",
        effect_vars={"metallicize": 6},
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "metallicize",
                "amount": {"var": "metallicize"}
            }
        ],
    )


def create_snecko_oil():
    return PotionTemplate(
        potion_id="potion.snecko_oil",
        name="异蛇之油",
        description="抽 5 张牌。随机化你手牌的耗能。",
        target="self",
        quantity="rare",
        effect_vars={"draw": 5},
        effects=[
            {
                "op": "draw_cards",
                "amount": {"var": "draw"}
            },
            {
                "op": "randomize_hand_costs"
            },
        ],
    )