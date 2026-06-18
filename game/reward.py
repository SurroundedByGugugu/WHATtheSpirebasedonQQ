# -*- coding: utf-8 -*-
# 战斗胜利后的奖励：选牌、金币、药水、遗物等

import copy
import random

from dataclasses import dataclass, field
from typing import List, Any

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card, has_upgrade
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from game.constants import DEBUG_SEED


# =========================
# 奖励池
# =========================

CARD_REWARD_POOL = [
    "card.gain_status_strength",
    "card.exhaust_strength",
    "card.ethereal_strength",
    "card.retain_strength",
    "card.clever_strength",
    "card.innate_thorns",
    "card.draw_discard_test",
    "card.test_heavy_strike",
    "card.hard_blow",
    "card.test_x_drill",

    "card.whirlwind",
    "card.clothesline",
    "card.heavy_blade",
    "card.anger",
    "card.double_strike",
    "card.sword_boomerang",
    "card.thunderclap",
    "card.cleave",
    "card.iron_wave",
    "card.wild_strike",
    "card.pommel_strike",
    "card.perfected_strike",
    "card.headbutt",
    "card.body_slam",
    "card.clash",
    "card.havoc",
    "card.shrug_it_off",
    "card.true_grit",
    "card.warcry",
    "card.uppercut",
    "card.pummel",
    "card.carnage",
    "card.reckless_charge",
    "card.bludgeon",
    "card.blood_for_blood",
    "card.dropkick",
    "card.hemokinesis",
    "card.rampage",
    "card.searing_blow",
    "card.sever_soul",
    "card.immolate_history",
    "card.shockwave",
    "card.intimidate",
    "card.battle_trance",
    "card.bloodletting",
    "card.burning_pact",
    "card.disarm",
    "card.dual_wield",
    "card.entrench",
    "card.flame_barrier",
    "card.ghostly_armor",
    "card.infernal_blade",
    "card.power_through",
    "card.rage",
    "card.second_wind",
    "card.seeing_red",
    "card.sentinel",
    "card.spot_weakness",
    "card.death_reaper",
    "card.immolate",
    "card.fiend_fire",
    "card.feed",
    "card.demon_form",
    "card.fire_strike",
    "card.fire_zone",

    "card.crystal_piercing",
    "card.crystal_zone",

    "card.mirage_shadows",
    "card.god_in_hand",
    "card.transfer",
    "card.inducing",
    "card.cheap_intuition",
    "card.energetic",
    "card.factor_separate",
    "card.fast_transfer",
    "card.brain_shockwave",
    "card.ok_next",
]

POTION_REWARD_POOL = [
    "potion.test_strength",
    "potion.test_fire",
    "potion.test_dexterity"
]

# 当前只有占位符石头。
# 如果不希望重复获得已有遗物，可以在 roll_relic_reward() 里过滤。
RELIC_REWARD_POOL = [
    "relic.placeholder_stone",
    "relic.ether_medium",
    "relic.charon_ashes",
    "relic.homunculus_prototype",
]

SHOP_RELIC_POOL = [
    "relic.x_potion",
]

COMMON_RELIC_POOL = [
]

UNCOMMON_RELIC_POOL = [
]

RARE_RELIC_POOL = [
]

EVENT_RELIC_POOL = [
]

MYTH_RELIC_POOL = [
]

SHOP_RELIC_POOL = [
]


# =========================
# 奖励参数
# =========================

POTION_DROP_CHANCE = 0.30

# 卡牌升级概率：
# 已完成节点数 * 每节点基础概率 * 系数
CARD_UPGRADE_CHANCE_PER_COMPLETED_NODE = 0.05
CARD_UPGRADE_CHANCE_MAX = 0.80

GOLD_RANGE_BY_NODE_TYPE = {
    "normal_enemy": (10, 20),
    "elite": (25, 40),
    "boss": (80, 120),
}

# 遗物奖励概率与战斗节点类型相关。
# 当前建议：普通战斗不掉遗物，精英和 Boss 必掉。
RELIC_CHANCE_BY_NODE_TYPE = {
    "normal_enemy": 0.0,
    "elite": 1.0,
    "boss": 1.0,
}


@dataclass
class RewardOption:
    """
    一个可领取的奖励选项。

    option_type:
    - gold
    - relic
    - potion
    - card
    """

    option_type: str
    title: str
    payload: Any = None
    claimed: bool = False
    skipped: bool = False


