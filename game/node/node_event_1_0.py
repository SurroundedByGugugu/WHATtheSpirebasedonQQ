# -*- coding: utf-8 -*-
# 塔1通用事件池。

import random

from game.node.node_event_0 import (
    EventChoice,
    EventState,
    EVENT_NLOTH,
    EVENT_HOLY_WATER,
    EVENT_DESIGNER,
    EVENT_DUPLICATOR,
    EVENT_FORGE,
    EVENT_BONFIRE_SPIRITS,
    EVENT_GOLDEN_SHRINE,
    EVENT_LAB,
    EVENT_PURIFIER_SHRINE,
    EVENT_TRANSFORM_SHRINE,
    EVENT_UPGRADE_SHRINE,
    EVENT_WHEEL_GAME,
    EVENT_BLUE_WOMAN,
    EVENT_FACE_TRADER,
    build_face_trader_event,
    get_ascension_level,
    has_removable_curse,
    get_non_basic_non_curse_card_indices,
    get_upgradable_cards,
)


def get_event_builders(run_state, seed=None, source_node_type="event"):
    """
    塔1通用事件池。
    第 x 层实际事件池 = 本文件通用事件 + node_event_1_x.py 本层专属事件。
    """
    builders = [
        build_nloth_event,
        build_designer_event,
        build_duplicator_event,
        build_forge_event,
        build_bonfire_spirits_event,
        build_golden_shrine_event,
        build_lab_event,
        build_purifier_shrine_event,
        build_transform_shrine_event,
        build_wheel_game_event,
        build_face_trader_event,
    ]

    if has_removable_curse(run_state):
        builders.append(build_holy_water_event)

    if get_upgradable_cards(run_state):
        builders.append(build_upgrade_shrine_event)

    if getattr(run_state, "gold", 0) >= 50:
        builders.append(build_blue_woman_event)

    # 尖端设计师：若玩家生命不足以承受“一拳过去”，则不会出现。
    punch_damage = 5 if get_ascension_level(run_state) >= 15 else 3
    if getattr(run_state, "hp", 0) <= punch_damage:
        builders = [b for b in builders if b is not build_designer_event]

    return builders


def build_nloth_event(run_state, rng=None, seed=None, source_node_type="event"):
    if rng is None:
        rng = random.Random(seed)

    relics = list(getattr(run_state, "relics", []) or [])
    indices = list(range(len(relics)))
    rng.shuffle(indices)
    chosen = indices[:2]

    choices = []
    for relic_index in chosen:
        relic = relics[relic_index]
        choices.append(EventChoice(
            "交出：【{}】。失去这件遗物。获得一件特别的遗物。".format(getattr(relic, "name", "遗物")),
            "nloth_relic",
            payload={"relic_index": relic_index},
        ))
    choices.append(EventChoice("离开。", "leave"))

    if not chosen:
        description = (
            "一个驼着背、背后长出几条触手的奇怪生物正在你面前的垃圾堆和废墟里翻找。\n"
            "“恩洛斯好饿，喂喂恩洛斯。”\n"
            "但你身上没有能喂给他的遗物。"
        )
    else:
        description = (
            "一个驼着背、背后长出几条触手的奇怪生物正在你面前的垃圾堆和废墟里翻找。\n"
            "当你靠近时，他可怜巴巴地拖着脚走到了你面前。\n"
            "“恩洛斯好饿，喂喂恩洛斯。”"
        )

    return EventState(
        title="恩洛斯",
        event_id=EVENT_NLOTH,
        description=description,
        choices=choices,
    )

