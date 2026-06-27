# -*- coding: utf-8 -*-
# 事件底层 / 模板 / 调度入口。

import random
import importlib
from dataclasses import dataclass, field
from typing import Any, List, Dict

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import has_upgrade, upgrade_card
from data.content_gate import is_content_enabled
from data.relic.AAAregistry import create_relic
from game.command_help import command_tip
from game.deck_utils import remove_card_from_master_deck, transform_card_in_master_deck
from game.node.node_rest import get_upgradable_cards
from game.relic_logic.bottle_utils import copy_bottled_flags, strip_bottled_flags
from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics, gain_gold_with_relics, increase_max_hp, try_block_curse_with_omamori, heal_run_hp_with_relics
from game.reward import get_available_relic_ids, create_potion_reward_state, record_reward_options_offered


@dataclass
class EventChoice:
    title: str
    effect_type: str
    amount: int = 0
    payload: Any = None


@dataclass
class EventState:
    title: str
    description: str
    choices: List[EventChoice] = field(default_factory=list)
    event_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


EVENT_BIG_FISH = "event.big_fish"
EVENT_CLERIC = "event.cleric"
EVENT_GOLDEN_IDOL = "event.golden_idol"
EVENT_WING_STATUE = "event.wing_statue"
EVENT_SLIME_WORLD = "event.slime_world"
EVENT_SERPENT = "event.serpent"
EVENT_LIVING_WALL = "event.living_wall"
EVENT_MUSHROOMS = "event.mushrooms"
EVENT_SCRAP_OOZE = "event.scrap_ooze"
EVENT_SHINING_LIGHT = "event.shining_light"
EVENT_ADVENTURER_CORPSE = "event.adventurer_corpse"

# 塔1通用事件
EVENT_NLOTH = "event.nloth"
EVENT_HOLY_WATER = "event.holy_water"
EVENT_DESIGNER = "event.designer"
EVENT_DUPLICATOR = "event.duplicator"
EVENT_FORGE = "event.forge"
EVENT_BONFIRE_SPIRITS = "event.bonfire_spirits"
EVENT_GOLDEN_SHRINE = "event.golden_shrine"
EVENT_LAB = "event.lab"
EVENT_PURIFIER_SHRINE = "event.purifier_shrine"
EVENT_TRANSFORM_SHRINE = "event.transform_shrine"
EVENT_UPGRADE_SHRINE = "event.upgrade_shrine"
EVENT_WHEEL_GAME = "event.wheel_game"
EVENT_BLUE_WOMAN = "event.blue_woman"
EVENT_CURSED_TOME = "event.cursed_tome"
EVENT_MIND_BLOOM = "event.mind_bloom"
EVENT_FACE_TRADER = "event.face_trader"
EVENT_AUGMENTER = "event.augmenter"


# 塔1 二层
EVENT_NEST = "event.nest"
EVENT_HOBO = "event.hobo"
EVENT_ANCIENT_WRITING = "event.ancient_writing"
EVENT_OLD_BEGGAR = "event.old_beggar"
EVENT_FORGOTTEN_ALTAR = "event.forgotten_altar"
EVENT_KNOWING_SKULL = "event.knowing_skull"
EVENT_MASKED_BANDITS = "event.masked_bandits"
EVENT_JOUST = "event.joust"
EVENT_GREAT_LIBRARY = "event.great_library"
EVENT_MAUSOLEUM = "event.mausoleum"
EVENT_VAMPIRES = "event.vampires"
EVENT_GHOST_COUNCIL = "event.ghost_council"
EVENT_ARENA = "event.arena"

def get_current_floor(run_state):
    node = run_state.get_current_node() if hasattr(run_state, "get_current_node") else None
    return int(getattr(node, "floor", -1))


def get_ascension_level(run_state):
    return int(getattr(run_state, "ascension_level", 0) or 0)


def event_rng(state, seed=None, salt=0):
    base_seed = seed
    if base_seed is None:
        base_seed = 0
    counter = int(state.data.get("_rng_counter", 0))
    state.data["_rng_counter"] = counter + 1
    return random.Random(int(base_seed) + int(salt) + counter * 1009)


