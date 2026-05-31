# -*- coding: utf-8 -*-

import random

from data.character.AAAregistry import create_character
from data.card.AAAregistry import create_deck
from data.relic.AAAregistry import create_relics
from data.enemy.AAAregistry import create_enemy
from data.potion.AAAregistry import create_potions
from game.status.status_defs import get_status_name

from game.constants import (DEBUG_SEED, EVENT_POTION_USE_AFTER,
                            EVENT_TURN_START, EVENT_TURN_END, 
                            EVENT_CARD_PLAY_AFTER,
                            DAMAGE_SOURCE_ENEMY_ACTION, BLOCK_SOURCE_ENEMY_ACTION)

from game.player_state import PlayerState
from game.game_state import GameState
from game.effects import apply_card_effects
from game.battle_context import BattleContext
from game.event_bus import dispatch_event
from game.damage import deal_damage
from game.modifiers import apply_modifier_profile
from game.x_value import is_x_cost_card, calculate_card_x_value
from data.card.keyword_rules import (
    should_exhaust_after_play,
    should_exhaust_at_turn_end,
    should_retain_at_turn_end,
    should_play_when_discarded,
    should_start_in_hand,
)

def move_innate_cards_to_opening_hand(player):
    """
    固有：战斗开始时进入起始手牌。
    固有牌会从抽牌堆中取出，放入手牌。
    """
    logs = []

    if not player.draw_pile:
        return logs

    new_draw_pile = []
    innate_cards = []

    for card in player.draw_pile:
        if should_start_in_hand(card):
            innate_cards.append(card)
        else:
            new_draw_pile.append(card)

    player.draw_pile = new_draw_pile

    max_hand_size = getattr(player, "max_hand_size", 10)

    for card in innate_cards:
        if len(player.hand) >= max_hand_size:
            player.draw_pile.append(card)
            logs.append("【{}】因手牌已满，固有没有生效，留在抽牌堆。".format(card.name))
            continue

        player.hand.append(card)
        logs.append("【{}】因固有进入起始手牌。".format(card.name))

    return logs

def format_enemy_start_info(enemies):
    """
    战斗开始时显示敌人信息。
    多敌人时逐个显示。
    """
    lines = []
    if not enemies:
        return "敌人：无"
    lines.append("敌人信息：")
    for index, enemy in enumerate(enemies):
        lines.append("[{}] {}".format(
            index,
            enemy.status_text()
        ))
    return "\n".join(lines)

def start_battle(session_id, character_id="character.test", enemy_ids=None, seed=DEBUG_SEED):
    """
    创建一场新战斗。
    """
    if enemy_ids is None:
        enemy_ids = ["enemy.test_dummy"]

    if seed is not None:
        random.seed(seed)

    character = create_character(character_id)
    relics = create_relics(character.starting_relic_ids)
    deck = create_deck(character.starting_deck_ids)
    potions = create_potions(getattr(character, "starting_potion_ids", []))
    enemies = [create_enemy(enemy_id) for enemy_id in enemy_ids]

    random.shuffle(deck)

    player = PlayerState(
        character_id=character.character_id,
        name=character.name,
        max_hp=character.max_hp,
        hp=character.max_hp,
        max_cost=character.max_cost,
        cost=character.max_cost,
        relics=relics,
        potions=potions,
        draw_pile=deck,
        discard_pile=[],
        exhaust_pile=[],
        hand=[]
    )

    game_state = GameState(
        session_id=session_id,
        character_id=character.character_id,
        player=player,
        enemies=enemies,
        turn_count=1
    )
    logs = []
    logs.append("战斗开始。")
    logs.append(format_enemy_start_info(enemies))
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player
    )
    logs.extend(dispatch_event(game_state, EVENT_TURN_START, context))
    logs.extend(move_innate_cards_to_opening_hand(player))
    logs.append(player.status_text())
    opening_draw_count = 5 - len(player.hand)
    if opening_draw_count < 0:
        opening_draw_count = 0
    logs.extend(player.draw_cards(opening_draw_count))
    return game_state, "\n".join(logs)

