# -*- coding: utf-8 -*-
# 先古之民节点

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List

from data.card.AAAregistry import CARD_REGISTRY, create_card
from data.card.special_curses import is_source_only_curse_card_id
from data.card.upgrade_rules import has_upgrade, upgrade_card
from data.content_gate import is_content_enabled
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from game.command_help import command_tip
from game.deck_utils import remove_card_from_master_deck, transform_card_in_master_deck
from game.node.node_rest import get_upgradable_cards
from game.relic_logic.bottle_utils import copy_bottled_flags
from game.relic_logic.run_relic_utils import (
    add_card_to_master_deck_with_relics,
    gain_gold_with_relics,
    increase_max_hp,
)
from game.reward import (
    RewardOption,
    RewardState,
    create_potion_reward_state,
    get_available_boss_relic_ids,
    get_available_potion_ids_by_quantity,
    get_available_relic_ids,
    get_card_reward_pool,
    record_reward_options_offered,
    roll_card_rewards,
    roll_potion_id_by_rarity,
    roll_rare_card_rewards,
)


@dataclass
class AncientChoice:
    title: str
    effect_type: str
    amount: int = 0
    payload: Any = None


@dataclass
class AncientState:
    title: str = "？？？"
    description: str = "沉默的存在注视着你。"
    choices: List[AncientChoice] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


LOW_REWARD_KEYS = (
    "gain_max_hp",
    "gain_neows_lament",
    "remove_one",
    "transform_one",
    "upgrade_one",
    "choose_random_cards",
    "gain_character_rare",
    "gain_uncommon_colorless",
    "gain_common_relic",
    "gain_gold_100",
    "gain_three_potions",
)

COST_KEYS = (
    "lose_max_hp",
    "take_damage",
    "gain_curse",
    "lose_all_gold",
)

HIGH_REWARD_KEYS = (
    "remove_two",
    "transform_two",
    "gain_gold_250",
    "choose_rare_cards",
    "gain_two_colorless",
    "gain_rare_relic",
    "gain_double_max_hp",
)


def _get_base_value(run_state):
    character_id = str(getattr(run_state, "character_id", "") or "")
    if character_id == "character.armored_warrior":
        return 8
    if character_id == "character.silent_huntress":
        return 6
    return 6


def _next_rng(state, seed=None, salt=0):
    counter = int(state.data.get("_rng_counter", 0) or 0)
    state.data["_rng_counter"] = counter + 1
    return random.Random(int(seed or 0) + int(salt) + counter * 1009)


def _is_removable_card(card):
    if getattr(card, "unremovable", False):
        return False
    return getattr(card, "card_id", "") not in (
        "card.curse.bell",
        "card.curse.necronomicurse",
    )


def _is_transformable_card(card):
    if getattr(card, "untransformable", False):
        return False
    return getattr(card, "card_id", "") != "card.curse.necronomicurse"


def _get_colorless_card_ids(allowed_quantities=("uncommon", "rare")):
    result = []
    allowed_quantities = set(allowed_quantities)

    for card_id in CARD_REGISTRY.keys():
        if not is_content_enabled("card", card_id):
            continue
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "owner_character_id", ""):
            continue
        if getattr(card, "card_type", "") not in ("attack", "skill", "power"):
            continue
        if getattr(card, "quantity", "") not in allowed_quantities:
            continue
        result.append(card_id)

    return result


def _get_character_rare_card_ids(run_state):
    result = []
    for card_id in get_card_reward_pool(run_state):
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "quantity", "") == "rare":
            result.append(card_id)
    return result


def _get_relic_ids_by_quantity(run_state, quantity):
    result = []
    for relic_id in get_available_relic_ids(run_state):
        try:
            relic = create_relic(relic_id)
        except Exception:
            continue
        if getattr(relic, "quantity", "") == quantity:
            result.append(relic_id)
    return result


def _has_available_potion(run_state):
    pools = get_available_potion_ids_by_quantity(
        run_state=run_state,
        include_event=False,
        include_test=False,
    )
    return any(pools.values())