@dataclass
class RewardState:
    """
    战斗胜利后的奖励状态。

    现在不再自动拾取。
    所有奖励都作为 options 等待玩家领取。
    """

    node_type: str = ""
    options: List[RewardOption] = field(default_factory=list)

    # 当前是否正在查看某个卡牌奖励选项
    active_card_option_index: int = -1

    def reward_text(self):
        lines = []
        lines.append("=== 战斗奖励 ===")

        if not self.options:
            lines.append("没有可领取的奖励。")
            return "\n".join(lines)

        for index, option in enumerate(self.options):
            status = ""

            if option.claimed:
                status = "（已领取）"
            elif option.skipped:
                status = "（已放弃）"

            lines.append("[{}] {}{}".format(
                index,
                option.title,
                status
            ))

        lines.append("")
        lines.append("使用 /card take 0 领取奖励。")
        lines.append("使用 /card take 0,1,2 批量领取奖励。")
        lines.append("卡牌奖励需要先 /card take 对应编号，再 /card pick 0 选择卡牌。")
        lines.append("使用 /card skip 放弃剩余奖励。")

        return "\n".join(lines)

    def all_done(self):
        for option in self.options:
            if not option.claimed and not option.skipped:
                return False
        return True

def create_battle_reward(run_state, node_type, seed=DEBUG_SEED):
    """
    生成一次战斗胜利奖励。

    注意：
    这里只生成奖励选项，不自动写入 RunState。
    """
    rng = random.Random(seed)

    reward_state = RewardState(
        node_type=node_type
    )

    # 1. 金币奖励
    gold = roll_gold_reward(node_type, rng)
    reward_state.options.append(RewardOption(
        option_type="gold",
        title="{}金币".format(gold),
        payload={
            "amount": gold
        }
    ))

    # 2. 遗物奖励
    relic = roll_relic_reward(run_state, node_type, rng)
    if relic is not None:
        reward_state.options.append(RewardOption(
            option_type="relic",
            title="遗物：【{}】".format(relic.name),
            payload={
                "relic": relic
            }
        ))

    # 3. 药水奖励，没roll到就不显示
    potion = roll_potion_reward(rng)
    if potion is not None:
        reward_state.options.append(RewardOption(
            option_type="potion",
            title="药水：【{}】".format(potion.name),
            payload={
                "potion": potion
            }
        ))

    # 4. 卡牌奖励
    upgrade_chance = get_card_reward_upgrade_chance(run_state)
    card_choices = roll_card_rewards(
        count=3,
        rng=rng,
        upgrade_chance=upgrade_chance,
        run_state=run_state
    )

    reward_state.options.append(RewardOption(
        option_type="card",
        title="卡牌：（选择以查看具体选项）",
        payload={
            "cards": card_choices
        }
    ))

    record_reward_options_offered(run_state, reward_state)
    return reward_state

def record_reward_options_offered(run_state, reward_state):
    run_state.init_reward_stats_if_needed()

    for option in reward_state.options:
        if option.option_type == "gold":
            run_state.reward_stats["gold_offered"] += 1
        elif option.option_type == "relic":
            run_state.reward_stats["relic_offered"] += 1
        elif option.option_type == "potion":
            run_state.reward_stats["potion_offered"] += 1
        elif option.option_type == "card":
            run_state.reward_stats["card_reward_offered"] += 1


def record_reward_taken(run_state, option_type):
    run_state.init_reward_stats_if_needed()

    key = "{}_taken".format(_reward_stat_prefix(option_type))

    if key in run_state.reward_stats:
        run_state.reward_stats[key] += 1


def record_reward_skipped(run_state, option_type):
    run_state.init_reward_stats_if_needed()

    key = "{}_skipped".format(_reward_stat_prefix(option_type))

    if key in run_state.reward_stats:
        run_state.reward_stats[key] += 1


def _reward_stat_prefix(option_type):
    if option_type == "card":
        return "card_reward"

    return option_type

def count_relic(run_state, relic_id):
    count = 0
    for relic in run_state.relics:
        if getattr(relic, "relic_id", "") == relic_id:
            count += 1
    return count


