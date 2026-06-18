# -*- coding: utf-8 -*-

import random

from data.character.AAAregistry import create_character
from data.card.AAAregistry import create_deck
from data.relic.AAAregistry import create_relics
from data.enemy.AAAregistry import create_enemy
from data.potion.AAAregistry import create_potions
from game.status.status_defs import get_status_name
from game.card_cost import get_card_current_cost

from game.constants import (DEBUG_SEED, EVENT_POTION_USE_AFTER,
                            EVENT_BATTLE_START,
                            EVENT_TURN_START, EVENT_TURN_END, 
                            EVENT_CARD_PLAY_AFTER, EVENT_CARD_EXHAUST,
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
    can_play_card,
)
from game.zone_utils import (
    tick_zone_turn_end, 
    tick_fields_turn_end, 
    format_zone_field_detail,
    is_card_first_play_this_battle,
    mark_card_played_this_battle,
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

def format_enemy_start_info(enemies, game_state=None):
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
            enemy.status_text(game_state)
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
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player
    )
    logs.extend(dispatch_event(game_state, EVENT_BATTLE_START, context))
    logs.append(format_enemy_start_info(enemies, game_state))
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
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player
    )
    logs.extend(dispatch_event(game_state, EVENT_BATTLE_START, context))
    logs.append(format_enemy_start_info(enemies, game_state))
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

def move_card_to_exhaust_pile(game_state, card, reason="after_play"):
    """
    将牌放入消耗堆，并分发“卡牌被消耗”事件。
    reason:
    - after_play：因“消耗”关键词打出后进入消耗堆
    - ethereal：因“虚无”在回合结束进入消耗堆
    """
    player = game_state.player
    logs = []
    player.exhaust_pile.append(card)
    reason_text_map = {
        "after_play": "因消耗",
        "ethereal": "因虚无",
    }
    reason_text = reason_text_map.get(reason, "因{}".format(reason))
    logs.append("【{}】{}进入消耗堆。".format(card.name, reason_text))
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        card=card,
        extra={
            "reason": reason
        }
    )
    logs.extend(dispatch_event(game_state, EVENT_CARD_EXHAUST, context))
    exhaust_effects = getattr(card, "exhaust_effects", [])
    if exhaust_effects:
        from game.effects import apply_card_effect

        effect_context = {
            "exhaust_reason": reason
        }

        for exhaust_effect in exhaust_effects:
            logs.extend(apply_card_effect(
                game_state=game_state,
                card=card,
                effect=exhaust_effect,
                target_index=0,
                effect_context=effect_context
            ))

            if game_state.battle_over:
                break
    return logs


def move_played_card_to_destination(game_state, card):
    logs = []
    player = game_state.player
    if getattr(card, "card_type", "") == "power":
        logs.append("【{}】作为能力牌生效，本场战斗中消失。".format(card.name))
        return logs
    if should_exhaust_after_play(card):
        logs.extend(move_card_to_exhaust_pile(
            game_state=game_state,
            card=card,
            reason="after_play"
        ))
    else:
        player.discard_pile.append(card)
        logs.append("【{}】进入弃牌堆。".format(card.name))
    return logs

def resolve_discarded_card(game_state, card, reason="丢弃", trigger_clever=False):
    player = game_state.player
    logs = []

    if trigger_clever and should_play_when_discarded(card):
        can_play, cannot_play_reason = can_play_card(
            game_state=game_state,
            card=card,
            play_reason="discard_trigger"
        )
        if not can_play:
            logs.append(cannot_play_reason)
            player.discard_pile.append(card)
            logs.append("【{}】被 {}，进入弃牌堆。".format(card.name, reason))
            return logs
        logs.append("【{}】因奇巧被{}，免费打出。".format(card.name, reason))

        target_index = get_default_target_index(game_state)
        effect_context = {
            "card_first_play_this_battle": is_card_first_play_this_battle(game_state, card)
        }
        logs.extend(apply_card_effects(
            game_state,
            card,
            target_index,
            effect_context=effect_context
        ))
        mark_card_played_this_battle(game_state, card)

        context = BattleContext(
            game_state=game_state,
            player=player,
            source=player,
            card=card
        )
        logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))

        logs.extend(move_played_card_to_destination(game_state, card))
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
            logs.extend(move_card_to_exhaust_pile(
                game_state=game_state,
                card=card,
                reason="ethereal"
            ))
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

