# -*- coding: utf-8 -*-
# Run 外层流程：创建一局游戏、进入路线节点、处理战斗结束、推进路线
import random
import copy
from data.character.AAAregistry import create_character
from data.card.AAAregistry import create_deck
from data.card.AAAregistry import create_card
from data.content_gate import filter_card_ids, filter_relic_ids, is_content_enabled
from data.relic.AAAregistry import create_relics, create_relic
from data.potion.AAAregistry import create_potions
from game.command_help import command_tip
# from data.route.route_templates import TEST_ROUTE
from data.route.route_templates import generate_act1_grid_route, generate_act2_grid_route, generate_act3_grid_route
from data.route.encounters import (
    ENCOUNTER_TABLE,
    get_encounter_display_name,
    get_encounter_seen_key,
    pick_encounter_id_by_node_type,
    resolve_encounter_enemy_ids,
)

from game.achievement import check_run_end_achievements, format_unlocked_achievements
from game.battle_context import BattleContext
from game.constants import EVENT_BATTLE_END, DEBUG_SEED
from game.display_names import format_potion_display_name, format_relic_display_name
from game.engine import start_battle_with_player, get_combat_view
from game.event_bus import dispatch_event
from game.player_state import PlayerState
from game.relic_logic.bottle_utils import format_pending_bottle, has_pending_bottle_selection
from game.relic_logic.run_relic_utils import (
    assign_new_card_master_uid, format_pending_astrolabe, has_pending_astrolabe_selection, choose_pending_astrolabe_cards,
    format_pending_empty_cage, has_pending_empty_cage_selection, choose_pending_empty_cage_cards,
    ensure_card_master_uid
)
from game.route import build_route, find_next_node_by_column, get_next_nodes, format_route_text, get_reachable_columns_text
from game.run_state import RunState
from game.status.status_container import StatusContainer

from game.reward import (
    RewardOption,
    RewardState,
    create_battle_reward,
    get_card_reward_upgrade_chance,
    pick_card_from_reward,
    replace_potion_reward,
    roll_card_rewards,
    skip_remaining_rewards,
    take_reward_option,
    take_singing_bowl_reward,
)
from game.relic_logic.run_relic_utils import gain_gold_with_relics, has_run_relic, increase_max_hp, heal_run_hp_with_relics
from game.node.node_shop import (
    create_shop_state,
    format_shop,
    format_shop_item_detail,
    buy_shop_item,
    buy_shop_items,
    format_remove_card_choices,
    remove_card_by_index,
    random_remove_card,
)
from game.node.node_rest import (
    create_rest_state,
    format_rest,
    rest_heal,
    format_smith_choices,
    smith_card,
    get_rest_options,
    has_miniature_tent,
    lift_girya,
    dig_relic,
    format_rest_remove_choices,
    rest_remove_card,
)
from game.node.node_event_0 import (
    create_event_state,
    format_event,
    choose_event_option as choose_event_option_impl,
)


def get_encounter_history_attr(effective_node_type):
    if effective_node_type in ("elite", "event_elite"):
        return "seen_elite_encounter_ids"
    if effective_node_type in ("starting", "normal_enemy", "event_normal"):
        return "seen_normal_encounter_ids"
    return ""


def get_seen_encounter_ids(run_state, effective_node_type):
    attr = get_encounter_history_attr(effective_node_type)
    if not attr:
        return []
    seen = getattr(run_state, attr, None)
    if seen is None:
        seen = []
        setattr(run_state, attr, seen)
    return seen


def mark_encounter_seen(run_state, effective_node_type, encounter_id):
    attr = get_encounter_history_attr(effective_node_type)
    if not attr or not encounter_id:
        return
    seen = getattr(run_state, attr, None)
    if seen is None:
        seen = []
        setattr(run_state, attr, seen)
    seen_key = get_encounter_seen_key(encounter_id)
    if seen_key not in seen:
        seen.append(seen_key)
from game.node.node_ancient import (
    create_ancient_state,
    format_ancient,
    choose_ancient_option as choose_ancient_option_impl,
)
from game.node.node_treasure import (
    create_treasure_state, format_treasure, open_pending_treasure,
    take_treasure_item, skip_unclaimed_treasure,
)

def start_run(session_id, character_id="character.test", seed=DEBUG_SEED):
    """
    创建一局新的 Run，并自动进入第一个路线节点。
    """
    if seed is None:
        run_seed = random.randint(1, 999999999)
    else:
        run_seed = int(seed)
    character = create_character(character_id)
    max_potion_slots = getattr(character, "max_potion_slots", 3)
    starting_deck_ids = filter_card_ids(getattr(character, "starting_deck_ids", []))
    starting_relic_ids = filter_relic_ids(getattr(character, "starting_relic_ids", []))
    starting_potions = create_potions(getattr(character, "starting_potion_ids", []))
    if len(starting_potions) > max_potion_slots:
        starting_potions = starting_potions[:max_potion_slots]
    run_state = RunState(
        run_seed=run_seed,
        session_id=session_id,
        character_id=character.character_id,
        character_name=character.name,
        max_hp=character.max_hp,
        hp=character.max_hp,
        max_cost=character.max_cost,
        master_deck=create_deck(starting_deck_ids),
        relics=create_relics(starting_relic_ids),
        potions=starting_potions,
        max_potion_slots=max_potion_slots,
        gold=getattr(character, "starting_gold", 0),
        route_nodes=build_route(generate_act1_grid_route(seed=run_seed))
    )
    prepare_visible_boss_for_route(run_state, seed=seed, act=1)
    if run_state.route_nodes:
        run_state.current_node_id = run_state.route_nodes[0].node_id
    enter_reply = enter_current_node(run_state, seed=seed)
    reply = []
    reply.append("新的路线开始。")
    boss_name = getattr(run_state, "boss_name", "")
    if boss_name:
        reply.append("本轮 Boss：{}。".format(boss_name))
    reply.append("")
    reply.append(enter_reply)

    return run_state, "\n".join(reply)

def prepare_visible_boss_for_route(run_state, seed=DEBUG_SEED, act=None):
    """
    在新路线开始时提前确定本层 Boss，并写入所有 Boss 节点。

    固定 5 列地图中，第 15 层有多个 boss RouteNode。
    如果只写入第一个 boss 节点，其他列进入时会重新随机 boss，
    造成“地图显示史莱姆老大，实际进入六火亡魂”的货不对板。
    """
    if act is None:
        current_node = None
        try:
            current_node = run_state.get_current_node()
        except Exception:
            current_node = None
        if current_node is not None:
            act = get_route_act_from_node(current_node)
        else:
            act = 1

    act = int(act or 1)

    boss_nodes = [
        node for node in run_state.route_nodes
        if getattr(node, "node_type", "") == "boss"
        and get_route_act_from_node(node) == act
    ]

    if not boss_nodes:
        run_state.boss_encounter_id = ""
        run_state.boss_name = ""
        return ""

    encounter_id = getattr(run_state, "boss_encounter_id", "")

    if not encounter_id:
        for node in boss_nodes:
            node_encounter_id = getattr(node, "encounter_id", "")
            if node_encounter_id:
                encounter_id = node_encounter_id
                break

    if not encounter_id:
        rng = random.Random(make_encounter_seed(
            run_state,
            boss_nodes[0],
            "boss",
            seed=seed
        ))
        pool_suffix = get_encounter_pool_suffix_for_node(boss_nodes[0])
        encounter_id = pick_encounter_id_by_node_type(
            "boss",
            rng,
            pool_suffix=pool_suffix
        )
    for node in boss_nodes:
        node.encounter_id = encounter_id

    run_state.boss_encounter_id = encounter_id
    run_state.boss_name = get_encounter_display_name(encounter_id)

    return encounter_id