def _get_low_reward_candidates(run_state):
    deck = list(getattr(run_state, "master_deck", []) or [])
    result = list(LOW_REWARD_KEYS)

    if not any(_is_removable_card(card) for card in deck):
        result.remove("remove_one")
    if not any(_is_transformable_card(card) for card in deck):
        result.remove("transform_one")
    if not get_upgradable_cards(run_state):
        result.remove("upgrade_one")
    if not get_card_reward_pool(run_state):
        result.remove("choose_random_cards")
    if not _get_character_rare_card_ids(run_state):
        result.remove("gain_character_rare")
    if not _get_colorless_card_ids(("uncommon",)):
        result.remove("gain_uncommon_colorless")
    if not _get_relic_ids_by_quantity(run_state, "common"):
        result.remove("gain_common_relic")
    if not _has_available_potion(run_state):
        result.remove("gain_three_potions")

    return result


def _get_high_reward_candidates(run_state, cost_key):
    deck = list(getattr(run_state, "master_deck", []) or [])
    result = list(HIGH_REWARD_KEYS)

    if sum(1 for card in deck if _is_removable_card(card)) < 2:
        result.remove("remove_two")
    if sum(1 for card in deck if _is_transformable_card(card)) < 2:
        result.remove("transform_two")
    if not _get_colorless_card_ids(("uncommon", "rare")):
        result.remove("gain_two_colorless")
    if not _get_relic_ids_by_quantity(run_state, "rare"):
        result.remove("gain_rare_relic")
    if not _get_character_rare_card_ids(run_state):
        result.remove("choose_rare_cards")

    # 直接失去与直接获得最大生命值不组成同一个选项。
    if cost_key == "lose_max_hp" and "gain_double_max_hp" in result:
        result.remove("gain_double_max_hp")

    # 获得诅咒不会与移除两张牌配对。
    if cost_key == "gain_curse" and "remove_two" in result:
        result.remove("remove_two")

    return result


def _low_reward_title(key, base_value):
    mapping = {
        "gain_max_hp": "最大生命值 +{}。".format(base_value),
        "gain_neows_lament": "获得遗物【涅奥的悲恸】。",
        "remove_one": "从你的牌组内选择一张牌移除。",
        "transform_one": "从你的牌组内选择一张牌变化。",
        "upgrade_one": "从你的牌组内选择一张牌升级。",
        "choose_random_cards": "从 3 张随机稀有度的牌中选择一张加入牌组。",
        "gain_character_rare": "获得本角色的一张随机稀有牌。",
        "gain_uncommon_colorless": "获得一张随机罕见无色卡。",
        "gain_common_relic": "获得一件随机普通遗物。",
        "gain_gold_100": "获得 100 金币。",
        "gain_three_potions": "获得 3 瓶随机药水。",
    }
    return mapping[key]


def _cost_title(key, base_value):
    damage = max(18, int(math.ceil(base_value * 2.5)))
    mapping = {
        "lose_max_hp": "失去 {} 点最大生命值".format(base_value),
        "take_damage": "受到 {} 点伤害".format(damage),
        "gain_curse": "获得一张随机诅咒牌",
        "lose_all_gold": "失去所有金币",
    }
    return mapping[key]


def _high_reward_title(key, base_value):
    mapping = {
        "remove_two": "从你的牌组内选择 2 张牌移除",
        "transform_two": "从你的牌组内选择 2 张牌变化",
        "gain_gold_250": "获得 250 金币",
        "choose_rare_cards": "从 3 张稀有牌中选择一张加入牌组",
        "gain_two_colorless": "随机获得 2 张无色卡",
        "gain_rare_relic": "获得一件随机稀有遗物",
        "gain_double_max_hp": "最大生命值 +{}".format(base_value * 2),
    }
    return mapping[key]