def clear_pending_discard_to_draw_top(game_state):
    game_state.pending_discard_to_draw_selection = False
    game_state.pending_discard_to_draw_source = ""
    game_state.pending_discard_to_draw_options = []

def clear_turn_temporary_card_costs(player):
    """
    清除本回合临时费用变化。
    例如地狱之刃生成的攻击牌：本回合费用为 0。
    """
    cleared = 0

    pile_names = [
        "draw_pile",
        "hand",
        "discard_pile",
        "exhaust_pile"
    ]

    for pile_name in pile_names:
        pile = getattr(player, pile_name, [])
        for card in pile:
            if hasattr(card, "temporary_cost_override"):
                delattr(card, "temporary_cost_override")
                cleared += 1

    return cleared

def choose_pending_discard_to_draw_top(game_state, choice_index):
    """
    处理头槌类效果：
    从 pending 选项中选择一张弃牌堆里的牌，放到抽牌堆顶。
    """
    if not game_state.pending_discard_to_draw_selection:
        return "当前没有需要处理的弃牌堆置顶选择。"

    options = getattr(game_state, "pending_discard_to_draw_options", [])

    if not options:
        clear_pending_discard_to_draw_top(game_state)
        return "没有可选择的弃牌堆卡牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.discard_pile:
        clear_pending_discard_to_draw_top(game_state)
        return "所选牌已经不在弃牌堆中，选择已取消。"

    player.discard_pile.remove(chosen_card)
    player.draw_pile.append(chosen_card)

    source = game_state.pending_discard_to_draw_source
    clear_pending_discard_to_draw_top(game_state)

    return "【{}】选择了【{}】，将其放到抽牌堆顶。它会成为下一张抽到的牌。".format(
        source,
        chosen_card.name
    )

def clear_pending_duplicate_hand_selection(game_state):
    game_state.pending_duplicate_hand_selection = False
    game_state.pending_duplicate_hand_source = ""
    game_state.pending_duplicate_hand_options = []
    game_state.pending_duplicate_hand_count = 0


def choose_pending_duplicate_hand_card(game_state, choice_index):
    """
    处理双持：
    选择一张攻击或能力牌，复制到手牌。
    若手牌已满，复制品进入弃牌堆。
    复制品保留原卡当前状态，包括升级、费用变化、card_vars 变化等。
    """
    if not game_state.pending_duplicate_hand_selection:
        return "当前没有需要处理的复制手牌选择。"

    options = getattr(game_state, "pending_duplicate_hand_options", [])

    if not options:
        clear_pending_duplicate_hand_selection(game_state)
        return "没有可选择的手牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.hand:
        clear_pending_duplicate_hand_selection(game_state)
        return "所选牌已经不在手牌中，选择已取消。"

    count = int(getattr(game_state, "pending_duplicate_hand_count", 0))
    source = game_state.pending_duplicate_hand_source

    import copy

    added_to_hand = 0
    added_to_discard = 0

    for _ in range(count):
        copied_card = copy.deepcopy(chosen_card)
        setattr(copied_card, "temporary", True)
        setattr(copied_card, "created_in_battle", True)

        if player.is_hand_full():
            player.discard_pile.append(copied_card)
            added_to_discard += 1
        else:
            player.hand.append(copied_card)
            added_to_hand += 1

    clear_pending_duplicate_hand_selection(game_state)

    logs = []

    if added_to_hand > 0:
        logs.append("【{}】复制了 {} 张【{}】到手牌。".format(
            source,
            added_to_hand,
            chosen_card.name
        ))

    if added_to_discard > 0:
        logs.append("手牌已满，{} 张【{}】的复制品进入弃牌堆。".format(
            added_to_discard,
            chosen_card.name
        ))

    if not logs:
        logs.append("【{}】没有添加复制品。".format(source))

    return "\n".join(logs)

def clear_pending_exhaust_hand_selection(game_state):
    game_state.pending_exhaust_hand_selection = False
    game_state.pending_exhaust_hand_source = ""
    game_state.pending_exhaust_hand_options = []
    game_state.pending_exhaust_hand_source_card = None
    game_state.pending_exhaust_hand_target_index = 0
    game_state.pending_exhaust_hand_required_card_types = []
    game_state.pending_exhaust_hand_after_effects = []