def take_reward(run_state, option_index):
    if run_state.pending_reward is None:
        return "当前没有待领取奖励。"

    reply = take_reward_option(
        run_state=run_state,
        reward_state=run_state.pending_reward,
        option_index=option_index
    )

    if run_state.pending_reward.all_done():
        run_state.pending_reward = None
        return "\n".join([
            reply,
            "",
            get_after_reward_text(run_state)
        ])

    return "\n".join([
        reply,
        "",
        run_state.pending_reward.reward_text()
    ])

def take_rewards(run_state, option_indices):
    """
    批量领取战斗奖励。

    规则：
    1. 按输入顺序依次领取。
    2. 已成功领取的奖励不回滚。
    3. 遇到卡牌奖励时会打开选牌界面并中止，等待 /card pick。
    4. 遇到药水栏满、无效编号、已领取等无法继续的情况时中止。
    """
    if run_state.pending_reward is None:
        return "当前没有待领取奖励。"

    if not option_indices:
        return "没有指定要领取的奖励编号。"

    reward_state = run_state.pending_reward
    logs = []

    for step_index, option_index in enumerate(option_indices):
        if run_state.pending_reward is None:
            logs.append("奖励已经全部处理完毕，批量领取结束。")
            break

        reward_state = run_state.pending_reward

        if option_index < 0 or option_index >= len(reward_state.options):
            logs.append("批量领取第 {} 项中止：奖励编号无效：{}。".format(
                step_index + 1,
                option_index
            ))
            break

        option = reward_state.options[option_index]

        if option.claimed:
            logs.append("批量领取第 {} 项中止：[{}] 已领取。".format(
                step_index + 1,
                option_index
            ))
            break

        if option.skipped:
            logs.append("批量领取第 {} 项中止：[{}] 已放弃。".format(
                step_index + 1,
                option_index
            ))
            break

        logs.append("批量领取第 {} 项：[{}] {}".format(
            step_index + 1,
            option_index,
            option.title
        ))

        before_claimed = option.claimed
        before_active_card_index = reward_state.active_card_option_index

        reply = take_reward_option(
            run_state=run_state,
            reward_state=reward_state,
            option_index=option_index
        )

        logs.append(reply)

        # 卡牌奖励不会直接 claimed，而是打开三选一。
        # 打开后必须让玩家 /card pick，不能继续批量领取后续奖励。
        if reward_state.active_card_option_index >= 0:
            logs.append("已打开卡牌奖励，批量领取中止。请使用 /card pick 0 选择卡牌。")
            break

        # 药水栏满等情况：没有 claimed，也没有打开卡牌选择。
        # 这种说明没有成功领取，停止批处理。
        if not before_claimed and not option.claimed:
            if before_active_card_index == reward_state.active_card_option_index:
                logs.append("该奖励未成功领取，批量领取中止。")
                break

        if reward_state.all_done():
            run_state.pending_reward = None
            logs.append("")
            logs.append(get_after_reward_text(run_state))
            return "\n".join(logs)

    if run_state.pending_reward is None:
        return "\n".join(logs)

    logs.append("")
    logs.append(run_state.pending_reward.reward_text())

    return "\n".join(logs)


def make_node_entry_snapshot(run_state):
    """
    生成“进入当前节点前”的快照。
    注意要临时断开 node_entry_snapshot，避免 deepcopy 时把旧快照套娃复制。
    """
    old_snapshot = getattr(run_state, "node_entry_snapshot", None)
    run_state.node_entry_snapshot = None
    snapshot = copy.deepcopy(run_state)
    run_state.node_entry_snapshot = old_snapshot
    snapshot.node_entry_snapshot = None
    return snapshot


def reset_current_node_from_snapshot(run_state, seed=DEBUG_SEED):
    """
    SL：回到“当前节点刚进入时”的 RunState。
    返回 (new_run_state, reply)。GameService 需要把 session 中的 run_state 替换成 new_run_state。
    """
    snapshot = getattr(run_state, "node_entry_snapshot", None)
    if snapshot is None:
        return run_state, "当前节点没有可回退的快照。"

    new_run_state = copy.deepcopy(snapshot)
    # 允许同一节点内多次 SL；快照自身断开递归引用。
    new_run_state.node_entry_snapshot = copy.deepcopy(snapshot)
    new_run_state.node_entry_snapshot.node_entry_snapshot = None

    return new_run_state, "已读取存档，回到进入当前节点时。\n\n" + get_run_view(new_run_state)

def check_run_failed_by_hp(run_state, reason="HP 归零"):
    """
    战斗外死亡检查。
    用于事件、遗物获得、商店、火堆、奖励等 Run 层流程中可能导致 HP <= 0 的情况。
    """
    if getattr(run_state, "run_over", False):
        return ""

    if getattr(run_state, "hp", 1) > 0:
        return ""

    run_state.hp = 0
    run_state.current_battle = None
    run_state.pending_reward = None
    run_state.clear_pending_nodes()
    run_state.run_over = True
    run_state.victory = False

    character_name = getattr(run_state, "character_name", "玩家")

    return "{} 已倒下，Run 失败。".format(character_name)

def enter_current_node(run_state, seed=DEBUG_SEED):
    """
    进入当前节点。
    战斗节点进入战斗；非战斗节点设置对应 pending 状态。

    进入完成后记录“节点入口快照”，用于 /card sl 精确回到刚进入节点时，
    包括敌人 HP、初始手牌、商店货架等随机结果。
    """
    node = run_state.get_current_node()
    if node is None:
        run_state.run_over = True
        return "路线节点不存在，Run 结束。"

    run_state.current_battle = None
    run_state.pending_reward = None
    run_state.clear_pending_nodes()

    pre_logs = []
    if (
        has_run_relic(run_state, "relic.maw_bank")
        and not getattr(run_state, "maw_bank_disabled", False)
        and len(getattr(run_state, "completed_node_ids", []) or []) > 0
    ):
        pre_logs.extend(gain_gold_with_relics(run_state, 12, source="巨口储蓄罐"))

    if node.node_type in ("starting", "normal_enemy", "elite", "boss"):
        result = enter_battle_node(
            run_state,
            node,
            seed=seed,
            effective_node_type=node.node_type
        )
    elif node.node_type == "mystery":
        result = enter_mystery_node(run_state, node, seed=seed)
    elif node.node_type == "shop":
        result = enter_shop_node(
            run_state,
            node,
            seed=seed,
            source_node_type="shop"
        )
    elif node.node_type == "event":
        result = enter_event_node(
            run_state,
            node,
            seed=seed,
            source_node_type="event"
        )
    elif node.node_type == "rest":
        result = enter_rest_node(
            run_state,
            node,
            source_node_type="rest"
        )
    elif node.node_type == "ancient":
        result = enter_ancient_node(run_state, node, seed=seed)
    elif node.node_type == "treasure":
        result = enter_treasure_node(run_state, node, seed=seed)
    elif node.node_type == "boss_empty":
        run_state.mark_current_node_completed()
        run_state.run_over = True
        run_state.victory = True
        result = "进入路线节点：{} ({})\n\n二层 Boss 还没有实现，当前版本到此为止。".format(
            node.name,
            node.node_type
        )
    else:
        result = "进入节点：{}。当前节点类型 {} 暂未实现。".format(
            node.name,
            node.node_type
        )

    if pre_logs:
        result = "\n".join(pre_logs + ["", result])

    run_state.node_entry_snapshot = make_node_entry_snapshot(run_state)
    return result

