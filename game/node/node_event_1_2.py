# -*- coding: utf-8 -*-
# 塔1二层（城市区）事件池。
# 说明：这里的 1_2 表示“塔1 / 第二阶段”，不是 route 的第 2 层地图节点。

import random

from game.node.node_event_0 import (
    EventChoice,
    EventState,
    EVENT_NLOTH,
    EVENT_NEST,
    EVENT_HOBO,
    EVENT_ANCIENT_WRITING,
    EVENT_OLD_BEGGAR,
    EVENT_FORGOTTEN_ALTAR,
    EVENT_KNOWING_SKULL,
    EVENT_MASKED_BANDITS,
    EVENT_JOUST,
    EVENT_GREAT_LIBRARY,
    EVENT_MAUSOLEUM,
    EVENT_VAMPIRES,
    EVENT_GHOST_COUNCIL,
    EVENT_ARENA,
    build_cursed_tome_event,
    build_augmenter_event,
    get_ascension_level,
    get_current_floor,
    has_relic,
)


def _rng(rng=None, seed=None):
    if rng is not None:
        return rng
    return random.Random(seed)


def _relic_count(run_state):
    return len(getattr(run_state, "relics", []) or [])


def get_event_builders(run_state, seed=None, source_node_type="event"):
    """
    返回塔1二层事件构造器。

    node_event_1_0.py 会作为塔1通用事件池额外加载，
    因此这里不重复加入换脸商，避免概率被重复抬高。
    """
    builders = [
        build_cursed_tome_event,
        build_augmenter_event,

        build_nest_event,
        build_hobo_event,
        build_ancient_writing_event,
        build_forgotten_altar_event,
        build_knowing_skull_event,
        build_masked_bandits_event,
        build_great_library_event,
        build_mausoleum_event,
        build_vampires_event,
        build_ghost_council_event,
    ]

    if _relic_count(run_state) >= 2:
        builders.append(build_nloth_event)

    if int(getattr(run_state, "gold", 0) or 0) >= 75:
        builders.append(build_old_beggar_event)

    if int(getattr(run_state, "gold", 0) or 0) >= 50:
        builders.append(build_joust_event)

    # 二层后半段。当前 Act2 仍然用 floor 记录 1..15，约定 7 层及以后开放。
    if get_current_floor(run_state) >= 7:
        builders.append(build_arena_event)

    return builders


def build_nloth_event(run_state, rng=None, seed=None, source_node_type="event"):
    rng = _rng(rng, seed)

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

    return EventState(
        title="恩洛斯",
        event_id=EVENT_NLOTH,
        description=(
            "一个驼着背、背后长出几条触手的奇怪生物正在你面前的垃圾堆和废墟里翻找。\n"
            "当你靠近时，他可怜巴巴地拖着脚走到了你面前。\n"
            "“恩洛斯好饿，喂喂恩洛斯。”"
        ),
        choices=choices,
    )


def build_nest_event(run_state, rng=None, seed=None, source_node_type="event"):
    asc = get_ascension_level(run_state)
    gold_amount = 50 if asc >= 15 else 99

    return EventState(
        title="巢穴",
        event_id=EVENT_NEST,
        description=(
            "你看到一长串戴着兜帽的人们正鱼贯走进一座看起来没什么特别的大教堂。\n\n"
            "于是你理所当然地加入了队伍里，很快你的周围就站满了邪教徒！"
            "他们似乎没有发现你，只是兴奋地挥舞着自己的武器并喜悦地呼喊着些什么。\n"
            "“杀！杀~杀杀杀！！”\n"
            "“咔~咔~咔-咔！”\n"
            "“杀！杀~杀杀杀！！”\n"
            "“咔~咔~咔-咔！”\n\n"
            "你看到前面有一个捐款箱。"
        ),
        choices=[
            EventChoice("抢了钱就跑。获得 {} 金币。".format(gold_amount), "nest_rob", payload={"gold": gold_amount}),
            EventChoice("留在队伍中。获得仪式匕首，失去 6 生命。", "nest_stay"),
        ],
    )


def build_hobo_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="流浪汉的恳求",
        event_id=EVENT_HOBO,
        description=(
            "你想要从一群披着斗篷的人旁边偷偷潜行过去，这时一个皮肤发红的赤裸男人跑到了你的面前。\n"
            "“你能给我点儿什么吗,朋友？求求你了……一点小钱就好？”\n\n"
            "“我只是需要找个地方过夜，我身上有财宝可以交换……”\n"
            "他看起来疯疯癫癫的，但并没有危险。"
        ),
        choices=[
            EventChoice("给他金币。85 金币：得到一件遗物。需要：85 金币。", "hobo_pay", amount=85),
            EventChoice("抢夺。获得一件遗物。被诅咒——羞耻。", "hobo_rob"),
            EventChoice("离开。", "leave"),
        ],
    )


