# -*- coding: utf-8 -*-
# Run 外层流程：创建一局游戏、进入路线节点、处理战斗结束、推进路线
import random
import copy
from data.character.AAAregistry import create_character
from data.card.AAAregistry import create_deck
from data.card.AAAregistry import create_card
from data.relic.AAAregistry import create_relics, create_relic
from data.potion.AAAregistry import create_potions
from game.command_help import command_tip
# from data.route.route_templates import TEST_ROUTE
from data.route.route_templates import generate_act1_grid_route

from data.route.encounters import (
    ENCOUNTER_TABLE,
    get_encounter_display_name,
    pick_encounter_id_by_node_type,
    resolve_encounter_enemy_ids,
)

from game.achievement import check_run_end_achievements, format_unlocked_achievements
from game.battle_context import BattleContext
from game.constants import EVENT_BATTLE_END, DEBUG_SEED
from game.engine import start_battle_with_player, get_combat_view
from game.event_bus import dispatch_event
from game.player_state import PlayerState
from game.relic_logic.bottle_utils import format_pending_bottle, has_pending_bottle_selection
from game.route import build_route, find_next_node_by_column, get_next_nodes, format_route_text, get_reachable_columns_text
from game.run_state import RunState
from game.status.status_container import StatusContainer

from game.reward import (
    create_battle_reward,
    take_reward_option,
    pick_card_from_reward,
    skip_remaining_rewards,
    replace_potion_reward
)
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
)
from game.node.node_event_0 import (
    create_event_state,
    format_event,
    choose_event_option as choose_event_option_impl,
)
from game.node.node_ancient import (
    create_ancient_state,
    format_ancient,
    choose_ancient_option as choose_ancient_option_impl,
)
from game.node.node_treasure import open_treasure

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
        master_deck=create_deck(character.starting_deck_ids),
        relics=create_relics(character.starting_relic_ids),
        potions=starting_potions,
        max_potion_slots=max_potion_slots,
        gold=getattr(character, "starting_gold", 0),
        route_nodes=build_route(generate_act1_grid_route(seed=run_seed))
    )
    prepare_visible_boss_for_route(run_state, seed=seed)
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