def run_has_relic(run_state, relic_id):
    for relic in getattr(run_state, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def enter_mystery_node(run_state, node, seed=DEBUG_SEED):
    pre_logs = []
    if run_has_relic(run_state, "relic.ssserpent_head"):
        pre_logs.extend(gain_gold_with_relics(run_state, 50, source="蛇的头"))

    result_type = roll_mystery_result(run_state, node, seed=seed)

    def with_pre_logs(text):
        if not pre_logs:
            return text
        return "\n".join(pre_logs + ["", text])

    if result_type == "normal_enemy":
        text = enter_battle_node(
            run_state,
            node,
            seed=seed,
            effective_node_type="normal_enemy"
        )
        return with_pre_logs("？节点的结果：战斗。\n\n" + text)
    if result_type == "elite":
        text = enter_battle_node(
            run_state,
            node,
            seed=seed,
            effective_node_type="elite"
        )
        return with_pre_logs("？节点的结果：精英战斗。\n\n" + text)
    if result_type == "shop":
        text = enter_shop_node(
            run_state,
            node,
            seed=seed,
            source_node_type="mystery"
        )
        return with_pre_logs("？节点的结果：商店。\n\n" + text)
    if result_type == "event":
        text = enter_event_node(
            run_state,
            node,
            seed=seed,
            source_node_type="mystery"
        )
        return with_pre_logs("？节点的结果：事件。\n\n" + text)
    if result_type == "treasure":
        text = enter_treasure_node(run_state, node, seed=seed)
        return with_pre_logs("？节点的结果：宝箱。\n\n" + text)
    return with_pre_logs("？节点结果异常：{}。".format(result_type))


MYSTERY_DIRECT_RESULT_TYPES = ("normal_enemy", "treasure", "shop")


def init_mystery_chances_if_needed(run_state):
    """
    初始化 ? 房间概率。

    基础值：
    - normal_enemy：10%
    - treasure：2%
    - shop：3%
    - elite：10%，只作为“冒险者尸体”事件的预留概率，普通 ? 房间不直接掷出精英。
    """
    base = dict(getattr(run_state, "mystery_base_chances", {}) or {})
    if not base:
        base = {
            "normal_enemy": 10,
            "treasure": 2,
            "shop": 3,
            "elite": 10,
        }
        run_state.mystery_base_chances = dict(base)

    current = getattr(run_state, "mystery_current_chances", None)
    if not current:
        run_state.mystery_current_chances = dict(base)
        return run_state.mystery_current_chances

    # 兼容旧存档 / 旧 RunState：缺少的键补成基础概率。
    for key, value in base.items():
        if key not in current:
            current[key] = value

    return current


def update_mystery_chances_after_result(run_state, result_type):
    """
    每进入一次 ? 房间后更新概率：
    - 命中的非事件遭遇：重置为基础概率。
    - 未命中的非事件遭遇：增加各自基础概率。
    - 事件本身没有概率槽；没有掷出其他遭遇时即为事件。
    """
    base = dict(getattr(run_state, "mystery_base_chances", {}) or {})
    current = init_mystery_chances_if_needed(run_state)

    for key in MYSTERY_DIRECT_RESULT_TYPES:
        base_value = int(base.get(key, 0))
        if base_value <= 0:
            continue

        if result_type == key:
            current[key] = base_value
        else:
            current[key] = min(100, int(current.get(key, base_value)) + base_value)


def roll_mystery_result(run_state, node, seed=DEBUG_SEED):
    """
    ? 房间概率：
    - 第一个 ? 房间：普通敌人 10%、宝箱 2%、商店 3%；未触发则为事件。
    - 每走到一个 ? 房间，命中的类型重置为初始概率，其他未命中的类型增加各自初始概率。
      例如连续 4 次未遇到商店，则下一次商店概率为 15%。
    - 精英 10% 暂时只给“冒险者尸体”事件使用，普通 ? 房间不会直接变成精英。
    """
    base_seed = seed

    if base_seed is None:
        base_seed = getattr(run_state, "run_seed", None)

    if base_seed is None:
        base_seed = random.randint(1, 999999999)

    node_seed = sum([
        ord(ch)
        for ch in getattr(node, "node_id", "")
    ])

    rng = random.Random(int(base_seed) + 7000 + node_seed)

    entered = int(getattr(run_state, "mystery_rooms_entered", 0) or 0) + 1
    run_state.mystery_rooms_entered = entered

    current = init_mystery_chances_if_needed(run_state)

    if run_has_relic(run_state, "relic.tiny_chest") and entered % 4 == 0:
        result_type = "treasure"
        update_mystery_chances_after_result(run_state, result_type)
        return result_type

    roll = rng.random() * 100.0

    threshold = 0.0
    result_type = "event"

    for key in MYSTERY_DIRECT_RESULT_TYPES:
        if key == "normal_enemy" and run_has_relic(run_state, "relic.juzu_bracelet"):
            continue
        threshold += float(current.get(key, 0))
        if roll < threshold:
            result_type = key
            break

    update_mystery_chances_after_result(run_state, result_type)
    return result_type


def enter_shop_node(run_state, node, seed=DEBUG_SEED, source_node_type="shop"):
    run_state.pending_shop = create_shop_state(
        run_state=run_state,
        seed=make_node_seed(run_state, node, seed, offset=100),
        source_node_type=source_node_type
    )

    relic_logs = []
    for relic in getattr(run_state, "relics", []) or []:
        handler = getattr(relic, "on_enter_shop", None)
        if handler is None:
            continue
        result = handler(run_state)
        if result:
            relic_logs.extend(result)

    lines = [
        "进入路线节点：{} ({})".format(node.name, node.node_type),
    ]
    if relic_logs:
        lines.append("")
        lines.extend(relic_logs)
    lines.extend([
        "",
        format_shop(run_state)
    ])
    return "\n".join(lines)


def enter_event_node(run_state, node, seed=DEBUG_SEED, source_node_type="event"):
    run_state.pending_event = create_event_state(
        run_state=run_state,
        seed=make_node_seed(run_state, node, seed, offset=200),
        source_node_type=source_node_type
    )

    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "",
        format_event(run_state)
    ])


def enter_rest_node(run_state, node, source_node_type="rest"):
    run_state.pending_rest = create_rest_state(
        source_node_type=source_node_type
    )

    logs = []
    if has_run_relic(run_state, "relic.eternal_feather"):
        deck_count = len(getattr(run_state, "master_deck", []) or [])
        heal = (deck_count // 5) * 3
        if heal > 0:
            logs.append("【永恒羽毛】触发：牌组 {} 张，尝试回复 {} 点生命。".format(deck_count, heal))
            logs.extend(heal_run_hp_with_relics(run_state, heal, source="永恒羽毛"))
        else:
            logs.append("【永恒羽毛】触发：牌组不足 5 张，没有回复生命。")
    if has_run_relic(run_state, "relic.ancient_tea_set"):
        run_state.ancient_tea_set_ready = True
        logs.append("【古茶具套装】准备就绪：下一场战斗开始时获得 2 点能量。")

    lines = [
        "进入路线节点：{} ({})".format(node.name, node.node_type),
    ]
    if logs:
        lines.append("")
        lines.extend(logs)
    lines.extend([
        "",
        format_rest(run_state)
    ])
    return "\n".join(lines)


def enter_ancient_node(run_state, node, seed=DEBUG_SEED):
    run_state.pending_ancient = create_ancient_state(
        run_state=run_state,
        seed=make_node_seed(run_state, node, seed, offset=300)
    )

    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "",
        format_ancient(run_state)
    ])


