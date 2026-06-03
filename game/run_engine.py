# -*- coding: utf-8 -*-
# Run 外层流程：创建一局游戏、进入路线节点、处理战斗结束、推进路线
import random
import copy
from data.character.AAAregistry import create_character
from data.card.AAAregistry import create_deck
from data.relic.AAAregistry import create_relics
from data.potion.AAAregistry import create_potions
from data.route.route_templates import TEST_ROUTE
from data.route.encounters import ENCOUNTER_TABLE, pick_encounter_id_by_node_type

from game.achievement import check_run_end_achievements, format_unlocked_achievements
from game.battle_context import BattleContext
from game.constants import EVENT_BATTLE_END, DEBUG_SEED
from game.engine import start_battle_with_player, get_combat_view
from game.event_bus import dispatch_event
from game.player_state import PlayerState
from game.route import build_route, get_next_nodes, format_route_text
from game.run_state import RunState
from game.status.status_container import StatusContainer

from game.reward import (
    create_battle_reward,
    take_reward_option,
    pick_card_from_reward,
    skip_remaining_rewards,
    replace_potion_reward
)
from game.node_shop import (
    create_shop_state,
    format_shop,
    format_shop_item_detail,
    buy_shop_item,
    buy_shop_items,
    format_remove_card_choices,
    remove_card_by_index,
    random_remove_card,
)
from game.node_rest import (
    create_rest_state,
    format_rest,
    rest_heal,
    format_smith_choices,
    smith_card,
)
from game.node_event_0 import (
    create_event_state,
    format_event,
    choose_event_option as choose_event_option_impl,
)
from game.node_ancient import (
    create_ancient_state,
    format_ancient,
    choose_ancient_option as choose_ancient_option_impl,
)
from game.node_treasure import open_treasure

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
        route_nodes=build_route(TEST_ROUTE)
    )
    if run_state.route_nodes:
        run_state.current_node_id = run_state.route_nodes[0].node_id
    enter_reply = enter_current_node(run_state, seed=seed)
    reply = []
    reply.append("新的路线开始。")
    reply.append("")
    reply.append(enter_reply)

    return run_state, "\n".join(reply)

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

def enter_current_node(run_state, seed=DEBUG_SEED):
    """
    进入当前节点。
    战斗节点进入战斗；非战斗节点设置对应 pending 状态。
    """
    node = run_state.get_current_node()
    if node is None:
        run_state.run_over = True
        return "路线节点不存在，Run 结束。"

    run_state.clear_pending_nodes()
    if node.node_type in ("normal_enemy", "elite", "boss"):
        return enter_battle_node(
            run_state,
            node,
            seed=seed,
            effective_node_type=node.node_type
        )
    if node.node_type == "mystery":
        return enter_mystery_node(run_state, node, seed=seed)
    if node.node_type == "shop":
        return enter_shop_node(
            run_state,
            node,
            seed=seed,
            source_node_type="shop"
        )
    if node.node_type == "event":
        return enter_event_node(
            run_state,
            node,
            seed=seed,
            source_node_type="event"
        )
    if node.node_type == "rest":
        return enter_rest_node(
            run_state,
            node,
            source_node_type="rest"
        )
    if node.node_type == "ancient":
        return enter_ancient_node(run_state, node, seed=seed)
    if node.node_type == "treasure":
        return enter_treasure_node(run_state, node, seed=seed)
    return "进入节点：{}。当前节点类型 {} 暂未实现。".format(
        node.name,
        node.node_type
    )


def enter_mystery_node(run_state, node, seed=DEBUG_SEED):
    result_type = roll_mystery_result(run_state, node, seed=seed)
    if result_type == "normal_enemy":
        text = enter_battle_node(
            run_state,
            node,
            seed=seed,
            effective_node_type="normal_enemy"
        )
        return "？节点的结果：战斗。\n\n" + text
    if result_type == "elite":
        text = enter_battle_node(
            run_state,
            node,
            seed=seed,
            effective_node_type="elite"
        )
        return "？节点的结果：精英战斗。\n\n" + text
    if result_type == "shop":
        text = enter_shop_node(
            run_state,
            node,
            seed=seed,
            source_node_type="mystery"
        )
        return "？节点的结果：商店。\n\n" + text
    if result_type == "event":
        text = enter_event_node(
            run_state,
            node,
            seed=seed,
            source_node_type="mystery"
        )
        return "？节点的结果：事件。\n\n" + text
    if result_type == "treasure":
        text = enter_treasure_node(run_state, node, seed=seed)
        return "？节点的结果：宝箱。\n\n" + text
    return "？节点结果异常：{}。".format(result_type)