def start_battle_with_player(session_id, character_id, player, enemy_ids=None, seed=DEBUG_SEED):
    """
    使用外部传入的 PlayerState 创建一场战斗。
    用于 RunState 流程：
    - HP 来自 RunState
    - 牌组来自 RunState.master_deck
    - 遗物、药水来自 RunState
    - 可预留跨战斗状态
    """
    if enemy_ids is None:
        enemy_ids = ["enemy.test_dummy"]
    if seed is not None:
        random.seed(seed)
    enemies = [create_enemy(enemy_id) for enemy_id in enemy_ids]

    # 每场战斗开始时，战斗内临时区重置
    player.cost = player.max_cost
    player.block = 0
    player.hand = []
    player.discard_pile = []
    player.exhaust_pile = []
    random.shuffle(player.draw_pile)
    game_state = GameState(
        session_id=session_id,
        character_id=character_id,
        player=player,
        enemies=enemies,
        turn_count=1
    )
    logs = []
    logs.append("战斗开始。")
    logs.append(format_enemy_start_info(enemies))
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player
    )
    logs.extend(dispatch_event(game_state, EVENT_TURN_START, context))
    logs.extend(move_innate_cards_to_opening_hand(player))
    logs.append(player.status_text())
    opening_draw_count = 5 - len(player.hand)
    if opening_draw_count < 0:
        opening_draw_count = 0
    logs.extend(player.draw_cards(opening_draw_count))
    return game_state, "\n".join(logs)

def get_default_target_index(game_state):
    for index, enemy in enumerate(game_state.enemies):
        if enemy.is_alive():
            return index
    return 0

def move_played_card_to_destination(player, card):
    logs = []

    if should_exhaust_after_play(card):
        player.exhaust_pile.append(card)
        logs.append("【{}】因消耗进入消耗堆。".format(card.name))
    else:
        player.discard_pile.append(card)
        logs.append("【{}】进入弃牌堆。".format(card.name))

    return logs

def resolve_discarded_card(game_state, card, reason="丢弃", trigger_clever=False):
    player = game_state.player
    logs = []

    if trigger_clever and should_play_when_discarded(card):
        logs.append("【{}】因奇巧被{}，免费打出。".format(card.name, reason))

        target_index = get_default_target_index(game_state)
        logs.extend(apply_card_effects(game_state, card, target_index))

        context = BattleContext(
            game_state=game_state,
            player=player,
            source=player,
            card=card
        )
        logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))

        logs.extend(move_played_card_to_destination(player, card))
        return logs

    player.discard_pile.append(card)
    logs.append("【{}】被{}，进入弃牌堆。".format(card.name, reason))
    return logs

def end_player_turn_hand_cleanup(game_state):
    player = game_state.player
    old_hand = player.hand
    player.hand = []

    logs = []
    retained_cards = []

    for card in old_hand:
        # 虚无优先级最高：回合结束仍在手牌时，直接进入消耗堆。
        if should_exhaust_at_turn_end(card):
            player.exhaust_pile.append(card)
            logs.append("【{}】因虚无进入消耗堆。".format(card.name))
            continue

        if should_retain_at_turn_end(card):
            retained_cards.append(card)
            logs.append("【{}】因保留留在手牌。".format(card.name))
            continue

        logs.extend(resolve_discarded_card(
            game_state,
            card,
            reason="回合结束丢弃",
            trigger_clever=False
        ))

    player.hand.extend(retained_cards)

    if not old_hand:
        logs.append("没有手牌需要处理。")

    return logs

def discard_selected_hand_cards(game_state, hand_indices):
    player = game_state.player
    logs = []

    unique_indices = []
    seen = set()

    for index in hand_indices:
        if index in seen:
            continue
        seen.add(index)
        unique_indices.append(index)

    if not unique_indices:
        if game_state.pending_discard_selection:
            game_state.pending_discard_selection = False
            game_state.pending_discard_source = ""
            return "未选择丢弃手牌。"
        return "没有指定要丢弃的手牌。"

    for index in unique_indices:
        if index < 0 or index >= len(player.hand):
            return "手牌编号无效：{}。".format(index)

    indexed_cards = [
        (index, player.hand[index])
        for index in unique_indices
    ]

    for index in sorted(unique_indices, reverse=True):
        player.hand.pop(index)

    for index, card in indexed_cards:
        logs.append("选择丢弃手牌 [{}] 【{}】。".format(index, card.name))
        logs.extend(resolve_discarded_card(
            game_state,
            card,
            reason="主动丢弃",
            trigger_clever=True
        ))

    if game_state.pending_discard_selection:
        game_state.pending_discard_selection = False
        game_state.pending_discard_source = ""

    result = check_battle_result(game_state)
    if result:
        logs.append(result)

    return "\n".join(logs)