def enter_treasure_node(run_state, node, seed=DEBUG_SEED):
    run_state.pending_treasure = create_treasure_state(
        run_state=run_state,
        seed=make_node_seed(run_state, node, seed, offset=400),
        source_node_type=getattr(node, "node_type", "treasure")
    )

    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "",
        format_treasure(run_state)
    ])


def handle_treasure_open(run_state):
    return open_pending_treasure(run_state)


def handle_treasure_take(run_state, item_index):
    reply = take_treasure_item(run_state, item_index)
    treasure = getattr(run_state, "pending_treasure", None)
    if treasure is not None and treasure.all_done():
        return "\n".join([reply, "", complete_current_node(run_state)])
    return "\n".join([reply, "", format_treasure(run_state)])


def leave_treasure(run_state):
    if getattr(run_state, "pending_treasure", None) is None:
        return "当前不在宝箱房间。"
    text = skip_unclaimed_treasure(run_state)
    return "\n".join([text, "", complete_current_node(run_state)])


def choose_astrolabe_cards(run_state, indices):
    return choose_pending_astrolabe_cards(run_state, indices)


def choose_empty_cage_cards(run_state, indices):
    return choose_pending_empty_cage_cards(run_state, indices)

def make_node_seed(run_state, node, seed=DEBUG_SEED, offset=0):
    base_seed = seed
    if base_seed is None:
        base_seed = getattr(run_state, "run_seed", None)
    if base_seed is None:
        base_seed = random.randint(1, 999999999)
    node_seed = sum([
        ord(ch)
        for ch in getattr(node, "node_id", "")
    ])
    return int(base_seed) + int(offset) + node_seed

def enter_battle_node(run_state, node, seed=DEBUG_SEED, effective_node_type=None):
    if effective_node_type is None:
        effective_node_type = node.node_type
    encounter_id = get_encounter_id_for_node(
        run_state,
        node,
        effective_node_type,
        seed=seed
    )
    encounter = ENCOUNTER_TABLE.get(encounter_id)
    if encounter is None:
        return "遭遇配置不存在：{}".format(encounter_id)
    mark_encounter_seen(run_state, effective_node_type, encounter_id)
    rng = random.Random(make_node_seed(run_state, node, seed=seed, offset=17))
    enemy_ids = resolve_encounter_enemy_ids(encounter_id, rng)
    run_state.current_battle_node_type = effective_node_type
    player = create_player_for_battle(run_state)
    game_state, battle_reply = start_battle_with_player(
        session_id=run_state.session_id,
        character_id=run_state.character_id,
        player=player,
        enemy_ids=enemy_ids,
        seed=seed,
        run_state=run_state
    )
    game_state.run_state = run_state
    run_state.current_battle = game_state
    run_state.current_battle_node_type = effective_node_type
    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "遭遇：{}".format(encounter_id),
        "",
        battle_reply
    ])


def start_forced_event_battle(
        run_state,
        encounter_id,
        effective_node_type="normal_enemy",
        seed=DEBUG_SEED,
        post_battle_effects=None,
        intro_text=""
    ):
    """
    从事件中启动一场指定遭遇。

    注意：
    - 事件战斗不使用当前节点自身的 encounter_id。
    - pending_event 会被清空，避免战斗期间仍被视为事件未完成。
    - 战斗胜利后由 finish_current_battle_if_needed 统一完成当前节点并生成奖励。
    """
    node = run_state.get_current_node()
    if not is_content_enabled("encounter", encounter_id):
        return "该遭遇当前被 private 内容开关过滤：{}。".format(encounter_id)
    encounter = ENCOUNTER_TABLE.get(encounter_id)
    if encounter is None:
        return "遭遇配置不存在：{}".format(encounter_id)

    mark_encounter_seen(run_state, effective_node_type, encounter_id)
    rng = random.Random(make_node_seed(run_state, node, seed=seed, offset=917))
    enemy_ids = resolve_encounter_enemy_ids(encounter_id, rng)
    run_state.current_battle_node_type = effective_node_type
    player = create_player_for_battle(run_state)
    game_state, battle_reply = start_battle_with_player(
        session_id=run_state.session_id,
        character_id=run_state.character_id,
        player=player,
        enemy_ids=enemy_ids,
        seed=seed,
        run_state=run_state
    )
    game_state.run_state = run_state
    run_state.current_battle = game_state
    run_state.current_battle_node_type = effective_node_type
    run_state.pending_event = None
    run_state.pending_post_battle_effects = list(post_battle_effects or [])

    lines = []
    if intro_text:
        lines.append(intro_text)
        lines.append("")
    lines.append("遭遇：{}".format(encounter_id))
    lines.append("")
    lines.append(battle_reply)
    return "\n".join(lines)

def resolve_encounter_id_for_node(run_state, node, seed=DEBUG_SEED):
    """
    兼容旧调用：根据节点类型推导实际战斗类型，再复用 get_encounter_id_for_node。
    """
    effective_node_type = getattr(node, "node_type", "normal_enemy")
    if effective_node_type not in ("starting", "normal_enemy", "elite", "boss"):
        effective_node_type = "normal_enemy"
    return get_encounter_id_for_node(
        run_state=run_state,
        node=node,
        effective_node_type=effective_node_type,
        seed=seed
    )


def get_pickable_encounter_node_type(effective_node_type):
    if effective_node_type in ("starting", "normal_enemy", "elite", "boss"):
        return effective_node_type
    if effective_node_type == "event_elite":
        return "elite"
    if effective_node_type in ("event_normal", "event_boss"):
        return "normal_enemy"
    return "normal_enemy"


def pick_replacement_encounter_id(run_state, effective_node_type, rng):
    pick_type = get_pickable_encounter_node_type(effective_node_type)
    seen = get_seen_encounter_ids(run_state, effective_node_type)
    if pick_type == "boss":
        return pick_encounter_id_by_node_type(pick_type, rng)
    return pick_encounter_id_by_node_type(pick_type, rng, seen)



def get_encounter_pool_suffix_for_node(node):
    act = get_route_act_from_node(node)
    if act >= 3:
        return "1_3"
    if act == 2:
        return "1_2"
    return None