def has_relic(run_state, relic_id):
    for relic in getattr(run_state, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def add_specific_relic(run_state, relic_id):
    relic = create_relic(relic_id)
    if has_relic(run_state, relic_id) and not getattr(relic, "allow_duplicate", False):
        return ["你已经拥有遗物【{}】，本次不会重复获得。".format(relic.name)]
    run_state.relics.append(relic)
    logs = ["获得遗物：【{}】。".format(relic.name)]
    if hasattr(relic, "on_obtained"):
        logs.extend(relic.on_obtained(run_state))
    return logs


def add_random_relic(run_state, rng):
    available_relic_ids = get_available_relic_ids(run_state)
    relic_id = rng.choice(available_relic_ids) if available_relic_ids else ""
    if not relic_id:
        return ["没有可获得的新遗物。"]
    relic = create_relic(relic_id)
    run_state.relics.append(relic)
    logs = ["获得遗物：【{}】。".format(relic.name)]
    if hasattr(relic, "on_obtained"):
        logs.extend(relic.on_obtained(run_state))
    return logs


def add_curse(run_state, card_id):
    card = create_card(card_id)
    logs = add_card_to_master_deck_with_relics(run_state, card, source="获得诅咒")
    if not logs:
        return "没有获得诅咒。"
    if logs and logs[0].startswith("【御守】"):
        return "\n".join(logs)
    return "\n".join(["获得诅咒：【{}】。".format(card.name)] + logs)

def remove_relic_by_id(run_state, relic_id):
    relics = getattr(run_state, "relics", []) or []
    for index, relic in enumerate(relics):
        if getattr(relic, "relic_id", "") == relic_id:
            return relics.pop(index)
    return None


def is_basic_strike_card(card):
    card_id = getattr(card, "card_id", "")
    name = getattr(card, "name", "")
    return card_id in ("card.strike", "card.global.strike") or name in ("打击", "打击+")


def is_basic_defend_card(card):
    card_id = getattr(card, "card_id", "")
    name = getattr(card, "name", "")
    return card_id in ("card.defend", "card.global.defend") or name in ("格挡", "格挡+", "防御", "防御+")


def remove_all_basic_strikes(run_state):
    deck = list(getattr(run_state, "master_deck", []) or [])
    kept = []
    removed = []

    for card in deck:
        if is_basic_strike_card(card):
            removed.append(card)
        else:
            kept.append(card)

    run_state.master_deck = kept
    return removed


def pick_uncommon_colorless_card_id(rng):
    from data.card.AAAregistry import CARD_REGISTRY
    from data.content_gate import is_content_enabled

    candidates = []

    for card_id in CARD_REGISTRY.keys():
        if not is_content_enabled("card", card_id):
            continue

        try:
            card = create_card(card_id)
        except Exception:
            continue

        if getattr(card, "owner_character_id", ""):
            continue

        if getattr(card, "quantity", "") != "uncommon":
            continue

        if getattr(card, "card_type", "") not in ("attack", "skill", "power"):
            continue

        candidates.append(card_id)

    return rng.choice(candidates) if candidates else ""


def make_event_card_reward(run_state, cards, title):
    from game.reward import RewardOption, RewardState, record_reward_options_offered

    reward_state = RewardState(
        node_type="event",
        options=[
            RewardOption(
                option_type="card",
                title=title,
                payload={"cards": cards},
            )
        ]
    )

    run_state.pending_reward = reward_state
    record_reward_options_offered(run_state, reward_state)
    return reward_state

def heal_by_max_hp_fraction(run_state, numerator, denominator):
    if denominator <= 0:
        denominator = 1
    amount = int(run_state.max_hp * numerator / float(denominator))
    if amount < 1:
        amount = 1
    old_hp = run_state.hp
    heal_run_hp_with_relics(run_state, amount, source="事件回复")
    actual = max(0, run_state.hp - old_hp)
    return actual, old_hp, run_state.hp


def lose_hp(run_state, amount):
    amount = int(amount)
    if amount < 0:
        amount = 0
    if amount > 0:
        try:
            from game.relic_logic.run_relic_utils import has_run_relic
            if has_run_relic(run_state, "relic.tungsten_rod"):
                amount = max(0, amount - 1)
        except Exception:
            pass
    old_hp = run_state.hp
    run_state.hp = max(0, run_state.hp - amount)
    return old_hp, run_state.hp


def lose_hp_percent_of_max(run_state, percent):
    amount = int(run_state.max_hp * percent)
    if amount < 1:
        amount = 1
    return amount, *lose_hp(run_state, amount)


def lose_max_hp_percent(run_state, percent):
    amount = int(run_state.max_hp * percent)
    if amount < 1:
        amount = 1
    old_max = run_state.max_hp
    old_hp = run_state.hp
    run_state.max_hp = max(1, run_state.max_hp - amount)
    if run_state.hp > run_state.max_hp:
        run_state.hp = run_state.max_hp
    return amount, old_max, run_state.max_hp, old_hp, run_state.hp


def get_single_base_damage(card):
    values = []
    if getattr(card, "card_type", "") != "attack":
        return 0

    for key, value in (getattr(card, "card_vars", {}) or {}).items():
        if "damage" not in str(key):
            continue
        try:
            values.append(int(value))
        except Exception:
            pass

    for effect in getattr(card, "effects", []) or []:
        if effect.get("op") != "deal_damage":
            continue
        amount = effect.get("amount")
        if isinstance(amount, int):
            values.append(amount)
        elif isinstance(amount, dict):
            if "base" in amount:
                try:
                    values.append(int(amount.get("base", 0)))
                except Exception:
                    pass
            base_var = amount.get("base_var") or amount.get("var")
            if base_var:
                try:
                    values.append(int((getattr(card, "card_vars", {}) or {}).get(base_var, 0)))
                except Exception:
                    pass
    return max(values or [0])


def has_damage_10_card(run_state):
    for card in getattr(run_state, "master_deck", []) or []:
        if get_single_base_damage(card) >= 10:
            return True
    return False


def build_deck_selection(state, run_state, title, effect_type, payload=None, only_upgradable=False):
    payload = dict(payload or {})
    choices = []

    if only_upgradable:
        source = get_upgradable_cards(run_state)
        for display_index, item in enumerate(source):
            deck_index, card = item
            upgraded_card = upgrade_card(card)
            choices.append(EventChoice(
                "牌组编号 {}：【{}】 -> 【{}】。".format(deck_index, card.name, upgraded_card.name),
                effect_type,
                payload=dict(payload, deck_index=deck_index)
            ))
    else:
        for deck_index, card in enumerate(getattr(run_state, "master_deck", []) or []):
            choices.append(EventChoice(
                "牌组编号 {}：{}".format(deck_index, card.summary_text()),
                effect_type,
                payload=dict(payload, deck_index=deck_index)
            ))

    if not choices:
        return False, "当前没有可选择的牌。"

    state.description = title
    state.choices = choices
    return True, format_event(run_state)


def is_curse_card(card):
    return getattr(card, "card_type", "") == "curse"


def is_removable_curse(card):
    return is_curse_card(card) and not getattr(card, "unremovable", False)


def has_removable_curse(run_state):
    return any(is_removable_curse(card) for card in getattr(run_state, "master_deck", []) or [])


def get_non_basic_non_curse_card_indices(run_state):
    result = []
    for index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if getattr(card, "card_type", "") == "curse":
            continue
        if getattr(card, "quantity", "") in ("starting", "basic"):
            continue
        result.append(index)
    return result


def copy_card_for_master_deck(card):
    import copy
    new_card = copy.deepcopy(card)
    strip_bottled_flags(new_card)
    return new_card


def add_random_potion_to_run(run_state, rng):
    from data.potion.AAAregistry import create_potion
    from game.reward import roll_potion_id_by_rarity
    from game.relic_logic.run_relic_utils import try_gain_potion_with_relics

    potion_id = roll_potion_id_by_rarity(rng, run_state=run_state, include_event=False)
    if not potion_id:
        return "没有可获得的药水。"
    potion = create_potion(potion_id)
    return "\n".join(try_gain_potion_with_relics(run_state, potion, source="事件"))


def roll_random_potions_for_event(run_state, rng, count):
    from data.potion.AAAregistry import create_potion
    from game.reward import roll_potion_id_by_rarity

    potions = []
    for _ in range(int(count)):
        potion_id = roll_potion_id_by_rarity(rng, run_state=run_state, include_event=False)
        if potion_id:
            potions.append(create_potion(potion_id))
    return potions


def add_random_potions_to_run(run_state, rng, count):
    """事件给药水时进入标准奖励流程，允许药水栏满时替换。"""
    potions = roll_random_potions_for_event(run_state, rng, count)
    if not potions:
        return ["没有可获得的药水。"]

    reward_state = create_potion_reward_state(
        potions,
        node_type="event",
        title_prefix="事件药水"
    )
    if not reward_state.options:
        return ["没有可获得的药水。"]

    # 事件一般在完成前不会已有 pending_reward；这里仍做兼容：若已有奖励则追加。
    if getattr(run_state, "pending_reward", None) is not None:
        run_state.pending_reward.options.extend(reward_state.options)
        record_reward_options_offered(run_state, reward_state)
    else:
        run_state.pending_reward = reward_state
        record_reward_options_offered(run_state, reward_state)

    return ["获得 {} 瓶药水，已加入待领取奖励。".format(len(reward_state.options))]


def upgrade_random_cards(run_state, rng, count):
    upgradable = get_upgradable_cards(run_state)
    rng.shuffle(upgradable)
    chosen = upgradable[:int(count)]
    logs = []

    for deck_index, card in chosen:
        upgraded_card = upgrade_card(card)
        upgraded_card = copy_bottled_flags(card, upgraded_card)
        run_state.master_deck[deck_index] = upgraded_card
        logs.append("随机升级：【{}】 -> 【{}】。".format(card.name, upgraded_card.name))

    if not logs:
        logs.append("当前没有可以升级的牌。")

    return logs


def transform_random_cards(run_state, rng, count):
    deck = getattr(run_state, "master_deck", []) or []
    candidates = [
        i for i, card in enumerate(deck)
        if getattr(card, "card_type", "") not in ("curse", "status")
    ]
    rng.shuffle(candidates)
    chosen = candidates[:int(count)]
    logs = []
    for deck_index in sorted(chosen, reverse=True):
        old_card, new_card, transform_logs = transform_card_in_master_deck(run_state, deck_index, rng=rng)
        logs.extend(transform_logs)
    if not logs:
        logs.append("当前没有可以变化的牌。")
    return logs


def remove_all_curses_from_master_deck(run_state, suppress_parasite_side_effect=False):
    deck = getattr(run_state, "master_deck", []) or []
    logs = []
    removed = []
    for index in range(len(deck) - 1, -1, -1):
        card = deck[index]
        if not is_removable_curse(card):
            continue
        removed.append(card)
        if suppress_parasite_side_effect:
            deck.pop(index)
            logs.append("移除诅咒：【{}】。".format(card.name))
        else:
            _, remove_logs = remove_card_from_master_deck(run_state, index, reason="event")
            logs.extend(remove_logs)
    if not removed:
        logs.append("当前牌组中没有可以移除的诅咒。")
    return removed, logs


def build_filtered_deck_selection(state, run_state, title, effect_type, predicate, payload=None):
    payload = dict(payload or {})
    choices = []
    for deck_index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if not predicate(card):
            continue
        choices.append(EventChoice(
            "牌组编号 {}：{}".format(deck_index, card.summary_text()),
            effect_type,
            payload=dict(payload, deck_index=deck_index)
        ))
    if not choices:
        return False, "当前没有可选择的牌。"
    state.description = title
    state.choices = choices
    return True, format_event(run_state)


def get_current_act_for_reward(run_state):
    act = get_current_act(run_state)
    if act < 1:
        act = 1
    if act > 3:
        act = 3
    return act


def get_current_act(run_state):
    """
    从当前路线节点推断塔/Act 编号。
    当前路线 node_id 形如 act1.floor02.col0，所以优先从 node_id 解析；解析失败则默认为 1。
    """
    node = run_state.get_current_node() if hasattr(run_state, "get_current_node") else None
    node_id = getattr(node, "node_id", "") if node is not None else ""
    if isinstance(node_id, str) and node_id.startswith("act"):
        digits = []
        for ch in node_id[3:]:
            if ch.isdigit():
                digits.append(ch)
            else:
                break
        if digits:
            return int("".join(digits))
    return 1

def get_common_event_builders(run_state, seed=None, source_node_type="event"):
    """
    塔1通用事件池入口。

    约定：
    - node_event_1_0.py：塔1通用事件池
    - node_event_1_1.py：塔1一层事件池
    - node_event_1_2.py：塔1二层事件池
    """
    module_name = "game.node.node_event_1_0"

    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", "") == module_name:
            return []
        raise

    if getattr(module, "__name__", "") == __name__:
        return []

    getter = getattr(module, "get_event_builders", None)
    if getter is None:
        return []

    return getter(
        run_state,
        seed=seed,
        source_node_type=source_node_type,
    )


def _load_event_stage_module(stage):
    module_name = "game.node.node_event_1_{}".format(int(stage))

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", "") == module_name:
            return None
        raise


def get_event_builders_for_current_node(run_state, seed=None, source_node_type="event"):
    """
    塔1事件池 = node_event_1_0 通用池 + node_event_1_{阶段} 阶段池。

    例：
    - 一层：node_event_1_0 + node_event_1_1
    - 二层：node_event_1_0 + node_event_1_2

    route node_id 里的 act1 / act2 表示当前第几阶段；
    事件文件名里的 1_x 表示“塔1 / 第 x 阶段”。
    """
    stage = get_current_act(run_state)

    builders = []

    builders.extend(get_common_event_builders(
        run_state,
        seed=seed,
        source_node_type=source_node_type,
    ))

    stage_module = _load_event_stage_module(stage)

    if stage_module is not None and hasattr(stage_module, "get_event_builders"):
        builders.extend(stage_module.get_event_builders(
            run_state,
            seed=seed,
            source_node_type=source_node_type,
        ))

    return builders




def _pick_random_book_relic(rng):
    return rng.choice([
        "relic.necronomicon",
        "relic.nilrys_codex",
        "relic.enchiridion",
    ])


def _get_removable_transformable_card_indices(run_state):
    result = []
    for index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if getattr(card, "unremovable", False) or getattr(card, "untransformable", False):
            continue
        result.append(index)
    return result


def _upgrade_all_cards(run_state):
    logs = []
    deck = getattr(run_state, "master_deck", []) or []
    for index, card in enumerate(list(deck)):
        if getattr(card, "upgraded", False) and not getattr(card, "multi_upgrade", False):
            continue
        if not has_upgrade(card):
            continue
        upgraded_card = upgrade_card(card)
        upgraded_card = copy_bottled_flags(card, upgraded_card)
        deck[index] = upgraded_card
        logs.append("升级：【{}】 -> 【{}】。".format(card.name, upgraded_card.name))
    if not logs:
        logs.append("没有可以升级的牌。")
    return logs


def build_cursed_tome_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="诅咒书本",
        event_id=EVENT_CURSED_TOME,
        description=(
            "在一所被遗弃的神庙里，你找到一本翻开着的巨大书本，里面满是神秘的文字。\n"
            "你刚试着想要解读这些复杂的文本，它就自己开始移动变化成了你熟悉的文字。"
        ),
        choices=[
            EventChoice("阅读。", "cursed_tome_read"),
            EventChoice("离开。", "leave"),
        ],
        data={"step": 0},
    )