def choose_pending_exhaust_hand(game_state, choice_index):
    """
    处理：
    - 坚毅+：选择 1 张手牌消耗。
    - 燔祭·旧：选择 1 张手牌消耗；如果是状态牌或诅咒牌，继续触发后续效果。
    """
    if not game_state.pending_exhaust_hand_selection:
        return "当前没有需要处理的手牌消耗选择。"

    options = getattr(game_state, "pending_exhaust_hand_options", [])

    if not options:
        clear_pending_exhaust_hand_selection(game_state)
        return "没有可选择的手牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.hand:
        clear_pending_exhaust_hand_selection(game_state)
        return "所选牌已经不在手牌中，选择已取消。"

    source = game_state.pending_exhaust_hand_source
    source_card = game_state.pending_exhaust_hand_source_card
    target_index = int(getattr(game_state, "pending_exhaust_hand_target_index", 0))
    required_types = list(getattr(game_state, "pending_exhaust_hand_required_card_types", []))
    after_effects = list(getattr(game_state, "pending_exhaust_hand_after_effects", []))
    player.hand.remove(chosen_card)
    logs = []
    logs.append("【{}】选择消耗手牌【{}】。".format(
        source,
        chosen_card.name
    ))
    logs.extend(move_card_to_exhaust_pile(
        game_state=game_state,
        card=chosen_card,
        reason="selected"
    ))
    clear_pending_exhaust_hand_selection(game_state)

    if required_types:
        chosen_type = getattr(chosen_card, "card_type", "")
        if chosen_type not in required_types:
            logs.append("【{}】不是指定类型，后续效果未触发。".format(
                chosen_card.name
            ))
            result = check_battle_result(game_state)
            if result:
                logs.append(result)
            return "\n".join(logs)
    if after_effects and source_card is not None:
        from game.effects import apply_card_effect

        effect_context = {
            "selected_exhausted_card": chosen_card,
            "selected_exhausted_card_type": getattr(chosen_card, "card_type", "")
        }
        for child_effect in after_effects:
            logs.extend(apply_card_effect(
                game_state=game_state,
                card=source_card,
                effect=child_effect,
                target_index=target_index,
                effect_context=effect_context
            ))
            if game_state.battle_over:
                break
    result = check_battle_result(game_state)
    if result:
        logs.append(result)

    return "\n".join(logs)

def clear_pending_hand_to_draw_top_selection(game_state):
    game_state.pending_hand_to_draw_top_selection = False
    game_state.pending_hand_to_draw_top_source = ""
    game_state.pending_hand_to_draw_top_options = []

def choose_pending_hand_to_draw_top(game_state, choice_index):
    """
    处理战吼：
    选择 1 张手牌放到抽牌堆顶。
    """
    if not game_state.pending_hand_to_draw_top_selection:
        return "当前没有需要处理的手牌置顶选择。"

    options = getattr(game_state, "pending_hand_to_draw_top_options", [])

    if not options:
        clear_pending_hand_to_draw_top_selection(game_state)
        return "没有可选择的手牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.hand:
        clear_pending_hand_to_draw_top_selection(game_state)
        return "所选牌已经不在手牌中，选择已取消。"

    player.hand.remove(chosen_card)
    player.draw_pile.append(chosen_card)

    source = game_state.pending_hand_to_draw_top_source
    clear_pending_hand_to_draw_top_selection(game_state)

    return "【{}】选择了【{}】，将其放到抽牌堆顶。它会成为下一张抽到的牌。".format(
        source,
        chosen_card.name
    )

def clear_pending_upgrade_hand_selection(game_state):
    game_state.pending_upgrade_hand_selection = False
    game_state.pending_upgrade_hand_source = ""
    game_state.pending_upgrade_hand_options = []