def get_encounter_id_for_node(run_state, node, effective_node_type, seed=DEBUG_SEED):
    """
    根据实际战斗类型选择 encounter。

    starting：开局普通战斗，走 STARTING_ENCOUNTER_POOL。
    normal_enemy：普通战斗，优先使用节点显式 encounter_id，否则走普通池。
    elite：无论普通 elite 节点，还是 mystery 随机出的 elite，都走精英池。
    boss：优先使用节点显式 encounter_id，否则走 boss 池。
    """
    rng = random.Random(make_encounter_seed(
        run_state,
        node,
        effective_node_type,
        seed=seed
    ))
    pool_suffix = get_encounter_pool_suffix_for_node(node)

    fixed_encounter_id = getattr(node, "fixed_encounter_id", "")
    if fixed_encounter_id:
        if is_content_enabled("encounter", fixed_encounter_id):
            return fixed_encounter_id
        return pick_replacement_encounter_id(run_state, effective_node_type, rng)

    if effective_node_type == "starting":
        if node.node_type != "mystery" and getattr(node, "encounter_id", ""):
            if is_content_enabled("encounter", node.encounter_id):
                return node.encounter_id
            return pick_encounter_id_by_node_type("starting", rng, get_seen_encounter_ids(run_state, effective_node_type), pool_suffix=pool_suffix)
        return pick_encounter_id_by_node_type("starting", rng, get_seen_encounter_ids(run_state, effective_node_type), pool_suffix=pool_suffix)

    if effective_node_type == "elite":
        return pick_encounter_id_by_node_type("elite", rng, get_seen_encounter_ids(run_state, effective_node_type), pool_suffix=pool_suffix)

    if effective_node_type == "boss":
        if getattr(node, "encounter_id", ""):
            if is_content_enabled("encounter", node.encounter_id):
                return node.encounter_id
            return pick_encounter_id_by_node_type(
                "boss",
                rng,
                pool_suffix=pool_suffix
            )
        return pick_encounter_id_by_node_type(
            "boss",
            rng,
            pool_suffix=pool_suffix
        )

    if effective_node_type == "normal_enemy":
        if node.node_type != "mystery" and getattr(node, "encounter_id", ""):
            if is_content_enabled("encounter", node.encounter_id):
                return node.encounter_id
            return pick_encounter_id_by_node_type("normal_enemy", rng, get_seen_encounter_ids(run_state, effective_node_type), pool_suffix=pool_suffix)
        return pick_encounter_id_by_node_type("normal_enemy", rng, get_seen_encounter_ids(run_state, effective_node_type), pool_suffix=pool_suffix)

    if getattr(node, "encounter_id", ""):
        if is_content_enabled("encounter", node.encounter_id):
            return node.encounter_id
    return pick_encounter_id_by_node_type("normal_enemy", rng)

def make_encounter_seed(run_state, node, effective_node_type, seed=DEBUG_SEED):
    base_seed = seed
    if base_seed is None:
        base_seed = getattr(run_state, "run_seed", None)
    if base_seed is None:
        base_seed = random.randint(1, 999999999)

    node_seed = sum([
        ord(ch)
        for ch in getattr(node, "node_id", "")
    ])

    type_offset_map = {
        "starting": 500,
        "normal_enemy": 1000,
        "elite": 2000,
        "boss": 3000,
    }

    type_offset = type_offset_map.get(effective_node_type, 0)
    return int(base_seed) + node_seed + type_offset


def process_post_battle_effects(run_state, rng=None):
    effects = list(getattr(run_state, "pending_post_battle_effects", []) or [])
    run_state.pending_post_battle_effects = []
    if rng is None:
        rng = random.Random()

    logs = []
    for effect in effects:
        effect_type = effect.get("type", "")

        if effect_type == "gain_relic":
            relic_id = effect.get("relic_id", "")
            if not relic_id:
                continue
            owned = {
                getattr(relic, "relic_id", "")
                for relic in getattr(run_state, "relics", [])
            }
            relic = create_relic(relic_id)
            if relic_id in owned and not getattr(relic, "allow_duplicate", False):
                logs.append("事件奖励遗物【{}】已拥有，本次不重复获得。".format(relic.name))
                continue
            run_state.relics.append(relic)
            logs.append("事件奖励：获得遗物【{}】。".format(relic.name))
            if hasattr(relic, "on_obtained"):
                logs.extend(relic.on_obtained(run_state))
            continue

        if effect_type == "gain_rare_relic":
            from game.reward import get_available_relic_ids, RewardOption
            available = []
            for relic_id in get_available_relic_ids(run_state):
                try:
                    relic = create_relic(relic_id)
                except Exception:
                    continue
                if getattr(relic, "quantity", "") == "rare":
                    available.append(relic_id)
            relic_id = rng.choice(available) if available else ""
            if relic_id:
                relic = create_relic(relic_id)
                injections = list(getattr(run_state, "pending_reward_injections", []) or [])
                injections.append(RewardOption(
                    option_type="relic",
                    title="心灵绽放：稀有遗物：{}".format(format_relic_display_name(relic)),
                    payload={"relic": relic, "source": "mind_bloom"},
                ))
                run_state.pending_reward_injections = injections
                logs.append("事件奖励：稀有遗物已加入战斗奖励。")
            else:
                logs.append("事件奖励：没有可获得的稀有遗物。")
            continue

        if effect_type == "adventurer_corpse_remaining_rewards":
            rewards = list(effect.get("remaining_rewards", []) or [])
            if not rewards:
                continue
            logs.append("击败回来的怪物后，你拿走了尸体上还没搜到的东西。")
            for reward in rewards:
                if reward == "gold":
                    logs.extend(gain_gold_with_relics(run_state, 30, source="尸体奖励"))
                elif reward == "relic":
                    from game.reward import get_available_relic_ids
                    available = get_available_relic_ids(run_state)
                    relic_id = rng.choice(available) if available else ""
                    if relic_id:
                        relic = create_relic(relic_id)
                        run_state.relics.append(relic)
                        logs.append("尸体奖励：获得遗物【{}】。".format(relic.name))
                        if hasattr(relic, "on_obtained"):
                            logs.extend(relic.on_obtained(run_state))
                    else:
                        logs.append("尸体奖励：没有可获得的遗物。")
                elif reward == "nothing":
                    logs.append("尸体奖励：什么也没有。")
            continue
        if effect_type == "arena_final_rewards":
            from game.reward import get_available_relic_ids, RewardOption

            def pick_relic_id_by_quantity(quantity):
                candidates = []

                for relic_id in get_available_relic_ids(run_state):
                    try:
                        relic = create_relic(relic_id)
                    except Exception:
                        continue

                    if getattr(relic, "quantity", "") == quantity:
                        candidates.append(relic_id)

                return rng.choice(candidates) if candidates else ""

            injections = list(getattr(run_state, "pending_reward_injections", []) or [])

            for quantity, title_prefix in (
                ("rare", "竞技场：稀有遗物"),
                ("uncommon", "竞技场：罕见遗物"),
            ):
                relic_id = pick_relic_id_by_quantity(quantity)

                if not relic_id:
                    logs.append("竞技场奖励：没有可获得的{}遗物。".format(
                        "稀有" if quantity == "rare" else "罕见"
                    ))
                    continue

                relic = create_relic(relic_id)
                injections.append(RewardOption(
                    option_type="relic",
                    title="{}：{}".format(title_prefix, format_relic_display_name(relic)),
                    payload={
                        "relic": relic,
                        "source": "arena",
                    },
                ))

            run_state.pending_reward_injections = injections
            logs.append("竞技场奖励：额外遗物已加入战斗奖励。")
            continue

    return logs