def build_ancient_writing_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="古老文字",
        event_id=EVENT_ANCIENT_WRITING,
        description=(
            "在攀爬城市区时，你注意到一面墙壁上写满了先古之民的文字。"
            "你正在努力推理这些奇怪的符号和图案可能的意思，却发现文字开始发起了光。\n"
            "突然之间，文字的意义变得清晰了……"
        ),
        choices=[
            EventChoice("简约。从你的牌组中移除一张牌。", "ancient_writing_remove"),
            EventChoice("质朴。升级所有打击与防御。", "ancient_writing_upgrade"),
        ],
    )


def build_old_beggar_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="老乞丐",
        event_id=EVENT_OLD_BEGGAR,
        description="一个裹着毛衣的老乞丐在你经过时向你伸出了双手，他对你说：“施舍点钱吧，孩子？”",
        choices=[
            EventChoice("给金币。失去 75 金币：从你的牌组中移除一张牌。需要：75 金币。", "old_beggar_pay", amount=75),
            EventChoice("离开。", "old_beggar_leave"),
        ],
    )


def build_forgotten_altar_event(run_state, rng=None, seed=None, source_node_type="event"):
    asc = get_ascension_level(run_state)
    hp_percent = 35 if asc >= 15 else 25

    choices = []

    if has_relic(run_state, "relic.golden_idol"):
        choices.append(EventChoice(
            "献上：金神像。得到一件特别的遗物。失去金神像。",
            "forgotten_altar_idol",
        ))
    else:
        choices.append(EventChoice(
            "献上：金神像。需要：金神像。",
            "forgotten_altar_idol",
        ))

    choices.extend([
        EventChoice(
            "献祭。获得 5 点最大生命。失去 {}% 生命。".format(hp_percent),
            "forgotten_altar_sacrifice",
            payload={"percent": hp_percent / 100.0},
        ),
        EventChoice("亵渎。被诅咒——腐朽。", "forgotten_altar_deface"),
    ])

    return EventState(
        title="被遗忘的祭坛",
        event_id=EVENT_FORGOTTEN_ALTAR,
        description=(
            "在你面前是一个早已被遗忘的神祇的祭坛。\n"
            "在祭坛上方，是一尊双手伸出的精致女性雕像。\n"
            "她呼唤着你，要求你献上祭品。"
        ),
        choices=choices,
    )


def build_knowing_skull_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="全知头骨",
        event_id=EVENT_KNOWING_SKULL,
        description=(
            "你发现自己在一个古老的有装饰的房间里，在房间正中央，有一个巨大的头骨被放在精致的高台上，"
            "在你靠近时，头骨迸发出火焰转向了你。\n"
            "“你想寻找什么？你会献出什么？”\n"
            "它的话音刚落，你背后的门就砰地关上了。"
        ),
        data={"uses": 0},
        choices=[
            EventChoice("来点喝的？得到一瓶药水。失去 6 生命。", "skull_potion"),
            EventChoice("财富？获得 90 金币。失去 6 生命。", "skull_gold"),
            EventChoice("成功？得到一张罕见无色牌。失去 6 生命。", "skull_card"),
        ],
    )


def build_masked_bandits_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="蒙面强盗",
        event_id=EVENT_MASKED_BANDITS,
        description=(
            "你遇见一群戴着巨大红面具的强盗。\n"
            "“你好啊，留下买路钱……价格公道，只要你身上所有的金币就行！嘿嘿嘿！”"
        ),
        choices=[
            EventChoice("付钱。失去所有金币。", "masked_bandits_pay"),
            EventChoice("战斗。与尖尖、罗密欧、熊战斗。胜利后获得红面具。", "masked_bandits_fight"),
        ],
    )


def build_joust_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="长枪决斗",
        event_id=EVENT_JOUST,
        description=(
            "你在巨大的建筑物间穿行时，遇见了一条长长的窄桥，两头似乎都有一名骑士彼此对望着。\n"
            "“决斗的见证者啊，你为什么不赌一赌最后谁会获得胜利呢？”"
        ),
        choices=[
            EventChoice("凶手。赌 50 金币——70%：赢得 100 金币。", "joust_murderer", amount=50),
            EventChoice("主人。赌 50 金币——30%：赢得 250 金币。", "joust_owner", amount=50),
        ],
    )


def build_great_library_event(run_state, rng=None, seed=None, source_node_type="event"):
    sleep_line = "傻子才读书呢。"
    if getattr(run_state, "character_id", "") == "character.yoirine":
        sleep_line = "你真的感觉很累。"

    return EventState(
        title="大图书馆",
        event_id=EVENT_GREAT_LIBRARY,
        description=(
            "你经过一栋被遗弃的华美建筑物。\n"
            "墙上的标牌掉在了地上，上面写着“大图书馆”几个大字。\n"
            "你走进建筑物中，看见了无数卷轴、手稿和书籍。"
        ),
        data={"sleep_line": sleep_line},
        choices=[
            EventChoice("阅读。从 20 张牌中选择一张加入你的牌组。", "great_library_read"),
            EventChoice("睡觉。回复 33% 生命。", "great_library_sleep"),
        ],
    )


