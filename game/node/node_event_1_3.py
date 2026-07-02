# -*- coding: utf-8 -*-
# 塔1三层（深处区）事件池。
# 说明：这里的 1_3 表示“塔1 / 第三阶段”。

import random

from game.node.node_event_0 import (
    EventChoice,
    EventState,
    EVENT_MIND_BLOOM,
    EVENT_SECRET_PORTAL,
    EVENT_SENSORY_STONE,
    EVENT_FALLING,
    EVENT_MOAI_HEAD,
    EVENT_MYSTERIOUS_SPHERE,
    EVENT_TOMB_RED_MASK,
    EVENT_WINDING_HALLS,
    build_mind_bloom_event,
    get_ascension_level,
    has_relic,
)


def _rng(rng=None, seed=None):
    if rng is not None:
        return rng
    return random.Random(seed)


def _card_type_name(card_type):
    return {
        "attack": "攻击牌",
        "skill": "技能牌",
        "power": "能力牌",
    }.get(card_type, card_type)


def _pick_random_deck_card_by_type(run_state, card_type, rng):
    candidates = []
    for index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if getattr(card, "card_type", "") != card_type:
            continue
        if getattr(card, "unremovable", False):
            continue
        candidates.append((index, card))
    return rng.choice(candidates) if candidates else None


def get_event_builders(run_state, seed=None, source_node_type="event"):
    """
    返回塔1三层事件构造器。
    """
    builders = [
        build_mind_bloom_event,
        build_secret_portal_event,
        build_sensory_stone_event,
        build_falling_event,
        build_mysterious_sphere_event,
        build_tomb_red_mask_event,
        build_winding_halls_event,
    ]

    # 摩艾石像：有金神像，或当前生命少于 50% 最大生命时才进入池。
    max_hp = int(getattr(run_state, "max_hp", 0) or 0)
    hp = int(getattr(run_state, "hp", 0) or 0)
    if has_relic(run_state, "relic.golden_idol") or (max_hp > 0 and hp * 2 < max_hp):
        builders.append(build_moai_head_event)

    return builders


def build_secret_portal_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="秘密传送门",
        event_id=EVENT_SECRET_PORTAL,
        description=(
            "在你面前有一样与周围奇异景观完全不符合的东西：在深处地区一面活墙壁上，"
            "奇怪地出现了一道石做的拱门，里面有一个旋转的魔法传送门。\n\n"
            "你不知道它会通向哪里，但它应该能够节约你爬塔的时间。"
        ),
        choices=[
            EventChoice("进入传送门。立即传送到 Boss 房间。", "secret_portal_enter"),
            EventChoice("离开。", "leave"),
        ],
    )


def build_sensory_stone_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="感知石",
        event_id=EVENT_SENSORY_STONE,
        description=(
            "你在高塔深处前进时，遇到一个悬浮在空中缓慢旋转且变幻着的发光超立方体。\n"
            "你触碰了超立方体。\n\n"
            "你浑身感到一股剧烈的疼痛，然后一段遥远的回忆清晰地闪现在你的脑中。\n"
            "……这是谁的记忆？"
        ),
        choices=[
            EventChoice("回忆。在你的牌组中加入 1 张无色牌。", "sensory_stone_cards", payload={"count": 1, "hp_loss": 0}),
            EventChoice("交互。在你的牌组中加入 2 张无色牌。失去 5 点生命。", "sensory_stone_cards", payload={"count": 2, "hp_loss": 5}),
            EventChoice("交互。在你的牌组中加入 3 张无色牌。失去 10 点生命。", "sensory_stone_cards", payload={"count": 3, "hp_loss": 10}),
        ],
    )


def build_falling_event(run_state, rng=None, seed=None, source_node_type="event"):
    rng = _rng(rng, seed)

    skill_pick = _pick_random_deck_card_by_type(run_state, "skill", rng)
    power_pick = _pick_random_deck_card_by_type(run_state, "power", rng)
    attack_pick = _pick_random_deck_card_by_type(run_state, "attack", rng)

    def make_choice(label, card_type, picked, effect):
        if picked is None:
            return EventChoice(
                "{}。需要：{}。".format(label, _card_type_name(card_type)),
                effect,
                payload={"deck_index": -1, "card_type": card_type},
            )

        deck_index, card = picked
        return EventChoice(
            "{}。失去【{}】。".format(label, getattr(card, "name", "未知卡牌")),
            effect,
            payload={"deck_index": deck_index, "card_type": card_type},
        )

    return EventState(
        title="坠落",
        event_id=EVENT_FALLING,
        description=(
            "你在悬浮在空中的平台上往上跳跃时，不慎滑了一跤。\n"
            "你开始坠落。\n\n"
            "在摔下的途中，你开始考虑自己有什么选择：\n"
            "用你最好的技术安全落地。\n"
            "释放能力牌的力量来抵御伤害。\n"
            "对墙壁猛击，让自己不再下坠。"
        ),
        choices=[
            make_choice("落地", "skill", skill_pick, "falling_lose_card"),
            make_choice("释放", "power", power_pick, "falling_lose_card"),
            make_choice("猛击", "attack", attack_pick, "falling_lose_card"),
        ],
    )