def finish_current_battle_if_needed(run_state):
    """
    如果当前战斗结束，则把结果同步回 RunState。
    返回需要追加显示的文本。
    """
    game_state = run_state.current_battle

    if game_state is None:
        return ""

    if not game_state.battle_over:
        return ""

    if not game_state.victory:
        sync_run_from_player_after_battle(run_state, game_state.player)
        if getattr(run_state, "pending_test_room", None) is not None:
            from game.test_room import finish_test_battle_room
            return finish_test_battle_room(
                run_state,
                victory=False,
                battle_end_logs=None
            )
        run_state.current_battle = None
        run_state.run_over = True
        run_state.victory = False
        return "战斗失败，Run 结束。"

    battle_end_logs = []
    context = BattleContext(
        game_state=game_state,
        player=game_state.player,
        source=game_state.player,
        extra={
            "victory": True
        }
    )
    battle_end_logs.extend(dispatch_event(
        game_state,
        EVENT_BATTLE_END,
        context
    ))
    sync_run_from_player_after_battle(run_state, game_state.player)
    run_state.pending_stolen_gold_rewards = list(getattr(
        game_state,
        "stolen_gold_rewards",
        []
    ))

    if getattr(run_state, "pending_test_room", None) is not None:
        from game.test_room import finish_test_battle_room
        return finish_test_battle_room(
            run_state,
            victory=True,
            battle_end_logs=battle_end_logs
        )

    escaped_by_smoke_bomb = bool(getattr(game_state, "smoke_bomb_escaped", False))

    current_node = run_state.get_current_node()
    node_type = getattr(run_state, "current_battle_node_type", "") or "normal_enemy"
    if not node_type and current_node is not None:
        node_type = current_node.node_type

    pending_post_battle_effects = list(getattr(run_state, "pending_post_battle_effects", []) or [])

    if any(effect.get("type") == "arena_after_first" for effect in pending_post_battle_effects):
        run_state.pending_post_battle_effects = []
        run_state.pending_stolen_gold_rewards = []
        run_state.current_battle = None
        run_state.current_battle_node_type = ""

        from game.node.node_event_1_2 import build_arena_after_first_event
        from game.node.node_event_0 import format_event

        run_state.pending_event = build_arena_after_first_event(run_state)

        lines = ["第一场战斗胜利。"]

        if battle_end_logs:
            lines.append("")
            lines.extend(battle_end_logs)

        lines.append("")
        lines.append(format_event(run_state))

        return "\n".join(lines)

    run_state.mark_current_node_completed()
    run_state.current_battle = None
    run_state.current_battle_node_type = ""

    if escaped_by_smoke_bomb:
        run_state.pending_stolen_gold_rewards = []
        run_state.pending_post_battle_effects = []
        lines = []
        lines.append("使用【烟雾弹】逃离，当前节点已完成，不获得任何奖励。")
        if battle_end_logs:
            lines.append("")
            lines.extend(battle_end_logs)
        return "\n".join(lines)

    post_battle_rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 8800 + int(getattr(run_state, "reward_count", 0)))
    post_battle_logs = process_post_battle_effects(run_state, rng=post_battle_rng)

    base_seed = getattr(run_state, "run_seed", None)
    reward_index = getattr(run_state, "reward_count", 0)
    if base_seed is None:
        reward_seed = None
    else:
        reward_seed = int(base_seed) + 1000 + int(reward_index)
    run_state.reward_count += 1

    reward_state = create_battle_reward(
        run_state=run_state,
        node_type=node_type,
        seed=reward_seed
    )

    injections = list(getattr(run_state, "pending_reward_injections", []) or [])
    if injections:
        reward_state.options.extend(injections)
        run_state.pending_reward_injections = []

    run_state.pending_reward = reward_state

    lines = []
    lines.append("战斗胜利，当前节点已完成。")

    if battle_end_logs:
        lines.append("")
        lines.extend(battle_end_logs)

    if post_battle_logs:
        lines.append("")
        lines.extend(post_battle_logs)

    lines.append("")
    lines.append(reward_state.reward_text())

    return "\n".join(lines)

def choose_next_node(run_state, choice_index, seed=DEBUG_SEED):
    """
    选择后续节点并进入。

    固定 5 列地图中，choice_index 表示下一层列号。
    旧路线中，choice_index 仍表示可选下一节点列表下标。
    """
    if has_pending_bottle_selection(run_state):
        return "当前还有待处理的瓶装遗物。请先使用 /card bottle 选择添加瓶装状态的牌。"

    if has_pending_astrolabe_selection(run_state):
        return "当前还有待处理的【星盘】选择。请先使用 /card astrolabe 0,1,2。"

    if has_pending_empty_cage_selection(run_state):
        return "当前还有待处理的【空鸟笼】选择。请先使用 /card cage 0,1。"

    if run_state.pending_reward is not None:
        return "当前还有待选择奖励。请先使用 /card reward 查看奖励，/card pick 0 选择卡牌，或 /card skip 跳过。"

    if run_state.current_battle is not None:
        return "当前仍在战斗中，不能选择下一节点。"

    if run_state.has_pending_node():
        return "当前节点还有未完成的操作，请先完成当前节点。"

    current_node = run_state.get_current_node()
    next_nodes = get_next_nodes(run_state.route_nodes, current_node)

    if not next_nodes:
        run_state.run_over = True
        run_state.victory = True
        return "没有可选下一节点，Run 已完成。"

    selected_node = find_next_node_by_column(
        run_state,
        current_node,
        choice_index
    )

    if selected_node is not None:
        run_state.current_node_id = selected_node.node_id
        return enter_current_node(run_state, seed=seed)

    # 旧路线兼容：没有 floor / col 元数据时继续按可选列表下标选择。
    if getattr(current_node, "floor", -1) < 0:
        if choice_index < 0 or choice_index >= len(next_nodes):
            return "下一节点编号无效。"

        selected_node = next_nodes[choice_index]
        run_state.current_node_id = selected_node.node_id
        return enter_current_node(run_state, seed=seed)

    return "下一节点列号无效或不可达。当前可选列：{}。".format(
        get_reachable_columns_text(run_state, current_node)
    )

def format_run_potion_summary(run_state):
    potions = getattr(run_state, "potions", [])
    max_slots = getattr(run_state, "max_potion_slots", 3)

    if not potions:
        return "药水：无（0/{})".format(max_slots)

    parts = []
    for index, potion in enumerate(potions):
        parts.append("[{}]{}".format(index, format_potion_display_name(potion)))

    return "药水：{}（{}/{})".format(
        "，".join(parts),
        len(potions),
        max_slots
    )


def format_run_relic_summary(run_state):
    relics = getattr(run_state, "relics", [])

    if not relics:
        return "遗物：无"

    parts = []
    for index, relic in enumerate(relics):
        parts.append("[{}]{}".format(index, format_relic_display_name(relic)))

    return "遗物：{}".format("，".join(parts))


def get_run_view(run_state):
    lines = []

    if run_state.current_battle is not None:
        lines.append(get_combat_view(run_state.current_battle))
        lines.append("")
        lines.append(format_run_potion_summary(run_state))
        return "\n".join(lines)

    lines.append("=== Run 状态 ===")
    lines.append("{} HP：{}/{}".format(
        run_state.character_name,
        run_state.hp,
        run_state.max_hp
    ))
    lines.append("金币：{}".format(run_state.gold))
    lines.append(format_run_potion_summary(run_state))
    lines.append(format_run_relic_summary(run_state))

    if has_pending_bottle_selection(run_state):
        lines.append("")
        lines.append(format_pending_bottle(run_state))
    elif has_pending_astrolabe_selection(run_state):
        lines.append("")
        lines.append(format_pending_astrolabe(run_state))
    elif has_pending_empty_cage_selection(run_state):
        lines.append("")
        lines.append(format_pending_empty_cage(run_state))
    elif run_state.pending_reward is not None:
        lines.append("")
        lines.append(run_state.pending_reward.reward_text())
    elif run_state.pending_shop is not None:
        lines.append("")
        lines.append(format_shop(run_state))
    elif run_state.pending_event is not None:
        lines.append("")
        lines.append(format_event(run_state))
    elif run_state.pending_rest is not None:
        lines.append("")
        lines.append(format_rest(run_state))
    elif run_state.pending_ancient is not None:
        lines.append("")
        lines.append(format_ancient(run_state))
    elif run_state.pending_treasure is not None:
        lines.append("")
        lines.append(format_treasure(run_state))
    else:
        lines.append("")
        lines.append(format_route_text(run_state))

    return "\n".join(lines)