def create_ancient_state(run_state, seed=None):
    node = run_state.get_current_node()
    node_id = getattr(node, "node_id", "")

    # 只有一层入口提供开局奖励；后续层入口的先古之民只做过渡。
    is_act1_opening = node_id.startswith("act1.")
    if not is_act1_opening or "after_boss" in node_id:
        return AncientState(
            description="先古之民站在通往下一层的门前。",
            choices=[AncientChoice("继续前进。", "continue")],
        )

    rng = random.Random(seed)
    base_value = _get_base_value(run_state)
    cost_key = rng.choice(COST_KEYS)
    high_reward_key = rng.choice(_get_high_reward_candidates(run_state, cost_key))

    blocked_low_rewards = set()

    # 失去最大生命值时，不再出现低阶的直接最大生命奖励。
    # 高阶直接最大生命奖励已经在配对池中排除。
    if cost_key == "lose_max_hp" or high_reward_key == "gain_double_max_hp":
        blocked_low_rewards.add("gain_max_hp")

    # 失去全部金币时，不再出现独立的 100 金币选项。
    # “失去全部金币，然后获得 250 金币”仍允许，结算顺序为先失去后获得。
    if cost_key == "lose_all_gold" or high_reward_key == "gain_gold_250":
        blocked_low_rewards.add("gain_gold_100")

    low_candidates = [
        key for key in _get_low_reward_candidates(run_state)
        if key not in blocked_low_rewards
    ]
    if len(low_candidates) < 2:
        raise RuntimeError("先古之民低阶奖励池不足 2 项。")

    low_keys = rng.sample(low_candidates, 2)

    return AncientState(
        description="‘僚机’所予之物。",
        choices=[
            AncientChoice(_low_reward_title(low_keys[0], base_value), "low_reward", payload={"key": low_keys[0]}),
            AncientChoice(_low_reward_title(low_keys[1], base_value), "low_reward", payload={"key": low_keys[1]}),
            AncientChoice(
                "【{}】，然后【{}】。".format(
                    _cost_title(cost_key, base_value),
                    _high_reward_title(high_reward_key, base_value),
                ),
                "cost_reward",
                payload={"cost_key": cost_key, "reward_key": high_reward_key},
            ),
            AncientChoice(
                "以一件随机 Boss 遗物替换玩家的全部初始遗物。",
                "replace_starting_relic",
            ),
        ],
        data={
            "phase": "top_level",
            "base_value": base_value,
            "cost_key": cost_key,
            "high_reward_key": high_reward_key,
            "_rng_counter": 0,
        },
    )


def format_ancient(run_state):
    state = run_state.pending_ancient

    if state is None:
        return "当前没有先古之民事件。"

    lines = ["=== {} ===".format(state.title), state.description, ""]

    for index, choice in enumerate(state.choices):
        lines.append("[{}] {}".format(index, choice.title))

    lines.append("")
    lines.append(command_tip("ancient", "使用 /card ancient 0 选择。"))

    return "\n".join(lines)


def _build_deck_selection(state, run_state, action, count, selected_indices=None):
    selected_indices = list(selected_indices or [])
    choices = []

    for deck_index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if deck_index in selected_indices:
            continue
        if action == "remove" and not _is_removable_card(card):
            continue
        if action == "transform" and not _is_transformable_card(card):
            continue
        if action == "upgrade":
            if not has_upgrade(card):
                continue
            if getattr(card, "upgraded", False) and not getattr(card, "multi_upgrade", False):
                continue

        choices.append(AncientChoice(
            "牌组编号 {}：{}".format(deck_index, card.summary_text()),
            "deck_select",
            payload={"deck_index": deck_index},
        ))

    needed = int(count) - len(selected_indices)
    if len(choices) < needed:
        return False

    action_name = {
        "remove": "移除",
        "transform": "变化",
        "upgrade": "升级",
    }[action]

    state.data.update({
        "phase": "deck_selection",
        "deck_action": action,
        "required_count": int(count),
        "selected_indices": selected_indices,
    })
    state.description = "请选择 {} 张牌进行{}。已选择 {}/{} 张。".format(
        count,
        action_name,
        len(selected_indices),
        count,
    )
    state.choices = choices
    return True


def _start_card_reward(run_state, cards, title):
    reward_state = RewardState(
        node_type="event",
        options=[RewardOption(
            option_type="card",
            title=title,
            payload={"cards": cards},
        )],
    )
    run_state.pending_reward = reward_state
    record_reward_options_offered(run_state, reward_state)
    return ["已生成卡牌选择。"]