def choose_pending_upgrade_hand_card(game_state, choice_index):
    """
    处理武装：
    选择 1 张手牌在本场战斗中临时升级。
    """
    if not game_state.pending_upgrade_hand_selection:
        return "当前没有需要处理的手牌升级选择。"

    options = getattr(game_state, "pending_upgrade_hand_options", [])

    if not options:
        clear_pending_upgrade_hand_selection(game_state)
        return "没有可选择的手牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.hand:
        clear_pending_upgrade_hand_selection(game_state)
        return "所选牌已经不在手牌中，选择已取消。"

    from game.effects import upgrade_card_for_this_combat

    upgraded_card = upgrade_card_for_this_combat(chosen_card)

    if upgraded_card is None:
        clear_pending_upgrade_hand_selection(game_state)
        return "【{}】不能被升级。".format(chosen_card.name)

    replaced = False

    for index, hand_card in enumerate(player.hand):
        if hand_card is chosen_card:
            player.hand[index] = upgraded_card
            replaced = True
            break

    source = game_state.pending_upgrade_hand_source
    clear_pending_upgrade_hand_selection(game_state)

    if not replaced:
        return "所选牌已经不在手牌中，选择已取消。"

    return "【{}】将【{}】临时升级为【{}】。".format(
        source,
        chosen_card.name,
        upgraded_card.name
    )

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
    can_play, cannot_play_reason = can_play_card(
        game_state=game_state,
        card=card,
        play_reason="normal"
    )
    if not can_play:
        return cannot_play_reason

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
        current_cost = get_card_current_cost(game_state, card)

        if current_cost > player.cost:
            return "费用不足。当前费用：{}，卡牌费用：{}。".format(
                player.cost,
                current_cost
            )

    target_error = validate_card_target(game_state, card, target_index)
    if target_error:
        return target_error

    if is_x_cost:
        spent_cost = player.cost
        player.cost = 0
    else:
        spent_cost = get_card_current_cost(game_state, card)
        player.cost -= spent_cost

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
    effect_context["card_first_play_this_battle"] = is_card_first_play_this_battle(game_state, card)

    logs.extend(apply_card_effects(
        game_state,
        card,
        target_index,
        effect_context=effect_context
    ))
    mark_card_played_this_battle(game_state, card)

    # 出牌后事件：先用于测试遗物的“打出技能牌”触发
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        card=card
    )
    logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))

    logs.extend(move_played_card_to_destination(game_state, card))

    if getattr(game_state, "force_end_turn_after_card", False):
        game_state.force_end_turn_after_card = False
        if not game_state.battle_over:
            logs.append("")
            logs.append("【{}】结束了你的回合。".format(card.name))
            logs.append(end_turn(game_state))
            return "\n".join(logs)
        
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
        can_play, cannot_play_reason = can_play_card(
            game_state=game_state,
            card=card,
            play_reason="batch"
        )
        if not can_play:
            logs.append("原手牌编号 [{}] 的【{}】无法打出，批量出牌中止：{}".format(
                original_index,
                card.name,
                cannot_play_reason
            ))
            break
        is_x_cost = is_x_cost_card(card)
        if not is_x_cost:
            try:
                fixed_cost = int(get_card_current_cost(game_state, card))
            except (TypeError, ValueError):
                logs.append("原手牌编号 [{}] 的【{}】费用类型无效，批量出牌中止：{}。".format(
                    original_index,
                    card.name,
                    card.cost
                ))
                break
            if fixed_cost > player.cost:
                logs.append("原手牌编号 [{}] 的【{}】费用不足，批量出牌中止。当前费用：{}，卡牌费用：{}。".format(
                    original_index,
                    card.name,
                    player.cost,
                    fixed_cost
                ))
                break
        card_target = getattr(card, "target", None)
        if card_target == "enemy":
            if target_index < 0 or target_index >= len(game_state.enemies):
                logs.append("目标敌人编号无效，批量出牌中止：{}。".format(target_index))
                break
            if not game_state.enemies[target_index].is_alive():
                logs.append("目标敌人已经死亡，批量出牌中止。")
                break
        elif card_target in ("all_enemies", "random_enemy"):
            if game_state.is_all_enemies_dead():
                logs.append("没有可攻击的敌人，批量出牌中止。")
                break
        elif card_target in ("self", "none", None):
            pass
        else:
            logs.append("原手牌编号 [{}] 的【{}】目标类型未知，批量出牌中止：{}。".format(
                original_index,
                card.name,
                card_target
            ))
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

def find_first_alive_enemy_by_id(game_state, enemy_id, exclude_enemy=None):
    for target in game_state.enemies:
        if target is exclude_enemy:
            continue
        if not target.is_alive():
            continue
        if target.enemy_id == enemy_id:
            return target
    return None