def check_battle_result(game_state):
    """
    检查战斗是否结束。
    """
    if game_state.is_all_enemies_dead():
        game_state.battle_over = True
        game_state.victory = True
        return "所有敌人已被击败，战斗胜利。"

    if not game_state.player.is_alive():
        game_state.battle_over = True
        game_state.victory = False
        return "{} 已倒下，战斗失败。".format(game_state.player.name)

    return None


def play_card(game_state, hand_index, target_index=0):
    """
    打出一张手牌。
    """
    logs = []

    if game_state.battle_over:
        return "战斗已经结束。"

    player = game_state.player

    if hand_index < 0 or hand_index >= len(player.hand):
        return "手牌编号无效。"

    card = player.hand[hand_index]

    is_x_cost = is_x_cost_card(card)
    x_value = None
    raw_x = None
    x_logs = []

    if is_x_cost:
        raw_x = player.cost
        x_value, x_logs = calculate_card_x_value(
            game_state=game_state,
            card=card,
            raw_x=raw_x
        )
    else:
        if card.cost > player.cost:
            return "费用不足。当前费用：{}，卡牌费用：{}。".format(
                player.cost,
                card.cost
            )

    if card.target == "enemy":
        if target_index < 0 or target_index >= len(game_state.enemies):
            return "目标敌人编号无效。"

        if not game_state.enemies[target_index].is_alive():
            return "目标敌人已经死亡。"

    if is_x_cost:
        spent_cost = player.cost
        player.cost = 0
    else:
        spent_cost = card.cost
        player.cost -= card.cost

    # 从手牌中取出
    player.hand.pop(hand_index)

    if is_x_cost:
        logs.append("打出【{}】，消耗全部剩余费用 {}，最终 X = {}。".format(
            card.name,
            spent_cost,
            x_value
        ))
        logs.extend(x_logs)
    else:
        logs.append("打出【{}】，消耗 {} 点费用。".format(
            card.name,
            spent_cost
        ))

    # 执行效果
    effect_context = {}
    if is_x_cost:
        effect_context = {
            "raw_x": raw_x,
            "x": x_value,
            "spent_cost": spent_cost
        }

    logs.extend(apply_card_effects(
        game_state,
        card,
        target_index,
        effect_context=effect_context
    ))

    # 出牌后事件：先用于测试遗物的“打出技能牌”触发
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        card=card
    )
    logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))

    logs.extend(move_played_card_to_destination(player, card))

    result = check_battle_result(game_state)
    if result:
        logs.append(result)

    return "\n".join(logs)

def play_cards_by_original_indices(game_state, hand_indices, target_index=0):
    """
    按命令输入时的原始手牌编号依次打出多张牌。

    规则：
    1. 先根据当前手牌快照锁定这些牌。
    2. 每张牌打出前重新检查它是否还在手牌中。
    3. 每张牌打出前检查费用、目标是否合法。
    4. 某张牌无法打出时，中止，后续牌不再计算。
    5. 已经打出的牌不会回滚。
    """
    logs = []

    if game_state.battle_over:
        return "战斗已经结束。"

    player = game_state.player

    if not hand_indices:
        return "没有指定要打出的手牌。"

    seen = set()
    selected_cards = []

    for original_index in hand_indices:
        if original_index in seen:
            return "手牌编号重复：{}。".format(original_index)

        seen.add(original_index)

        if original_index < 0 or original_index >= len(player.hand):
            return "手牌编号无效：{}。".format(original_index)

        selected_cards.append((original_index, player.hand[original_index]))

    is_multi_play = len(selected_cards) > 1

    for step_index, item in enumerate(selected_cards):
        original_index, card = item

        if game_state.battle_over:
            logs.append("战斗已经结束，后续牌不再计算。")
            break

        current_index = -1

        for index, hand_card in enumerate(player.hand):
            if hand_card is card:
                current_index = index
                break

        if current_index < 0:
            logs.append("原手牌编号 [{}] 的【{}】已不在手牌中，批量出牌中止。".format(
                original_index,
                card.name
            ))
            break

        if card.cost > player.cost:
            logs.append("原手牌编号 [{}] 的【{}】费用不足，批量出牌中止。当前费用：{}，卡牌费用：{}。".format(
                original_index,
                card.name,
                player.cost,
                card.cost
            ))
            break

        if card.target == "enemy":
            if target_index < 0 or target_index >= len(game_state.enemies):
                logs.append("目标敌人编号无效，批量出牌中止：{}。".format(target_index))
                break

            if not game_state.enemies[target_index].is_alive():
                logs.append("目标敌人已经死亡，批量出牌中止。")
                break

        if is_multi_play:
            logs.append("批量出牌 {}/{}：原手牌编号 [{}]【{}】。".format(
                step_index + 1,
                len(selected_cards),
                original_index,
                card.name
            ))

        logs.append(play_card(game_state, current_index, target_index))

    return "\n".join(logs)