def build_mausoleum_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="陵墓",
        event_id=EVENT_MAUSOLEUM,
        description=(
            "你在一系列坟墓间穿行，前方出现了一个圆形房间，中间是一口镶嵌着许多宝石的巨大石棺。\n"
            "你辨认不出石棺上的字迹，但你能注意到有黑色的雾气从石棺的两侧渗透出来。"
        ),
        choices=[
            EventChoice("打开棺材。得到一件遗物。50%：被诅咒——苦恼。", "mausoleum_open"),
            EventChoice("离开。", "leave"),
        ],
    )


def build_vampires_event(run_state, rng=None, seed=None, source_node_type="event"):
    choices = [
        EventChoice(
            "接受。移除所有打击牌。获得 5 张噬咬牌。失去 30% 最大生命。",
            "vampires_accept",
        ),
    ]

    if has_relic(run_state, "relic.blood_vial"):
        choices.append(EventChoice(
            "失去小血瓶。移除所有打击牌。获得等量的噬咬。",
            "vampires_blood_vial",
        ))

    choices.append(EventChoice("拒绝。", "leave"))

    return EventState(
        title="吸血鬼（？）",
        event_id=EVENT_VAMPIRES,
        description=(
            "在一条昏暗的街上，你遇见几个戴着兜帽的人在进行某种黑暗的仪式。\n"
            "其中个子最高的一个微微一笑，露出了长长的尖牙，向你伸出了一只苍白而瘦长的手：\n"
            "“加入我们。一起来感受高塔的温暖吧。”"
        ),
        choices=choices,
    )


def build_ghost_council_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="幽灵议会",
        event_id=EVENT_GHOST_COUNCIL,
        description=(
            "在你向上攀升时，突然四周的墙壁和地面开始冒出浓重的黑烟，逐渐聚成了三个戴着面具的形状。\n"
            "第三个存在有着巨大的嘴，它露出了一个大到夸张的微笑对你说：\n"
            "“总之你想不想尝试一下我们的力量呢?”"
        ),
        choices=[
            EventChoice("接受。获得 5 张灵体牌。失去 50% 的最大生命值。", "ghost_council_accept"),
            EventChoice("拒绝。", "ghost_council_refuse"),
        ],
    )


def build_arena_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="竞技场",
        event_id=EVENT_ARENA,
        description=(
            "哐！！！\n…\n…………\n……\n你被打晕了……\n\n"
            "你悠悠醒转，发现自己正处于一座巨大竞技场的中央，观众席上挤满了奴隶贩子、邪教徒和城市区的其它居民们！\n"
            "一个头戴金冠的重甲巨人伫立在上方，他对你咆哮：“那么现在，就让我们开始第4200轮战斗！！！！”\n"
            "在你对面的大门缓缓打开了……"
        ),
        choices=[
            EventChoice("开始战斗。强制与蓝奴隶主和红奴隶主战斗。", "arena_start"),
        ],
    )


def build_arena_after_first_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="竞技场",
        event_id=EVENT_ARENA,
        description=(
            "“打得不错，弱者啊！”\n"
            "那名巨人假装鼓了鼓掌，用夸张的手势开始鼓动起观众们。\n"
            "金币和彩纸从天而降洒落在你身旁！\n"
            "“接下来才是真正的挑战！！”\n\n"
            "上一场战斗在竞技场的围墙上留下了一个小小的缺口，你完全有机会在众人们没留意时从那里逃出去。\n"
            "你想要留下来继续战斗吗？"
        ),
        choices=[
            EventChoice("怂了。逃跑，避免下一场战斗。", "arena_coward"),
            EventChoice("继续。开始一场艰难的战斗，赢得众多奖赏。", "arena_continue"),
        ],
    )


build_nloth_event.__event_id__ = EVENT_NLOTH
build_nest_event.__event_id__ = EVENT_NEST
build_hobo_event.__event_id__ = EVENT_HOBO
build_ancient_writing_event.__event_id__ = EVENT_ANCIENT_WRITING
build_old_beggar_event.__event_id__ = EVENT_OLD_BEGGAR
build_forgotten_altar_event.__event_id__ = EVENT_FORGOTTEN_ALTAR
build_knowing_skull_event.__event_id__ = EVENT_KNOWING_SKULL
build_masked_bandits_event.__event_id__ = EVENT_MASKED_BANDITS
build_joust_event.__event_id__ = EVENT_JOUST
build_great_library_event.__event_id__ = EVENT_GREAT_LIBRARY
build_mausoleum_event.__event_id__ = EVENT_MAUSOLEUM
build_vampires_event.__event_id__ = EVENT_VAMPIRES
build_ghost_council_event.__event_id__ = EVENT_GHOST_COUNCIL
build_arena_event.__event_id__ = EVENT_ARENA