def build_moai_head_event(run_state, rng=None, seed=None, source_node_type="event"):
    asc = get_ascension_level(run_state)
    max_hp_loss_percent = 0.18 if asc >= 15 else 0.125
    max_hp_loss_text = "18%" if asc >= 15 else "12.5%"

    choices = [
        EventChoice(
            "跳进去。回复所有生命。失去 {} 最大生命。".format(max_hp_loss_text),
            "moai_jump",
            payload={"percent": max_hp_loss_percent},
        )
    ]

    if has_relic(run_state, "relic.golden_idol"):
        choices.append(EventChoice("献上：金神像。得到 333 金币。失去金神像。", "moai_golden_idol"))
    else:
        choices.append(EventChoice("献上：金神像。需要：金神像。", "moai_golden_idol"))

    choices.append(EventChoice("离开。", "leave"))

    return EventState(
        title="摩艾石像",
        event_id=EVENT_MOAI_HEAD,
        description=(
            "你遇到了一个和四周完全不搭的东西。在你面前有一道与周围不同、没有在移动和变化的墙壁，"
            "一个巨大的石制头像从墙壁上凸出来。\n\n"
            "石像的嘴大张着，里面有许多巨大的染着血迹的牙齿。石像表面上写着许多象形文字，"
            "似乎是说有许多人会自己跳进嘴里被石像吞噬。为什么会有人这样做呢？"
        ),
        choices=choices,
    )


def build_mysterious_sphere_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="神秘圆球",
        event_id=EVENT_MYSTERIOUS_SPHERE,
        description=(
            "在四周混乱的地形中间，一个骨质圆球伫立在地上，似乎包裹着一样神秘的发光物体。\n"
            "你很好奇里面有什么东西，但你注意到圆球周围有一些哨兵正在看守。"
        ),
        choices=[
            EventChoice("打开圆球。战斗。奖励：稀有遗物。", "mysterious_sphere_open"),
            EventChoice("离开。", "leave"),
        ],
    )


def build_tomb_red_mask_event(run_state, rng=None, seed=None, source_node_type="event"):
    choices = []

    if has_relic(run_state, "relic.red_mask"):
        choices.append(EventChoice("戴上红面具。获得 222 金币。", "tomb_red_mask_wear"))
    else:
        choices.append(EventChoice("戴上红面具。需要：红面具。", "tomb_red_mask_wear"))

    choices.extend([
        EventChoice("献上：所有金币。失去所有金币。获得遗物红面具。", "tomb_red_mask_offer_gold"),
        EventChoice("离开。", "leave"),
    ])

    return EventState(
        title="红面具大人之墓",
        event_id=EVENT_TOMB_RED_MASK,
        description=(
            "在一条悬浮道路的尽头，你可以看见一处装饰华丽的古墓。"
            "当你到达古墓时，你看到有一个可以投放金币的开口，"
            "但上面的铭文已经被划得看不清楚了。"
        ),
        choices=choices,
    )


def build_winding_halls_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="蜿蜒走廊",
        event_id=EVENT_WINDING_HALLS,
        description=(
            "你沿着弯曲的道路慢慢前进，却多次发现自己迷失了方向，仿佛墙壁和地面就在你的眼前突然移动了位置。\n\n"
            "更糟糕的是，你的脑中似乎还有许多声音在对你轻声低语。"
        ),
        choices=[
            EventChoice("......", "winding_halls_next"),
        ],
    )


build_mind_bloom_event.__event_id__ = EVENT_MIND_BLOOM
build_secret_portal_event.__event_id__ = EVENT_SECRET_PORTAL
build_sensory_stone_event.__event_id__ = EVENT_SENSORY_STONE
build_falling_event.__event_id__ = EVENT_FALLING
build_moai_head_event.__event_id__ = EVENT_MOAI_HEAD
build_mysterious_sphere_event.__event_id__ = EVENT_MYSTERIOUS_SPHERE
build_tomb_red_mask_event.__event_id__ = EVENT_TOMB_RED_MASK
build_winding_halls_event.__event_id__ = EVENT_WINDING_HALLS