def _start_potion_reward(run_state, rng, count):
    potions = []
    for _ in range(int(count)):
        potion_id = roll_potion_id_by_rarity(
            rng,
            run_state=run_state,
            include_event=False,
        )
        if potion_id:
            potions.append(create_potion(potion_id))

    if not potions:
        return ["当前没有可获得的药水。"]

    reward_state = create_potion_reward_state(
        potions,
        node_type="event",
        title_prefix="先古之民药水",
    )
    run_state.pending_reward = reward_state
    record_reward_options_offered(run_state, reward_state)
    return ["获得 {} 瓶随机药水，已加入待领取奖励。".format(len(potions))]


def _obtain_relic(run_state, relic_id, source_name="先古之民"):
    relic = create_relic(relic_id)
    run_state.relics.append(relic)
    logs = ["{}：获得遗物【{}】。".format(source_name, relic.name)]
    on_obtained = getattr(relic, "on_obtained", None)
    if on_obtained is not None:
        result = on_obtained(run_state)
        if result:
            logs.extend(result)
    return logs


def _roll_random_curse_id(rng):
    candidates = []
    for card_id in CARD_REGISTRY.keys():
        if not is_content_enabled("card", card_id):
            continue
        if card_id == "card.curse.bell" or is_source_only_curse_card_id(card_id):
            continue
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "card_type", "") == "curse":
            candidates.append(card_id)
    return rng.choice(candidates) if candidates else "card.curse.injury"


def _apply_cost(run_state, cost_key, base_value, rng):
    logs = []

    if cost_key == "lose_max_hp":
        old_max_hp = int(getattr(run_state, "max_hp", 0) or 0)
        old_hp = int(getattr(run_state, "hp", 0) or 0)
        run_state.max_hp = max(1, old_max_hp - int(base_value))
        run_state.hp = min(old_hp, run_state.max_hp)
        logs.append("失去 {} 点最大生命值：最大生命 {} -> {}，HP {} -> {}。".format(
            base_value,
            old_max_hp,
            run_state.max_hp,
            old_hp,
            run_state.hp,
        ))
        return logs

    if cost_key == "take_damage":
        damage = max(18, int(math.ceil(base_value * 2.5)))
        old_hp = int(getattr(run_state, "hp", 0) or 0)
        run_state.hp = max(0, old_hp - damage)
        logs.append("受到 {} 点伤害：HP {} -> {}。".format(damage, old_hp, run_state.hp))
        return logs

    if cost_key == "gain_curse":
        curse = create_card(_roll_random_curse_id(rng))
        logs.extend(add_card_to_master_deck_with_relics(run_state, curse, source="先古之民代价"))
        return logs

    if cost_key == "lose_all_gold":
        old_gold = int(getattr(run_state, "gold", 0) or 0)
        run_state.gold = 0
        logs.append("失去全部金币：{} -> 0。".format(old_gold))
        return logs

    return ["未知先古之民代价：{}。".format(cost_key)]