def on_relic_obtained(run_state, relic):
    """
    获得遗物后的特殊检查。
    当前占位：
    - 造物原型达到一定数量后，未来可以触发隐藏事件 / 成就 / 特殊 Boss / 文本变化。
    """
    relic_id = getattr(relic, "relic_id", "")
    if relic_id == "relic.homunculus_prototype":
        count = count_relic(run_state, relic_id)
        # 先占位，不触发实际效果。
        if count >= 3:
            return "【造物原型】似乎正在发生某种变化……不过现在什么也没有发生。"
    return ""

def roll_gold_reward(node_type, rng):
    gold_range = GOLD_RANGE_BY_NODE_TYPE.get(node_type, (10, 20))
    return rng.randint(gold_range[0], gold_range[1])


def roll_potion_reward(rng):
    if rng.random() >= POTION_DROP_CHANCE:
        return None

    potion_id = rng.choice(POTION_REWARD_POOL)
    return create_potion(potion_id)


def roll_relic_reward(run_state, node_type, rng):
    chance = RELIC_CHANCE_BY_NODE_TYPE.get(node_type, 0.0)

    if rng.random() >= chance:
        return None

    available_relic_ids = get_available_relic_ids(run_state)

    if not available_relic_ids:
        return None

    relic_id = rng.choice(available_relic_ids)
    return create_relic(relic_id)


FALLBACK_RELIC_ID = "relic.homunculus_prototype"


def get_available_relic_ids(run_state):
    """
    获取当前还能获得的遗物 id。

    默认规则：
    - allow_duplicate=False 的遗物，已有后不再进入奖励池
    - allow_duplicate=True 的遗物，可以重复进入奖励池
    - relic.homunculus_prototype 不进入正常遗物池
    - 只有没有其他可获取遗物时，才返回 relic.homunculus_prototype 作为兜底
    """
    owned_relic_ids = set()

    for relic in run_state.relics:
        owned_relic_ids.add(getattr(relic, "relic_id", ""))

    result = []

    for relic_id in RELIC_REWARD_POOL:
        # 造物原型只作为兜底，不参与正常随机
        if relic_id == FALLBACK_RELIC_ID:
            continue
        relic = create_relic(relic_id)
        # 商店遗物不进入战斗 / 宝箱等普通遗物奖励池。
        if getattr(relic, "quantity", "") == "shop":
            continue
        relic_owner = getattr(relic, "owner_character_id", "")
        current_character_id = getattr(run_state, "character_id", "")
        if relic_owner and relic_owner != current_character_id:
            continue
        allow_duplicate = getattr(relic, "allow_duplicate", False)
        if allow_duplicate:
                result.append(relic_id)
                continue
        if relic_id not in owned_relic_ids:
            result.append(relic_id)

    if result:
        return result

    # 没有其他可获取遗物时，才给造物原型
    return [FALLBACK_RELIC_ID]


def get_card_reward_upgrade_chance(run_state):
    """
    卡牌奖励升级概率。

    当前公式：
    已完成节点数量 * 5% * 系数

    例如：
    完成 1 个节点，系数 1.0 -> 5%
    完成 5 个节点，系数 1.0 -> 25%
    完成 10 个节点，系数 1.0 -> 50%
    """
    completed_count = len(getattr(run_state, "completed_node_ids", []))
    multiplier = getattr(run_state, "card_reward_upgrade_chance_multiplier", 1.0)

    chance = completed_count * CARD_UPGRADE_CHANCE_PER_COMPLETED_NODE * multiplier

    if chance < 0:
        chance = 0.0

    if chance > CARD_UPGRADE_CHANCE_MAX:
        chance = CARD_UPGRADE_CHANCE_MAX

    return chance


def roll_card_rewards(count, rng, upgrade_chance, run_state=None):
    if run_state is None:
        pool = list(CARD_REWARD_POOL)
    else:
        pool = get_card_reward_pool(run_state)

    if count <= len(pool):
        card_ids = rng.sample(pool, count)
    else:
        card_ids = [
            rng.choice(pool)
            for _ in range(count)
        ]

    cards = []

    for card_id in card_ids:
        card = create_card(card_id)

        if has_upgrade(card) and rng.random() < upgrade_chance:
            card = upgrade_card(card)

        cards.append(card)

    return cards


def take_card_reward(reward_state, index):
    if reward_state is None:
        return None, "当前没有待选择奖励。"

    if index < 0 or index >= len(reward_state.card_choices):
        return None, "奖励编号无效。"

    card = copy.deepcopy(reward_state.card_choices[index])

    return card, "获得卡牌：【{}】。".format(card.name)