def get_reward_view(run_state):
    if run_state.pending_reward is None:
        if getattr(run_state, "pending_treasure", None) is not None:
            return format_treasure(run_state)
        return "当前没有待选择奖励。"

    return run_state.pending_reward.reward_text()

def replace_reward_potion(run_state, option_index, potion_index):
    if run_state.pending_reward is None:
        return "当前没有待领取奖励。"

    reply = replace_potion_reward(
        run_state=run_state,
        reward_state=run_state.pending_reward,
        option_index=option_index,
        potion_index=potion_index
    )

    if run_state.pending_reward.all_done():
        run_state.pending_reward = None
        return "\n".join([
            reply,
            "",
            get_after_reward_text(run_state)
        ])

    return "\n".join([
        reply,
        "",
        run_state.pending_reward.reward_text()
    ])

def choose_reward_card(run_state, choice_index):
    if run_state.pending_reward is None:
        return "当前没有待领取奖励。"

    reply = pick_card_from_reward(
        run_state=run_state,
        reward_state=run_state.pending_reward,
        card_index=choice_index
    )

    if run_state.pending_reward.all_done():
        run_state.pending_reward = None
        return "\n".join([
            reply,
            "",
            get_after_reward_text(run_state)
        ])

    # 感知石这类连续卡牌奖励会在 pick 后自动打开下一组卡牌。
    # 此时 reply 已经包含下一组三选一界面，不再额外追加 reward_text，避免重复刷屏。
    if run_state.pending_reward.active_card_option_index >= 0:
        return reply

    return "\n".join([
        reply,
        "",
        run_state.pending_reward.reward_text()
    ])


def choose_singing_bowl_reward(run_state):
    if run_state.pending_reward is None:
        return "当前没有待领取奖励。"

    reply = take_singing_bowl_reward(
        run_state=run_state,
        reward_state=run_state.pending_reward
    )

    if run_state.pending_reward.all_done():
        run_state.pending_reward = None
        return "\n".join([
            reply,
            "",
            get_after_reward_text(run_state)
        ])

    return "\n".join([
        reply,
        "",
        run_state.pending_reward.reward_text()
    ])


def skip_reward(run_state):
    if run_state.pending_reward is None:
        return "当前没有待领取奖励。"

    reply = skip_remaining_rewards(
        run_state=run_state,
        reward_state=run_state.pending_reward
    )
    run_state.pending_reward = None
    return "\n".join([
        reply,
        "",
        get_after_reward_text(run_state)
    ])

def apply_persistent_statuses_to_player(run_state, player):
    """
    把 RunState 中声明为跨战斗保留的状态写入 PlayerState。
    当前默认不会保留力量、敏捷、荆棘。
    """
    for key, value in run_state.persistent_status_values.items():
        if value:
            player.statuses.set(key, value)


def sync_persistent_statuses_from_player(run_state, player):
    """
    战斗结束后，只同步白名单中的跨战斗状态。
    """
    values = {}

    for key in run_state.persistent_status_keys:
        value = player.statuses.get(key)
        if value:
            values[key] = value

    run_state.persistent_status_values = values


def create_player_for_battle(run_state):
    """
    根据 RunState 创建当前战斗用 PlayerState。
    每场战斗的抽牌堆来自 master_deck 的拷贝。
    """
    seen_uids = set()
    for card in getattr(run_state, "master_deck", []) or []:
        uid = getattr(card, "_master_deck_uid", None)
        if not uid or uid in seen_uids:
            assign_new_card_master_uid(run_state, card)
            uid = getattr(card, "_master_deck_uid", None)
        seen_uids.add(uid)
    player = PlayerState(
        character_id=run_state.character_id,
        name=run_state.character_name,
        max_hp=run_state.max_hp,
        hp=run_state.hp,
        max_cost=run_state.max_cost,
        cost=run_state.max_cost,
        relics=run_state.relics,
        max_potion_slots=getattr(run_state, "max_potion_slots", 3),
        potions=run_state.potions,
        draw_pile=copy.deepcopy(run_state.master_deck),
        discard_pile=[],
        exhaust_pile=[],
        hand=[],
        statuses=StatusContainer()
    )
    player.run_state = run_state

    apply_persistent_statuses_to_player(run_state, player)

    return player

def get_after_reward_text(run_state):
    """
    兼容旧调用：战斗奖励处理完成后，进入统一节点完成逻辑。
    """
    return complete_current_node(run_state)



def get_route_act_from_node(node):
    node_id = getattr(node, "node_id", "")
    if not isinstance(node_id, str) or not node_id.startswith("act"):
        return 1
    digits = []
    for ch in node_id[3:]:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if not digits:
        return 1
    return int("".join(digits))


def has_route_act(run_state, act):
    prefix = "act{}.".format(int(act))
    return any(
        isinstance(getattr(node, "node_id", ""), str)
        and getattr(node, "node_id", "").startswith(prefix)
        for node in getattr(run_state, "route_nodes", []) or []
    )


def get_post_boss_heal_ratio(run_state):
    ratio = float(getattr(run_state, "post_boss_heal_ratio", 1.0) or 0.0)
    for relic in getattr(run_state, "relics", []) or []:
        modifier = getattr(relic, "modify_post_boss_heal_ratio", None)
        if modifier is None:
            continue
        try:
            ratio = float(modifier(ratio, run_state=run_state))
        except TypeError:
            ratio = float(modifier(ratio))
    if ratio < 0.0:
        ratio = 0.0
    if ratio > 1.0:
        ratio = 1.0
    return ratio


def apply_post_boss_act_heal(run_state):
    import math
    ratio = get_post_boss_heal_ratio(run_state)
    old_hp = int(getattr(run_state, "hp", 0) or 0)
    max_hp = int(getattr(run_state, "max_hp", 0) or 0)
    if max_hp <= 0:
        return "Boss 后回复：最大生命异常，未处理。"
    target_hp = int(math.ceil(max_hp * ratio))
    if ratio >= 1.0:
        target_hp = max_hp
    if target_hp < 1:
        target_hp = 1
    run_state.hp = max(old_hp, min(max_hp, target_hp))
    if ratio >= 1.0:
        return "进入下一层前回复生命：{} -> {}（满血）。".format(old_hp, run_state.hp)
    return "进入下一层前回复生命：{} -> {}（{}% 最大生命）。".format(
        old_hp,
        run_state.hp,
        int(round(ratio * 100))
    )