def build_mind_bloom_event(run_state, rng=None, seed=None, source_node_type="event"):
    floor = get_current_floor(run_state)
    rich_choice = EventChoice("我将富有。获得 999 金币。被诅咒——2 张凡庸。", "mind_bloom_rich")
    if floor >= 40:
        rich_choice = EventChoice("我无伤痛。恢复所有生命。被诅咒——疑虑。", "mind_bloom_no_pain")
    return EventState(
        title="心灵绽放",
        event_id=EVENT_MIND_BLOOM,
        description=(
            "你在高塔的混沌深处不断攀行，不知不觉间，你愕然发现自己的思绪开始变得非常……真实……\n"
            "各种怪物和财宝的影响开始有了实体。这些感觉稍纵即逝，你准备怎么做？"
        ),
        choices=[
            EventChoice("我必凯旋。与一名第一阶段的 BOSS 战斗，胜利后获得一件稀有遗物。", "mind_bloom_victory"),
            EventChoice("我已觉醒。升级所有牌。获得绽放印记。", "mind_bloom_awakened"),
            rich_choice,
        ],
    )


def build_face_trader_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="换脸商",
        event_id=EVENT_FACE_TRADER,
        description=(
            "你经过一尊举着许多不同面具的奇怪雕像，但没走几步，就听见身后传来一个轻柔的声音：\n"
            "“请留步。”\n"
            "那尊雕像转向了你。仔细一看，这并不是雕像，只是一个肤色如同雕像的消瘦男人……\n"
            "“你的脸，让我碰碰？或者，想要交易？”"
        ),
        choices=[
            EventChoice("触碰。失去 10% 最大生命值的生命，获得 75 金币。", "face_touch"),
            EventChoice("交易。50% 获得好脸，50% 获得坏脸。", "face_trade"),
            EventChoice("离开。", "leave"),
        ],
    )


def build_augmenter_event(run_state, rng=None, seed=None, source_node_type="event"):
    return EventState(
        title="增益研究者",
        event_id=EVENT_AUGMENTER,
        description=(
            "一个戴着眼罩、邪笑着的男人大摇大摆地走到你面前：\n"
            "“嘿陌生人，想不想试试高端的科技吗？可会让你变得比任何训练和祝福都要强哦。”"
        ),
        choices=[
            EventChoice("来点猛药。获得 J.A.X.。", "augmenter_jax"),
            EventChoice("当一下实验对象。选择两张牌进行变化。", "augmenter_transform"),
            EventChoice("喝下突变剂。获得突变之力。", "augmenter_mutagen"),
        ],
    )


def create_empty_event_state(run_state, seed=None, source_node_type="event"):
    return EventState(
        title="空事件池",
        event_id="event.empty_pool",
        description=(
            "当前楼层没有可用事件。\n"
            "请检查当前 Act 的通用事件池 node_event_x_0.py，或补充当前楼层对应的 node_event_x_y.py。"
        ),
        choices=[
            EventChoice("离开。", "leave"),
        ]
    )

def get_builder_event_id(builder):
    return (
        getattr(builder, "event_id", "")
        or getattr(builder, "__event_id__", "")
        or getattr(builder, "__name__", "")
    )


def resolve_builder_event_id(builder, run_state, seed=None, source_node_type="event"):
    event_id = getattr(builder, "event_id", "") or getattr(builder, "__event_id__", "")
    if event_id:
        return event_id

    try:
        probe_state = builder(
            run_state,
            rng=random.Random(seed),
            seed=seed,
            source_node_type=source_node_type,
        )
    except Exception:
        return get_builder_event_id(builder)

    event_id = getattr(probe_state, "event_id", "") or get_builder_event_id(builder)
    try:
        setattr(builder, "__event_id__", event_id)
    except Exception:
        pass
    return event_id


def filter_event_builders(builders, run_state, seed=None, source_node_type="event"):
    result = []
    for builder in builders:
        event_id = resolve_builder_event_id(
            builder,
            run_state,
            seed=seed,
            source_node_type=source_node_type,
        )
        if is_content_enabled("event", event_id):
            result.append(builder)
    return result


def get_seen_event_ids(run_state):
    seen = getattr(run_state, "seen_event_ids", None)
    if seen is None:
        seen = []
        setattr(run_state, "seen_event_ids", seen)
    return seen


def mark_event_seen(run_state, event_id):
    if not event_id:
        return
    if event_id == "event.empty_pool":
        return

    seen = get_seen_event_ids(run_state)
    if event_id not in seen:
        seen.append(event_id)


def choose_event_builder_with_seen_priority(run_state, builders, rng):
    """
    事件随机规则：
    - 优先从没有遇到过的事件中随机。
    - 若当前事件池全都遇到过，则从完整事件池中随机。
    """
    seen = set(get_seen_event_ids(run_state))

    unseen_builders = []
    for builder in builders:
        event_id = get_builder_event_id(builder)
        if event_id and event_id not in seen:
            unseen_builders.append(builder)

    pool = unseen_builders if unseen_builders else builders
    return rng.choice(pool)

def create_event_state(run_state, seed=None, source_node_type="event"):
    rng = random.Random(seed)
    builders = get_event_builders_for_current_node(
        run_state,
        seed=seed,
        source_node_type=source_node_type,
    )
    builders = filter_event_builders(
        builders,
        run_state,
        seed=seed,
        source_node_type=source_node_type,
    )

    if not builders:
        return create_empty_event_state(
            run_state,
            seed=seed,
            source_node_type=source_node_type,
        )

    builder = choose_event_builder_with_seen_priority(run_state, builders, rng)
    state = builder(
        run_state,
        rng=rng,
        seed=seed,
        source_node_type=source_node_type,
    )

    event_id = getattr(state, "event_id", "") or get_builder_event_id(builder)
    mark_event_seen(run_state, event_id)

    return state


def format_event(run_state):
    state = run_state.pending_event

    if state is None:
        return "当前没有事件。"

    lines = []
    lines.append("=== 事件：{} ===".format(state.title))
    lines.append(state.description)
    lines.append("")

    for index, choice in enumerate(state.choices):
        lines.append("[{}] {}".format(index, choice.title))

    lines.append("")
    lines.append(command_tip("event", "使用 /card event 0 选择。"))

    return "\n".join(lines)


