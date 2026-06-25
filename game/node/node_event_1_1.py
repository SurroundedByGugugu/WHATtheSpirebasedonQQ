# -*- coding: utf-8 -*-
# 塔1一层专属事件池。当前从旧 node_event_0.py 迁移而来。

from game.node.node_event_0 import (
    EventChoice,
    EventState,
    EVENT_BIG_FISH,
    EVENT_CLERIC,
    EVENT_GOLDEN_IDOL,
    EVENT_WING_STATUE,
    EVENT_SLIME_WORLD,
    EVENT_SERPENT,
    EVENT_LIVING_WALL,
    EVENT_MUSHROOMS,
    EVENT_SCRAP_OOZE,
    EVENT_SHINING_LIGHT,
    EVENT_ADVENTURER_CORPSE,
    get_current_floor,
)


def get_event_builders(run_state, seed=None, source_node_type="event"):
    """
    返回塔1一层专属事件构造器。
    后续如果要做塔1二层事件，新建 node_event_1_2.py，并提供同名函数即可。
    """
    builders = [
        build_big_fish_event,
        build_golden_idol_event,
        build_wing_statue_event,
        build_slime_world_event,
        build_serpent_event,
        build_living_wall_event,
        build_mushrooms_event,
        build_scrap_ooze_event,
        build_shining_light_event,
    ]

    if getattr(run_state, "gold", 0) >= 35:
        builders.append(build_cleric_event)

    if get_current_floor(run_state) >= 6:
        builders.append(build_adventurer_corpse_event)

    return builders


def build_big_fish_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="大鱼",
        event_id=EVENT_BIG_FISH,
        description=(
            "当你走过一条长廊时，你看见空中漂浮着一根香蕉，一个甜甜圈，和一个盒子。\n"
            "不……仔细一看，它们都是被用绳子系着，从天花板上的几个洞里悬挂下来的。\n"
            "你在接近这几样东西时，上方似乎传来一阵咯咯的笑声。\n"
            "你会怎么做？"
        ),
        choices=[
            EventChoice("香蕉。回复最大生命值的 1/3。", "big_fish_banana"),
            EventChoice("甜甜圈。最大生命值 +5。", "big_fish_donut", amount=5),
            EventChoice("盒子。获得一件遗物。被诅咒——悔恨。", "big_fish_box"),
        ]
    )


def build_cleric_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="牧师",
        event_id=EVENT_CLERIC,
        description=(
            "一个戴着金头盔（？）的奇怪蓝色人形生物脸上带着大大的微笑走到了你面前。\n"
            "“你好啊朋友！我是牧师！你想不想试试我的服务呐？！”那个生物大声喊叫起来。"
        ),
        choices=[
            EventChoice("治疗。35 金币：回复 25% 生命。需要：35 金币。", "cleric_heal"),
            EventChoice("净化。50 金币：从你的牌组中移除一张牌。需要：50 金币。", "cleric_purge"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_golden_idol_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="金神像",
        event_id=EVENT_GOLDEN_IDOL,
        description=(
            "在一个不引人注意的小高台上，你发现了一个闪闪发光的金神像安然放置在上面，看起来非常值钱。\n"
            "周围看起来完全没有什么陷阱的样子。"
        ),
        choices=[
            EventChoice("拿走。得到金神像。触发一个陷阱。", "golden_idol_take"),
            EventChoice("离开。", "golden_idol_leave"),
        ]
    )


def build_wing_statue_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="翅膀雕像",
        event_id=EVENT_WING_STATUE,
        description=(
            "在形状不同的巨石之间，你看见一尊做工精细的翅膀形状的蓝色雕像。\n"
            "你可以看见雕像的裂缝中有金币掉出来。或许里面还有更多……"
        ),
        choices=[
            EventChoice("祈祷。从你的牌组中移除一张牌。失去 7 生命。", "wing_pray"),
            EventChoice("摧毁。获得 50-80 金币。需要：伤害等于或超过 10 的牌。", "wing_destroy"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_slime_world_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="黏液世界",
        event_id=EVENT_SLIME_WORLD,
        description=(
            "你掉进了一个水坑里。\n可是坑里全是史莱姆黏液！\n"
            "你感觉到这黏液似乎会灼伤你，便拼命想要从坑中脱身。\n"
            "你的耳朵、鼻子和全身都被黏液给浸透了。\n"
            "爬出来后，你发现自己的金币似乎变少了。你回头一看，发现水坑里不但有你掉落的钱，还有不少其他不幸的冒险者们落下的金币。"
        ),
        choices=[
            EventChoice("收集金币。获得 75 金币。失去 11 生命。", "slime_world_collect"),
            EventChoice("放手吧。失去 20~50 金币。", "slime_world_let_go"),
        ]
    )


def build_serpent_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="蛇～",
        event_id=EVENT_SERPENT,
        description=(
            "你走进一间房间，看见地上有一个大洞。当你靠近洞时，一条巨大的蛇形生物从里面钻了出来。\n"
            "“嚯嚯嚯！你好，你好啊！这是谁呀？哎呀呀，你好冒险者，我就问一个简单的问题。\n"
            "最幸福的人生当然就是什么东西都能买得起的土豪生活了！　\n你同意吗？”"
        ),
        choices=[
            EventChoice("同意。得到 175 金币。被诅咒——疑虑。", "serpent_agree"),
            EventChoice("反对。", "serpent_disagree"),
        ]
    )


def build_living_wall_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="活墙壁",
        event_id=EVENT_LIVING_WALL,
        description=(
            "你走进一条死路，正准备要回头时，四周突然有墙壁从天花板上哐地一下砸了下来！\n"
            "三张脸出现在墙壁上，开始对你说话：\n"
            "“忘记你所知道的，我就让你走。”\n"
            "“有所改变，我就让你看见新的道路。”\n"
            "“如果你想要从我这里通过，你就必须有所成长。”"
        ),
        choices=[
            EventChoice("遗忘。移除你牌组中的一张牌。", "living_wall_forget"),
            EventChoice("改变。变化你牌组中的一张牌。", "living_wall_change"),
            EventChoice("成长。升级你牌组中的一张牌。需要：可以升级的牌。", "living_wall_grow"),
        ]
    )