def get_enemy_action_target(game_state, enemy, target_key):
    """
    解析敌人行动目标。

    当前支持：
    - player：玩家
    - self：行动敌人自身
    - corsoal_or_player：优先选择存活珊瑚，没有珊瑚时选择玩家
    - enemy_id:<id>：选择第一个指定 id 的存活敌人
    """
    if not target_key:
        target_key = "player"

    if target_key == "player":
        return game_state.player

    if target_key == "self":
        return enemy

    if target_key == "corsoal_or_player":
        corsoal = find_first_alive_enemy_by_id(
            game_state,
            "enemy.corsoal",
            exclude_enemy=enemy
        )
        if corsoal is not None:
            return corsoal
        return game_state.player

    if target_key.startswith("enemy_id:"):
        enemy_id = target_key.split(":", 1)[1]
        return find_first_alive_enemy_by_id(
            game_state,
            enemy_id,
            exclude_enemy=enemy
        )

    return game_state.player


def process_enemy_action_payload(game_state, enemy, action, logs):
    op = action.get("op")
    attack_type = action.get("attack_type", "")
    attack_element = action.get("attack_element", "")

    from game.zone_utils import (
        get_effective_zone_element_for_enemy_action,
        get_zone_replay_extra,
    )

    zone_element = get_effective_zone_element_for_enemy_action(
        game_state=game_state,
        attack_element=attack_element
    )

    if zone_element and not action.get("_zone_replay_applied", False) and op != "enemy_multi_action":
        replay_extra = get_zone_replay_extra(game_state, zone_element)
        if replay_extra > 0:
            total_times = 1 + replay_extra
            logs.append("{} 的 Zone 使本次意图重放，总结算 {} 次。".format(
                enemy.name,
                total_times
            ))
            replay_action = dict(action)
            replay_action["_zone_replay_applied"] = True
            for replay_index in range(total_times):
                if not enemy.is_alive() or game_state.battle_over:
                    break
                logs.append("{} 的 Zone 重放第 {}/{} 次：".format(
                    enemy.name,
                    replay_index + 1,
                    total_times
                ))
                process_enemy_action_payload(game_state, enemy, replay_action, logs)
            return

    if op == "enemy_multi_action":
        child_actions = action.get("actions", [])
        if not child_actions:
            logs.append("敌人复合行动缺少 actions。")
            return

        for child_action in child_actions:
            process_enemy_action_payload(game_state, enemy, child_action, logs)
            result = check_battle_result(game_state)
            if result:
                logs.append(result)
                break
        return

    if op == "enemy_attack":
        target_key = action.get("target", "player")
        target = get_enemy_action_target(game_state, enemy, target_key)
        if target is None:
            logs.append("敌人攻击目标无效。")
            return
        if not target.is_alive():
            logs.append("{} 的攻击目标已经死亡。".format(enemy.name))
            return
        damage = int(action.get("damage", 0))
        attack_type = action.get("attack_type", "")
        attack_element = action.get("attack_element", "")
        damage = apply_modifier_profile(
            value=damage,
            modifier_profile="attack_damage",
            game_state=game_state,
            source=enemy,
            target=target,
            card=None,
            damage_source=DAMAGE_SOURCE_ENEMY_ACTION,
            attack_type=attack_type,
            attack_element=attack_element
        )
        from game.zone_utils import (
            apply_zone_amount_modifier,
            apply_zone_source_hp_loss_if_needed,
            get_zone_burn_amount,
            add_status_to_target,
        )
        damage = apply_zone_amount_modifier(damage, game_state, zone_element)
        logs.extend(deal_damage(
            game_state=game_state,
            source=enemy,
            target=target,
            amount=damage,
            damage_kind="attack",
            card=None,
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        ))
        burn = get_zone_burn_amount(game_state, zone_element)
        if burn > 0 and target.is_alive():
            logs.append(add_status_to_target(target, "burn", burn))
        apply_zone_source_hp_loss_if_needed(
            game_state=game_state,
            source=enemy,
            zone_element=zone_element,
            logs=logs,
            label="阴 Zone"
        )
        return
    if op == "enemy_gain_block":
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
        from game.zone_utils import (
            apply_zone_amount_modifier,
            apply_earth_zone_temp_thorns,
            apply_zone_source_hp_loss_if_needed,
        )
        block = apply_zone_amount_modifier(block, game_state, zone_element)
        if block < 0:
            block = 0
        enemy.block += block
        logs.append("{} 获得 {} 点格挡。".format(
            enemy.name,
            block
        ))
        apply_earth_zone_temp_thorns(
            game_state=game_state,
            target=enemy,
            zone_element=zone_element,
            block_amount=block,
            logs=logs
        )
        apply_zone_source_hp_loss_if_needed(
            game_state=game_state,
            source=enemy,
            zone_element=zone_element,
            logs=logs,
            label="阴 Zone"
        )
        return
    
    if op == "enemy_add_card_to_discard":
        card_id = action.get("card_id", "")
        count = int(action.get("count", 1))
        if not card_id:
            logs.append("敌人加牌行动缺少 card_id。")
            return
        if count <= 0:
            logs.append("敌人加牌数量为 0。")
            return
        from data.card.AAAregistry import create_card
        added_cards = []
        for _ in range(count):
            card = create_card(card_id)
            game_state.player.discard_pile.append(card)
            added_cards.append(card)
        card_name = added_cards[0].name if added_cards else card_id
        logs.append("{} 向你的弃牌堆加入 {} 张【{}】。".format(
            enemy.name,
            count,
            card_name
        ))
        return
    
    if op == "enemy_gain_status":
        target_key = action.get("target", "player")
        status_key = action.get("status", "")
        amount = int(action.get("amount", 0))
        from game.zone_utils import apply_zone_amount_modifier, apply_zone_source_hp_loss_if_needed
        amount = apply_zone_amount_modifier(amount, game_state, zone_element)
        if not status_key:
            logs.append("敌人状态行动缺少 status。")
            return
        target = get_enemy_action_target(game_state, enemy, target_key)
        if target is None:
            logs.append("敌人状态行动目标无效。")
            return
        if not target.is_alive():
            logs.append("{} 的状态行动目标已经死亡。".format(enemy.name))
            return
        if hasattr(target, "gain_status_with_result"):
            result = target.gain_status_with_result(status_key, amount)
            from game.status.status_gain import format_status_gain_log
            logs.append(format_status_gain_log(target, status_key, amount, result))
        else:
            current = target.gain_status(status_key, amount)
            status_name = get_status_name(status_key)
            logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
                target.name,
                amount,
                status_name,
                status_name,
                current
            ))
        apply_zone_source_hp_loss_if_needed(
            game_state=game_state,
            source=enemy,
            zone_element=zone_element,
            logs=logs,
            label="阴 Zone"
        )
        return
    logs.append("敌人行动未处理：{}".format(op))