def roll_mystery_result(run_state, node, seed=DEBUG_SEED):
    """
    ？节点概率：
    battle / shop / event / treasure = 3 / 2 / 4 / 1

    特别规则：
    随机到 battle 后，有 20% 概率变成 elite。
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

    result = rng.choices(
        population=["battle", "shop", "event", "treasure"],
        weights=[3, 2, 4, 1],
        k=1
    )[0]

    if result == "battle":
        if rng.random() < 0.20:
            return "elite"

        return "normal_enemy"

    return result


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
    enemy_ids = encounter.get("enemy_ids", [])
    player = create_player_for_battle(run_state)
    game_state, battle_reply = start_battle_with_player(
        session_id=run_state.session_id,
        character_id=run_state.character_id,
        player=player,
        enemy_ids=enemy_ids,
        seed=seed
    )
    run_state.current_battle = game_state
    run_state.current_battle_node_type = effective_node_type
    return "\n".join([
        "进入路线节点：{} ({})".format(node.name, node.node_type),
        "遭遇：{}".format(encounter_id),
        "",
        battle_reply
    ])

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
    关键点：
    1. normal_enemy：优先用路线节点显式 encounter_id，没有则从普通池抽。
    2. elite：无论普通 elite 节点，还是 mystery 随机出的 elite，都从精英池抽。
    3. boss：优先用路线节点显式 encounter_id，没有则从 boss 池抽。
    """
    rng = random.Random(make_encounter_seed(
        run_state,
        node,
        effective_node_type,
        seed=seed
    ))
    # 精英统一走精英池。
    # 这样普通 elite 节点和 ? -> elite 都能抽到混沌群友。
    if effective_node_type == "elite":
        return pick_encounter_id_by_node_type("elite", rng)
    # Boss 可以先允许路线显式指定。
    # 现在你的 boss 可能还在用 encounter.boss_dummy。
    if effective_node_type == "boss":
        if getattr(node, "encounter_id", ""):
            return node.encounter_id
        return pick_encounter_id_by_node_type("boss", rng)
    # 普通战斗：正常节点可以显式指定 encounter。
    # mystery 随机出的 normal_enemy 一般没有 encounter_id，会走普通池。
    if effective_node_type == "normal_enemy":
        if node.node_type != "mystery" and getattr(node, "encounter_id", ""):
            return node.encounter_id

        return pick_encounter_id_by_node_type("normal_enemy", rng)
    # 兜底。
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
        "normal_enemy": 1000,
        "elite": 2000,
        "boss": 3000,
    }
    type_offset = type_offset_map.get(effective_node_type, 0)
    return int(base_seed) + node_seed + type_offset

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

    lines.append("")
    lines.append(reward_state.reward_text())

    return "\n".join(lines)

def choose_next_node(run_state, choice_index, seed=DEBUG_SEED):
    """
    选择后续节点并进入。
    """
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

    if choice_index < 0 or choice_index >= len(next_nodes):
        return "下一节点编号无效。"

    selected_node = next_nodes[choice_index]
    run_state.current_node_id = selected_node.node_id

    return enter_current_node(run_state, seed=seed)


def get_run_view(run_state):
    lines = []
    lines.append("=== Run 状态 ===")
    # lines.append("{} HP：{}/{}".format(
    #     run_state.character_name,
    #     run_state.hp,
    #     run_state.max_hp
    # ))
    lines.append("金币：{}".format(run_state.gold))
    if run_state.current_battle is not None:
        lines.append("")
        lines.append(get_combat_view(run_state.current_battle))
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
        "使用 /card next 0 选择下一个节点。"
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