def format_card_reward_choice(card):
    """
    奖励卡显示。

    如果奖励本身已经升级：
    【打击+】
    获得：1费 attack，造成 9 点伤害。
    状态：已升级

    如果奖励未升级：
    【打击】
    当前：1费 attack，造成 6 点伤害。
    升级：1费 attack，造成 9 点伤害。
    """
    lines = []
    lines.append("【{}】".format(card.name))

    if getattr(card, "upgraded", False):
        lines.append("获得：{}".format(format_card_full_effect(card)))
        lines.append("状态：已升级")
        return "\n".join(lines)

    lines.append("当前：{}".format(format_card_full_effect(card)))

    if has_upgrade(card):
        upgraded_card = upgrade_card(card)
        lines.append("升级：{}".format(format_card_full_effect(upgraded_card)))
    else:
        lines.append("升级：暂时没有可用的升级。")

    return "\n".join(lines)

def take_reward_option(run_state, reward_state, option_index):
    """
    领取一个奖励选项。

    金币 / 遗物 / 药水：直接领取。
    卡牌：打开三选一界面，不立即领取。
    """
    if reward_state is None:
        return "当前没有待领取奖励。"
    if option_index < 0 or option_index >= len(reward_state.options):
        return "奖励编号无效。"
    option = reward_state.options[option_index]
    if option.claimed:
        return "该奖励已经领取过。"
    if option.skipped:
        return "该奖励已经放弃。"
    if option.option_type == "gold":
        amount = option.payload.get("amount", 0)
        run_state.gold += amount
        option.claimed = True
        record_reward_taken(run_state, "gold")
        return "获得 {} 金币。当前金币：{}。".format(amount, run_state.gold)

    if option.option_type == "relic":
        relic = option.payload.get("relic")
        if relic is None:
            option.claimed = True
            return "遗物奖励异常，已跳过。"
        run_state.relics.append(relic)
        option.claimed = True
        record_reward_taken(run_state, "relic")
        logs = []
        logs.append("获得遗物：【{}】。".format(relic.name))
        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))
        return "\n".join(logs)

    if option.option_type == "potion":
        potion = option.payload.get("potion")
        if potion is None:
            option.claimed = True
            return "药水奖励异常，已跳过。"
        max_slots = getattr(run_state, "max_potion_slots", 3)
        if len(run_state.potions) >= max_slots:
            return "\n".join([
                "药水栏已满，无法直接获得【{}】。".format(potion.name),
                "",
                format_potion_slots(run_state),
                "",
                "可以使用 /card replace_potion {} 已有药水编号 来替换。".format(option_index),
                "例如：/card replace_potion {} 0".format(option_index),
                "也可以使用 /card skip 放弃剩余奖励。"
            ])
        run_state.potions.append(potion)
        option.claimed = True
        record_reward_taken(run_state, "potion")
        return "获得药水：【{}】。".format(potion.name)
    if option.option_type == "card":
        reward_state.active_card_option_index = option_index
        return format_card_choices(option.payload.get("cards", []))
    return "未知奖励类型：{}。".format(option.option_type)


def format_card_choices(cards):
    lines = []
    lines.append("=== 卡牌奖励 ===")
    if not cards:
        lines.append("没有可选卡牌。")
        return "\n".join(lines)
    for index, card in enumerate(cards):
        lines.append("[{}] {}".format(
            index,
            format_card_reward_choice(card)
        ))
    lines.append("")
    lines.append("使用 /card pick 0 选择卡牌。")
    lines.append("使用 /card skip 放弃剩余奖励。")
    return "\n".join(lines)

def skip_remaining_rewards(run_state, reward_state):
    """
    放弃所有尚未领取的奖励。
    """
    if reward_state is None:
        return "当前没有待领取奖励。"

    skipped_count = 0

    for option in reward_state.options:
        if not option.claimed and not option.skipped:
            option.skipped = True
            skipped_count += 1
            record_reward_skipped(run_state, option.option_type)

    reward_state.active_card_option_index = -1

    return "已放弃剩余 {} 项奖励。".format(skipped_count)