def advance_to_next_act_after_boss_if_needed(run_state, current_node):
    """
    Boss 奖励结算完后，若还有下一阶段路线，则追加并进入下一阶段。
    """
    if current_node is None:
        return ""

    if getattr(current_node, "node_type", "") != "boss":
        return ""

    current_act = get_route_act_from_node(current_node)
    next_act = current_act + 1
    #后续测试楼层开关
    route_generator_by_act = {
        # 2: generate_act2_grid_route,
        # 3: generate_act3_grid_route,
    }

    route_generator = route_generator_by_act.get(next_act)
    if route_generator is None:
        return ""

    if not has_route_act(run_state, next_act):
        seed = int(getattr(run_state, "run_seed", 0) or 0) + next_act * 100000
        run_state.route_nodes.extend(build_route(route_generator(seed=seed)))

    run_state.current_node_id = "act{}.floor00".format(next_act)
    run_state.boss_encounter_id = ""
    run_state.boss_name = ""

    prepare_visible_boss_for_route(
        run_state,
        seed=getattr(run_state, "run_seed", DEBUG_SEED),
        act=next_act
    )

    heal_text = apply_post_boss_act_heal(run_state)
    entry_text = enter_current_node(run_state, seed=getattr(run_state, "run_seed", DEBUG_SEED))

    return "\n\n".join([
        "Boss 已击败，通往下一层的道路打开了。",
        heal_text,
        entry_text,
    ])

def complete_current_node(run_state):
    """
    所有节点完成后的统一出口。
    战斗节点可能已经在战斗胜利时 mark 过一次，这里重复调用不会重复写入。
    """
    death_text = check_run_failed_by_hp(run_state)
    if death_text:
        return death_text

    run_state.mark_current_node_completed()
    run_state.clear_pending_nodes()

    current_node = run_state.get_current_node()
    next_nodes = get_next_nodes(run_state.route_nodes, current_node)

    if not next_nodes:
        next_act_text = advance_to_next_act_after_boss_if_needed(run_state, current_node)
        if next_act_text:
            return next_act_text

        if getattr(current_node, "node_type", "") == "boss_empty":
            run_state.run_over = True
            run_state.victory = True
            return "二层 Boss 还没有实现，当前版本到此为止。"

        run_state.run_over = True
        run_state.victory = True

        unlocked = check_run_end_achievements(run_state)
        achievement_text = format_unlocked_achievements(unlocked)

        if achievement_text:
            return "\n".join([
                "当前路线已经完成，Run 胜利。",
                "",
                achievement_text
            ])

        return "当前路线已经完成，Run 胜利。"

    return "\n".join([
        format_route_text(run_state),
        "",
        command_tip("next", "使用 /card next 0 选择下一个节点。")
    ])

def leave_shop(run_state):
    if run_state.pending_shop is None:
        return "当前不在商店。"

    return "\n".join([
        "你离开了商店。",
        "",
        complete_current_node(run_state)
    ])


def handle_shop_buy(run_state, item_index):
    return "\n".join([
        buy_shop_item(run_state, item_index),
        "",
        format_shop(run_state)
    ])

def handle_shop_buy_batch(run_state, item_indices):
    return "\n".join([
        buy_shop_items(run_state, item_indices),
        "",
        format_shop(run_state)
    ])

def handle_shop_item_detail(run_state, item_index):
    return "\n".join([
        format_shop_item_detail(run_state, item_index),
        "",
        "使用 /card buy {} 购买该商品。".format(item_index)
    ])

def handle_remove_card_view_or_choose(run_state, card_index=None):
    if card_index is None:
        return format_remove_card_choices(run_state)

    return "\n".join([
        remove_card_by_index(run_state, card_index),
        "",
        format_shop(run_state)
    ])


def handle_random_remove_card(run_state, seed=DEBUG_SEED):
    node = run_state.get_current_node()

    return "\n".join([
        random_remove_card(
            run_state,
            seed=make_node_seed(run_state, node, seed, offset=500)
        ),
        "",
        format_shop(run_state)
    ])


def _finish_or_continue_rest(run_state, text):
    if has_miniature_tent(run_state):
        return "\n".join([
            text,
            "",
            format_rest(run_state)
        ])
    return "\n".join([
        text,
        "",
        complete_current_node(run_state)
    ])


def handle_rest_option(run_state, choice_index):
    if run_state.pending_rest is None:
        return "当前不在火堆。"
    options = get_rest_options(run_state)
    if choice_index < 0 or choice_index >= len(options):
        return "火堆选项编号无效。"
    action, _name = options[choice_index]

    if action == "leave":
        run_state.pending_rest = None
        return complete_current_node(run_state)

    if action == "rest":
        done, text = rest_heal(run_state)
        if done:
            if has_run_relic(run_state, "relic.dream_catcher"):
                node = run_state.get_current_node()
                rng = random.Random(make_node_seed(run_state, node, DEBUG_SEED, offset=812))
                cards = roll_card_rewards(
                    count=3 + (1 if has_run_relic(run_state, "relic.question_card") else 0),
                    rng=rng,
                    upgrade_chance=get_card_reward_upgrade_chance(run_state),
                    run_state=run_state
                )
                reward_state = RewardState(
                    node_type="dream_catcher",
                    options=[RewardOption(
                        option_type="card",
                        title="捕梦网：卡牌（三选一）",
                        payload={"cards": cards}
                    )]
                )
                run_state.pending_reward = reward_state
                run_state.pending_rest = None
                return "\n".join([
                    text,
                    "",
                    "【捕梦网】触发：休息后可以选择一张牌加入牌组。",
                    "",
                    reward_state.reward_text()
                ])
            return _finish_or_continue_rest(run_state, text)
        return text

    if action == "smith":
        return format_smith_choices(run_state)

    if action == "girya":
        done, text = lift_girya(run_state)
        if done:
            return _finish_or_continue_rest(run_state, text)
        return text

    if action == "pipe":
        return format_rest_remove_choices(run_state)

    if action == "shovel":
        node = run_state.get_current_node()
        done, text = dig_relic(run_state, seed=make_node_seed(run_state, node, DEBUG_SEED, offset=813))
        if done:
            return _finish_or_continue_rest(run_state, text)
        return text

    return "火堆选项暂未实现：{}。".format(action)


def handle_smith_card(run_state, choice_index):
    done, text = smith_card(run_state, choice_index)
    if done:
        return _finish_or_continue_rest(run_state, text)
    return text


def handle_rest_remove_card(run_state, card_index):
    done, text = rest_remove_card(run_state, card_index)
    if done:
        return _finish_or_continue_rest(run_state, text)
    return text

def handle_event_option(run_state, choice_index, seed=DEBUG_SEED):
    node = run_state.get_current_node()
    done, text = choose_event_option_impl(
        run_state,
        choice_index,
        seed=make_node_seed(run_state, node, seed, offset=600)
    )

    death_text = check_run_failed_by_hp(run_state)
    if death_text:
        return "\n".join([
            text,
            "",
            death_text
        ])

    if done:
        if getattr(run_state, "pending_test_room", None) is not None:
            from game.test_room import finish_test_event_room
            return finish_test_event_room(run_state, text)
        if run_state.pending_reward is not None:
            run_state.pending_event = None
            return "\n".join([
                text,
                "",
                run_state.pending_reward.reward_text()
            ])
        return "\n".join([
            text,
            "",
            complete_current_node(run_state)
        ])

    return text

def handle_ancient_option(run_state, choice_index, seed=DEBUG_SEED):
    node = run_state.get_current_node()
    done, text = choose_ancient_option_impl(
        run_state,
        choice_index,
        seed=make_node_seed(run_state, node, seed, offset=700)
    )
    if done:
        return "\n".join([
            text,
            "",
            complete_current_node(run_state)
        ])
    return text

def sync_run_from_player_after_battle(run_state, player):
    """
    战斗结束后，把长期状态同步回 RunState。
    """
    run_state.hp = player.hp
    run_state.max_hp = player.max_hp
    run_state.relics = player.relics
    run_state.potions = player.potions

    sync_persistent_statuses_from_player(run_state, player)