def use_potion(game_state, potion_index, target_index=0):
    """
    使用药水。
    """
    logs = []

    if game_state.battle_over:
        return "战斗已经结束。"

    player = game_state.player

    if potion_index < 0 or potion_index >= len(player.potions):
        return "药水编号无效。"

    potion = player.potions[potion_index]

    if potion.target == "enemy":
        if target_index < 0 or target_index >= len(game_state.enemies):
            return "目标敌人编号无效。"

        if not game_state.enemies[target_index].is_alive():
            return "目标敌人已经死亡。"

    player.potions.pop(potion_index)

    logs.append("{} 使用了【{}】。".format(player.name, potion.name))

    logs.extend(apply_card_effects(
        game_state=game_state,
        card=potion,
        target_index=target_index
    ))

    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        target=None,
        card=None,
        extra={
            "potion": potion
        }
    )
    logs.extend(dispatch_event(game_state, EVENT_POTION_USE_AFTER, context))

    result = check_battle_result(game_state)
    if result:
        logs.append(result)
    return "\n".join(logs)

def get_status_decay_entities(game_state):
    """
    获取需要进行自然状态衰减的战斗实体。
    当前包括：
    - 玩家
    - 存活敌人
    """
    entities = []
    player = getattr(game_state, "player", None)
    if player is not None and player.is_alive():
        entities.append(player)
    for enemy in game_state.enemies:
        if enemy.is_alive():
            entities.append(enemy)
    return entities


def decay_statuses_by_timing(game_state, timing):
    """
    按指定时机衰减所有战斗实体的状态。
    例如：
    易伤 / 虚弱：turn_end 时 -1。
    """
    logs = []
    for entity in get_status_decay_entities(game_state):
        statuses = getattr(entity, "statuses", None)
        if statuses is None:
            continue
        decay_logs = statuses.decay_by_timing(timing)
        for log in decay_logs:
            logs.append("{} 的 {}".format(entity.name, log))
    return logs

def process_enemy_action(game_state, enemy):
    """
    处理单个敌人的行动。
    enemy.act() 只返回动作，不直接处理玩家扣血。
    """
    logs = []

    old_block = enemy.clear_block()
    if old_block > 0:
        logs.append("{} 的 {} 点格挡消失。".format(enemy.name, old_block))
        
    result = enemy.act()

    for log in result.logs:
        logs.append(log)

    action = result.action
    op = action.get("op")

    if op == "enemy_attack":
        damage = int(action.get("damage", 0))

        damage = apply_modifier_profile(
            value=damage,
            modifier_profile="attack_damage",
            game_state=game_state,
            source=enemy,
            target=game_state.player,
            card=None,
            damage_source=DAMAGE_SOURCE_ENEMY_ACTION
        )

        logs.extend(deal_damage(
            game_state=game_state,
            source=enemy,
            target=game_state.player,
            amount=damage,
            damage_kind="attack",
            card=None
        ))

    elif op == "enemy_gain_block":
        block = int(action.get("block", 0))
        block = apply_modifier_profile(
            value=block,
            modifier_profile="block",
            game_state=game_state,
            source=enemy,
            target=enemy,
            card=None,
            block_source=BLOCK_SOURCE_ENEMY_ACTION
        )
        if block < 0:
            block = 0
        enemy.block += block
        logs.append("{} 获得 {} 点格挡。".format(
            enemy.name,
            block
        ))

    elif op == "enemy_gain_status":
        target_key = action.get("target", "player")
        status_key = action.get("status", "")
        amount = int(action.get("amount", 0))
        if not status_key:
            logs.append("敌人状态行动缺少 status。")
            return logs
        if target_key == "self":
            target = enemy
        else:
            target = game_state.player
        current = target.gain_status(status_key, amount)
        status_name = get_status_name(status_key)
        logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
            target.name,
            amount,
            status_name,
            status_name,
            current
        ))

    else:
        logs.append("敌人行动未处理：{}".format(op))

    return logs