def pick_card_from_reward(run_state, reward_state, card_index):
    """
    从当前激活的卡牌奖励选项中选择一张卡。
    """
    if reward_state is None:
        return "当前没有待领取奖励。"
    option_index = reward_state.active_card_option_index
    if option_index < 0 or option_index >= len(reward_state.options):
        return "当前没有打开卡牌奖励。请先使用 /card take 对应编号查看卡牌选项。"
    option = reward_state.options[option_index]
    if option.option_type != "card":
        return "当前打开的奖励不是卡牌奖励。"
    if option.claimed:
        return "该卡牌奖励已经领取过。"
    cards = option.payload.get("cards", [])
    if card_index < 0 or card_index >= len(cards):
        return "卡牌编号无效。"
    card = copy.deepcopy(cards[card_index])
    run_state.master_deck.append(card)
    option.claimed = True
    reward_state.active_card_option_index = -1
    record_reward_taken(run_state, "card")
    return "获得卡牌：【{}】。".format(card.name)

def format_card_full_effect(card):
    keyword_text = format_keywords(card)

    parts = []
    parts.append("{}费".format(card.cost))
    parts.append(card.card_type)

    if keyword_text:
        parts.append(keyword_text)

    header = " ".join(parts)

    return "{}，{}".format(header, card.description)


def format_keywords(card):
    keywords = getattr(card, "keywords", [])

    if not keywords:
        return ""

    display_names = []

    for keyword in keywords:
        display_names.append(get_keyword_display_name(keyword))

    return "，".join(display_names)


def get_keyword_display_name(keyword):
    keyword_names = {
        "exhaust": "消耗",
        "ethereal": "虚无",
        "retain": "保留",
        "innate": "固有",
        "clever": "奇巧",
    }

    return keyword_names.get(keyword, keyword)

def format_potion_slots(run_state):
    potions = getattr(run_state, "potions", [])
    max_slots = getattr(run_state, "max_potion_slots", 3)

    lines = []
    lines.append("当前药水栏：{}/{}".format(len(potions), max_slots))

    if not potions:
        lines.append("无药水。")
        return "\n".join(lines)

    for index, potion in enumerate(potions):
        lines.append("[{}] 【{}】：{}".format(
            index,
            potion.name,
            potion.description
        ))

    return "\n".join(lines)

def replace_potion_reward(run_state, reward_state, option_index, potion_index):
    """
    药水栏已满时，丢弃一个已有药水，领取奖励药水。
    """
    if reward_state is None:
        return "当前没有待领取奖励。"
    if option_index < 0 or option_index >= len(reward_state.options):
        return "奖励编号无效。"
    option = reward_state.options[option_index]
    if option.option_type != "potion":
        return "该奖励不是药水奖励。"
    if option.claimed:
        return "该药水奖励已经领取过。"
    if option.skipped:
        return "该药水奖励已经放弃。"
    potion = option.payload.get("potion")
    if potion is None:
        option.claimed = True
        return "药水奖励异常，已跳过。"
    potions = getattr(run_state, "potions", [])
    if potion_index < 0 or potion_index >= len(potions):
        return "已有药水编号无效。"
    old_potion = potions[potion_index]
    potions[potion_index] = potion
    option.claimed = True
    record_reward_taken(run_state, "potion")
    return "丢弃【{}】，获得药水：【{}】。".format(
        old_potion.name,
        potion.name
    )

def get_card_reward_pool(run_state, include_colorless=True, include_test_cards=False):
    """
    获取当前角色可用的战斗卡牌奖励池。

    规则：
    - 当前角色有色卡：owner_character_id == run_state.character_id
    - 可选无色卡：owner_character_id == ""
    - 默认排除 starting / status / test
    """
    current_character_id = getattr(run_state, "character_id", "")
    result = []

    for card_id in CARD_REWARD_POOL:
        card = create_card(card_id)
        owner = getattr(card, "owner_character_id", "")
        quantity = getattr(card, "quantity", "")
        card_type = getattr(card, "card_type", "")

        if card_type == "status" or quantity == "status":
            continue

        if quantity == "starting":
            continue

        if quantity == "test" and not include_test_cards:
            continue

        if owner == current_character_id:
            result.append(card_id)
            continue

        if include_colorless and owner == "":
            result.append(card_id)
            continue

    # 小卡池兜底，防止测试角色没有奖励牌。
    if not result:
        return list(CARD_REWARD_POOL)

    return result