def process_enemy_action(game_state, enemy):
    """
    处理单个敌人的行动。
    enemy.act() 只返回动作，不直接处理玩家扣血。
    """
    logs = []
    old_block = enemy.clear_block()
    if old_block > 0:
        logs.append("{} 的 {} 点格挡消失。".format(enemy.name, old_block))
    if enemy.get_status_value("stun") > 0:
        current_stun = enemy.gain_status("stun", -1)
        logs.append("{} 被眩晕，无法行动。剩余眩晕：{}。".format(
            enemy.name,
            current_stun
        ))
        return logs
    result = enemy.act()
    for log in result.logs:
        logs.append(log)
    process_enemy_action_payload(
        game_state=game_state,
        enemy=enemy,
        action=result.action,
        logs=logs
    )
    return logs

def format_enemy_current_status(game_state):
    """
    进入新回合时显示敌人当前状态。
    死亡敌人不从显示中跳过，意图会显示为“已经走了有一会了。”。
    """
    enemies = game_state.enemies
    lines = []
    alive_enemies = [
        enemy for enemy in enemies
        if enemy.is_alive()
    ]
    if not alive_enemies:
        return "敌人状态：无存活敌人"
    lines.append("敌人状态：")
    for index, enemy in enumerate(enemies):
        lines.append("[{}] {}".format(
            index,
            enemy.status_text(game_state)
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
    clear_pending_discard_to_draw_top(game_state)
    clear_pending_exhaust_hand_selection(game_state)
    clear_pending_hand_to_draw_top_selection(game_state)
    clear_pending_upgrade_hand_selection(game_state)
    logs.extend(end_player_turn_hand_cleanup(game_state))
    result = check_battle_result(game_state)
    if result:
        logs.append(result)
        return "\n".join(logs)
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

    turn_end_context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        extra={
            "timing": EVENT_TURN_END
        }
    )

    turn_end_logs = dispatch_event(game_state, EVENT_TURN_END, turn_end_context)
    if turn_end_logs:
        logs.append("")
        logs.append("回合结束状态结算：")
        logs.extend(turn_end_logs)

    zone_tick_logs = tick_zone_turn_end(game_state)
    field_tick_logs = tick_fields_turn_end(game_state)
    if zone_tick_logs or field_tick_logs:
        logs.append("")
        logs.append("场地结算：")
        logs.extend(zone_tick_logs)
        logs.extend(field_tick_logs)
    result = check_battle_result(game_state)
    if result:
        logs.append(result)
        return "\n".join(logs)
    from game.target_lock import tick_attack_target_lock_turn_end
    target_lock_logs = tick_attack_target_lock_turn_end(game_state)
    if target_lock_logs:
        logs.append("")
        logs.append("锁定目标结算：")
        logs.extend(target_lock_logs)
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
    turn_start_logs = dispatch_event(game_state, EVENT_TURN_START, context)
    logs.extend(turn_start_logs)
    result = check_battle_result(game_state)
    if result:
        logs.append(result)
        return "\n".join(logs)
    logs.append(player.status_text())
    logs.append(format_enemy_current_status(game_state))
    logs.extend(player.draw_cards(5))

    return "\n".join(logs)


def validate_card_target(game_state, card, target_index):
    """
    校验卡牌目标。
    enemy：需要玩家选择一个存活敌人。
    all_enemies / random_enemy：不需要玩家选择具体敌人，但场上必须有存活敌人。
    self / none：不需要敌方目标。
    """
    if card.target == "enemy":
        if target_index < 0 or target_index >= len(game_state.enemies):
            return "目标敌人编号无效。"
        if not game_state.enemies[target_index].is_alive():
            return "目标敌人已经死亡。"
        if getattr(card, "card_type", "") == "attack":
            from game.target_lock import (
                get_locked_attack_target_index,
                get_locked_attack_target_text
            )
            locked_index = get_locked_attack_target_index(game_state)
            if locked_index is not None and target_index != locked_index:
                return "当前已锁定攻击目标 {}，不能切换到 [{}]。".format(
                    get_locked_attack_target_text(game_state),
                    target_index
                )
        return ""
    if card.target in ("all_enemies", "random_enemy"):
        if game_state.is_all_enemies_dead():
            return "没有可攻击的敌人。"
        return ""
    if card.target in ("self", "none"):
        return ""
    return "未知的卡牌目标类型：{}。".format(card.target)


def get_status(game_state):
    return game_state.status_text()

def format_entity_status_detail(entity):
    from game.status.status_defs import get_status_def, iter_status_defs
    from game.status.status_display import format_status
    statuses = getattr(entity, "statuses", None)
    if statuses is None:
        return ["无状态。"]
    active = statuses.all_active()
    if not active:
        return ["无状态。"]
    lines = []
    handled = set()
    for status_def in iter_status_defs():
        key = status_def.key
        if key not in active:
            continue
        value = active.get(key, 0)
        category = getattr(status_def, "category", "neutral")
        description = getattr(status_def, "description", "") or "暂无说明。"
        lines.append("- {} [{}]：{}".format(
            format_status(key, value),
            category,
            description
        ))
        handled.add(key)
    for key, value in active.items():
        if key in handled:
            continue
        status_def = get_status_def(key)
        if status_def is None:
            lines.append("- {}：未注册状态，暂无说明。".format(format_status(key, value)))
        else:
            category = getattr(status_def, "category", "neutral")
            description = getattr(status_def, "description", "") or "暂无说明。"
            lines.append("- {} [{}]：{}".format(
                format_status(key, value),
                category,
                description
            ))
    return lines


def get_status_detail(game_state):
    lines = []
    lines.append("=== 全场状态说明 ===")
    lines.append("玩家：{} HP：{}/{}，格挡：{}".format(
        game_state.player.name,
        game_state.player.hp,
        game_state.player.max_hp,
        game_state.player.block
    ))
    lines.extend(format_entity_status_detail(game_state.player))
    lines.append("")
    lines.append("敌人：")
    for index, enemy in enumerate(game_state.enemies):
        alive_text = "存活" if enemy.is_alive() else "已死亡"
        lines.append("[{}] {} HP：{}/{}，格挡：{}，{}".format(
            index,
            enemy.name,
            enemy.hp,
            enemy.max_hp,
            enemy.block,
            alive_text
        ))
        lines.extend(format_entity_status_detail(enemy))
    return "\n".join(lines)


def get_zone_field_view(game_state):
    return format_zone_field_detail(game_state)

def get_hand(game_state):
    return game_state.player.hand_text(game_state)

def get_combat_view(game_state):
    return "\n\n".join([
        game_state.status_text(),
        game_state.player.hand_text(game_state)
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