def prepare_visible_boss_for_route(run_state, seed=DEBUG_SEED):
    """
    在新路线开始时提前确定本层 Boss，并写入 Boss 节点。

    这样玩家可以一开局就看到本轮 Boss，后续真正进入 Boss 节点时
    也会使用同一个 encounter_id，不会出现显示和实际战斗不一致。
    """
    for node in run_state.route_nodes:
        if getattr(node, "node_type", "") != "boss":
            continue

        encounter_id = getattr(node, "encounter_id", "")

        if not encounter_id:
            rng = random.Random(make_encounter_seed(
                run_state,
                node,
                "boss",
                seed=seed
            ))
            encounter_id = pick_encounter_id_by_node_type("boss", rng)
            node.encounter_id = encounter_id

        run_state.boss_encounter_id = encounter_id
        run_state.boss_name = get_encounter_display_name(encounter_id)
        return encounter_id

    run_state.boss_encounter_id = ""
    run_state.boss_name = ""
    return ""

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
    else:
        result = "进入节点：{}。当前节点类型 {} 暂未实现。".format(
            node.name,
            node.node_type
        )

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
        run_state.gold += 50
        pre_logs.append("【蛇的头】生效：进入 ? 房间时获得 50 金币。当前金币：{}。".format(run_state.gold))

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

    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "",
        format_shop(run_state)
    ])


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

    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "",
        format_rest(run_state)
    ])


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
    text = open_treasure(
        run_state=run_state,
        seed=make_node_seed(run_state, node, seed, offset=400)
    )

    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "",
        text,
        "",
        complete_current_node(run_state)
    ])

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
    rng = random.Random(make_node_seed(run_state, node, seed=seed, offset=17))
    enemy_ids = resolve_encounter_enemy_ids(encounter_id, rng)
    player = create_player_for_battle(run_state)
    game_state, battle_reply = start_battle_with_player(
        session_id=run_state.session_id,
        character_id=run_state.character_id,
        player=player,
        enemy_ids=enemy_ids,
        seed=seed
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
    encounter = ENCOUNTER_TABLE.get(encounter_id)
    if encounter is None:
        return "遭遇配置不存在：{}".format(encounter_id)

    rng = random.Random(make_node_seed(run_state, node, seed=seed, offset=917))
    enemy_ids = resolve_encounter_enemy_ids(encounter_id, rng)
    player = create_player_for_battle(run_state)
    game_state, battle_reply = start_battle_with_player(
        session_id=run_state.session_id,
        character_id=run_state.character_id,
        player=player,
        enemy_ids=enemy_ids,
        seed=seed
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
    根据节点类型决定本次战斗使用哪个 encounter。

    规则：
    1. 如果普通节点 / Boss 节点显式写了 encounter_id，则优先使用。
    2. 精英节点默认从 ELITE_ENCOUNTER_POOL 随机抽。
    3. 如果以后想固定某个精英，也可以给 elite 节点写 fixed_encounter_id。
    """
    # 可选：给特殊节点强行固定遭遇
    fixed_encounter_id = getattr(node, "fixed_encounter_id", "")

    if fixed_encounter_id:
        return fixed_encounter_id

    if node.node_type == "elite":
        rng = random.Random(make_encounter_seed(run_state, node, seed=seed))
        return pick_encounter_id_by_node_type("elite", rng)

    encounter_id = getattr(node, "encounter_id", "")

    if encounter_id:
        return encounter_id

    rng = random.Random(make_encounter_seed(run_state, node, seed=seed))
    return pick_encounter_id_by_node_type(node.node_type, rng)


def make_encounter_seed(run_state, node, seed=DEBUG_SEED):
    base_seed = seed
    if base_seed is None:
        base_seed = getattr(run_state, "run_seed", None)
    if base_seed is None:
        base_seed = random.randint(1, 999999999)
    node_seed = sum([
        ord(ch)
        for ch in getattr(node, "node_id", "")
    ])
    return int(base_seed) + 3000 + node_seed

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

    fixed_encounter_id = getattr(node, "fixed_encounter_id", "")
    if fixed_encounter_id:
        return fixed_encounter_id

    if effective_node_type == "starting":
        if node.node_type != "mystery" and getattr(node, "encounter_id", ""):
            return node.encounter_id
        return pick_encounter_id_by_node_type("starting", rng)

    if effective_node_type == "elite":
        return pick_encounter_id_by_node_type("elite", rng)

    if effective_node_type == "boss":
        if getattr(node, "encounter_id", ""):
            return node.encounter_id
        return pick_encounter_id_by_node_type("boss", rng)

    if effective_node_type == "normal_enemy":
        if node.node_type != "mystery" and getattr(node, "encounter_id", ""):
            return node.encounter_id
        return pick_encounter_id_by_node_type("normal_enemy", rng)

    if getattr(node, "encounter_id", ""):
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

        if effect_type == "adventurer_corpse_remaining_rewards":
            rewards = list(effect.get("remaining_rewards", []) or [])
            if not rewards:
                continue
            logs.append("击败回来的怪物后，你拿走了尸体上还没搜到的东西。")
            for reward in rewards:
                if reward == "gold":
                    run_state.gold += 30
                    logs.append("尸体奖励：获得 30 金币。当前金币：{}。".format(run_state.gold))
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

    post_battle_rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 8800 + int(getattr(run_state, "reward_count", 0)))
    post_battle_logs = process_post_battle_effects(run_state, rng=post_battle_rng)

    current_node = run_state.get_current_node()
    node_type = getattr(run_state, "current_battle_node_type", "") or "normal_enemy"
    if not node_type and current_node is not None:
        node_type = current_node.node_type
    run_state.mark_current_node_completed()
    run_state.current_battle = None
    run_state.current_battle_node_type = ""

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
        parts.append("[{}]{}".format(index, potion.name))

    return "药水：{}（{}/{})".format(
        "，".join(parts),
        len(potions),
        max_slots
    )


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

    if has_pending_bottle_selection(run_state):
        lines.append("")
        lines.append(format_pending_bottle(run_state))
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
    else:
        lines.append("")
        lines.append(format_route_text(run_state))

    return "\n".join(lines)


def get_reward_view(run_state):
    if run_state.pending_reward is None:
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
    player = PlayerState(
        character_id=run_state.character_id,
        name=run_state.character_name,
        max_hp=run_state.max_hp,
        hp=run_state.hp,
        max_cost=run_state.max_cost,
        cost=run_state.max_cost,
        relics=run_state.relics,
        potions=run_state.potions,
        draw_pile=copy.deepcopy(run_state.master_deck),
        discard_pile=[],
        exhaust_pile=[],
        hand=[],
        statuses=StatusContainer()
    )

    apply_persistent_statuses_to_player(run_state, player)

    return player

def get_after_reward_text(run_state):
    """
    兼容旧调用：战斗奖励处理完成后，进入统一节点完成逻辑。
    """
    return complete_current_node(run_state)


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


def handle_rest_option(run_state, choice_index):
    if choice_index == 0:
        done, text = rest_heal(run_state)
        if done:
            return "\n".join([
                text,
                "",
                complete_current_node(run_state)
            ])
        return text
    if choice_index == 1:
        return format_smith_choices(run_state)
    return "火堆选项编号无效。"


def handle_smith_card(run_state, choice_index):
    done, text = smith_card(run_state, choice_index)
    if done:
        return "\n".join([
            text,
            "",
            complete_current_node(run_state)
        ])
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