def _apply_low_reward(run_state, state, key, base_value, rng):
    if key == "gain_max_hp":
        return True, "\n".join(increase_max_hp(run_state, base_value, source_name="先古之民"))

    if key == "gain_neows_lament":
        return True, "\n".join(_obtain_relic(run_state, "relic.neows_lament"))

    if key == "remove_one":
        if not _build_deck_selection(state, run_state, "remove", 1):
            return True, "当前没有可移除的牌。"
        return False, format_ancient(run_state)

    if key == "transform_one":
        if not _build_deck_selection(state, run_state, "transform", 1):
            return True, "当前没有可变化的牌。"
        return False, format_ancient(run_state)

    if key == "upgrade_one":
        if not _build_deck_selection(state, run_state, "upgrade", 1):
            return True, "当前没有可升级的牌。"
        return False, format_ancient(run_state)

    if key == "choose_random_cards":
        cards = roll_card_rewards(
            count=3,
            rng=rng,
            upgrade_chance=0.0,
            run_state=run_state,
        )
        logs = _start_card_reward(run_state, cards, "先古之民：随机稀有度卡牌（三选一）")
        return True, "\n".join(logs)

    if key == "gain_character_rare":
        card_ids = _get_character_rare_card_ids(run_state)
        if not card_ids:
            return True, "当前角色没有可获得的稀有牌。"
        card = create_card(rng.choice(card_ids))
        logs = add_card_to_master_deck_with_relics(run_state, card, source="先古之民")
        return True, "\n".join(logs)

    if key == "gain_uncommon_colorless":
        card_ids = _get_colorless_card_ids(("uncommon",))
        if not card_ids:
            return True, "当前没有可获得的罕见无色卡。"
        card = create_card(rng.choice(card_ids))
        logs = add_card_to_master_deck_with_relics(run_state, card, source="先古之民")
        return True, "\n".join(logs)

    if key == "gain_common_relic":
        relic_ids = _get_relic_ids_by_quantity(run_state, "common")
        if not relic_ids:
            return True, "当前没有可获得的普通遗物。"
        return True, "\n".join(_obtain_relic(run_state, rng.choice(relic_ids)))

    if key == "gain_gold_100":
        return True, "\n".join(gain_gold_with_relics(run_state, 100, source="先古之民"))

    if key == "gain_three_potions":
        return True, "\n".join(_start_potion_reward(run_state, rng, 3))

    return False, "未知低阶奖励：{}。".format(key)


def _apply_high_reward(run_state, state, key, base_value, rng):
    if key == "remove_two":
        if not _build_deck_selection(state, run_state, "remove", 2):
            return True, "当前没有两张可移除的牌。"
        return False, format_ancient(run_state)

    if key == "transform_two":
        if not _build_deck_selection(state, run_state, "transform", 2):
            return True, "当前没有两张可变化的牌。"
        return False, format_ancient(run_state)

    if key == "gain_gold_250":
        return True, "\n".join(gain_gold_with_relics(run_state, 250, source="先古之民"))

    if key == "choose_rare_cards":
        cards = roll_rare_card_rewards(
            count=3,
            rng=rng,
            upgrade_chance=0.0,
            run_state=run_state,
        )
        logs = _start_card_reward(run_state, cards, "先古之民：稀有牌（三选一）")
        return True, "\n".join(logs)

    if key == "gain_two_colorless":
        pool = _get_colorless_card_ids(("uncommon", "rare"))
        if not pool:
            return True, "当前没有可获得的无色卡。"
        if len(pool) >= 2:
            chosen_ids = rng.sample(pool, 2)
        else:
            chosen_ids = [rng.choice(pool), rng.choice(pool)]
        logs = []
        for card_id in chosen_ids:
            card = create_card(card_id)
            logs.extend(add_card_to_master_deck_with_relics(run_state, card, source="先古之民"))
        return True, "\n".join(logs)

    if key == "gain_rare_relic":
        relic_ids = _get_relic_ids_by_quantity(run_state, "rare")
        if not relic_ids:
            return True, "当前没有可获得的稀有遗物。"
        return True, "\n".join(_obtain_relic(run_state, rng.choice(relic_ids)))

    if key == "gain_double_max_hp":
        amount = int(base_value) * 2
        return True, "\n".join(increase_max_hp(run_state, amount, source_name="先古之民"))

    return False, "未知高阶奖励：{}。".format(key)