def build_holy_water_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="神圣泉水",
        event_id=EVENT_HOLY_WATER,
        description="你经过墙壁上的一处饮水池，里面流淌着源源不断闪着光的水。",
        choices=[
            EventChoice("喝水。移除所有诅咒牌。", "holy_water_drink"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_designer_event(run_state, rng=None, seed=None, source_node_type="event"):
    if rng is None:
        rng = random.Random(seed)
    small_random = rng.choice([True, False])
    clean_remove = rng.choice([True, False])

    small_effect = "designer_small_random" if small_random else "designer_small_choose"
    small_text = "小修一下。失去 50 金币。{}。".format(
        "随机升级两张牌" if small_random else "选择升级一张牌"
    )

    clean_effect = "designer_clean_remove" if clean_remove else "designer_clean_transform"
    clean_text = "清洁一下。失去 75 金币。{}。".format(
        "移除 1 张牌" if clean_remove else "随机变化两张牌"
    )

    punch_damage = 5 if get_ascension_level(run_state) >= 15 else 3

    return EventState(
        title="尖端设计师",
        event_id=EVENT_DESIGNER,
        description=(
            "你发现一家五彩斑斓的店，横幅上挂着大大的“尖端”两个字，就走进去想看看里面有什么。\n"
            "“等等，别，不行，你不能进来！”\n"
            "一个穿着打扮无比荒唐的男人出现在门口把你拦了下来。\n"
            "他夸张地叹了一口气，伸手指向一张服务目录。\n"
            "服务内容看起来还挺正常的，但你现在一心只想对着这自我感觉良好的家伙得意洋洋的脸上一拳揍过去。"
        ),
        choices=[
            EventChoice(small_text, small_effect),
            EventChoice(clean_text, clean_effect),
            EventChoice("全套服务。失去 110 金币。移除一张牌，然后随机升级一张牌。", "designer_full"),
            EventChoice("一拳过去。失去 {} 点生命值。".format(punch_damage), "designer_punch"),
        ]
    )


def build_duplicator_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="复制祭坛",
        event_id=EVENT_DUPLICATOR,
        description="在你面前是一个用来崇拜某种古老存在的华丽祭坛。",
        choices=[
            EventChoice("祈祷。从你的牌组中复制一张牌。", "duplicator_pray"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_forge_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="邪恶熔炉",
        event_id=EVENT_FORGE,
        description=(
            "你钻进一个小屋，在里面似乎有一个锻造熔炉，旁边的铁匠工具都已经布满了灰尘，可是炉中的火却仍然熊熊燃烧。"
            "你觉得有些不安……"
        ),
        choices=[
            EventChoice("锻造。升级一张牌。需要：可以升级的牌。", "forge_upgrade"),
            EventChoice("翻查。获得弯曲铁钳。被诅咒——疼痛。", "forge_rummage"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_bonfire_spirits_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="篝火精灵",
        event_id=EVENT_BONFIRE_SPIRITS,
        description=(
            "你遇见一群看似是紫色火精灵的东西在一个巨大的篝火堆旁起舞。\n"
            "精灵们将小小的骨头和不知什么碎片丢进火中，每一次都会爆发出炫目的火焰。\n"
            "当你靠近时，所有精灵都转向了你，似乎在期待着些什么……"
        ),
        choices=[
            EventChoice("献上。根据献上的贡品获得相应的奖励。", "bonfire_offer"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_golden_shrine_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="金色神龛",
        event_id=EVENT_GOLDEN_SHRINE,
        description="在你面前是一座古老神灵的精巧神龛。",
        choices=[
            EventChoice("祈祷。获得 100 金币。", "golden_shrine_pray"),
            EventChoice("亵渎。获得 250 金币。被诅咒——悔恨。", "golden_shrine_desecrate"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_lab_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="实验室",
        event_id=EVENT_LAB,
        description=(
            "你发现了一个满是试管、烧杯、烧瓶、药瓶、钳子、夹子、玻璃棒、手术钳、眼镜、漏斗、吸液管、玻璃筒、冷凝器甚至还有螺旋玻璃管的房间。\n"
            "你怎么会知道这些工具都叫什么名字的？这不重要，你四处翻找了起来。"
        ),
        choices=[EventChoice("搜索。找到一些药水！", "lab_search")]
    )


def build_purifier_shrine_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="净化神龛",
        event_id=EVENT_PURIFIER_SHRINE,
        description="在你面前是一个被遗忘神灵的精致神龛。",
        choices=[
            EventChoice("祈祷。从你的牌组中移除一张牌。", "purifier_shrine_pray"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_transform_shrine_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="转化神龛",
        event_id=EVENT_TRANSFORM_SHRINE,
        description="在你面前是一个被遗忘神灵的精致神龛。",
        choices=[
            EventChoice("祈祷。变化一张牌。", "transform_shrine_pray"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_upgrade_shrine_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="升级神龛",
        event_id=EVENT_UPGRADE_SHRINE,
        description="在你面前是一个被遗忘神灵的精致神龛。",
        choices=[
            EventChoice("祈祷。升级一张牌。需要：可以升级的牌。", "upgrade_shrine_pray"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_wheel_game_event(run_state, rng=None, seed=None, source_node_type="event"):
    if rng is None:
        rng = random.Random(seed)
    intro = rng.choice([
        "“是时候转动转盘了！你准备好了吗？你当然准备好了！”",
        "“中奖概率倍儿高，奖品也嘛倍儿好，手机钞票奔驰金条，还有大金劳儿！（这对吗？！”",
        "“是时候转动转盘了！你准备好了吗？你当然准备好了！”",
        "“是时候转动转盘了！你准备好了吗？你当然准备好了！”",
    ])
    prize = rng.choice(["gold", "relic", "heal", "curse", "remove", "damage"])
    return EventState(
        title="变化大转盘",
        event_id=EVENT_WHEEL_GAME,
        description="你见到一位穿着帅气、满面笑容的地精。\n" + intro,
        choices=[EventChoice("玩小游戏。随机获得奖品。", "wheel_play", payload={"prize": prize})]
    )


def build_blue_woman_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="蓝衣女子",
        event_id=EVENT_BLUE_WOMAN,
        description=(
            "从黑暗中，一只手伸出来把你拉进了一家小店。眼睛适应了这里的亮度之后，你看见一个穿着鲜艳衣服的苍白女子正伸手展示整整一墙壁的药水。\n"
            "“来买药水，快点！”她对你说。"
        ),
        choices=[
            EventChoice("买 1 瓶药水。20 金币。", "blue_woman_buy", payload={"count": 1, "cost": 20}),
            EventChoice("买 2 瓶药水。30 金币。", "blue_woman_buy", payload={"count": 2, "cost": 30}),
            EventChoice("买 3 瓶药水。40 金币。", "blue_woman_buy", payload={"count": 3, "cost": 40}),
            EventChoice("离开。", "blue_woman_leave"),
        ]
    )

def _mark_event_builder_ids():
    mapping = {
        build_nloth_event: EVENT_NLOTH,
        build_holy_water_event: EVENT_HOLY_WATER,
        build_designer_event: EVENT_DESIGNER,
        build_duplicator_event: EVENT_DUPLICATOR,
        build_forge_event: EVENT_FORGE,
        build_bonfire_spirits_event: EVENT_BONFIRE_SPIRITS,
        build_golden_shrine_event: EVENT_GOLDEN_SHRINE,
        build_lab_event: EVENT_LAB,
        build_purifier_shrine_event: EVENT_PURIFIER_SHRINE,
        build_transform_shrine_event: EVENT_TRANSFORM_SHRINE,
        build_upgrade_shrine_event: EVENT_UPGRADE_SHRINE,
        build_wheel_game_event: EVENT_WHEEL_GAME,
        build_blue_woman_event: EVENT_BLUE_WOMAN,
    }

    for builder, event_id in mapping.items():
        setattr(builder, "event_id", event_id)


_mark_event_builder_ids()