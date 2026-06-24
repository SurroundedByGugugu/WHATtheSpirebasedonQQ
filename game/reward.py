# -*- coding: utf-8 -*-
# 战斗胜利后的奖励：选牌、金币、药水、遗物等

import copy
import random

from dataclasses import dataclass, field
from typing import List, Any

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card, has_upgrade
from data.potion.AAAregistry import create_potion, POTION_REGISTRY
from data.relic.AAAregistry import create_relic
from game.command_help import command_tip
from game.constants import DEBUG_SEED
from game.relic_logic.run_relic_utils import (
    add_card_to_master_deck_with_relics,
    can_upgrade_starting_relic,
    gain_gold_with_relics,
    is_relic_available_by_floor,
    has_run_relic,
    increase_max_hp,
    apply_card_gain_preview_relics,
    try_gain_potion_with_relics,
)


# =========================
# 奖励池
# =========================

CARD_REWARD_POOL = [
    #测试存档无色
    "card.gain_status_strength",
    "card.exhaust_strength",
    "card.ethereal_strength",
    "card.retain_strength",
    "card.clever_strength",
    "card.innate_thorns",
    "card.draw_discard_test",
    "card.test_heavy_strike",
    "card.test_x_drill",

    #战士哥
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
    "card.molten_fist",
    "card.dominate",
    "card.breakthrough",
    "card.setup_strike",
    "card.cinder",
    "card.tremble",
    "card.blood_wall",
    "card.combust",
    "card.dark_embrace",
    "card.feel_no_pain",
    "card.fire_breathing",
    "card.fire_breathing_history",
    "card.inflame",
    "card.metallicize",
    "card.rupture",
    "card.evolve",
    "card.barricade",
    "card.berserk",
    "card.brutality",
    "card.corruption",
    "card.juggernaut",
    "card.impervious",
    "card.double_tap",
    "card.burst",
    "card.limit_break",
    "card.offering",
    "card.amplify",
    "card.exhume",
    "card.fire_strike",
    "card.fire_zone",

    #yoi
    "card.crystal_piercing",
    "card.crystal_zone",
    "card.crystal_cocoon",
    "card.crystal_thorns",
    "card.abyssal_form",
    "card.phantom_form",

    #昼
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


COMMON_POTION_POOL=[
    "potion.attack",
    "potion.skill",
    "potion.power",
    "potion.forges_blessing",
    ]
UNCOMMON_POTION_POOL=[
    "potion.duplication",
    "potion.liquid_memories",
    "potion.cunning",
    "potion.elixir",
    ]
RARE_POTION_POOL=[
    "potion.fairy_in_a_bottle",
    "potion.chaos",
    "potion.smoke_bomb",
    ]
EVENT_POTION_POOL=[]

POTION_REWARD_POOL = COMMON_POTION_POOL + UNCOMMON_POTION_POOL + RARE_POTION_POOL + EVENT_POTION_POOL


COMMON_RELIC_POOL = [
    "relic.juzu_bracelet",
    "relic.tiny_chest",
    "relic.bag_of_marbles",
    "relic.blood_vial",
    "relic.bronze_scales",
    "relic.centennial_puzzle",
    "relic.the_boot",
    "relic.dream_catcher",
    "relic.happy_flower",
    "relic.lantern",
    "relic.oddly_smooth_stone",
    "relic.vajra",
    "relic.omamori",
    "relic.orichalcum",
    "relic.red_skull",
    "relic.regal_pillow",
    "relic.smiling_mask",
    "relic.snake_skull",
    "relic.strawberry",
    "relic.potion_belt",
    "relic.meal_ticket",
    "relic.whetstone",
    "relic.maw_bank",
    "relic.nunchaku",
    "relic.preserved_insect",
    "relic.ceramic_fish",
    "relic.akabeko",
    "relic.pen_nib",
    "relic.toy_ornithopter",
    "relic.bag_of_preparation",
    "relic.ancient_tea_set",
    "relic.art_of_war",
    "relic.anchor",
]

UNCOMMON_RELIC_POOL = [
    "relic.ether_medium",
    "relic.bottled_lightning",
    "relic.bottled_flame",
    "relic.bottled_tornado",
    "relic.pear",
    "relic.war_paint",
    "relic.the_courier",
    "relic.horn_cleat",
    "relic.blue_candle",
    "relic.eternal_feather",
    "relic.frozen_egg",
    "relic.toxic_egg",
    "relic.molten_egg",
    "relic.darkstone_periapt",
    "relic.gremlin_horn",
    "relic.kunai",
    "relic.shuriken",
    "relic.ornamental_fan",
    "relic.letter_opener",
    "relic.matryoshka",
    "relic.meat_on_the_bone",
    "relic.mercury_hourglass",
    "relic.mummified_hand",
    "relic.ninja_scroll",
    "relic.pantograph",
    "relic.paper_crane",
    "relic.paper_frog",
    "relic.question_card",
    "relic.self_forming_clay",
    "relic.singing_bowl",
    "relic.white_beast_statue",
    "relic.ink_bottle",
    "relic.strike_dummy",
    "relic.sundial",
]

RARE_RELIC_POOL = [
    "relic.charon_ashes",
    "relic.placeholder_stone",
    "relic.calipers",
    "relic.keystone_of_the_tomb",
    "relic.mango",
    "relic.captains_wheel",
    "relic.ice_cream",
    "relic.incense_burner",
    "relic.stone_calendar",
    "relic.pocketwatch",
    "relic.fossilized_helix",
    "relic.cloak_clasp",
    "relic.tungsten_rod",
    "relic.gambling_chip",
    "relic.bird_faced_urn",
    "relic.champion_belt",
    "relic.du_vu_doll",
    "relic.dead_branch",
    "relic.ginger",
    "relic.turnip",
    "relic.cabbage",
    "relic.girya",
    "relic.peace_pipe",
    "relic.shovel",
    "relic.lizard_tail",
    "relic.magic_flower",
    "relic.old_coin",
    "relic.prayer_wheel",
    "relic.the_specimen",
    "relic.thread_and_needle",
    "relic.tingsha",
    "relic.torii",
    "relic.tough_bandages",
    "relic.unceasing_top",
]

EVENT_RELIC_POOL = [
    "relic.bloody_idol",
    "relic.enchiridion",
    "relic.necronomicon",
    "relic.nilrys_codex",
    "relic.nloths_gift",
    "relic.mark_of_the_bloom",
    "relic.nloths_mask",
    "relic.face_of_cleric",
    "relic.cultist_mask",
    "relic.gremlin_mask",
    "relic.mutagenic_strength",
    "relic.golden_idol",
    "relic.odd_mushroom",
    "relic.ssserpent_head",
    "relic.warped_tongs",
    "relic.spirit_poop",
    "relic.red_mask",
]

SHOP_RELIC_POOL = [
    "relic.x_potion",
    "relic.twisted_funnel",
    "relic.membership_card",
    "relic.dragon_fruit",
    "relic.medical_kit",
    "relic.miniature_tent",
]

RELIC_REWARD_POOL = [
    "relic.homunculus_prototype",
] + COMMON_RELIC_POOL + UNCOMMON_RELIC_POOL + RARE_RELIC_POOL + EVENT_RELIC_POOL

BOSS_RELIC_POOL = [
    "relic.astrolabe",
    "relic.xanthosis",
    "relic.black_star",
    "relic.white_star",
    "relic.calling_bell",
    "relic.cursed_key",
    "relic.mark_of_pain",
    "relic.pandoras_box",
    "relic.philosophers_stone",
    "relic.runic_cube",
    "relic.runic_dome",
    "relic.runic_pyramid",
    "relic.snecko_eye",
    "relic.sozu",
    "relic.ectoplasm",
    "relic.tiny_house",
    "relic.velvet_choker",
    "relic.busted_crown",
    "relic.empty_cage",
    "relic.fusion_hammer",
    "relic.coffee_dripper",
    "relic.hovering_kite",
    "relic.wrist_blade",
    "relic.sacred_bark",
    "relic.slavers_collar",
]

MYTH_RELIC_POOL = [
]


# =========================
# 奖励参数
# =========================

POTION_DROP_CHANCE = 0.30

# 原作近似：先判定药水掉落，再按稀有度抽取。
POTION_RARITY_WEIGHTS = [
    ("common", 65),
    ("uncommon", 25),
    ("rare", 10),
]

# 卡牌升级概率：
# 已完成节点数 * 每节点基础概率 * 系数
CARD_UPGRADE_CHANCE_PER_COMPLETED_NODE = 0.05
CARD_UPGRADE_CHANCE_MAX = 0.80

GOLD_RANGE_BY_NODE_TYPE = {
    "normal_enemy": (10, 20),
    "elite": (25, 40),
    "event_elite": (25, 40),
    "boss": (80, 120),
}

# 遗物奖励概率与战斗节点类型相关。
# 当前建议：普通战斗不掉遗物，精英和 Boss 必掉。
RELIC_CHANCE_BY_NODE_TYPE = {
    "normal_enemy": 0.0,
    "elite": 1.0,
    "event_elite": 0.0,
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
    - boss_relic
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
        lines.append(command_tip("take", "使用 /card take 0 领取奖励。"))
        lines.append(command_tip("take", "使用 /card take 0,1,2 批量领取奖励。"))
        lines.append(command_tip("pick", "卡牌奖励需要先 /card take 对应编号，再 /card pick 0 选择卡牌。"))
        lines.append(command_tip("skip", "使用 /card skip 放弃剩余奖励。"))

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
    gold = apply_battle_gold_reward_modifiers(run_state, gold)
    reward_state.options.append(RewardOption(
        option_type="gold",
        title="{}金币".format(gold),
        payload={
            "amount": gold
        }
    ))

    # 1.5 被盗金币返还奖励
    stolen_gold_rewards = list(getattr(run_state, "pending_stolen_gold_rewards", []))

    for stolen_reward in stolen_gold_rewards:
        amount = int(stolen_reward.get("amount", 0))
        if amount <= 0:
            continue
        source = stolen_reward.get("source", "盗贼")
        reward_state.options.append(RewardOption(
            option_type="gold",
            title="（被偷的）{}金币".format(amount),
            payload={
                "amount": amount,
                "source": source,
                "reward_source": "stolen_gold"
            }
        ))
    run_state.pending_stolen_gold_rewards = []

    # 2. 遗物奖励
    if node_type == "boss":
        boss_relics = roll_boss_relic_choices(run_state, rng, count=3)
        for relic in boss_relics:
            reward_state.options.append(RewardOption(
                option_type="boss_relic",
                title="Boss 遗物：【{}】".format(relic.name),
                payload={"relic": relic, "group": "boss_relic"}
            ))
    else:
        relic = roll_relic_reward(run_state, node_type, rng)
        if relic is not None:
            reward_state.options.append(RewardOption(
                option_type="relic",
                title="遗物：【{}】".format(relic.name),
                payload={
                    "relic": relic
                }
            ))
        if node_type in ("elite", "event_elite") and has_run_relic(run_state, "relic.black_star"):
            extra_relic = roll_relic_reward_force(run_state, rng)
            if extra_relic is not None:
                reward_state.options.append(RewardOption(
                    option_type="relic",
                    title="黑星：额外遗物：【{}】".format(extra_relic.name),
                    payload={"relic": extra_relic}
                ))

    # 3. 药水奖励，没roll到就不显示
    potion = roll_potion_reward(rng, run_state=run_state)
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
    reward_card_count = get_card_reward_choice_count(run_state)
    card_choices = roll_card_rewards(
        count=reward_card_count,
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

    if node_type == "normal_enemy" and has_run_relic(run_state, "relic.prayer_wheel"):
        extra_card_choices = roll_card_rewards(
            count=reward_card_count,
            rng=rng,
            upgrade_chance=upgrade_chance,
            run_state=run_state
        )
        reward_state.options.append(RewardOption(
            option_type="card",
            title="转经轮：额外卡牌奖励（选择以查看具体选项）",
            payload={"cards": extra_card_choices}
        ))


    if node_type in ("elite", "event_elite") and has_run_relic(run_state, "relic.white_star"):
        rare_card_choices = roll_rare_card_rewards(
            count=reward_card_count,
            rng=rng,
            upgrade_chance=upgrade_chance,
            run_state=run_state
        )
        reward_state.options.append(RewardOption(
            option_type="card",
            title="白星：额外稀有卡牌奖励（选择以查看具体选项）",
            payload={"cards": rare_card_choices}
        ))

    record_reward_options_offered(run_state, reward_state)
    return reward_state

def record_reward_options_offered(run_state, reward_state):
    run_state.init_reward_stats_if_needed()

    for option in reward_state.options:
        if option.option_type == "gold":
            run_state.reward_stats["gold_offered"] += 1
        elif option.option_type in ("relic", "boss_relic"):
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
    if option_type == "boss_relic":
        return "relic"

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


def apply_battle_gold_reward_modifiers(run_state, amount):
    """应用战斗掉落金币修正。被盗金币返还不走这里。"""
    value = int(amount)
    for relic in getattr(run_state, "relics", []) or []:
        modifier = getattr(relic, "modify_battle_gold_reward", None)
        if modifier is None:
            continue
        try:
            value = int(modifier(value, context={"run_state": run_state}))
        except TypeError:
            value = int(modifier(value))
    if value < 0:
        value = 0
    return value

def roll_gold_reward(node_type, rng):
    gold_range = GOLD_RANGE_BY_NODE_TYPE.get(node_type, (10, 20))
    return rng.randint(gold_range[0], gold_range[1])


def _weighted_choice_quantity(rng, weights):
    total = sum(int(weight) for _, weight in weights)
    if total <= 0:
        return weights[0][0]
    roll = rng.uniform(0, total)
    upto = 0
    for quantity, weight in weights:
        upto += int(weight)
        if roll <= upto:
            return quantity
    return weights[-1][0]


def get_available_potion_ids_by_quantity(run_state=None, include_event=False, include_test=False):
    current_character_id = getattr(run_state, "character_id", "") if run_state is not None else ""
    result = {"common": [], "uncommon": [], "rare": [], "event": []}
    for potion_id in POTION_REGISTRY.keys():
        if potion_id.startswith("potion.test_") and not include_test:
            continue
        potion = create_potion(potion_id)
        owner = getattr(potion, "owner_character_id", "")
        if owner and owner != current_character_id:
            continue
        quantity = getattr(potion, "quantity", "common")
        if quantity == "test" and not include_test:
            continue
        if quantity == "event" and not include_event:
            continue
        if quantity not in result:
            if not include_test:
                continue
            result.setdefault(quantity, [])
        result.setdefault(quantity, []).append(potion_id)
    return result


def roll_potion_id_by_rarity(rng, run_state=None, include_event=False):
    by_quantity = get_available_potion_ids_by_quantity(run_state=run_state, include_event=include_event)
    available_all = []
    for ids in by_quantity.values():
        available_all.extend(ids)
    if not available_all:
        return None
    target_quantity = _weighted_choice_quantity(rng, POTION_RARITY_WEIGHTS)
    candidates = by_quantity.get(target_quantity, [])
    if candidates:
        return rng.choice(candidates)
    return rng.choice(available_all)


def roll_potion_reward(rng, run_state=None):
    if not (run_state is not None and has_run_relic(run_state, "relic.white_beast_statue")) and rng.random() >= POTION_DROP_CHANCE:
        return None

    if run_state is not None and has_run_relic(run_state, "relic.sozu"):
        return None
    potion_id = roll_potion_id_by_rarity(rng, run_state=run_state, include_event=False)
    if potion_id is None:
        return None
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




def roll_relic_reward_force(run_state, rng):
    available_relic_ids = get_available_relic_ids(run_state)
    if not available_relic_ids:
        return None
    return create_relic(rng.choice(available_relic_ids))


def get_available_boss_relic_ids(run_state):
    owned = {getattr(relic, "relic_id", "") for relic in getattr(run_state, "relics", []) or []}
    result = []
    current_character_id = getattr(run_state, "character_id", "")
    for relic_id in BOSS_RELIC_POOL:
        if relic_id in owned:
            continue
        relic = create_relic(relic_id)
        if not is_relic_available_by_floor(run_state, relic):
            continue
        owner = getattr(relic, "owner_character_id", "")
        if owner and owner != current_character_id:
            continue
        if relic_id == "relic.xanthosis" and not can_upgrade_starting_relic(run_state):
            continue
        result.append(relic_id)
    return result


def roll_boss_relic_choices(run_state, rng, count=3):
    ids = get_available_boss_relic_ids(run_state)
    if not ids:
        return []
    if len(ids) <= count:
        chosen = list(ids)
    else:
        chosen = rng.sample(ids, count)
    return [create_relic(relic_id) for relic_id in chosen]


def get_card_reward_choice_count(run_state):
    count = 3
    if has_run_relic(run_state, "relic.question_card"):
        count += 1
    if has_run_relic(run_state, "relic.busted_crown"):
        count -= 2
    if count < 1:
        count = 1
    return count


def roll_rare_card_rewards(count, rng, upgrade_chance, run_state=None):
    pool = get_card_reward_pool(run_state) if run_state is not None else list(CARD_REWARD_POOL)
    rare_pool = []
    for card_id in pool:
        card = create_card(card_id)
        if getattr(card, "quantity", "") == "rare":
            rare_pool.append(card_id)
    if not rare_pool:
        rare_pool = pool
    if count <= len(rare_pool):
        card_ids = rng.sample(rare_pool, count)
    else:
        card_ids = [rng.choice(rare_pool) for _ in range(count)]
    cards = []
    for card_id in card_ids:
        card = create_card(card_id)
        if run_state is not None:
            card = apply_card_gain_preview_relics(run_state, card)
        if has_upgrade(card) and rng.random() < upgrade_chance:
            card = upgrade_card(card)
        cards.append(card)
    return cards

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
        if not is_relic_available_by_floor(run_state, relic):
            continue
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

    if run_state is not None and has_run_relic(run_state, "relic.nloths_gift"):
        rare_pool = []
        non_rare_pool = []
        for cid in pool:
            c = create_card(cid)
            if getattr(c, "quantity", "") == "rare":
                rare_pool.append(cid)
            else:
                non_rare_pool.append(cid)
        card_ids = []
        for _ in range(count):
            # 简化实现：恩洛斯的礼物使稀有牌被抽中的权重约 3 倍。
            weighted_pool = list(non_rare_pool) + rare_pool * 3
            card_ids.append(rng.choice(weighted_pool or pool))
    elif count <= len(pool):
        card_ids = rng.sample(pool, count)
    else:
        card_ids = [
            rng.choice(pool)
            for _ in range(count)
        ]

    cards = []

    for card_id in card_ids:
        card = create_card(card_id)
        if run_state is not None:
            card = apply_card_gain_preview_relics(run_state, card)

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


def format_card_quantity_name(quantity):
    mapping = {
        "starting": "初始",
        "common": "普通",
        "uncommon": "罕见",
        "rare": "稀有",
        "myth": "神话",
        "special": "特殊",
        "status": "状态",
        "curse": "诅咒",
        "boss": "Boss",
    }
    return mapping.get(str(quantity), str(quantity))


def format_card_type_name(card_type):
    mapping = {
        "attack": "攻击",
        "skill": "技能",
        "power": "能力",
        "status": "状态",
        "curse": "诅咒",
        "boss": "Boss",
    }
    return mapping.get(str(card_type), str(card_type))


def format_card_attack_type_name(attack_type):
    mapping = {
        "slash": "斩",
        "piercing": "突",
        "blunt": "钝",
        "magic": "术",
    }
    attack_type = str(attack_type or "").strip()
    if not attack_type:
        return "-"
    return mapping.get(attack_type, attack_type)


def format_card_element_name(element):
    element = str(element or "").strip()
    if not element:
        return "-"
    try:
        from data.zones.element_zones import get_element_display_name
        return get_element_display_name(element) or element
    except Exception:
        return element


def format_card_header(card):
    return "【{}】（{} / {} / {} / {}）".format(
        card.name,
        format_card_quantity_name(getattr(card, "quantity", "")),
        format_card_type_name(getattr(card, "card_type", "")),
        format_card_attack_type_name(getattr(card, "attack_type", "")),
        format_card_element_name(getattr(card, "attack_element", ""))
    )


def format_card_reward_summary(card):
    return format_card_header(card)


def collect_effect_refs_from_value(value, status_keys, card_ids):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in ("status", "status_key") and isinstance(child, str):
                status_keys.add(child)
            if key in ("card_id", "add_card_id", "generated_card_id") and isinstance(child, str):
                card_ids.add(child)
            collect_effect_refs_from_value(child, status_keys, card_ids)
        return

    if isinstance(value, (list, tuple)):
        for child in value:
            collect_effect_refs_from_value(child, status_keys, card_ids)


def collect_card_related_refs(card):
    status_keys = set()
    card_ids = set()
    collect_effect_refs_from_value(getattr(card, "effects", []), status_keys, card_ids)
    collect_effect_refs_from_value(getattr(card, "exhaust_effects", []), status_keys, card_ids)
    collect_effect_refs_from_value(getattr(card, "upgrade_patch", {}), status_keys, card_ids)
    if getattr(card, "card_id", "") in card_ids:
        card_ids.remove(getattr(card, "card_id", ""))
    return sorted(status_keys), sorted(card_ids)


def format_status_detail_line(status_key):
    from game.status.status_defs import get_status_def, get_status_name

    override_descriptions = {
        "weak": "造成的攻击伤害减少 25%。",
        "vulnerable": "受到的攻击伤害增加 50%。",
        "frail": "获得的格挡减少 25%。",
        "strength": "攻击伤害按层数增加。层数可以为负。",
        "dexterity": "技能牌获得格挡按层数增加。层数可以为负。",
        "ritual": "敌人在敌方回合结束时获得等量力量；玩家逻辑等效恶魔形态。",
        "artifact": "抵消下一次负面状态。",
        "stun": "跳过行动。",
    }

    status_def = get_status_def(status_key)
    name = get_status_name(status_key)
    description = override_descriptions.get(status_key)
    if description is None and status_def is not None:
        description = getattr(status_def, "description", "")
    if not description:
        description = "暂无详细说明。"
    return "- 状态【{}】（{}）：{}".format(name, status_key, description)


def format_related_card_line(card_id):
    try:
        related_card = create_card(card_id)
    except Exception:
        return "- 相关卡牌（{}）：无法创建。".format(card_id)
    return "- 相关卡牌【{}】（{} / {}）：{}".format(
        related_card.name,
        format_card_quantity_name(getattr(related_card, "quantity", "")),
        format_card_type_name(getattr(related_card, "card_type", "")),
        related_card.description
    )


def format_card_related_details(card):
    status_keys, card_ids = collect_card_related_refs(card)
    lines = []
    for status_key in status_keys:
        lines.append(format_status_detail_line(status_key))
    for card_id in card_ids:
        lines.append(format_related_card_line(card_id))
    if not lines:
        return ""
    return "相关说明：\n" + "\n".join(lines)


def format_card_reward_choice(card):
    """
    奖励、商店、牌库详情共用的卡牌说明。
    """
    lines = []
    lines.append(format_card_header(card))

    if getattr(card, "upgraded", False):
        lines.append("效果：{}".format(format_card_full_effect(card)))
        lines.append("状态：已升级")
        detail = format_card_related_details(card)
        if detail:
            lines.append(detail)
        return "\n".join(lines)

    lines.append("效果：{}".format(format_card_full_effect(card)))

    if has_upgrade(card):
        upgraded_card = upgrade_card(card)
        lines.append("升级后：{}".format(format_card_full_effect(upgraded_card)))
    else:
        lines.append("升级后：暂时没有可用的升级。")

    detail = format_card_related_details(card)
    if detail:
        lines.append(detail)

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
        option.claimed = True
        record_reward_taken(run_state, "gold")
        logs = gain_gold_with_relics(run_state, amount, source="奖励")
        if not logs:
            logs = ["获得 0 金币。当前金币：{}。".format(run_state.gold)]
        return "\n".join(logs)

    if option.option_type in ("relic", "boss_relic"):
        relic = option.payload.get("relic")
        if relic is None:
            option.claimed = True
            return "遗物奖励异常，已跳过。"
        run_state.relics.append(relic)
        option.claimed = True
        if option.option_type == "boss_relic":
            for other in reward_state.options:
                if other is option:
                    continue
                if other.option_type == "boss_relic" and not other.claimed:
                    other.skipped = True
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
        logs = try_gain_potion_with_relics(run_state, potion, source="奖励")
        option.claimed = True
        record_reward_taken(run_state, "potion")
        return "\n".join(logs)
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
            format_card_reward_summary(card)
        ))
    lines.append("")
    lines.append("格式：稀有度 / 牌类型 / 伤害类型 / 属性。没有对应标注时显示 -。")
    lines.append(command_tip("pick", "使用 /card pick 0 选择卡牌。"))
    lines.append(command_tip("bowl", "若拥有颂钵，可使用 /card bowl 将本次卡牌奖励转为 +2 最大生命值。"))
    lines.append(command_tip("deck", "选入牌库后，可使用 /card deck 编号 查看完整说明。"))
    lines.append(command_tip("skip", "使用 /card skip 放弃剩余奖励。"))
    return "\n".join(lines)


def take_singing_bowl_reward(run_state, reward_state):
    """颂钵：把当前打开的卡牌奖励转为 +2 最大生命值。"""
    if reward_state is None:
        return "当前没有待领取奖励。"
    if not has_run_relic(run_state, "relic.singing_bowl"):
        return "你没有【颂钵】，不能将卡牌奖励转为最大生命。"
    option_index = reward_state.active_card_option_index
    if option_index < 0 or option_index >= len(reward_state.options):
        return "当前没有打开卡牌奖励。请先使用 /card take 对应编号查看卡牌选项。"
    option = reward_state.options[option_index]
    if option.option_type != "card":
        return "当前打开的奖励不是卡牌奖励。"
    if option.claimed:
        return "该卡牌奖励已经领取过。"
    option.claimed = True
    reward_state.active_card_option_index = -1
    record_reward_taken(run_state, "card")
    return "【颂钵】触发：放弃本次卡牌奖励，获得 +2 最大生命值。\n" + "\n".join(increase_max_hp(run_state, 2, "颂钵"))


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
    add_logs = add_card_to_master_deck_with_relics(run_state, card, source="获得卡牌")
    option.claimed = True
    reward_state.active_card_option_index = -1
    record_reward_taken(run_state, "card")
    return "\n".join(add_logs)

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
    extra = ""
    if getattr(potion, "potion_id", "") == "potion.fairy_in_a_bottle" and getattr(run_state, "character_id", "") == "character.yoirine":
        extra = "\n昼·里辛塔法：“我没见过这个。但本能地……不太喜欢它。”"
    return "丢弃【{}】，获得药水：【{}】。{}".format(
        old_potion.name,
        potion.name,
        extra
    )

def get_card_reward_pool(run_state, include_colorless=True, include_test_cards=False, ignore_prismatic=False):
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

        has_prismatic = (not ignore_prismatic) and has_run_relic(run_state, "relic.prismatic_shard")

        if has_prismatic:
            result.append(card_id)
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