def format_enemy_current_status(enemies):
    """
    进入新回合时显示敌人当前状态。
    主要用于查看敌人 HP、格挡、状态、下一步意图。
    """
    lines = []
    alive_enemies = [
        enemy for enemy in enemies
        if enemy.is_alive()
    ]
    if not alive_enemies:
        return "敌人状态：无存活敌人"
    lines.append("敌人状态：")
    for index, enemy in enumerate(enemies):
        if not enemy.is_alive():
            continue
        lines.append("[{}] {}".format(
            index,
            enemy.status_text()
        ))
    return "\n".join(lines)

def end_turn(game_state):
    """
    结束玩家回合，敌人行动，然后进入下一回合。
    """
    logs = []

    if game_state.battle_over:
        return "战斗已经结束。"

    player = game_state.player

    logs.append("玩家回合结束。")
    game_state.pending_discard_selection = False
    game_state.pending_discard_source = ""
    logs.extend(end_player_turn_hand_cleanup(game_state))

    logs.append("")
    logs.append("敌人行动：")

    for enemy in game_state.enemies:
        if not enemy.is_alive():
            continue
        logs.extend(process_enemy_action(game_state, enemy))
        result = check_battle_result(game_state)
        if result:
            logs.append(result)
            return "\n".join(logs)
    status_decay_logs = decay_statuses_by_timing(game_state, EVENT_TURN_END)
    if status_decay_logs:
        logs.append("")
        logs.append("状态衰减：")
        logs.extend(status_decay_logs)
    # 进入下一回合
    game_state.turn_count += 1
    player.start_turn()
    logs.append("")
    logs.append("进入第 {} 回合。".format(game_state.turn_count))
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player
    )
    logs.extend(dispatch_event(game_state, EVENT_TURN_START, context))
    logs.append(player.status_text())
    logs.append(format_enemy_current_status(game_state.enemies))
    logs.extend(player.draw_cards(5))
    return "\n".join(logs)


def get_status(game_state):
    return game_state.status_text()


def get_hand(game_state):
    return game_state.player.hand_text()

def get_combat_view(game_state):
    return "\n\n".join([
        game_state.status_text(),
        game_state.player.hand_text()
    ])

def format_relic_list(relics):
    relic_count_map = {}
    relic_map = {}

    for relic in relics:
        relic_id = getattr(relic, "relic_id", "")

        if relic_id not in relic_count_map:
            relic_count_map[relic_id] = 0
            relic_map[relic_id] = relic

        relic_count_map[relic_id] += 1

    lines = []
    lines.append("=== 当前遗物 ===")

    for relic_id, relic in relic_map.items():
        count = relic_count_map[relic_id]

        if count > 1:
            name_text = "{}（{}）".format(relic.name, count)
        else:
            name_text = relic.name

        lines.append("【{}】：{}".format(
            name_text,
            relic.description
        ))

    return "\n".join(lines)

def get_relics(game_state):
    player = game_state.player

    if not player.relics:
        return "当前没有遗物。"

    return format_relic_list(player.relics)

def get_draw_pile(game_state):
    return game_state.player.draw_pile_text()

def get_discard_pile(game_state):
    return game_state.player.discard_pile_text()

def get_exhaust_pile(game_state):
    return game_state.player.exhaust_pile_text()

def get_potions(game_state):
    return game_state.player.potions_text()