def _resolve_deck_selection(run_state, state, choice, rng):
    payload = dict(choice.payload or {})
    deck_index = int(payload.get("deck_index", -1))
    action = state.data.get("deck_action", "")
    required_count = int(state.data.get("required_count", 1) or 1)
    selected_indices = list(state.data.get("selected_indices", []) or [])
    deck = getattr(run_state, "master_deck", []) or []

    if deck_index < 0 or deck_index >= len(deck):
        return False, "卡牌编号无效。"
    if deck_index in selected_indices:
        return False, "需要选择不同的牌。"

    card = deck[deck_index]
    if action == "remove" and not _is_removable_card(card):
        return False, "这张牌无法移除。"
    if action == "transform" and not _is_transformable_card(card):
        return False, "这张牌无法变化。"
    if action == "upgrade":
        if not has_upgrade(card):
            return False, "这张牌不能升级。"
        if getattr(card, "upgraded", False) and not getattr(card, "multi_upgrade", False):
            return False, "这张牌已经升级。"

    selected_indices.append(deck_index)

    if len(selected_indices) < required_count:
        if not _build_deck_selection(
            state,
            run_state,
            action,
            required_count,
            selected_indices=selected_indices,
        ):
            return False, "剩余牌组中没有足够的合法选择。"
        return False, format_ancient(run_state)

    logs = []

    if action == "remove":
        for index in sorted(selected_indices, reverse=True):
            removed, sub_logs = remove_card_from_master_deck(run_state, index, reason="ancient")
            if removed is None:
                return False, "\n".join(sub_logs)
            logs.extend(sub_logs)
        return True, "\n".join(logs)

    if action == "transform":
        for index in sorted(selected_indices, reverse=True):
            old_card, new_card, sub_logs = transform_card_in_master_deck(run_state, index, rng=rng)
            if old_card is None:
                return False, "\n".join(sub_logs)
            logs.extend(sub_logs)
        return True, "\n".join(logs)

    if action == "upgrade":
        for index in selected_indices:
            card = run_state.master_deck[index]
            upgraded_card = upgrade_card(card)
            upgraded_card = copy_bottled_flags(card, upgraded_card)
            run_state.master_deck[index] = upgraded_card
            logs.append("升级卡牌：【{}】 -> 【{}】。".format(card.name, upgraded_card.name))
        return True, "\n".join(logs)

    return False, "未知牌组选择效果：{}。".format(action)


def _replace_starting_relics(run_state, rng):
    starting_relics = [
        relic for relic in getattr(run_state, "relics", []) or []
        if getattr(relic, "quantity", "") == "starting"
    ]
    if not starting_relics:
        return True, "当前没有可替换的初始遗物。"

    boss_relic_ids = [
        relic_id for relic_id in get_available_boss_relic_ids(run_state)
        if relic_id != "relic.xanthosis"
    ]
    if not boss_relic_ids:
        return True, "当前没有可获得的 Boss 遗物。"

    relic_id = rng.choice(boss_relic_ids)
    starting_ids = {id(relic) for relic in starting_relics}
    run_state.relics = [
        relic for relic in run_state.relics
        if id(relic) not in starting_ids
    ]

    logs = ["失去初始遗物：{}。".format(
        "，".join("【{}】".format(relic.name) for relic in starting_relics)
    )]
    logs.extend(_obtain_relic(run_state, relic_id, source_name="先古之民替换"))
    return True, "\n".join(logs)


def choose_ancient_option(run_state, choice_index, seed=None):
    state = run_state.pending_ancient

    if state is None:
        return False, "当前没有先古之民事件。"

    if choice_index < 0 or choice_index >= len(state.choices):
        return False, "选项编号无效。"

    choice = state.choices[choice_index]
    rng = _next_rng(state, seed=seed, salt=choice_index * 97)

    if choice.effect_type == "continue":
        return True, "继续前进。"

    if choice.effect_type == "deck_select":
        return _resolve_deck_selection(run_state, state, choice, rng)

    base_value = int(state.data.get("base_value", _get_base_value(run_state)) or 0)

    if choice.effect_type == "low_reward":
        key = dict(choice.payload or {}).get("key", "")
        return _apply_low_reward(run_state, state, key, base_value, rng)

    if choice.effect_type == "cost_reward":
        payload = dict(choice.payload or {})
        cost_key = payload.get("cost_key", "")
        reward_key = payload.get("reward_key", "")
        cost_logs = _apply_cost(run_state, cost_key, base_value, rng)
        done, reward_text = _apply_high_reward(
            run_state,
            state,
            reward_key,
            base_value,
            rng,
        )
        parts = list(cost_logs)
        if reward_text:
            parts.extend(["", reward_text])
        return done, "\n".join(parts)

    if choice.effect_type == "replace_starting_relic":
        return _replace_starting_relics(run_state, rng)

    return False, "未知先古之民效果：{}。".format(choice.effect_type)