def build_mushrooms_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="蘑菇",
        event_id=EVENT_MUSHROOMS,
        description=(
            "你走进一条遍地是五彩斑斓蘑菇的走廊，\n"
            "由于你对真菌学毫无研究，你无法辨识它们的种类。\n"
            "你想要离开这里，但却有一种奇怪的冲动想要去吃一个蘑菇……"
        ),
        choices=[
            EventChoice("踩扁。激怒蘑菇们。", "mushrooms_stomp"),
            EventChoice("吃下。回复 25% 生命。被诅咒——寄生。", "mushrooms_eat"),
        ]
    )


def build_scrap_ooze_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="破烂软泥",
        event_id=EVENT_SCRAP_OOZE,
        description=(
            "你刚走进房间，就听见奇怪的咕嘟声和金属的摩擦声。在你面前的是一个史莱姆状的生物，它显然是吃了太多的破铜烂铁，消化不良了。\n"
            "你在这个生物的中央见到了奇怪的光芒，或许是什么有魔法的物品？看起来只要你愿意把手伸进这东西的……开口，你就能得到什么财宝。当然，酸液和尖锐的破烂有可能会让你受伤。"
        ),
        choices=[
            EventChoice("伸手进去。失去 3 生命。25%：找到一件遗物。", "scrap_ooze_reach"),
            EventChoice("离开。", "leave"),
        ],
        data={"attempts": 0}
    )


def build_shining_light_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="闪耀之光",
        event_id=EVENT_SHINING_LIGHT,
        description=(
            "你发现在房间中央围绕着一束很粗的光柱。\n"
            "光柱上有着温暖而闪烁的美丽花纹仿佛在邀请你进入。"
        ),
        choices=[
            EventChoice("走进。随机升级 2 张牌。失去（20%×最大生命值）的生命。需要：可以升级的牌。", "shining_light_enter"),
            EventChoice("离开。", "leave"),
        ]
    )


def build_adventurer_corpse_event(run_state, rng=None, seed=None, source_node_type="event"):
    if rng is None:
        import random
        rng = random.Random(seed)

    variants = [
        {
            "clue": "他的护甲和脸似乎被火焰灼烧过。",
            "encounter_id": "encounter.elite.sentries_bab",
            "monster_name": "哨卫",
        },
        {
            "clue": "看起来他被一个带角的生物戳伤和踩踏过。",
            "encounter_id": "encounter.elite.gremlin_nob",
            "monster_name": "地精大块头",
        },
        {
            "clue": "他的内脏似乎被巨大的爪子撕扯出来并切碎了。",
            "encounter_id": "encounter.event.lagavulin_awake",
            "monster_name": "乐加维林",
        },
    ]
    try:
        from data.content_gate import is_content_enabled
        from data.route.encounters import get_encounter_seen_key
        enabled_variants = [
            variant for variant in variants
            if is_content_enabled("encounter", variant["encounter_id"])
        ]
        variants = enabled_variants or variants
        seen_elites = set(getattr(run_state, "seen_elite_encounter_ids", []) or [])
        unseen_variants = [
            variant for variant in variants
            if get_encounter_seen_key(variant["encounter_id"]) not in seen_elites
        ]
        variant = rng.choice(unseen_variants or variants)
    except Exception:
        variant = rng.choice(variants)

    return EventState(
        title="冒险者尸体",
        event_id=EVENT_ADVENTURER_CORPSE,
        description=(
            "你发现地上有一具冒险者尸体。\n"
            "他的裤子都被偷了！而且，{}\n"
            "尽管他随身携带的东西好像都还在，你实在是不想知道这里究竟发生了什么……"
        ).format(variant["clue"]),
        choices=[
            EventChoice("搜索。寻找东西。25%：遇见回来的怪物。", "corpse_search"),
            EventChoice("离开。", "corpse_leave"),
        ],
        data={
            "attempts": 0,
            "remaining_rewards": ["gold", "nothing", "relic"],
            "encounter_id": variant["encounter_id"],
            "monster_name": variant["monster_name"],
        }
    )

def _mark_event_builder_ids():
    mapping = {
        build_big_fish_event: EVENT_BIG_FISH,
        build_cleric_event: EVENT_CLERIC,
        build_golden_idol_event: EVENT_GOLDEN_IDOL,
        build_wing_statue_event: EVENT_WING_STATUE,
        build_slime_world_event: EVENT_SLIME_WORLD,
        build_serpent_event: EVENT_SERPENT,
        build_living_wall_event: EVENT_LIVING_WALL,
        build_mushrooms_event: EVENT_MUSHROOMS,
        build_scrap_ooze_event: EVENT_SCRAP_OOZE,
        build_shining_light_event: EVENT_SHINING_LIGHT,
        build_adventurer_corpse_event: EVENT_ADVENTURER_CORPSE,
    }

    for builder, event_id in mapping.items():
        setattr(builder, "event_id", event_id)


_mark_event_builder_ids()