def choose_event_option(run_state, choice_index, seed=None):
    state = run_state.pending_event

    if state is None:
        return False, "当前没有事件。"

    if choice_index < 0 or choice_index >= len(state.choices):
        return False, "选项编号无效。"

    choice = state.choices[choice_index]
    rng = event_rng(state, seed=seed, salt=17)
    payload = choice.payload or {}
    effect = choice.effect_type

    if effect in ("leave", "corpse_leave"):
        return True, "你离开了这里。"

    if effect == "big_fish_banana":
        amount, old_hp, new_hp = heal_by_max_hp_fraction(run_state, 1, 3)
        return True, "你吃下了香蕉，它很有营养，似乎还有些魔法，回复了你的生命。\n恢复 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp)

    if effect == "big_fish_donut":
        amount = int(choice.amount or 5)
        old_max_hp = run_state.max_hp
        old_hp = run_state.hp
        run_state.max_hp += amount
        run_state.hp += amount
        return True, "你吃下了甜甜圈，真是太好吃了！你的最大生命值增加了。\n最大生命值：{} -> {}。HP：{} -> {}。".format(old_max_hp, run_state.max_hp, old_hp, run_state.hp)

    if effect == "big_fish_box":
        logs = ["你抓住了盒子，在里面找到了一个遗物！"]
        logs.extend(add_random_relic(run_state, rng))
        logs.append("可是，你真的很想吃那个甜甜圈……")
        logs.append("你的心中充满了悲伤，尤其是一份悔恨。")
        logs.append(add_curse(run_state, "card.curse.regret"))
        return True, "\n".join(logs)

    if effect == "cleric_heal":
        if run_state.gold < 35:
            return False, "金币不足。当前金币：{}，需要：35。".format(run_state.gold)
        run_state.gold -= 35
        amount, old_hp, new_hp = heal_by_max_hp_fraction(run_state, 1, 4)
        return True, "一道温暖的金光笼罩了你然后消散了。\n那个生物咧嘴一笑：“牧师最强奶妈。那么祝你愉快啦！”\n花费 35 金币，恢复 {} 点生命：{} -> {}。当前金币：{}。".format(amount, old_hp, new_hp, run_state.gold)

    if effect == "cleric_purge":
        if run_state.gold < 50:
            return False, "金币不足。当前金币：{}，需要：50。".format(run_state.gold)
        ok, text = build_deck_selection(
            state,
            run_state,
            "一道寒冷的蓝色火焰正在等待你的选择。请选择要净化的牌。",
            "select_remove_card",
            payload={"gold_cost": 50, "after_text": "一道寒冷的蓝色火焰笼罩了你然后消散了。\n那个生物咧嘴一笑：“牧师就是能干。那么祝你愉快啦！”"}
        )
        return False, text if ok else text

    if effect == "golden_idol_leave":
        return True, "没有比这更明显的陷阱了吧。\n你决定还是不要去碰高台上的东西了。"

    if effect == "golden_idol_take":
        logs = []
        logs.extend(add_specific_relic(run_state, "relic.golden_idol"))
        logs.append("你拿住金神像放入囊中，突然天花板上一块巨大的圆石掉到了你身边的地上。")
        logs.append("石头开始向你滚来，你这才发现地面有一点倾斜。")
        state.description = "\n".join(logs)
        smash_pct = 0.35 if get_ascension_level(run_state) >= 15 else 0.25
        hide_pct = 0.10 if get_ascension_level(run_state) >= 15 else 0.08
        state.choices = [
            EventChoice("逃跑。被诅咒——受伤。", "golden_idol_escape"),
            EventChoice("砸烂。失去 {}% 生命。".format(int(smash_pct * 100)), "golden_idol_smash", payload={"percent": smash_pct}),
            EventChoice("躲藏。失去 {}% 最大生命。".format(int(hide_pct * 100)), "golden_idol_hide", payload={"percent": hide_pct}),
        ]
        return False, format_event(run_state)

    if effect == "golden_idol_escape":
        return True, "快跑！\n你勉强在石头碾到你之前跳进了旁边的一条小路，不幸的是你似乎扭伤了关节。\n{}".format(add_curse(run_state, "card.curse.injury"))

    if effect == "golden_idol_smash":
        pct = float(payload.get("percent", 0.25))
        amount, old_hp, new_hp = lose_hp_percent_of_max(run_state, pct)
        return True, "你用尽全力向巨石发起了攻击。尘埃落定之后，你可以寻找安全的出路。\n失去 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp)

    if effect == "golden_idol_hide":
        pct = float(payload.get("percent", 0.08))
        amount, old_max, new_max, old_hp, new_hp = lose_max_hp_percent(run_state, pct)
        return True, "咕叽！\n巨石滚过时压到了你一点，但看起来你并没有大碍，可以离开了。\n失去 {} 点最大生命：{} -> {}。HP：{} -> {}。".format(amount, old_max, new_max, old_hp, new_hp)

    if effect == "wing_pray":
        ok, text = build_deck_selection(
            state,
            run_state,
            "你跪下祷告。请选择要从牌组中移除的牌。",
            "select_remove_card",
            payload={"hp_loss": 7, "after_text": "你曾听人提起过一个崇拜巨大鸟类的邪教。当你跪下祷告的时候，你开始觉得有一些头晕……\n过了一会儿，你醒了过来，感觉脚步有点变轻了。"}
        )
        return False, text if ok else text

    if effect == "wing_destroy":
        if not has_damage_10_card(run_state):
            return False, "你没有伤害等于或超过 10 的牌，无法砸开雕像。"
        amount = rng.randint(50, 80)
        logs = [
            "你使出浑身的力气开始砸雕像。",
            "很快它就彻底裂开，里面是一大堆金币。你把钱尽可能收集起来，重新上路。",
        ]
        logs.extend(gain_gold_with_relics(run_state, amount, source="砸碎雕像"))
        return True, "\n".join(logs)

    if effect == "slime_world_collect":
        old_hp, new_hp = lose_hp(run_state, 11)
        logs = [
            "在长时间与黏液接触而导致你的皮肤被烧走之前，你成功地捞出了不少金币。",
            "HP：{} -> {}。".format(old_hp, new_hp),
        ]
        logs.extend(gain_gold_with_relics(run_state, 75, source="黏液世界"))
        return True, "\n".join(logs)

    if effect == "slime_world_let_go":
        amount = rng.randint(20, 50)
        actual = min(amount, run_state.gold)
        old_gold = run_state.gold
        run_state.gold -= actual
        return True, "你决定这样做不值得。\n失去 {} 金币：{} -> {}。".format(actual, old_gold, run_state.gold)

    if effect == "serpent_agree":
        logs = [
            "“对～！\n这会很值～得的。\n嘶……嘶～嘶……”",
            "蛇抬起头，往上喷出了一堆金币！",
            "这令人震惊又有点可怕。",
            "你把金币收好，谢过蛇后，重新上路。",
        ]
        logs.extend(gain_gold_with_relics(run_state, 175, source="蛇"))
        logs.append(add_curse(run_state, "card.curse.doubt"))
        return True, "\n".join(logs)

    if effect == "serpent_disagree":
        return True, "蛇非常失望地看着你。"

    if effect == "living_wall_forget":
        ok, text = build_deck_selection(
            state,
            run_state,
            "“忘记你所知道的，我就让你走。”\n请选择要移除的牌。",
            "select_remove_card",
            payload={"after_text": "你面前的墙壁满意地缩回了天花板，你的眼前出现了道路。"}
        )
        return False, text if ok else text

    if effect == "living_wall_change":
        ok, text = build_deck_selection(
            state,
            run_state,
            "“有所改变，我就让你看见新的道路。”\n请选择要变化的牌。",
            "select_transform_card",
            payload={"after_text": "你面前的墙壁满意地缩回了天花板，你的眼前出现了道路。"}
        )
        return False, text if ok else text

    if effect == "living_wall_grow":
        ok, text = build_deck_selection(
            state,
            run_state,
            "“如果你想要从我这里通过，你就必须有所成长。”\n请选择要升级的牌。",
            "select_upgrade_card",
            payload={"after_text": "你面前的墙壁满意地缩回了天花板，你的眼前出现了道路。"},
            only_upgradable=True
        )
        return False, text if ok else text

    if effect == "mushrooms_stomp":
        from game.run_engine import start_forced_event_battle
        return False, start_forced_event_battle(
            run_state,
            encounter_id="encounter.fungi_beast_3",
            effective_node_type="normal_enemy",
            seed=seed,
            post_battle_effects=[{"type": "gain_relic", "relic_id": "relic.odd_mushroom"}],
            intro_text="有埋伏！！\n被蘑菇感染的啮齿类动物们不知从哪里冒了出来！"
        )

    if effect == "mushrooms_eat":
        amount, old_hp, new_hp = heal_by_max_hp_fraction(run_state, 1, 4)
        logs = [
            "你顺从了这份不自然的食欲，吃下一个又一个蘑菇后，你觉得自己有点晕晕的，然后就失去了意识。",
            "当你醒来时，你觉得有点怪怪的。",
            "回复 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp),
            add_curse(run_state, "card.curse.parasite"),
        ]
        return True, "\n".join(logs)

    if effect == "scrap_ooze_reach":
        attempts = int(state.data.get("attempts", 0))
        damage = 3 + attempts
        success_chance = 25 + attempts * 10
        state.data["attempts"] = attempts + 1
        old_hp, new_hp = lose_hp(run_state, damage)
        logs = ["你把手伸进破烂软泥。失去 {} 点生命：{} -> {}。".format(damage, old_hp, new_hp)]
        if rng.random() * 100.0 < success_chance:
            logs.append("成功！")
            logs.append("在金属和酸液之中翻找了好久，你终于抓住了一件遗物把它拉了出来。")
            logs.extend(add_random_relic(run_state, rng))
            return True, "\n".join(logs)
        logs.append("啊呀！")
        logs.append("你找到的只是已被腐蚀的金属和一点灼伤的疼痛。")
        logs.append("可是你还是很确定，里面一定有一件遗物……")
        next_attempts = int(state.data.get("attempts", 0))
        next_damage = 3 + next_attempts
        next_success = 25 + next_attempts * 10
        state.description = "\n".join(logs)
        state.choices = [
            EventChoice("接着往里伸。失去 {} 生命。{}%：找到一件遗物。".format(next_damage, next_success), "scrap_ooze_reach"),
            EventChoice("离开。", "scrap_ooze_leave"),
        ]
        return False, format_event(run_state)

    if effect == "scrap_ooze_leave":
        return True, "你决定离开这个地方。\n史莱姆并不在意，接着慢慢消化它的美餐。"

    if effect == "shining_light_enter":
        upgradable = get_upgradable_cards(run_state)
        if not upgradable:
            return False, "当前没有可以升级的牌。"
        rng.shuffle(upgradable)
        chosen = upgradable[:2]
        logs = [
            "你走进光柱，注意到光似乎被吸入了你的身体。",
            "这道光热得发烫！可是痛楚很快消失了。",
            "你觉得自己精神焕发，就像是在需要被打醒的时候被人好好地抽了一个耳光。",
        ]
        for deck_index, card in chosen:
            upgraded_card = upgrade_card(card)
            upgraded_card = copy_bottled_flags(card, upgraded_card)
            run_state.master_deck[deck_index] = upgraded_card
            logs.append("随机升级：【{}】 -> 【{}】。".format(card.name, upgraded_card.name))
        amount, old_hp, new_hp = lose_hp_percent_of_max(run_state, 0.20)
        logs.append("失去 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp))
        return True, "\n".join(logs)

    if effect == "corpse_search":
        attempts = int(state.data.get("attempts", 0))
        chances = [25, 50, 75]
        chance = chances[min(attempts, len(chances) - 1)]
        if rng.random() * 100.0 < chance:
            monster_name = state.data.get("monster_name", "怪物")
            state.description = "在搜刮冒险者时你被偷袭了！\n回来的怪物是：{}。".format(monster_name)
            state.choices = [EventChoice("……战斗！", "corpse_fight")]
            return False, format_event(run_state)

        remaining = list(state.data.get("remaining_rewards", []) or [])
        reward = rng.choice(remaining) if remaining else "nothing"
        if reward in remaining:
            remaining.remove(reward)
        state.data["remaining_rewards"] = remaining
        state.data["attempts"] = attempts + 1

        logs = []
        if reward == "gold":
            logs.append("你找到了一些金币！")
            logs.extend(gain_gold_with_relics(run_state, 30, source="冒险者尸体"))
        elif reward == "relic":
            logs.append("你找到一件遗物！")
            logs.extend(add_random_relic(run_state, rng))
        else:
            logs.append("唔，什么也没找到……")

        if state.data["attempts"] >= 3 or not remaining:
            logs.append("看起来你成功翻遍了他的所有物，什么事也没发生！")
            return True, "\n".join(logs)

        next_chance = chances[min(state.data["attempts"], len(chances) - 1)]
        state.description = "\n".join(logs) + "\n要继续找吗？"
        state.choices = [
            EventChoice("继续。寻找东西。{}%：遇见回来的怪物。".format(next_chance), "corpse_search"),
            EventChoice("离开。", "corpse_leave"),
        ]
        return False, format_event(run_state)

    if effect == "corpse_fight":
        from game.run_engine import start_forced_event_battle
        return False, start_forced_event_battle(
            run_state,
            encounter_id=state.data.get("encounter_id", "encounter.elite.gremlin_nob"),
            effective_node_type="event_elite",
            seed=seed,
            post_battle_effects=[{
                "type": "adventurer_corpse_remaining_rewards",
                "remaining_rewards": list(state.data.get("remaining_rewards", []) or []),
            }],
            intro_text="你别无选择，只能迎战。"
        )

    if effect == "nloth_potion":
        potion_index = int(payload.get("potion_index", -1))
        potions = getattr(run_state, "potions", []) or []
        if potion_index < 0 or potion_index >= len(potions):
            return False, "当前没有可交出的药水。"
        potion = potions.pop(potion_index)
        logs = [
            "“太好了！我正口渴呢。”",
            "咕嘟咕嘟咕嘟",
            "他一口气喝完了药水，满意地打了个饱嗝。",
            "他在自己身上的众多口袋摸索了半天……",
            "“看我今天为你准备了什么！给你给你！”",
            "失去药水：【{}】。".format(potion.name),
        ]
        logs.extend(add_random_relic(run_state, rng))
        return True, "\n".join(logs)

    if effect == "nloth_gold":
        amount = int(payload.get("gold_amount", 0) or 0)
        if amount < 50 or run_state.gold < amount:
            return False, "金币不足。当前金币：{}，需要：至少 50。".format(run_state.gold)
        run_state.gold -= amount
        logs = [
            "“太棒了！之后要是再遇见那些戴面具的流氓，这一定会很有用的。”",
            "他在自己身上的众多口袋摸索了半天……",
            "“看我今天为你准备了什么！给你给你！”",
            "失去 {} 金币。当前金币：{}。".format(amount, run_state.gold),
        ]
        logs.extend(add_random_relic(run_state, rng))
        return True, "\n".join(logs)

    if effect == "nloth_card":
        deck_index = int(payload.get("deck_index", -1))
        removed_card, remove_logs = remove_card_from_master_deck(run_state, deck_index, reason="event")
        if removed_card is None:
            return False, "\n".join(remove_logs)
        logs = [
            "“有意思！我会回去好好研究的。”",
            "他在自己身上的众多口袋摸索了半天……",
            "“看我今天为你准备了什么！给你给你！”",
        ]
        logs.extend(remove_logs)
        logs.extend(add_random_relic(run_state, rng))
        return True, "\n".join(logs)

    if effect == "nloth_attack":
        return True, "“啊！！哎呀你这人有时真是老混蛋了！”\n他飞快地跑开了。"

    if effect == "holy_water_drink":
        if not has_removable_curse(run_state):
            return False, "当前牌组中没有可以被泉水移除的诅咒。"
        removed, logs = remove_all_curses_from_master_deck(run_state, suppress_parasite_side_effect=True)
        logs.insert(0, "喝下水后，感觉到身体中不再有黑暗的束缚。")
        return True, "\n".join(logs)

    if effect == "designer_small_random":
        cost = 50
        if run_state.gold < cost:
            return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, cost)
        if not get_upgradable_cards(run_state):
            return False, "当前没有可以升级的牌。"
        run_state.gold -= cost
        logs = ["“好啦，那下次再来哦。”", "...刚刚真该一拳揍上去的。", "花费 {} 金币。当前金币：{}。".format(cost, run_state.gold)]
        logs.extend(upgrade_random_cards(run_state, rng, 2))
        return True, "\n".join(logs)

    if effect == "designer_small_choose":
        if run_state.gold < 50:
            return False, "金币不足。当前金币：{}，需要：50。".format(run_state.gold)
        ok, text = build_deck_selection(
            state,
            run_state,
            "尖端设计师掏出了荒唐的工具。请选择要升级的牌。",
            "select_upgrade_card",
            payload={"gold_cost": 50, "after_text": "“好啦，那下次再来哦。”\n...刚刚真该一拳揍上去的。"},
            only_upgradable=True
        )
        return False, text if ok else text

    if effect == "designer_clean_remove":
        if run_state.gold < 75:
            return False, "金币不足。当前金币：{}，需要：75。".format(run_state.gold)
        ok, text = build_deck_selection(
            state,
            run_state,
            "尖端设计师皱着眉打量你的牌组。请选择要移除的牌。",
            "select_remove_card",
            payload={"gold_cost": 75, "after_text": "“好啦，那下次再来哦。”\n...刚刚真该一拳揍上去的。"}
        )
        return False, text if ok else text

    if effect == "designer_clean_transform":
        cost = 75
        if run_state.gold < cost:
            return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, cost)
        run_state.gold -= cost
        logs = ["“好啦，那下次再来哦。”", "...刚刚真该一拳揍上去的。", "花费 {} 金币。当前金币：{}。".format(cost, run_state.gold)]
        logs.extend(transform_random_cards(run_state, rng, 2))
        return True, "\n".join(logs)

    if effect == "designer_full":
        if run_state.gold < 110:
            return False, "金币不足。当前金币：{}，需要：110。".format(run_state.gold)
        ok, text = build_deck_selection(
            state,
            run_state,
            "全套服务开始。请选择要移除的牌，随后会随机升级一张牌。",
            "designer_full_select_remove",
            payload={"gold_cost": 110}
        )
        return False, text if ok else text

    if effect == "designer_punch":
        damage = 5 if get_ascension_level(run_state) >= 15 else 3
        if run_state.hp <= damage:
            return False, "当前生命值不足，不能选择一拳过去。"
        old_hp, new_hp = lose_hp(run_state, damage)
        return True, "你一拳揍了过去，打到你的手都疼了。\n“我的脸啊!!这下我要一一”他晕了过去。\n呵呵，现在谁才又恶心又流着血啦?\n失去 {} 点生命：{} -> {}。".format(damage, old_hp, new_hp)

    if effect == "designer_full_select_remove":
        deck_index = int(payload.get("deck_index", -1))
        if run_state.gold < 110:
            return False, "金币不足。当前金币：{}，需要：110。".format(run_state.gold)
        run_state.gold -= 110
        removed_card, remove_logs = remove_card_from_master_deck(run_state, deck_index, reason="event")
        if removed_card is None:
            return False, "\n".join(remove_logs)
        logs = ["“好啦，那下次再来哦。”", "...刚刚真该一拳揍上去的。", "花费 110 金币。当前金币：{}。".format(run_state.gold)]
        logs.extend(remove_logs)
        logs.extend(upgrade_random_cards(run_state, rng, 1))
        return True, "\n".join(logs)

    if effect == "duplicator_pray":
        ok, text = build_deck_selection(
            state,
            run_state,
            "祭坛上出现一个可怖的镜像影像。请选择要复制的牌。",
            "select_duplicate_card",
            payload={"after_text": "你尊敬地跪了下来，祭坛上出现一个可怖的镜像影像，撞到了你的身上。"}
        )
        return False, text if ok else text

    if effect == "select_duplicate_card":
        deck_index = int(payload.get("deck_index", -1))
        deck = getattr(run_state, "master_deck", []) or []
        if deck_index < 0 or deck_index >= len(deck):
            return False, "卡牌编号无效。"
        old_card = deck[deck_index]
        new_card = copy_card_for_master_deck(old_card)
        deck.append(new_card)
        after_text = payload.get("after_text", "")
        logs = []
        if after_text:
            logs.append(after_text)
        logs.append("复制卡牌：【{}】。".format(new_card.name))
        return True, "\n".join(logs)

    if effect == "forge_upgrade":
        ok, text = build_deck_selection(
            state,
            run_state,
            "你决定好好利用这个熔炉……请选择要强化的卡牌。",
            "select_upgrade_card",
            payload={"after_text": "铛 铛 铛！\n……来强化你的卡牌!"},
            only_upgradable=True
        )
        return False, text if ok else text

    if effect == "forge_rummage":
        logs = [
            "你决定看看能不能找到什么其他有用的东西。",
            "在掀开不少盖布、翻开不少箱子和在角落四处搜寻之后，你找到了一件满是灰尘的遗物！",
        ]
        logs.extend(add_specific_relic(run_state, "relic.warped_tongs"))
        logs.append("在你离开小屋时，你感觉到了一阵挥之不去的疼痛，或许是你的行为惊扰了什么恶灵？")
        logs.append(add_curse(run_state, "card.curse.pain"))
        return True, "\n".join(logs)

    if effect == "bonfire_offer":
        ok, text = build_deck_selection(
            state,
            run_state,
            "精灵们期待地看着你。请选择要献上的贡品。",
            "bonfire_select_card",
            payload={}
        )
        return False, text if ok else text

    if effect == "bonfire_select_card":
        deck_index = int(payload.get("deck_index", -1))
        deck = getattr(run_state, "master_deck", []) or []
        if deck_index < 0 or deck_index >= len(deck):
            return False, "卡牌编号无效。"
        card = deck[deck_index]
        quantity = getattr(card, "quantity", "")
        card_type = getattr(card, "card_type", "")
        removed_card, remove_logs = remove_card_from_master_deck(run_state, deck_index, reason="event")
        if removed_card is None:
            return False, "\n".join(remove_logs)
        logs = ["你将一件贡品丢入篝火中。"]
        logs.extend(remove_logs)
        if card_type == "curse":
            logs.append("精灵显然对于你献上诅咒很不满意……这张牌滋滋冒出了黑烟。")
            logs.extend(add_specific_relic(run_state, "relic.spirit_poop"))
        elif quantity in ("starting", "basic"):
            logs.append("什么也没有发生……精灵们似乎不再理你了。总觉得有点失望……")
        elif quantity == "common":
            old_hp = run_state.hp
            run_state.hp = min(run_state.max_hp, run_state.hp + 5)
            logs.append("火焰稍稍变亮了一些。你回复了 5 生命：{} -> {}。".format(old_hp, run_state.hp))
        elif quantity == "uncommon":
            old_hp = run_state.hp
            run_state.hp = run_state.max_hp
            logs.append("火焰喷射出来，变亮了许多！你的生命回复到最大：{} -> {}。".format(old_hp, run_state.hp))
        elif quantity == "rare":
            old_max = run_state.max_hp
            run_state.max_hp += 10
            run_state.hp = run_state.max_hp
            logs.append("火焰爆发起来，几乎将你震倒在地。最大生命值 {} -> {}，生命回复到最大。".format(old_max, run_state.max_hp))
        else:
            logs.append("火焰闪了闪，但没有明显变化。")
        return True, "\n".join(logs)

    if effect == "golden_shrine_pray":
        logs = ["当你的手触碰神龛时，天空中开始掉落金币，赚钱了！"]
        logs.extend(gain_gold_with_relics(run_state, 100, source="黄金神龛"))
        return True, "\n".join(logs)

    if effect == "golden_shrine_desecrate":
        logs = [
            "你每攻击一次神龛，就有更多的金币掉落出来！",
            "当你收起所有钱时，心中有了一种沉重的感觉。",
        ]
        logs.extend(gain_gold_with_relics(run_state, 250, source="亵渎黄金神龛"))
        logs.append(add_curse(run_state, "card.curse.regret"))
        return True, "\n".join(logs)

    if effect == "lab_search":
        logs = ["找到一些药水！"]
        logs.extend(add_random_potions_to_run(run_state, rng, 3))
        return True, "\n".join(logs)

    if effect == "purifier_shrine_pray":
        ok, text = build_deck_selection(
            state,
            run_state,
            "你敬畏地在神龛前下跪。请选择要移除的牌。",
            "select_remove_card",
            payload={"after_text": "你敬畏地在神龛前下跪，感觉到肩头的重量变轻了。"}
        )
        return False, text if ok else text

    if effect == "transform_shrine_pray":
        ok, text = build_deck_selection(
            state,
            run_state,
            "神龛的力量涌入你。请选择要变化的牌。",
            "select_transform_card",
            payload={"after_text": "神龛的力量涌入你，你感觉自己的内心发生了一些变化。"}
        )
        return False, text if ok else text

    if effect == "upgrade_shrine_pray":
        ok, text = build_deck_selection(
            state,
            run_state,
            "神龛的力量涌入你。请选择要升级的牌。",
            "select_upgrade_card",
            payload={"after_text": "神龛的力量涌入你，让你变强了。"},
            only_upgradable=True
        )
        return False, text if ok else text

    if effect == "wheel_play":
        prize = payload.get("prize", "") or rng.choice(["gold", "relic", "heal", "curse", "remove", "damage"])
        if prize == "gold":
            amount_map = {1: 100, 2: 200, 3: 300}
            amount = amount_map.get(get_current_act_for_reward(run_state), 100)
            logs = ["“你赢得了一些金币！", "噢耶！！！”"]
            logs.extend(gain_gold_with_relics(run_state, amount, source="命运转盘"))
            return True, "\n".join(logs)
        if prize == "relic":
            logs = ["“啊，一件礼物！\n请收下吧！”"]
            logs.extend(add_random_relic(run_state, rng))
            return True, "\n".join(logs)
        if prize == "heal":
            old_hp = run_state.hp
            run_state.hp = run_state.max_hp
            return True, "“哦哦，一次免费的回复！”\nHP：{} -> {}。".format(old_hp, run_state.hp)
        if prize == "curse":
            logs = ["“看起来你赢得了一个诅咒！\n这就比较糟糕啦。\n好吧！那么祝你下次好运啦！”", add_curse(run_state, "card.curse.decay")]
            return True, "\n".join(logs)
        if prize == "remove":
            ok, text = build_deck_selection(
                state,
                run_state,
                "“哦哦，黑暗的力量……”\n在你的牌组中选择一张移除吧！",
                "select_remove_card",
                payload={}
            )
            return False, text if ok else text
        damage = max(1, int(run_state.max_hp * 0.10))
        old_hp, new_hp = lose_hp(run_state, damage)
        return True, "“呃欧！\n你输了！”\n你被他的小刀砍中了几次。\n“代价已经付清！！”\n失去 {} 点生命：{} -> {}。".format(damage, old_hp, new_hp)

    if effect == "blue_woman_buy":
        count = int(payload.get("count", 1) or 1)
        cost = int(payload.get("cost", 20) or 20)
        if run_state.gold < cost:
            return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, cost)
        run_state.gold -= cost
        logs = ["“很好，现在给我出去。”", "你小心地离开了这家店。", "花费 {} 金币。当前金币：{}。".format(cost, run_state.gold)]
        logs.extend(add_random_potions_to_run(run_state, rng, count))
        return True, "\n".join(logs)

    if effect == "blue_woman_leave":
        return True, "砰\n她戴着手套的拳头狠狠打在了你的脸上，差点就把你打翻在地。\n“在我把你打得满地找牙之前给我滚出去。”你觉得她有可能说到做到，趁着牙齿还没事赶紧离开了这家店。"

    if effect == "nloth_relic":
        relic_index = int(payload.get("relic_index", -1))
        relics = getattr(run_state, "relics", []) or []
        if relic_index < 0 or relic_index >= len(relics):
            return False, "当前没有可交出的遗物。"
        relic = relics.pop(relic_index)
        logs = [
            "你把遗物递给恩洛斯，他用触手一把将东西抓过去，大张开嘴，一口就啊呜吞了下去。",
            "失去遗物：【{}】。".format(getattr(relic, "name", "遗物")),
            "恩洛斯露齿一笑，塞给你一个整洁的小盒子。",
        ]
        logs.extend(add_specific_relic(run_state, "relic.nloths_gift"))
        return True, "\n".join(logs)

    if effect == "cursed_tome_read":
        state.description = (
            "真奇怪。这本书的内容似乎是关于一名叫做涅奥的先古之民。\n"
            "这引起了你的兴趣，但你总觉得这本书有点让你不适。"
        )
        state.data["step"] = 0
        state.choices = [
            EventChoice("继续。失去 1 生命。", "cursed_tome_continue", amount=1),
            EventChoice("离开。", "leave"),
        ]
        return False, format_event(run_state)

    if effect == "cursed_tome_continue":
        step = int(state.data.get("step", 0))
        losses = [1, 2, 3]
        texts = [
            "涅奥是司管复活的先古之民，他被放逐到了高塔的底端。\n你觉得自己必须要读下去，可是你的身体开始觉得有一点疼痛。",
            "寻求复仇的涅奥会给予外来人祝福，利用他们来达成自己的目的。\n你开始觉得自己非常虚弱和疲劳……",
            "那些被涅奥复活的人们只能零碎想起自己过去人生的记忆，他们被诅咒要永远战斗下去。\n当你快要翻到最后一页时，你的旧伤口似乎要绽开了！",
        ]
        loss = losses[min(step, len(losses)-1)]
        old_hp, new_hp = lose_hp(run_state, loss)
        prefix = "失去 {} 点生命：{} -> {}。\n".format(loss, old_hp, new_hp)
        state.data["step"] = step + 1
        state.description = prefix + texts[min(step, len(texts)-1)]
        if step + 1 >= 3:
            state.choices = [
                EventChoice("停止。失去 3 生命。", "cursed_tome_stop"),
                EventChoice("拿走。得到书。失去 10 生命。", "cursed_tome_take"),
            ]
        else:
            next_loss = losses[min(step + 1, len(losses)-1)]
            state.choices = [EventChoice("继续。失去 {} 生命。".format(next_loss), "cursed_tome_continue", amount=next_loss)]
        return False, format_event(run_state)

    if effect == "cursed_tome_stop":
        old_hp, new_hp = lose_hp(run_state, 3)
        return True, "你顶着极大的压力，强行用意志力抵抗住书本的魔力，砰地一下使劲把书合上了。\n失去 3 点生命：{} -> {}。".format(old_hp, new_hp)

    if effect == "cursed_tome_take":
        old_hp, new_hp = lose_hp(run_state, 10)
        relic_id = _pick_random_book_relic(rng)
        logs = [
            "看完书后，你决定把它带上。或许手握证据的现在，你会有可能取回你的记忆？",
            "失去 10 点生命：{} -> {}。".format(old_hp, new_hp),
        ]
        logs.extend(add_specific_relic(run_state, relic_id))
        return True, "\n".join(logs)

    if effect == "mind_bloom_victory":
        from game.run_engine import start_forced_event_battle
        return False, start_forced_event_battle(
            run_state,
            encounter_id="encounter.boss.slime_boss",
            effective_node_type="event_boss",
            seed=seed,
            post_battle_effects=[{"type": "gain_rare_relic"}],
            intro_text="思维凝成实体。你必须击败曾经的强敌。",
        )

    if effect == "mind_bloom_awakened":
        logs = [
            "一切都明白了。失去的记忆、不断地攀登、那个先古之民。",
            "你的牌组被全部唤醒。",
        ]
        logs.extend(_upgrade_all_cards(run_state))
        logs.extend(add_specific_relic(run_state, "relic.mark_of_the_bloom"))
        return True, "\n".join(logs)

    if effect == "mind_bloom_rich":
        logs = ["真的有这么简单的事吗？"]
        logs.extend(gain_gold_with_relics(run_state, 999, source="心灵绽放"))
        logs.append(add_curse(run_state, "card.curse.normality"))
        logs.append(add_curse(run_state, "card.curse.normality"))
        return True, "\n".join(logs)

    if effect == "mind_bloom_no_pain":
        logs = ["真的有这么简单的事吗？"]
        logs.extend(heal_run_hp_with_relics(run_state, int(getattr(run_state, "max_hp", 0)), source="心灵绽放"))
        logs.append(add_curse(run_state, "card.curse.doubt"))
        return True, "\n".join(logs)

    if effect == "face_touch":
        amount, old_hp, new_hp = lose_hp_percent_of_max(run_state, 0.10)
        logs = [
            "“补偿吗？当然了。”他机械地伸出手，将一叠金币放进了你的钱袋里。",
            "失去 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp),
        ]
        logs.extend(gain_gold_with_relics(run_state, 75, source="换脸商"))
        return True, "\n".join(logs)

    if effect == "face_trade":
        if rng.random() < 0.5:
            relic_id = rng.choice(["relic.face_of_cleric", "relic.ssserpent_head", "relic.cultist_mask"])
            mood = "好脸"
        else:
            relic_id = rng.choice(["relic.gremlin_mask", "relic.nloths_mask"])
            mood = "坏脸"
        logs = ["你的脸和面具交换了。你获得了{}。".format(mood)]
        logs.extend(add_specific_relic(run_state, relic_id))
        return True, "\n".join(logs)

    if effect == "augmenter_jax":
        logs = ["男人递给你一个看起来很危险的、装着发光液体的针筒。"]
        logs.extend(add_card_to_master_deck_with_relics(run_state, create_card("card.jax"), source="增益研究者"))
        return True, "\n".join(logs)

    if effect == "augmenter_transform":
        indices = _get_removable_transformable_card_indices(run_state)
        if len(indices) < 2:
            return False, "牌组中可变化的牌不足 2 张。"
        ok, text = build_filtered_deck_selection(
            state,
            run_state,
            "增益研究者拿出笔记本。请选择第 1 张要变化的牌。",
            "augmenter_transform_first",
            predicate=lambda card: not getattr(card, "unremovable", False) and not getattr(card, "untransformable", False),
            payload={},
        )
        return False, text if ok else text

    if effect == "augmenter_transform_first":
        first = int(payload.get("deck_index", -1))
        if first < 0 or first >= len(getattr(run_state, "master_deck", []) or []):
            return False, "卡牌编号无效。"
        state.data["augmenter_first_index"] = first
        ok, text = build_filtered_deck_selection(
            state,
            run_state,
            "请选择第 2 张要变化的牌。",
            "augmenter_transform_second",
            predicate=lambda card: not getattr(card, "unremovable", False) and not getattr(card, "untransformable", False),
            payload={"first_index": first},
        )
        return False, text if ok else text

    if effect == "augmenter_transform_second":
        first = int(payload.get("first_index", state.data.get("augmenter_first_index", -1)))
        second = int(payload.get("deck_index", -1))
        if first == second:
            return False, "需要选择两张不同的牌。"
        logs = ["“太棒了。”你感觉自己有点飘忽，他则飞快地记起了笔记。"]
        for deck_index in sorted([first, second], reverse=True):
            old_card, new_card, transform_logs = transform_card_in_master_deck(run_state, deck_index, rng=rng)
            logs.extend(transform_logs)
        return True, "\n".join(logs)

    if effect == "augmenter_mutagen":
        logs = ["你喝下神秘液体，立即感觉肌肉纤维仿佛抖动了起来！"]
        logs.extend(add_specific_relic(run_state, "relic.mutagenic_strength"))
        return True, "\n".join(logs)

    if effect == "select_remove_card":
        deck_index = int(payload.get("deck_index", -1))
        gold_cost = int(payload.get("gold_cost", 0) or 0)
        hp_loss = int(payload.get("hp_loss", 0) or 0)
        if gold_cost > 0:
            if run_state.gold < gold_cost:
                return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, gold_cost)
            run_state.gold -= gold_cost
        removed_card, remove_logs = remove_card_from_master_deck(run_state, deck_index, reason="event")
        if removed_card is None:
            return False, "\n".join(remove_logs)
        logs = []
        after_text = payload.get("after_text", "")
        if after_text:
            logs.append(after_text)
        if gold_cost > 0:
            logs.append("花费 {} 金币。当前金币：{}。".format(gold_cost, run_state.gold))
        logs.extend(remove_logs)
        if hp_loss > 0:
            old_hp, new_hp = lose_hp(run_state, hp_loss)
            logs.append("失去 {} 点生命：{} -> {}。".format(hp_loss, old_hp, new_hp))
        return True, "\n".join(logs)

    if effect == "select_transform_card":
        deck_index = int(payload.get("deck_index", -1))
        gold_cost = int(payload.get("gold_cost", 0) or 0)
        if gold_cost > 0:
            if run_state.gold < gold_cost:
                return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, gold_cost)
            run_state.gold -= gold_cost
        old_card, new_card, logs = transform_card_in_master_deck(run_state, deck_index, rng=rng)
        if old_card is None:
            return False, "\n".join(logs)
        after_text = payload.get("after_text", "")
        if after_text:
            logs.insert(0, after_text)
        if gold_cost > 0:
            logs.append("花费 {} 金币。当前金币：{}。".format(gold_cost, run_state.gold))
        return True, "\n".join(logs)

    if effect == "select_upgrade_card":
        deck_index = int(payload.get("deck_index", -1))
        gold_cost = int(payload.get("gold_cost", 0) or 0)
        if gold_cost > 0:
            if run_state.gold < gold_cost:
                return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, gold_cost)
            run_state.gold -= gold_cost
        deck = getattr(run_state, "master_deck", []) or []
        if deck_index < 0 or deck_index >= len(deck):
            return False, "卡牌编号无效。"
        card = deck[deck_index]
        if getattr(card, "upgraded", False) and not getattr(card, "multi_upgrade", False):
            return False, "这张牌已经升级。"
        if not has_upgrade(card):
            return False, "这张牌不能升级。"
        upgraded_card = upgrade_card(card)
        upgraded_card = copy_bottled_flags(card, upgraded_card)
        deck[deck_index] = upgraded_card
        logs = []
        after_text = payload.get("after_text", "")
        if after_text:
            logs.append(after_text)
        if gold_cost > 0:
            logs.append("花费 {} 金币。当前金币：{}。".format(gold_cost, run_state.gold))
        logs.append("升级卡牌：【{}】 -> 【{}】。".format(card.name, upgraded_card.name))
        return True, "\n".join(logs)
    if effect == "nest_rob":
        amount = int(payload.get("gold", choice.amount or 99) or 99)
        logs = ["他们甚至完全没有注意到你的行动。"]
        logs.extend(gain_gold_with_relics(run_state, amount, source="巢穴"))
        return True, "\n".join(logs)

    if effect == "nest_stay":
        old_hp, new_hp = lose_hp(run_state, 6)
        logs = [
            "你决定留在队列中，看看究竟会发生什么。",
            "失去 6 点生命：{} -> {}。".format(old_hp, new_hp),
        ]
        logs.extend(add_card_to_master_deck_with_relics(
            run_state,
            create_card("card.ritual_dagger"),
            source="巢穴",
        ))
        logs.append("“咔~咔~咔-咔！”你也跟着喊了起来，为什么不呢？")
        return True, "\n".join(logs)

    if effect == "hobo_pay":
        cost = int(choice.amount or 85)
        if run_state.gold < cost:
            return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, cost)

        run_state.gold -= cost
        logs = ["失去 {} 金币。当前金币：{}。".format(cost, run_state.gold)]
        logs.extend(add_random_relic(run_state, rng))
        logs.append("“啊啊，太好了，太好了！来，给你，这很公平吧！”")
        return True, "\n".join(logs)

    if effect == "hobo_rob":
        logs = ["你一把抓过他手中珍贵的遗物转身就走。"]
        logs.extend(add_random_relic(run_state, rng))
        logs.append(add_curse(run_state, "card.curse.shame"))
        logs.append("“你不知道什么是羞耻吗？你就不知道~什么是羞耻吗？！~”")
        return True, "\n".join(logs)

    if effect == "ancient_writing_remove":
        ok, text = build_deck_selection(
            state,
            run_state,
            "答案当然是简洁。请选择要移除的牌。",
            "select_remove_card",
            payload={"after_text": "答案当然是简洁。"},
        )
        return False, text if ok else text

    if effect == "ancient_writing_upgrade":
        logs = ["真相总是朴素的。"]
        count = 0

        for index, card in enumerate(list(getattr(run_state, "master_deck", []) or [])):
            if not (is_basic_strike_card(card) or is_basic_defend_card(card)):
                continue
            if not has_upgrade(card):
                continue

            upgraded = upgrade_card(card)
            upgraded = copy_bottled_flags(card, upgraded)
            run_state.master_deck[index] = upgraded
            logs.append("升级：【{}】 -> 【{}】。".format(card.name, upgraded.name))
            count += 1

        if count <= 0:
            logs.append("没有可升级的打击或防御。")

        return True, "\n".join(logs)

    if effect == "old_beggar_pay":
        cost = int(choice.amount or 75)
        if run_state.gold < cost:
            return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, cost)

        ok, text = build_deck_selection(
            state,
            run_state,
            "乞丐突然脱下了外套，原来他是牧师！请选择要移除的牌。",
            "select_remove_card",
            payload={
                "gold_cost": cost,
                "after_text": "乞丐突然脱下了外套，原来他是牧师！\n“你真是个善良的人，接受我的净化吧！”",
            },
        )
        return False, text if ok else text

    if effect == "old_beggar_leave":
        return True, "乞丐在你经过时低头看着地板，喃喃自语：\n“你永远也成就不了什么事情的……永远不会。”"

    if effect == "forgotten_altar_idol":
        relic = remove_relic_by_id(run_state, "relic.golden_idol")
        if relic is None:
            return False, "你没有【金神像】。"

        logs = [
            "你小心翼翼地将金神像放到了祭坛上，一阵寒风瞬间吹过了房间。",
            "失去遗物：【{}】。".format(getattr(relic, "name", "金神像")),
        ]
        logs.extend(add_specific_relic(run_state, "relic.bloody_idol"))
        logs.append("你的金神像开始变暗，然后双眼开始流出血液。血始终也没有停止流下。")
        return True, "\n".join(logs)

    if effect == "forgotten_altar_sacrifice":
        percent = float(payload.get("percent", 0.25) or 0.25)
        amount, old_hp, new_hp = lose_hp_percent_of_max(run_state, percent)
        logs = [
            "你站在祭坛前，割开了你自己的手腕。",
            "失去 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp),
        ]
        logs.extend(increase_max_hp(run_state, 5, source_name="被遗忘的祭坛"))
        logs.append("你在一段时间后苏醒了过来，感觉自己体内有了新的潜力。")
        return True, "\n".join(logs)

    if effect == "forgotten_altar_deface":
        logs = ["你使劲开始砸面前的雕像，终于打破了这个房间对你施加的魔力。"]
        logs.append(add_curse(run_state, "card.curse.decay"))
        logs.append("四周回荡起一声黑暗的恸哭，你能感觉到诅咒的魔法渗入了你的骨髓。")
        return True, "\n".join(logs)

    if effect in ("skull_potion", "skull_gold", "skull_card"):
        uses = int(state.data.get("uses", 0) or 0)
        hp_loss = 6 + uses

        old_hp, new_hp = lose_hp(run_state, hp_loss)
        logs = ["失去 {} 点生命：{} -> {}。".format(hp_loss, old_hp, new_hp)]

        if effect == "skull_potion":
            logs.append("“喝了吧！”")
            logs.extend(add_random_potions_to_run(run_state, rng, 1))

        elif effect == "skull_gold":
            logs.append("“你们这些人类真是从来都不会变。愿望达成了。”")
            logs.extend(gain_gold_with_relics(run_state, 90, source="全知头骨"))

        else:
            card_id = pick_uncommon_colorless_card_id(rng)
            if card_id:
                logs.append("“说不定这个能行？”")
                logs.extend(add_card_to_master_deck_with_relics(
                    run_state,
                    create_card(card_id),
                    source="全知头骨",
                ))
            else:
                logs.append("没有可获得的罕见无色牌。")

        state.data["uses"] = uses + 1
        next_loss = 6 + int(state.data.get("uses", 0) or 0)

        state.choices = [
            EventChoice("来点喝的？得到一瓶药水。失去 {} 生命。".format(next_loss), "skull_potion"),
            EventChoice("财富？获得 90 金币。失去 {} 生命。".format(next_loss), "skull_gold"),
            EventChoice("成功？得到一张罕见无色牌。失去 {} 生命。".format(next_loss), "skull_card"),
            EventChoice("我要怎么离开？失去 6 生命。", "skull_leave"),
        ]

        logs.append("“还有没有别的？”")
        return False, "\n".join(logs) + "\n\n" + format_event(run_state)

    if effect == "skull_leave":
        old_hp, new_hp = lose_hp(run_state, 6)
        return True, "“看你背后，人类。”\n失去 6 点生命：{} -> {}。".format(old_hp, new_hp)

    if effect == "masked_bandits_pay":
        lost = int(getattr(run_state, "gold", 0) or 0)
        run_state.gold = 0
        return True, "失去所有金币：{}。\n嘿嘿嘿……谢谢你的金币啦！\n*噗嗤*……白痴……哈哈哈哈哈".format(lost)

    if effect == "masked_bandits_fight":
        from game.run_engine import start_forced_event_battle

        return False, start_forced_event_battle(
            run_state,
            encounter_id="encounter.event.masked_bandits",
            effective_node_type="event_elite",
            seed=seed,
            post_battle_effects=[
                {"type": "gain_relic", "relic_id": "relic.red_mask"},
            ],
            intro_text="你举起武器。强盗们大笑着围了上来。",
        )

    if effect in ("joust_murderer", "joust_owner"):
        cost = int(choice.amount or 50)

        if run_state.gold < cost:
            return False, "金币不足。当前金币：{}，需要：{}。".format(run_state.gold, cost)

        run_state.gold -= cost

        if effect == "joust_murderer":
            win = rng.random() < 0.70
            prize = 100
        else:
            win = rng.random() < 0.30
            prize = 250

        logs = [
            "失去 {} 金币。当前金币：{}。".format(cost, run_state.gold),
            "*哐啷*！！ *铛！！*",
            "*砰！！*",
        ]

        if win:
            logs.append("你赌赢了。虽然你还是搞不太清楚情况，但有得赚就好。")
            logs.extend(gain_gold_with_relics(run_state, prize, source="长枪决斗"))
        else:
            logs.append("你赌输了。但至少被长枪捅穿的人不是你。")

        return True, "\n".join(logs)

    if effect == "great_library_read":
        from game.reward import roll_card_rewards, get_card_reward_upgrade_chance

        cards = roll_card_rewards(
            count=20,
            rng=rng,
            upgrade_chance=get_card_reward_upgrade_chance(run_state),
            run_state=run_state,
        )

        make_event_card_reward(
            run_state,
            cards,
            "大图书馆：从 20 张牌中选择 1 张",
        )

        text = rng.choice([
            "这本书是关于一个被昆虫控制的想当英雄的少女的。读完书，你觉得心满意足。",
            "这本书是关于一个在群星旅行，最后落难在一个荒芜陌生星球上的男人的。读来令人神往。",
            "这本书是关于一个巨大的废弃地下建筑的。你开始思考是否在高塔中也存在着类似的关系网。",
        ])

        return True, text

    if effect == "great_library_sleep":
        amount, old_hp, new_hp = heal_by_max_hp_fraction(run_state, 1, 3)
        logs = [
            state.data.get("sleep_line", "傻子才读书呢。"),
            "你在沙发椅上打了个盹儿。\nZzz...zzz.....Zz....",
            "醒来后，你觉得神清气爽。",
            "恢复 {} 点生命：{} -> {}。".format(amount, old_hp, new_hp),
        ]
        return True, "\n".join(logs)

    if effect == "mausoleum_open":
        cursed = rng.random() < 0.50
        logs = []

        logs.extend(add_random_relic(run_state, rng))

        if cursed:
            logs.append(add_curse(run_state, "card.curse.writhe"))
            logs.append("一股黑雾涌了出来，淹没了整个房间！")
        else:
            logs.append("雾气很快消散了。你拿走了石棺中的遗物，离开了房间。")

        return True, "\n".join(logs)

    if effect == "vampires_accept":
        removed = remove_all_basic_strikes(run_state)
        amount, old_max, new_max, old_hp, new_hp = lose_max_hp_percent(run_state, 0.30)

        logs = [
            "高个男人抓住你的手臂将你拉了过去，他的尖牙咬进你的脖子。",
            "移除了 {} 张打击。".format(len(removed)),
            "失去 {} 点最大生命：{} -> {}，HP：{} -> {}。".format(amount, old_max, new_max, old_hp, new_hp),
        ]

        for _ in range(5):
            logs.extend(add_card_to_master_deck_with_relics(
                run_state,
                create_card("card.bite"),
                source="吸血鬼",
            ))

        logs.append("你必须进食……")
        return True, "\n".join(logs)

    if effect == "vampires_blood_vial":
        relic = remove_relic_by_id(run_state, "relic.blood_vial")

        if relic is None:
            return False, "你没有【小血瓶】。"

        removed = remove_all_basic_strikes(run_state)
        bite_count = len(removed)

        logs = [
            "失去遗物：【{}】。".format(getattr(relic, "name", "小血瓶")),
            "“主人的血……主人的血！主 人 的 血！！”",
            "移除了 {} 张打击。".format(len(removed)),
        ]

        for _ in range(bite_count):
            logs.extend(add_card_to_master_deck_with_relics(
                run_state,
                create_card("card.bite"),
                source="吸血鬼",
            ))

        logs.append("你必须进食……")
        return True, "\n".join(logs)

    if effect == "ghost_council_accept":
        amount, old_max, new_max, old_hp, new_hp = lose_max_hp_percent(run_state, 0.50)

        logs = [
            "浓重的黑烟笼罩了整个房间。",
            "失去 {} 点最大生命：{} -> {}，HP：{} -> {}。".format(amount, old_max, new_max, old_hp, new_hp),
        ]

        for _ in range(5):
            logs.extend(add_card_to_master_deck_with_relics(
                run_state,
                create_card("card.ghostly"),
                source="幽灵议会",
            ))

        logs.append("你重新上路，但总觉得自己的内心变得有些空洞。")
        return True, "\n".join(logs)

    if effect == "ghost_council_refuse":
        return True, "“真令人失望....”\n“反正你迟早会成为我们的一员。”\n“哈哈哈哈哈哈!”"

    if effect == "arena_start":
        from game.run_engine import start_forced_event_battle

        return False, start_forced_event_battle(
            run_state,
            encounter_id="encounter.event.arena_slavers_first",
            effective_node_type="event_normal",
            seed=seed,
            post_battle_effects=[
                {"type": "arena_after_first"},
            ],
            intro_text="在你对面的大门缓缓打开了……",
        )

    if effect == "arena_coward":
        return True, "你从竞技场围墙上那个小小的缺口逃了出去。"

    if effect == "arena_continue":
        from game.run_engine import start_forced_event_battle

        return False, start_forced_event_battle(
            run_state,
            encounter_id="encounter.event.arena_final",
            effective_node_type="arena_final",
            seed=seed,
            post_battle_effects=[
                {"type": "arena_final_rewards"},
            ],
            intro_text="你选择留下来。观众席爆发出刺耳的欢呼声。",
        )
    return False, "未知事件效果：{}。".format(effect)
