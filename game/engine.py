# -*- coding: utf-8 -*-

import random
import copy
from data.character.AAAregistry import create_character
from data.card.AAAregistry import create_deck
from data.relic.AAAregistry import create_relics
from data.enemy.AAAregistry import create_enemy
from data.potion.AAAregistry import create_potions
from data.zones.element_zones import ElementZone

from game.block import gain_block_without_modifiers
from game.status.status_defs import get_status_def, get_status_name
from game.card_cost import get_card_current_cost
from game.constants import (DEBUG_SEED, EVENT_POTION_USE_AFTER,
                            EVENT_BATTLE_START,
                            EVENT_TURN_START, EVENT_TURN_END, EVENT_PLAYER_TURN_END,
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
    record_player_card_played_this_turn,
    make_empty_player_card_type_played_counts
)
from game.pending_choice import (
    clear_pending_choice,
    format_pending_choice_hint,
    get_pending_choice,
    has_pending_choice,
    pending_choice_is,
)


def move_bottled_cards_to_opening_hand(player):
    """
    瓶装遗物：被瓶装的牌在战斗开始时进入起始手牌。
    该标记存放在长期牌组卡牌对象上，并随 deepcopy 进入战斗牌堆。
    """
    logs = []

    if not player.draw_pile:
        return logs

    new_draw_pile = []
    bottled_cards = []

    for card in player.draw_pile:
        if getattr(card, "bottled_by", "") or getattr(card, "bottled_relic_id", ""):
            bottled_cards.append(card)
        else:
            new_draw_pile.append(card)

    player.draw_pile = new_draw_pile
    max_hand_size = getattr(player, "max_hand_size", 10)

    for card in bottled_cards:
        if len(player.hand) >= max_hand_size:
            player.draw_pile.append(card)
            logs.append("【{}】因手牌已满，瓶装没有生效，留在抽牌堆。".format(card.name))
            continue
        player.hand.append(card)
        logs.append("【{}】因瓶装进入起始手牌。".format(card.name))

    return logs


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

def get_opening_draw_bonus(game_state):
    player = game_state.player
    bonus = 0
    for relic in getattr(player, "relics", []) or []:
        getter = getattr(relic, "get_opening_draw_bonus", None)
        if getter is None:
            continue
        try:
            bonus += int(getter(game_state=game_state, player=player))
        except TypeError:
            bonus += int(getter(game_state, player))
    if bonus < 0:
        bonus = 0
    return bonus


def get_turn_draw_bonus(game_state):
    player = game_state.player
    bonus = 0
    for relic in getattr(player, "relics", []) or []:
        getter = getattr(relic, "get_turn_draw_bonus", None)
        if getter is None:
            continue
        try:
            bonus += int(getter(game_state=game_state, player=player))
        except TypeError:
            bonus += int(getter(game_state, player))
    if bonus < 0:
        bonus = 0
    return bonus

def get_turn_draw_reduction(game_state):
    player = game_state.player
    amount = int(player.get_status_value("draw_reduction"))

    if amount <= 0:
        return 0

    player.gain_status("draw_reduction", -1)
    return 1

def apply_card_play_start_relics(game_state, card):
    """打出卡牌、正式结算效果前触发的遗物。当前用于钢笔尖。"""
    logs = []
    player = game_state.player
    for relic in getattr(player, "relics", []) or []:
        handler = getattr(relic, "on_card_play_start", None)
        if handler is None:
            continue
        result = handler(game_state=game_state, player=player, card=card)
        if result:
            logs.extend(result)
    return logs


def apply_turn_start_hand_ready_effects(game_state):
    """
    抽完起始手牌/回合开始手牌后触发的遗物效果。
    当前用于弯曲铁钳：随机临时升级一张手牌。
    """
    logs = []
    player = game_state.player
    for relic in getattr(player, "relics", []) or []:
        handler = getattr(relic, "on_turn_start_hand_ready", None)
        if handler is None:
            continue
        result = handler(game_state=game_state, player=player)
        if result:
            logs.extend(result)
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

def apply_initial_enemy_flags(enemies):
    """
    处理遭遇生成后需要根据阵容补充的敌人标记。

    地精首领精英战中，开局自带的小地精全部是爪牙；
    后续由地精首领召唤的小地精已在 enemy_summon_gremlins 中标记。
    """
    enemy_list = list(enemies or [])

    has_gremlin_leader = any(
        getattr(enemy, "enemy_id", "") == "enemy.gremlin_leader"
        for enemy in enemy_list
    )

    if not has_gremlin_leader:
        return

    gremlin_minion_ids = {
        "enemy.mad_gremlin",
        "enemy.sneaky_gremlin",
        "enemy.fat_gremlin",
        "enemy.gremlin_wizard",
        "enemy.shield_gremlin",
    }

    for enemy in enemy_list:
        if getattr(enemy, "enemy_id", "") in gremlin_minion_ids:
            enemy.is_minion = True

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
    apply_initial_enemy_flags(enemies)

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
    logs.extend(move_bottled_cards_to_opening_hand(player))
    logs.extend(move_innate_cards_to_opening_hand(player))
    logs.append(player.status_text())
    opening_draw_count = 5 + get_opening_draw_bonus(game_state) - len(player.hand)
    if opening_draw_count < 0:
        opening_draw_count = 0
    logs.extend(player.draw_cards(
        opening_draw_count,
        game_state=game_state,
        draw_source="opening_hand"
    ))
    logs.extend(apply_turn_start_hand_ready_effects(game_state))
    logs.append("")
    logs.append(player.hand_text(game_state))
    return game_state, "\n".join(logs)

def start_battle_with_player(session_id, character_id, player, enemy_ids=None, seed=DEBUG_SEED, run_state=None):
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
    apply_initial_enemy_flags(enemies)
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
    if run_state is not None:
        game_state.run_state = run_state
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
    logs.extend(move_bottled_cards_to_opening_hand(player))
    logs.extend(move_innate_cards_to_opening_hand(player))
    logs.append(player.status_text())
    opening_draw_count = 5 + get_opening_draw_bonus(game_state) - len(player.hand)
    if opening_draw_count < 0:
        opening_draw_count = 0
    logs.extend(player.draw_cards(
        opening_draw_count,
        game_state=game_state,
        draw_source="opening_hand"
    ))
    logs.extend(apply_turn_start_hand_ready_effects(game_state))
    logs.append("")
    logs.append(player.hand_text(game_state))
    return game_state, "\n".join(logs)

def get_default_target_index(game_state):
    for index, enemy in enumerate(game_state.enemies):
        if enemy.is_alive():
            return index
    return 0


def resolve_auto_target_index(game_state, card_or_item, target_index):
    """
    target=enemy 的牌 / 药水在未指定目标时，自动选最前的存活敌人。
    target_index=None 表示命令层没有指定目标。
    """
    target = getattr(card_or_item, "target", None)
    if target == "enemy" and target_index is None:
        return get_default_target_index(game_state)
    if target_index is None:
        return 0
    return target_index


def has_pending_player_choice(game_state):
    return any([
        has_pending_choice(game_state),
        getattr(game_state, "pending_discard_selection", False),
        getattr(game_state, "pending_discard_to_draw_selection", False),
        getattr(game_state, "pending_exhaust_hand_selection", False),
        getattr(game_state, "pending_hand_to_draw_top_selection", False),
        getattr(game_state, "pending_upgrade_hand_selection", False),
        getattr(game_state, "pending_duplicate_hand_selection", False),
        getattr(game_state, "pending_exhume_selection", False),
        getattr(game_state, "pending_potion_card_selection", False),
        getattr(game_state, "pending_elixir_selection", False),
        getattr(game_state, "pending_nilrys_selection", False),
        getattr(game_state, "pending_toolbox_selection", False),
    ])


def get_pending_player_choice_hint(game_state):
    pending_choice_hint = format_pending_choice_hint(game_state)
    if pending_choice_hint:
        return pending_choice_hint
    if getattr(game_state, "pending_discard_selection", False):
        return "当前需要先处理丢弃选择。用法：/card drop 0 2 3。若不丢弃，使用 /card drop none。\ndrop 等效 drop_hand，丢弃手牌，选择丢弃。"
    if getattr(game_state, "pending_discard_to_draw_selection", False):
        return "当前需要先处理弃牌堆置顶选择。用法：/card top 0。\ntop 等效 headbutt，置顶，选择弃牌置顶。"
    if getattr(game_state, "pending_exhaust_hand_selection", False):
        return "当前需要先处理手牌消耗选择。用法：/card exhaust_hand 0。\nexhaust_hand 等效 burn，consume，选择消耗，消耗手牌。"
    if getattr(game_state, "pending_hand_to_draw_top_selection", False):
        return "当前需要先处理手牌置顶选择。用法：/card handtop 0。\nhandtop 等效 hand_top，warcry，置顶手牌，手牌置顶。"
    if getattr(game_state, "pending_upgrade_hand_selection", False):
        return "当前需要先处理手牌升级选择。用法：/card upgrade_hand 0。\nupgrade_hand 等效 upgradehand，armaments，选择升级，升级手牌。"
    if getattr(game_state, "pending_duplicate_hand_selection", False):
        return "当前需要先处理复制手牌选择。用法：/card duplicate_hand 0。\nduplicate_hand 等效 dual_wield，复制手牌，双持。"
    if getattr(game_state, "pending_exhume_selection", False):
        return "当前需要先处理发掘选择。用法：/card exhume 0。\nexhume 等效 发掘，选择发掘。"
    if getattr(game_state, "pending_potion_card_selection", False):
        return "当前需要先处理药水选牌。用法：/card potion_pick 0。\npotion_pick 等效 potion_card，药水选牌。"
    if getattr(game_state, "pending_elixir_selection", False):
        return "当前需要先处理万灵药水选择。用法：/card elixir 0,1,2；不消耗则 /card elixir none。"
    if getattr(game_state, "pending_nilrys_selection", False):
        return "当前需要先处理尼利的宝典选择。用法：/card codex 0；跳过则 /card codex skip。"
    if getattr(game_state, "pending_toolbox_selection", False):
        return "当前需要先处理工具箱选择。用法：/card toolbox 0。"
    return ""

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
        "relic_play": "因遗物允许打出后",
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
    if getattr(card, "card_id", "") == "card.curse.necronomicurse":
        try:
            player.exhaust_pile.remove(card)
        except ValueError:
            pass
        if player.is_hand_full():
            player.discard_pile.append(card)
            logs.append("【死灵诅咒】无法逃脱，但手牌已满，回到弃牌堆。")
        else:
            player.hand.append(card)
            logs.append("【死灵诅咒】无法逃脱，立刻回到你的手牌。")
    return logs


def move_played_card_to_destination(game_state, card):
    logs = []
    player = game_state.player

    if getattr(card, "force_exhaust_after_play", False):
        logs.extend(move_card_to_exhaust_pile(
            game_state=game_state,
            card=card,
            reason="relic_play"
        ))
        return logs

    if getattr(card, "card_type", "") == "power":
        logs.append("【{}】作为能力牌生效，本场战斗中消失。".format(card.name))
        return logs

    from game.modifiers import get_status_value

    if (
        getattr(card, "card_type", "") == "skill"
        and get_status_value(player, "corruption") > 0
    ):
        logs.extend(move_card_to_exhaust_pile(
            game_state=game_state,
            card=card,
            reason="corruption"
        ))
        return logs

    if should_exhaust_after_play(card):
        has_spoon = any(getattr(relic, "relic_id", "") == "relic.strange_spoon" for relic in getattr(player, "relics", []) or [])
        if has_spoon:
            if random.random() < 0.5:
                player.discard_pile.append(card)
                logs.append("【奇怪的勺子】触发：【{}】没有被消耗，改为进入弃牌堆。".format(card.name))
                return logs
        logs.extend(move_card_to_exhaust_pile(
            game_state=game_state,
            card=card,
            reason="after_play"
        ))
    else:
        player.discard_pile.append(card)
        logs.append("【{}】进入弃牌堆。".format(card.name))

    return logs


def apply_card_discard_relics(game_state, card, reason="丢弃"):
    logs = []
    if reason == "回合结束丢弃":
        return logs
    player = game_state.player
    for relic in getattr(player, "relics", []) or []:
        handler = getattr(relic, "on_card_discard", None)
        if handler is None:
            continue
        result = handler(game_state=game_state, player=player, card=card, reason=reason)
        if result:
            logs.extend(result)
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
            logs.extend(apply_card_discard_relics(game_state, card, reason=reason))
            return logs

        logs.append("【{}】因奇巧被{}，免费打出。".format(card.name, reason))

        target_index = get_default_target_index(game_state)
        effect_context = {
            "card_first_play_this_battle": is_card_first_play_this_battle(game_state, card)
        }
        apply_next_card_replay_statuses(
            game_state=game_state,
            card=card,
            effect_context=effect_context,
            logs=logs
        )
        logs.extend(apply_card_play_start_relics(game_state, card))
        logs.extend(apply_card_effects(
            game_state,
            card,
            target_index,
            effect_context=effect_context
        ))
        mark_card_played_this_battle(game_state, card)
        record_player_card_played_this_turn(game_state, card, player)

        context = BattleContext(
            game_state=game_state,
            player=player,
            source=player,
            card=card
        )
        logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))
        logs.extend(resolve_pain_cards_after_card_play(game_state, card))

        logs.extend(move_played_card_to_destination(game_state, card))
        return logs

    player.discard_pile.append(card)
    logs.append("【{}】被{}，进入弃牌堆。".format(card.name, reason))
    logs.extend(apply_card_discard_relics(game_state, card, reason=reason))
    return logs

def resolve_pain_cards_after_card_play(game_state, played_card):
    """
    疼痛：当这张牌在手牌中时，每打出一张其他牌，失去 1 生命。
    """
    logs = []
    player = game_state.player
    if player is None or not player.is_alive():
        return logs

    for curse in list(getattr(player, "hand", []) or []):
        if getattr(curse, "card_id", "") != "card.curse.pain":
            continue
        logs.append("【{}】在手牌中刺痛你，失去 1 点生命。".format(curse.name))
        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=player,
            amount=1,
            damage_kind="curse",
            card=curse,
            is_reaction_damage=False,
            ignore_block=True
        ))
        if game_state.battle_over:
            break
    return logs


def resolve_status_card_turn_end(game_state, card, hand_count=None):
    """
    处理回合结束时仍在手牌中的状态牌 / 诅咒牌效果。
    当前用于灼伤 I / II、悔恨。
    """
    logs = []
    card_id = getattr(card, "card_id", "")
    player = game_state.player

    if player is None or not player.is_alive():
        return logs

    if card_id == "card.curse.regret":
        if hand_count is None:
            hand_count = len(getattr(player, "hand", []))

        damage = int(hand_count)
        if damage <= 0:
            return logs

        logs.append("【{}】在回合结束时令你充满悔意，失去 {} 点生命。".format(
            card.name,
            damage
        ))
        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=player,
            amount=damage,
            damage_kind="curse",
            card=card,
            is_reaction_damage=False,
            ignore_block=True
        ))
        return logs

    if card_id == "card.curse.doubt":
        current = player.gain_status("weak", 1)
        logs.append("【{}】在回合结束时加深疑虑，获得 1 层虚弱。当前虚弱：{}。".format(
            card.name,
            current
        ))
        return logs
    if card_id == "card.curse.shame":
        current = player.gain_status("frail", 1)
        logs.append("【{}】在回合结束时刺痛你的自尊，获得 1 层脆弱。当前脆弱：{}。".format(
            card.name,
            current
        ))
        return logs
    
    burn_damage_map = {
        "card.status.burn_i": 2,
        "card.status.burn_ii": 4,
        "card.curse.decay": 2,
    }
    damage = burn_damage_map.get(card_id, 0)
    if damage <= 0:
        return logs

    if card_id == "card.curse.decay":
        logs.append("【{}】在回合结束时腐朽发作，造成 {} 点伤害。".format(
            card.name,
            damage
        ))
    else:
        logs.append("【{}】在回合结束时灼伤你，造成 {} 点伤害。".format(
            card.name,
            damage
        ))
    logs.extend(deal_damage(
        game_state=game_state,
        source=player,
        target=player,
        amount=damage,
        damage_kind="status_card",
        card=card,
        is_reaction_damage=False,
        ignore_block=False
    ))
    return logs

def end_player_turn_hand_cleanup(game_state):
    player = game_state.player
    old_hand = player.hand
    player.hand = []

    logs = []
    retained_cards = []

    hand_count_at_turn_end = len(old_hand)

    for card in old_hand:
        logs.extend(resolve_status_card_turn_end(
            game_state,
            card,
            hand_count=hand_count_at_turn_end
        ))
        if game_state.battle_over:
            break
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

        if any(getattr(relic, "relic_id", "") == "relic.runic_pyramid" for relic in getattr(player, "relics", []) or []):
            retained_cards.append(card)
            logs.append("【符文金字塔】保留【{}】。".format(card.name))
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
    clear_pending_choice(game_state, "discard_to_draw_top")
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
    use_pending_choice = pending_choice_is(game_state, "discard_to_draw_top")

    if not use_pending_choice and not game_state.pending_discard_to_draw_selection:
        return "当前没有需要处理的弃牌堆置顶选择。"

    if use_pending_choice:
        pending_choice = get_pending_choice(game_state)
        options = list(getattr(pending_choice, "options", []) or [])
        source = getattr(pending_choice, "source", "")
    else:
        options = getattr(game_state, "pending_discard_to_draw_options", [])
        source = game_state.pending_discard_to_draw_source

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
    clear_pending_choice(game_state, "hand_to_draw_top")
    game_state.pending_hand_to_draw_top_selection = False
    game_state.pending_hand_to_draw_top_source = ""
    game_state.pending_hand_to_draw_top_options = []

def choose_pending_hand_to_draw_top(game_state, choice_index):
    """
    处理战吼：
    选择 1 张手牌放到抽牌堆顶。
    """
    use_pending_choice = pending_choice_is(game_state, "hand_to_draw_top")

    if not use_pending_choice and not game_state.pending_hand_to_draw_top_selection:
        return "当前没有需要处理的手牌置顶选择。"

    if use_pending_choice:
        pending_choice = get_pending_choice(game_state)
        options = list(getattr(pending_choice, "options", []) or [])
        source = getattr(pending_choice, "source", "")
        payload = getattr(pending_choice, "payload", {}) or {}
    else:
        options = getattr(game_state, "pending_hand_to_draw_top_options", [])
        source = game_state.pending_hand_to_draw_top_source
        payload = {}

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
    if payload.get("set_cost_zero", False):
        try:
            chosen_card.cost = 0
        except Exception:
            setattr(chosen_card, "temporary_cost_override", 0)

    destination = payload.get("destination", "top")
    if destination == "bottom":
        player.draw_pile.insert(0, chosen_card)
    else:
        player.draw_pile.append(chosen_card)

    clear_pending_hand_to_draw_top_selection(game_state)

    if destination == "bottom":
        return "【{}】选择了【{}】，将其放到抽牌堆底，并使其耗能变为 0。".format(
            source,
            chosen_card.name
        )

    return "【{}】选择了【{}】，将其放到抽牌堆顶。它会成为下一张抽到的牌。".format(
        source,
        chosen_card.name
    )

def clear_pending_upgrade_hand_selection(game_state):
    clear_pending_choice(game_state, "upgrade_hand")
    game_state.pending_upgrade_hand_selection = False
    game_state.pending_upgrade_hand_source = ""
    game_state.pending_upgrade_hand_options = []

def choose_pending_upgrade_hand_card(game_state, choice_index):
    """
    处理武装：
    选择 1 张手牌在本场战斗中临时升级。
    """
    use_pending_choice = pending_choice_is(game_state, "upgrade_hand")

    if not use_pending_choice and not game_state.pending_upgrade_hand_selection:
        return "当前没有需要处理的手牌升级选择。"

    if use_pending_choice:
        pending_choice = get_pending_choice(game_state)
        options = list(getattr(pending_choice, "options", []) or [])
        source = getattr(pending_choice, "source", "")
    else:
        options = getattr(game_state, "pending_upgrade_hand_options", [])
        source = game_state.pending_upgrade_hand_source

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

    clear_pending_upgrade_hand_selection(game_state)

    if not replaced:
        return "所选牌已经不在手牌中，选择已取消。"

    return "【{}】将【{}】临时升级为【{}】。".format(
        source,
        chosen_card.name,
        upgraded_card.name
    )

def clear_pending_element_plating_selection(game_state):
    clear_pending_choice(game_state, "element_plating")

def card_has_gain_block_effect(card):
    def walk(value):
        if isinstance(value, dict):
            if value.get("op") == "gain_block":
                return True
            for sub_value in value.values():
                if walk(sub_value):
                    return True
            return False

        if isinstance(value, list):
            for item in value:
                if walk(item):
                    return True
            return False

        return False

    return walk(getattr(card, "effects", []) or [])

def choose_pending_element_plating(game_state, choice_index):
    """
    处理【深渊镀层】/【结晶镀层】：
    选择一张当前手牌中的无属性攻击牌，临时添加属性标签。
    """
    if not pending_choice_is(game_state, "element_plating"):
        return "当前没有需要处理的镀层选择。"

    pending_choice = get_pending_choice(game_state)
    options = list(getattr(pending_choice, "options", []) or [])
    source = getattr(pending_choice, "source", "镀层")
    payload = getattr(pending_choice, "payload", {}) or {}

    if not options:
        clear_pending_element_plating_selection(game_state)
        return "没有可选择的无属性攻击牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.hand:
        clear_pending_element_plating_selection(game_state)
        return "所选牌已经不在手牌中，选择已取消。"

    allowed_card_types = list(payload.get("allowed_card_types", ["attack"]) or ["attack"])
    type_text = str(payload.get("type_text", "攻击牌") or "攻击牌")
    require_gain_block = bool(payload.get("require_gain_block", False))

    if getattr(chosen_card, "card_type", "") not in allowed_card_types:
        clear_pending_element_plating_selection(game_state)
        return "【{}】不是{}，无法添加镀层。".format(chosen_card.name, type_text)

    if str(getattr(chosen_card, "attack_element", "") or "").strip():
        clear_pending_element_plating_selection(game_state)
        return "【{}】已经有属性，无法添加镀层。".format(chosen_card.name)
    
    if require_gain_block and not card_has_gain_block_effect(chosen_card):
        clear_pending_element_plating_selection(game_state)
        return "【{}】不能产生格挡，无法添加地词条。".format(chosen_card.name)
    
    element = str(payload.get("element", "") or "").strip().lower()
    suffix = str(payload.get("suffix", "") or "")

    if not element:
        clear_pending_element_plating_selection(game_state)
        return "镀层缺少属性，选择已取消。"

    if not suffix:
        suffix = {
            "shade": "·阴",
            "crystal": "·晶",
            "earth": "·地",
        }.get(element, "·{}".format(element))

    old_name = chosen_card.name
    base_name = getattr(chosen_card, "_element_plating_original_name", old_name)

    setattr(chosen_card, "_element_plating_original_name", base_name)
    setattr(chosen_card, "attack_element", element)
    setattr(chosen_card, "temporary_combat_attack_element", element)
    setattr(chosen_card, "temporary_element_plating_suffix", suffix)
    setattr(chosen_card, "name", "{}{}".format(base_name, suffix))

    clear_pending_element_plating_selection(game_state)

    element_name = {
        "shade": "阴",
        "crystal": "晶",
        "earth": "地",
    }.get(element, element)

    return "【{}】为【{}】添加{}属性镀层，本场战斗中临时显示为【{}】。".format(
        source,
        old_name,
        element_name,
        chosen_card.name
    )

def clear_pending_retain_hand_selection(game_state):
    clear_pending_choice(game_state, "retain_hand")


def choose_pending_retain_hand_cards(game_state, choice_indices=None, skip=False):
    if not pending_choice_is(game_state, "retain_hand"):
        return "当前没有需要处理的保留选择。"

    pending_choice = get_pending_choice(game_state)
    options = list(getattr(pending_choice, "options", []) or [])
    source = getattr(pending_choice, "source", "保留")
    payload = getattr(pending_choice, "payload", {}) or {}
    max_count = int(payload.get("max_count", 1) or 1)

    if skip:
        clear_pending_retain_hand_selection(game_state)
        return "【{}】未选择添加保留的手牌。".format(source)

    if choice_indices is None:
        choice_indices = []

    unique_indices = []
    seen = set()

    for index in choice_indices:
        if index in seen:
            continue
        seen.add(index)
        unique_indices.append(index)

    if not unique_indices:
        clear_pending_retain_hand_selection(game_state)
        return "【{}】未选择添加保留的手牌。".format(source)

    if len(unique_indices) > max_count:
        return "最多只能选择 {} 张手牌。".format(max_count)

    for index in unique_indices:
        if index < 0 or index >= len(options):
            return "选择编号无效：{}。".format(index)

    from game.constants import KEYWORD_RETAIN

    player = game_state.player
    chosen_cards = []

    for index in unique_indices:
        chosen_card = options[index]

        if chosen_card not in player.hand:
            clear_pending_retain_hand_selection(game_state)
            return "所选牌已经不在手牌中，选择已取消。"

        if KEYWORD_RETAIN not in getattr(chosen_card, "keywords", []):
            chosen_card.keywords.append(KEYWORD_RETAIN)

        chosen_cards.append(chosen_card)

    clear_pending_retain_hand_selection(game_state)

    return "【{}】为 {} 添加保留。".format(
        source,
        "、".join(["【{}】".format(card.name) for card in chosen_cards])
    )

def clear_pending_radiant_reflection_selection(game_state):
    clear_pending_choice(game_state, "radiant_reflection")


def choose_pending_radiant_reflection_cards(game_state, choice_indices):
    if not pending_choice_is(game_state, "radiant_reflection"):
        return "当前没有需要处理的辉晶映照选择。"

    pending_choice = get_pending_choice(game_state)
    options = list(getattr(pending_choice, "options", []) or [])
    source = getattr(pending_choice, "source", "辉晶映照")
    payload = getattr(pending_choice, "payload", {}) or {}
    max_count = int(payload.get("max_count", 1) or 1)

    if not options:
        clear_pending_radiant_reflection_selection(game_state)
        return "没有可选择的非消耗堆卡牌。"

    if choice_indices is None:
        choice_indices = []

    unique_indices = []
    seen = set()

    for index in choice_indices:
        if index in seen:
            continue
        seen.add(index)
        unique_indices.append(index)

    if not unique_indices:
        return "至少选择 1 张牌。"

    if len(unique_indices) > max_count:
        return "最多只能选择 {} 张牌。".format(max_count)

    for index in unique_indices:
        if index < 0 or index >= len(options):
            return "选择编号无效：{}。".format(index)

    player = game_state.player
    logs = []

    for index in unique_indices:
        item = options[index]
        pile_name = item.get("pile_name", "")
        pile_label = item.get("pile_label", pile_name)
        chosen_card = item.get("card")

        if chosen_card is None:
            clear_pending_radiant_reflection_selection(game_state)
            return "选择项异常，选择已取消。"

        pile = getattr(player, pile_name, None)
        if pile is None or chosen_card not in pile:
            clear_pending_radiant_reflection_selection(game_state)
            return "所选牌已经不在{}中，选择已取消。".format(pile_label)

        old_replay = int(getattr(chosen_card, "replay_extra", 0) or 0)
        setattr(chosen_card, "replay_extra", old_replay + 1)

        logs.append("【{}】为{}中的【{}】添加重放 1。当前额外重放：{}。".format(
            source,
            pile_label,
            chosen_card.name,
            old_replay + 1
        ))

    clear_pending_radiant_reflection_selection(game_state)

    return "\n".join(logs)

def clear_pending_exhume_selection(game_state):
    game_state.pending_exhume_selection = False
    game_state.pending_exhume_source = ""
    game_state.pending_exhume_options = []


def choose_pending_exhume_card(game_state, choice_index):
    """
    处理发掘：
    选择一张消耗堆中的牌。
    - 手牌未满：加入手牌
    - 手牌已满：加入弃牌堆
    """
    if not game_state.pending_exhume_selection:
        return "当前没有需要处理的发掘选择。"

    options = getattr(game_state, "pending_exhume_options", [])

    if not options:
        clear_pending_exhume_selection(game_state)
        return "没有可选择的消耗堆卡牌。"

    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效：{}。".format(choice_index)

    player = game_state.player
    chosen_card = options[choice_index]

    if chosen_card not in player.exhaust_pile:
        clear_pending_exhume_selection(game_state)
        return "所选牌已经不在消耗堆中，选择已取消。"

    player.exhaust_pile.remove(chosen_card)

    source = game_state.pending_exhume_source

    if player.is_hand_full():
        player.discard_pile.append(chosen_card)
        clear_pending_exhume_selection(game_state)

        return "手牌已满，【{}】将【{}】从消耗堆移入弃牌堆。".format(
            source,
            chosen_card.name
        )

    player.hand.append(chosen_card)
    clear_pending_exhume_selection(game_state)

    return "【{}】将【{}】从消耗堆加入手牌。".format(
        source,
        chosen_card.name
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
            source = getattr(game_state, "pending_discard_source", "")
            game_state.pending_discard_selection = False
            game_state.pending_discard_source = ""
            if source == "gambling_chip":
                return "【赌博筹码】未选择丢弃手牌。"
            if source == "gamblers_brew":
                return "【赌徒特酿】未选择丢弃手牌。"
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

    pending_source = getattr(game_state, "pending_discard_source", "")
    for index, card in indexed_cards:
        logs.append("选择丢弃手牌 [{}] 【{}】。".format(index, card.name))
        logs.extend(resolve_discarded_card(
            game_state,
            card,
            reason="主动丢弃",
            trigger_clever=True
        ))

    if pending_source in ("gambling_chip", "gamblers_brew") and indexed_cards:
        source_name = "赌博筹码" if pending_source == "gambling_chip" else "赌徒特酿"
        logs.append("【{}】抽取与丢弃数量相同的牌：{} 张。".format(
            source_name,
            len(indexed_cards)
        ))
        logs.extend(player.draw_cards(
            len(indexed_cards),
            game_state=game_state,
            draw_source=pending_source
        ))

    if game_state.pending_discard_selection:
        game_state.pending_discard_selection = False
        game_state.pending_discard_source = ""

    result = check_battle_result(game_state)
    if result:
        logs.append(result)

    return "\n".join(logs)


def try_prevent_player_death(game_state):
    player = game_state.player
    if player is None or player.is_alive():
        return []
    if any(getattr(relic, "relic_id", "") == "relic.mark_of_the_bloom" for relic in getattr(player, "relics", []) or []):
        return ["【绽放印记】阻止了濒死回复，无法免于死亡。"]
    # 瓶中精灵优先于蜥蜴尾巴。
    for index, potion in enumerate(list(getattr(player, "potions", []) or [])):
        if getattr(potion, "potion_id", "") == "potion.fairy_in_a_bottle":
            try:
                player.potions.pop(index)
            except Exception:
                pass
            heal_to = max(1, int(player.max_hp * 0.30))
            old_hp = player.hp
            player.hp = heal_to
            return ["【瓶中精灵】触发：免于死亡，丢弃该药水，HP：{} -> {}。".format(old_hp, player.hp)]
    for relic in getattr(player, "relics", []) or []:
        if getattr(relic, "relic_id", "") == "relic.lizard_tail" and not getattr(relic, "used", False):
            relic.used = True
            heal_to = max(1, int(player.max_hp * 0.50))
            old_hp = player.hp
            player.hp = heal_to
            return ["【{}】触发：免于死亡，HP：{} -> {}。".format(relic.name, old_hp, player.hp)]
    return []

def resolve_all_minions_escape(game_state):
    """
    如果场上剩余存活敌人全部都是爪牙，则这些爪牙立即逃跑，战斗胜利。
    """
    alive_enemies = [
        enemy for enemy in getattr(game_state, "enemies", []) or []
        if enemy.is_alive()
    ]

    if not alive_enemies:
        return None

    if not all(bool(getattr(enemy, "is_minion", False)) for enemy in alive_enemies):
        return None

    names = []

    for enemy in alive_enemies:
        names.append(enemy.name)
        setattr(enemy, "_escaped", True)
        enemy.hp = 0
        enemy.block = 0

    game_state.battle_over = True
    game_state.victory = True

    return "场上只剩爪牙，{} 逃离了战斗。战斗胜利。".format(
        "、".join(names)
    )

def check_battle_result(game_state):
    """
    检查战斗是否结束。
    玩家优先：
    用于处理“攻击牌击杀敌人，但敌人的反应伤害同时击杀玩家”的情况。
    这种情况下按失败处理。
    """
    if not game_state.player.is_alive():
        prevent_logs = try_prevent_player_death(game_state)
        if prevent_logs:
            return "\n".join(prevent_logs)
        game_state.battle_over = True
        game_state.victory = False
        return "{} 已倒下，战斗失败。".format(game_state.player.name)
    minion_escape_result = resolve_all_minions_escape(game_state)
    if minion_escape_result:
        return minion_escape_result

    if game_state.is_all_enemies_dead():
        game_state.battle_over = True
        game_state.victory = True
        return "所有敌人已被击败，战斗胜利。"
    return None

def _safe_int_card_cost(value):
    """
    将卡牌当前费用安全转成 int。

    返回：
    - int：正常整数费用
    - None：X费、None、非法字符串等不能参与“>= 2”判断的费用
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int):
        return value

    text = str(value).strip()
    if not text:
        return None

    if text.upper() == "X":
        return None

    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def apply_next_card_replay_statuses(game_state, card, effect_context, logs):
    """
    处理本回合下一张牌额外结算一次的状态。

    - double_tap：攻击牌
    - burst：技能牌
    - amplify：能力牌
    - duplication_potion_next_card：任意牌
    - necronomicon：每回合第一张当前耗能 >=2 的攻击牌
    """
    player = game_state.player
    card_type = getattr(card, "card_type", "")

    replay_status_by_type = {
        "attack": ("double_tap", "双发"),
        "skill": ("burst", "爆发"),
        "power": ("amplify", "增幅"),
    }

    status_pair = replay_status_by_type.get(card_type)
    if status_pair is not None:
        status_key, status_name = status_pair
        if player.statuses.get(status_key) > 0:
            effect_context["replay_extra"] = int(effect_context.get("replay_extra", 0)) + 1
            remaining = player.statuses.add(status_key, -1)
            logs.append("{} 触发，【{}】将额外结算 1 次。剩余次数：{}。".format(
                status_name,
                card.name,
                remaining
            ))

    if player.statuses.get("duplication_potion_next_card") > 0:
        effect_context["replay_extra"] = int(effect_context.get("replay_extra", 0)) + 1
        remaining = player.statuses.add("duplication_potion_next_card", -1)
        logs.append("复制药水触发，【{}】将额外结算 1 次。剩余次数：{}。".format(
            card.name,
            remaining
        ))

    # 死灵之书：每回合第一张当前耗能 >=2 的攻击牌额外结算 1 次。
    if card_type == "attack":
        has_book = any(
            getattr(relic, "relic_id", "") == "relic.necronomicon"
            for relic in getattr(player, "relics", []) or []
        )

        if has_book:
            current_turn = int(getattr(game_state, "turn_count", 0))
            used_turn = int(getattr(game_state, "necronomicon_used_turn", 0) or 0)

            try:
                current_cost = get_card_current_cost(game_state, card)
            except Exception:
                current_cost = getattr(card, "cost", 0)

            current_cost_int = _safe_int_card_cost(current_cost)

            if (
                used_turn != current_turn
                and current_cost_int is not None
                and current_cost_int >= 2
            ):
                effect_context["replay_extra"] = int(effect_context.get("replay_extra", 0)) + 1
                game_state.necronomicon_used_turn = current_turn
                logs.append("【死灵之书】触发：【{}】将额外结算 1 次。".format(
                    getattr(card, "name", "攻击牌")
                ))

    return effect_context

def clear_current_virtual_mist_zone(game_state):
    if hasattr(game_state, "_current_virtual_mist_zone"):
        delattr(game_state, "_current_virtual_mist_zone")


def _real_active_zone_exists(game_state):
    zone = getattr(game_state, "active_zone", None)
    if zone is None:
        return False
    try:
        return not zone.is_expired()
    except Exception:
        return True

def _set_current_virtual_mist_zone(game_state, element, is_extreme=False):
    # 虚拟薄雾 Zone 只服务于当前打出的这一张牌，不参与回合倒计时。
    # 极 Zone 如果 duration=0，会被 ZoneTemplate.is_expired() 判定为已过期。
    virtual_zone = ElementZone(
        element=element,
        is_extreme=bool(is_extreme),
        duration=1 if is_extreme else 0
    )
    setattr(virtual_zone, "is_virtual_mist_zone", True)
    setattr(game_state, "_current_virtual_mist_zone", virtual_zone)
    return virtual_zone


def apply_next_card_virtual_zone_statuses(game_state, card, effect_context, logs):
    """
    处理【结晶薄雾】/【深渊薄雾】。

    规则：
    - 真实 active_zone 存在时，薄雾不触发、不消耗。
    - 深渊薄雾只等待攻击牌。
    - 结晶薄雾等待任意牌；无属性牌也会消耗层数。
    - 同时存在时，攻击牌优先触发深渊薄雾。
    """
    player = game_state.player

    clear_current_virtual_mist_zone(game_state)

    if _real_active_zone_exists(game_state):
        return effect_context

    card_type = getattr(card, "card_type", "")

    # 深渊薄雾：下一张攻击牌一定占用次数，但只有阴属性攻击牌实际吃效果。
    if card_type == "attack":
        if player.statuses.get("abyss_mist_extreme") > 0:
            remaining = player.statuses.add("abyss_mist_extreme", -1)
            _set_current_virtual_mist_zone(
                game_state=game_state,
                element="shade",
                is_extreme=True
            )
            effect_context["virtual_mist_zone_element"] = "shade"
            effect_context["virtual_mist_zone_is_extreme"] = True

            if str(getattr(card, "attack_element", "") or "").strip().lower() == "shade":
                logs.append("【极·深渊薄雾】触发：【{}】在极阴 Zone 下结算。剩余：{}。".format(
                    card.name,
                    remaining
                ))
            else:
                logs.append("【极·深渊薄雾】被【{}】占用，但该牌不是阴属性，未触发 Zone 效果。剩余：{}。".format(
                    card.name,
                    remaining
                ))
            return effect_context

        if player.statuses.get("abyss_mist") > 0:
            remaining = player.statuses.add("abyss_mist", -1)
            _set_current_virtual_mist_zone(
                game_state=game_state,
                element="shade",
                is_extreme=False
            )
            effect_context["virtual_mist_zone_element"] = "shade"
            effect_context["virtual_mist_zone_is_extreme"] = False

            if str(getattr(card, "attack_element", "") or "").strip().lower() == "shade":
                logs.append("【深渊薄雾】触发：【{}】在阴 Zone 下结算。剩余：{}。".format(
                    card.name,
                    remaining
                ))
            else:
                logs.append("【深渊薄雾】被【{}】占用，但该牌不是阴属性，未触发 Zone 效果。剩余：{}。".format(
                    card.name,
                    remaining
                ))
            return effect_context

    # 结晶薄雾：下一张任意牌一定占用次数，但只有晶属性牌实际吃效果。
    if player.statuses.get("crystal_mist") > 0:
        remaining = player.statuses.add("crystal_mist", -1)
        _set_current_virtual_mist_zone(
            game_state=game_state,
            element="crystal",
            is_extreme=False
        )
        effect_context["virtual_mist_zone_element"] = "crystal"
        effect_context["virtual_mist_zone_is_extreme"] = False

        if str(getattr(card, "attack_element", "") or "").strip().lower() == "crystal":
            logs.append("【结晶薄雾】触发：【{}】在晶 Zone 下结算。剩余：{}。".format(
                card.name,
                remaining
            ))
        else:
            logs.append("【结晶薄雾】被【{}】占用，但该牌不是晶属性，未触发 Zone 效果。剩余：{}。".format(
                card.name,
                remaining
            ))
        return effect_context

    return effect_context

def play_card(game_state, hand_index, target_index=None):
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

    target_index = resolve_auto_target_index(game_state, card, target_index)
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

    # 蓝蜡烛 / 医药箱允许打出的诅咒、状态牌：打出后强制消耗。
    if getattr(card, "card_type", "") == "curse" and any(getattr(relic, "relic_id", "") == "relic.blue_candle" for relic in getattr(player, "relics", []) or []):
        setattr(card, "force_exhaust_after_play", True)
        logs.append("【蓝蜡烛】触发：打出诅咒牌【{}】，失去 1 点生命。".format(card.name))
        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=player,
            amount=1,
            damage_kind="curse",
            card=card,
            is_reaction_damage=False,
            ignore_block=True
        ))
    elif getattr(card, "card_type", "") == "status" and any(getattr(relic, "relic_id", "") == "relic.medical_kit" for relic in getattr(player, "relics", []) or []):
        setattr(card, "force_exhaust_after_play", True)
        logs.append("【医药箱】触发：打出状态牌【{}】，该牌将被消耗。".format(card.name))

    # 执行效果
    effect_context = {}
    if is_x_cost:
        effect_context = {
            "raw_x": raw_x,
            "x": x_value,
            "spent_cost": spent_cost
        }
    effect_context["card_first_play_this_battle"] = is_card_first_play_this_battle(game_state, card)

    apply_next_card_virtual_zone_statuses(
        game_state=game_state,
        card=card,
        effect_context=effect_context,
        logs=logs
    )

    apply_next_card_replay_statuses(
        game_state=game_state,
        card=card,
        effect_context=effect_context,
        logs=logs
    )

    logs.extend(apply_card_play_start_relics(game_state, card))
    logs.extend(apply_card_effects(
        game_state,
        card,
        target_index,
        effect_context=effect_context
    ))

    clear_current_virtual_mist_zone(game_state)
    mark_card_played_this_battle(game_state, card)
    record_player_card_played_this_turn(game_state, card, player)

    # 出牌后事件：先用于测试遗物的“打出技能牌”触发
    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        card=card
    )
    logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))
    logs.extend(resolve_pain_cards_after_card_play(game_state, card))

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

def play_cards_by_original_indices(game_state, hand_indices, target_index=None):
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
        effective_target_index = resolve_auto_target_index(game_state, card, target_index)
        if card_target == "enemy":
            if effective_target_index < 0 or effective_target_index >= len(game_state.enemies):
                logs.append("目标敌人编号无效，批量出牌中止：{}。".format(effective_target_index))
                break
            if not game_state.enemies[effective_target_index].is_alive():
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

        if has_pending_player_choice(game_state):
            logs.append("")
            logs.append("出现待处理事务，连续出牌已中断。")
            hint = get_pending_player_choice_hint(game_state)
            if hint:
                logs.append(hint)
            break
    return "\n".join(logs)


def player_has_relic(player, relic_id):
    return any(getattr(relic, "relic_id", "") == relic_id for relic in getattr(player, "relics", []) or [])


def potion_has_sacred_bark(player, potion):
    if not player_has_relic(player, "relic.sacred_bark"):
        return False
    sacred_bark_excluded = {
        "potion.fairy_in_a_bottle",
        "potion.chaos",
        "potion.smoke_bomb",
        "potion.forges_blessing",
        "potion.elixir",
        "potion.stance",
        "potion.ambrosia",
        "potion.gamblers_brew",
    }
    return getattr(potion, "potion_id", "") not in sacred_bark_excluded


def add_temporary_card_to_hand_or_discard(game_state, card, source_name="药水", temporary_cost_zero=False):
    player = game_state.player
    logs = []
    new_card = copy.deepcopy(card)
    setattr(new_card, "temporary", True)
    setattr(new_card, "created_in_battle", True)
    if temporary_cost_zero:
        if getattr(new_card, "cost", None) == "X":
            logs.append("【{}】是 X 费牌，暂不改变 X 费用。".format(new_card.name))
        else:
            setattr(new_card, "temporary_cost_override", 0)
    if player.is_hand_full():
        player.discard_pile.append(new_card)
        if temporary_cost_zero and getattr(new_card, "cost", None) != "X":
            logs.append("手牌已满，【{}】进入弃牌堆。本回合其费用变为 0。".format(new_card.name))
        else:
            logs.append("手牌已满，【{}】进入弃牌堆。".format(new_card.name))
    else:
        player.hand.append(new_card)
        if temporary_cost_zero and getattr(new_card, "cost", None) != "X":
            logs.append("【{}】将【{}】加入手牌。本回合其费用变为 0。".format(source_name, new_card.name))
        else:
            logs.append("【{}】将【{}】加入手牌。".format(source_name, new_card.name))
    return logs


def get_potion_card_pool(game_state, wanted_card_type=None, colorless_only=False):
    from data.card.AAAregistry import CARD_REGISTRY, create_card
    from data.content_gate import filter_card_ids
    from game.reward import get_card_reward_pool, CARD_REWARD_POOL

    run_state = getattr(game_state, "run_state", None)

    if colorless_only:
        pool_ids = filter_card_ids(CARD_REGISTRY.keys())
    elif run_state is not None:
        pool_ids = get_card_reward_pool(run_state, ignore_prismatic=True)
    else:
        pool_ids = filter_card_ids(CARD_REWARD_POOL)

    result = []

    for card_id in pool_ids:
        try:
            card = create_card(card_id)
        except Exception:
            continue

        if colorless_only and getattr(card, "owner_character_id", "") != "":
            continue

        if wanted_card_type and getattr(card, "card_type", "") != wanted_card_type:
            continue

        if getattr(card, "card_type", "") in ("status", "curse"):
            continue

        if getattr(card, "quantity", "") in ("status", "curse", "starting", "test"):
            continue

        if getattr(card, "cost", None) == "X":
            continue

        result.append(card_id)

    return result


def roll_potion_card_options(game_state, wanted_card_type=None, count=3, colorless_only=False):
    from data.card.AAAregistry import create_card

    pool = get_potion_card_pool(
        game_state,
        wanted_card_type,
        colorless_only=colorless_only
    )

    if not pool:
        return []

    if len(pool) <= count:
        selected = list(pool)
    else:
        selected = random.sample(pool, count)

    cards = []

    for card_id in selected:
        card = create_card(card_id)
        setattr(card, "temporary", True)
        setattr(card, "created_in_battle", True)
        setattr(card, "temporary_cost_override", 0)
        cards.append(card)

    return cards


def format_pending_potion_card_selection(game_state):
    if not getattr(game_state, "pending_potion_card_selection", False):
        return "当前没有需要处理的药水选牌。"
    source = getattr(game_state, "pending_potion_card_source", "药水")
    options = getattr(game_state, "pending_potion_card_options", []) or []
    copy_count = int(getattr(game_state, "pending_potion_card_copy_count", 1) or 1)
    lines = ["=== {}：选择一张牌 ===".format(source)]
    if copy_count > 1:
        lines.append("神圣树皮：选中的牌会加入手牌 {} 次。".format(copy_count))
    lines.append("")
    for index, card in enumerate(options):
        try:
            text = card.summary_text()
        except Exception:
            text = "【{}】".format(getattr(card, "name", "未知卡牌"))
        lines.append("[{}] {}".format(index, text))
    lines.append("")
    lines.append("使用 /card potion_pick 0 选择。")
    return "\n".join(lines)


def clear_pending_potion_card_selection(game_state):
    game_state.pending_potion_card_selection = False
    game_state.pending_potion_card_source = ""
    game_state.pending_potion_card_options = []
    game_state.pending_potion_card_copy_count = 1
    game_state.pending_potion_card_mode = ""


def choose_pending_potion_card(game_state, choice_index):
    if not getattr(game_state, "pending_potion_card_selection", False):
        return "当前没有需要处理的药水选牌。"
    options = getattr(game_state, "pending_potion_card_options", []) or []
    if not options:
        clear_pending_potion_card_selection(game_state)
        return "没有可选择的药水牌。"
    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效。"
    source = getattr(game_state, "pending_potion_card_source", "药水")
    copy_count = int(getattr(game_state, "pending_potion_card_copy_count", 1) or 1)
    mode = getattr(game_state, "pending_potion_card_mode", "")
    chosen = options[choice_index]
    logs = ["【{}】选择了【{}】。".format(source, chosen.name)]

    if mode == "liquid_memories":
        # 液态记忆：从弃牌堆中移除选中牌，再把该牌加入手牌。神圣树皮额外加入复制品。
        removed = False
        for i, pile_card in enumerate(list(game_state.player.discard_pile)):
            if pile_card is chosen:
                game_state.player.discard_pile.pop(i)
                removed = True
                break
        if not removed:
            clear_pending_potion_card_selection(game_state)
            return "选中的牌已经不在弃牌堆中。"

    for n in range(copy_count):
        logs.extend(add_temporary_card_to_hand_or_discard(
            game_state,
            chosen,
            source_name=source,
            temporary_cost_zero=True,
        ))
    clear_pending_potion_card_selection(game_state)
    result = check_battle_result(game_state)
    if result:
        logs.append(result)
    return "\n".join(logs)


def format_pending_elixir_selection(game_state):
    if not getattr(game_state, "pending_elixir_selection", False):
        return "当前没有需要处理的万灵药水选择。"
    source = getattr(game_state, "pending_elixir_source", "万灵药水")
    options = getattr(game_state, "pending_elixir_options", []) or []
    lines = ["=== {}：选择要消耗的手牌 ===", "可以选择任意张。".format(source)]
    lines = ["=== {}：选择要消耗的手牌 ===".format(source), "可以选择任意张。", ""]
    for index, card in options:
        try:
            text = card.summary_text()
        except Exception:
            text = "【{}】".format(getattr(card, "name", "未知卡牌"))
        lines.append("[{}] {}".format(index, text))
    lines.append("")
    lines.append("使用 /card elixir 0,1,2；不消耗则 /card elixir none。")
    return "\n".join(lines)


def clear_pending_elixir_selection(game_state):
    game_state.pending_elixir_selection = False
    game_state.pending_elixir_source = ""
    game_state.pending_elixir_options = []
    game_state.pending_elixir_max_count = 0


def choose_pending_elixir_cards(game_state, indices):
    if not getattr(game_state, "pending_elixir_selection", False):
        return "当前没有需要处理的万灵药水选择。"
    source = getattr(game_state, "pending_elixir_source", "万灵药水")
    if not indices:
        clear_pending_elixir_selection(game_state)
        return "【{}】未选择消耗手牌。".format(source)
    unique = []
    for idx in indices:
        if idx not in unique:
            unique.append(idx)
    hand = game_state.player.hand
    for idx in unique:
        if idx < 0 or idx >= len(hand):
            return "手牌编号无效：{}。".format(idx)
    max_count = int(getattr(game_state, "pending_elixir_max_count", 0) or 0)
    if max_count > 0 and len(unique) > max_count:
        return "【{}】最多只能选择 {} 张手牌。".format(source, max_count)
    indexed_cards = [(idx, hand[idx]) for idx in unique]
    for idx in sorted(unique, reverse=True):
        hand.pop(idx)
    logs = ["【{}】消耗 {} 张手牌。".format(source, len(indexed_cards))]
    for idx, card in indexed_cards:
        logs.append("选择消耗手牌 [{}] 【{}】。".format(idx, card.name))
        logs.extend(move_card_to_exhaust_pile(game_state, card, reason="elixir"))
    clear_pending_elixir_selection(game_state)
    result = check_battle_result(game_state)
    if result:
        logs.append(result)
    return "\n".join(logs)




def queue_nilrys_codex_selection(game_state, source_name="尼利的宝典"):
    from data.card.AAAregistry import create_card
    from data.content_gate import filter_card_ids
    from game.reward import get_card_reward_pool, CARD_REWARD_POOL
    run_state = getattr(game_state, "run_state", None)
    pool = get_card_reward_pool(run_state, ignore_prismatic=True) if run_state is not None else filter_card_ids(CARD_REWARD_POOL)
    candidates = []
    for card_id in pool:
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "quantity", "") in ("starting", "status", "curse", "test"):
            continue
        if getattr(card, "card_type", "") in ("status", "curse"):
            continue
        candidates.append(card_id)
    if not candidates:
        return ["【{}】触发，但没有可生成的卡牌。".format(source_name)]
    rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + int(getattr(game_state, "turn_count", 1)) * 9173 + len(getattr(game_state.player, "draw_pile", []) or [])) if run_state is not None else random
    if len(candidates) <= 3:
        ids = list(candidates)
    else:
        ids = rng.sample(candidates, 3)
    options = []
    for card_id in ids:
        card = create_card(card_id)
        setattr(card, "created_by_nilrys_codex", True)
        options.append(card)
    entry = {"source": source_name, "options": options}
    queue = list(getattr(game_state, "pending_nilrys_queue", []) or [])
    if getattr(game_state, "pending_nilrys_selection", False):
        queue.append(entry)
        game_state.pending_nilrys_queue = queue
        return ["【{}】触发：已加入尼利的宝典后续选择队列。".format(source_name)]
    game_state.pending_nilrys_selection = True
    game_state.pending_nilrys_source = source_name
    game_state.pending_nilrys_options = options
    game_state.pending_nilrys_queue = queue
    return [format_pending_nilrys_selection(game_state)]


def format_pending_nilrys_selection(game_state):
    if not getattr(game_state, "pending_nilrys_selection", False):
        return "当前没有需要处理的尼利的宝典选择。"
    source = getattr(game_state, "pending_nilrys_source", "尼利的宝典")
    options = getattr(game_state, "pending_nilrys_options", []) or []
    lines = ["=== {}：选择一张牌洗入抽牌堆 ===".format(source), "可跳过。问号牌与三蛋不会影响本次选择。", ""]
    for index, card in enumerate(options):
        try:
            text = card.summary_text()
        except Exception:
            text = "【{}】".format(getattr(card, "name", "未知卡牌"))
        lines.append("[{}] {}".format(index, text))
    lines.append("")
    lines.append("使用 /card codex 0 选择；跳过则 /card codex skip。")
    return "\n".join(lines)


def _advance_pending_nilrys_selection(game_state):
    queue = list(getattr(game_state, "pending_nilrys_queue", []) or [])
    if queue:
        entry = queue.pop(0)
        game_state.pending_nilrys_queue = queue
        game_state.pending_nilrys_selection = True
        game_state.pending_nilrys_source = entry.get("source", "尼利的宝典")
        game_state.pending_nilrys_options = entry.get("options", [])
        return True
    game_state.pending_nilrys_selection = False
    game_state.pending_nilrys_source = ""
    game_state.pending_nilrys_options = []
    game_state.pending_nilrys_queue = []
    return False


def clear_pending_nilrys_selection(game_state):
    _advance_pending_nilrys_selection(game_state)


def choose_pending_nilrys_card(game_state, choice_index=None, skip=False):
    if not getattr(game_state, "pending_nilrys_selection", False):
        return "当前没有需要处理的尼利的宝典选择。"
    source = getattr(game_state, "pending_nilrys_source", "尼利的宝典")
    if skip:
        clear_pending_nilrys_selection(game_state)
        text = "【{}】未选择卡牌。".format(source)
        if getattr(game_state, "pending_nilrys_selection", False):
            text += "\n" + format_pending_nilrys_selection(game_state)
        return text
    options = getattr(game_state, "pending_nilrys_options", []) or []
    if choice_index is None or choice_index < 0 or choice_index >= len(options):
        return "卡牌编号无效。"
    card = copy.deepcopy(options[choice_index])
    player = game_state.player
    # 随机洗入抽牌堆。
    pos = random.randint(0, len(player.draw_pile)) if player.draw_pile is not None else 0
    player.draw_pile.insert(pos, card)
    clear_pending_nilrys_selection(game_state)
    text = "【{}】选择【{}】，随机洗入抽牌堆。".format(source, getattr(card, "name", "未知卡牌"))
    if getattr(game_state, "pending_nilrys_selection", False):
        text += "\n" + format_pending_nilrys_selection(game_state)
    return text

def add_upgraded_shivs_to_hand(game_state, count, source_name="狡诈药水"):
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card
    base = create_card("card.shiv")
    shiv = upgrade_card(base)
    logs = []
    for _ in range(int(count)):
        logs.extend(add_temporary_card_to_hand_or_discard(game_state, shiv, source_name=source_name, temporary_cost_zero=False))
    return logs

def use_potion(game_state, potion_index, target_index=None):
    """
    使用药水。
    """
    logs = []

    if game_state.battle_over:
        return "战斗已经结束。"

    if has_pending_player_choice(game_state):
        return get_pending_player_choice_hint(game_state)

    player = game_state.player

    if potion_index < 0 or potion_index >= len(player.potions):
        return "药水编号无效。"

    potion = player.potions[potion_index]
    potion_id = getattr(potion, "potion_id", "")

    target_index = resolve_auto_target_index(game_state, potion, target_index)

    if potion.target == "enemy":
        if target_index < 0 or target_index >= len(game_state.enemies):
            return "目标敌人编号无效。"

        if not game_state.enemies[target_index].is_alive():
            return "目标敌人已经死亡。"

    # 烟雾弹不能用于 Boss 战。这里在弹出药水前判断，避免误消耗。
    if potion_id == "potion.smoke_bomb":
        run_state = getattr(game_state, "run_state", None)
        node_type = getattr(run_state, "current_battle_node_type", "") if run_state is not None else ""
        if node_type == "boss":
            return "【烟雾弹】不能从 Boss 战中逃离。"

    player.potions.pop(potion_index)

    logs.append("{} 使用了【{}】。".format(player.name, potion.name))

    def dispatch_potion_after():
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
        return dispatch_event(game_state, EVENT_POTION_USE_AFTER, context)

    bark = potion_has_sacred_bark(player, potion)

    # 攻击 / 技能 / 能力药水：只选择一次；神圣树皮使选中的牌加入两次。
    potion_card_type = {
        "potion.attack": "attack",
        "potion.skill": "skill",
        "potion.power": "power",
    }.get(potion_id)

    if potion_card_type:
        options = roll_potion_card_options(game_state, potion_card_type, count=3)
        logs.extend(dispatch_potion_after())

        if not options:
            logs.append("【{}】没有可生成的{}牌。".format(potion.name, potion_card_type))
        else:
            game_state.pending_potion_card_selection = True
            game_state.pending_potion_card_source = potion.name
            game_state.pending_potion_card_options = options
            game_state.pending_potion_card_copy_count = 2 if bark else 1
            game_state.pending_potion_card_mode = "generated_card"

            if bark:
                logs.append("【神圣树皮】触发：选中的牌将加入手牌 2 次。")

            logs.append(format_pending_potion_card_selection(game_state))

        return "\n".join(logs)

    # 无色药水：只选择一次；神圣树皮使选中的牌加入两次。
    if potion_id == "potion.colorless":
        options = roll_potion_card_options(
            game_state,
            wanted_card_type=None,
            count=3,
            colorless_only=True
        )

        logs.extend(dispatch_potion_after())

        if not options:
            logs.append("【{}】没有可生成的无色牌。".format(potion.name))
        else:
            game_state.pending_potion_card_selection = True
            game_state.pending_potion_card_source = potion.name
            game_state.pending_potion_card_options = options
            game_state.pending_potion_card_copy_count = 2 if bark else 1
            game_state.pending_potion_card_mode = "generated_card"

            if bark:
                logs.append("【神圣树皮】触发：选中的牌将加入手牌 2 次。")

            logs.append(format_pending_potion_card_selection(game_state))

        return "\n".join(logs)

    # 液态记忆：只选择一次；神圣树皮使选中的弃牌加入两次。
    if potion_id == "potion.liquid_memories":
        options = [(i, card) for i, card in enumerate(getattr(player, "discard_pile", []) or [])]
        logs.extend(dispatch_potion_after())

        if not options:
            logs.append("【{}】没有可选择的弃牌堆卡牌。".format(potion.name))
        else:
            game_state.pending_potion_card_selection = True
            game_state.pending_potion_card_source = potion.name
            game_state.pending_potion_card_options = [card for _, card in options]
            game_state.pending_potion_card_copy_count = 2 if bark else 1
            game_state.pending_potion_card_mode = "liquid_memories"

            if bark:
                logs.append("【神圣树皮】触发：选中的牌将加入手牌 2 次。")

            logs.append(format_pending_potion_card_selection(game_state))

        return "\n".join(logs)

    # 万灵药水：消耗任意张手牌。神圣树皮排除，不翻倍。
    if potion_id == "potion.elixir":
        logs.extend(dispatch_potion_after())

        options = [(i, card) for i, card in enumerate(getattr(player, "hand", []) or [])]

        if not options:
            logs.append("【{}】当前没有可消耗的手牌。".format(potion.name))
        else:
            game_state.pending_elixir_selection = True
            game_state.pending_elixir_source = potion.name
            game_state.pending_elixir_options = options
            logs.append(format_pending_elixir_selection(game_state))

        return "\n".join(logs)

    # 狡诈药水：3 张小刀+；神圣树皮改为 6 张。
    if potion_id == "potion.cunning":
        amount = 6 if bark else 3

        if bark:
            logs.append("【神圣树皮】触发：【{}】生成数量 3 -> 6。".format(potion.name))

        logs.extend(add_upgraded_shivs_to_hand(game_state, amount, source_name=potion.name))
        logs.extend(dispatch_potion_after())

        result = check_battle_result(game_state)
        if result:
            logs.append(result)

        return "\n".join(logs)

    # 赌徒特酿：丢弃任意张牌，然后抽相同数量。神圣树皮排除，不翻倍。
    if potion_id == "potion.gamblers_brew":
        logs.extend(dispatch_potion_after())

        options = [(i, card) for i, card in enumerate(getattr(player, "hand", []) or [])]

        if not options:
            logs.append("【{}】当前没有可丢弃的手牌。".format(potion.name))
        else:
            game_state.pending_discard_selection = True
            game_state.pending_discard_source = "gamblers_brew"

            logs.append("=== {}：选择任意张手牌丢弃 ===".format(potion.name))
            logs.append("丢弃后抽取相同数量的牌。可选择 0 张。")
            logs.append("")

            for index, hand_card in options:
                logs.append("[{}] {}".format(index, hand_card.summary_text()))

            logs.append("")
            logs.append("使用 /card drop 0,1,2；不丢弃则 /card drop none。")

        return "\n".join(logs)

    # 混沌药水：填满所有空药水栏；可产出混沌药水。神圣树皮排除，不翻倍。
    if potion_id == "potion.chaos":
        from data.potion.AAAregistry import create_potion
        from game.reward import POTION_REWARD_POOL
        from game.relic_logic.run_relic_utils import try_gain_potion_with_relics

        empty_slots = int(getattr(player, "max_potion_slots", 3)) - len(getattr(player, "potions", []) or [])

        if empty_slots <= 0:
            logs.append("【{}】没有空药水栏位。".format(potion.name))
        else:
            logs.append("【{}】填充 {} 个空药水栏位。".format(potion.name, empty_slots))

            for _ in range(empty_slots):
                new_potion = create_potion(random.choice(POTION_REWARD_POOL))
                logs.extend(try_gain_potion_with_relics(player, new_potion, source=potion.name))

        logs.extend(dispatch_potion_after())

        result = check_battle_result(game_state)
        if result:
            logs.append(result)

        return "\n".join(logs)

    # 烟雾弹：非 Boss 战逃离，不获得任何奖励；仍分发药水使用与战斗结束事件。
    if potion_id == "potion.smoke_bomb":
        logs.append("【{}】触发：你从战斗中逃离。".format(potion.name))
        logs.extend(dispatch_potion_after())

        game_state.battle_over = True
        game_state.victory = True
        game_state.smoke_bomb_escaped = True

        return "\n".join(logs)

    # 其他普通效果药水：神圣树皮使数值翻倍。
    potion_amount_multiplier = 2 if bark else 1

    if potion_amount_multiplier > 1:
        logs.append("【神圣树皮】触发：【{}】的数值翻倍。".format(potion.name))

    logs.extend(apply_card_effects(
        game_state=game_state,
        card=potion,
        target_index=target_index,
        effect_context={
            "potion_amount_multiplier": potion_amount_multiplier
        }
    ))

    logs.extend(dispatch_potion_after())

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


def defer_player_turn_end_decay_from_enemy_action(game_state, target, status_key, amount, before_value, applied):
    """
    敌人行动发生在玩家回合结束后、自然衰减前。
    若此时给玩家新挂 turn_end 状态，先跳过同一轮末尾的第一次自然衰减。
    """
    if target is not getattr(game_state, "player", None):
        return
    if int(amount) <= 0 or int(before_value) > 0 or not applied:
        return

    status_def = get_status_def(status_key)
    if status_def is None:
        return
    if status_def.decay_timing != EVENT_TURN_END:
        return
    if int(getattr(status_def, "decay_amount", 0)) <= 0:
        return

    statuses = getattr(target, "statuses", None)
    if hasattr(statuses, "skip_next_decay"):
        statuses.skip_next_decay(status_key, EVENT_TURN_END)

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

    message = action.get("message", "")
    if message:
        suppress_message = False

        if (
            getattr(enemy, "enemy_id", "") == "enemy.romeo"
            and message == "上啊，熊！"
        ):
            bear_alive = any(
                getattr(other, "enemy_id", "") == "enemy.bear" and other.is_alive()
                for other in getattr(game_state, "enemies", []) or []
            )
            if not bear_alive:
                suppress_message = True

        if not suppress_message:
            logs.append("{}：「{}」".format(enemy.name, message))

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

        from game.status.status_effects import resolve_pending_flying_after_action

        old_flying_action_key = getattr(game_state, "_current_flying_action_key", None)
        flying_action_key = ("enemy_multi_action", id(action), int(getattr(game_state, "turn_count", 0)))

        setattr(game_state, "_current_flying_action_key", flying_action_key)

        try:
            for child_action in child_actions:
                process_enemy_action_payload(game_state, enemy, child_action, logs)
                result = check_battle_result(game_state)
                if result:
                    logs.append(result)
                    break

            logs.extend(resolve_pending_flying_after_action(
                game_state=game_state,
                action_key=flying_action_key
            ))
        finally:
            if old_flying_action_key is None:
                try:
                    delattr(game_state, "_current_flying_action_key")
                except AttributeError:
                    pass
            else:
                setattr(game_state, "_current_flying_action_key", old_flying_action_key)

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
            attack_element=attack_element,
            zone_element=zone_element
        )
        from game.zone_utils import (
            apply_zone_amount_modifier,
            apply_zone_source_hp_loss_if_needed,
            get_zone_burn_amount,
            add_status_to_target,
        )
        damage = apply_zone_amount_modifier(damage, game_state, zone_element)
        old_target_hp = int(getattr(target, "hp", 0))
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

        real_damage = old_target_hp - int(getattr(target, "hp", 0))
        if real_damage < 0:
            real_damage = 0

        if bool(action.get("heal_unblocked", False)) and real_damage > 0 and enemy.is_alive():
            old_enemy_hp = int(getattr(enemy, "hp", 0))
            enemy.hp = min(int(getattr(enemy, "max_hp", old_enemy_hp)), old_enemy_hp + real_damage)
            real_heal = int(enemy.hp) - old_enemy_hp
            logs.append("{} 回复 {} 点生命。当前 HP：{}/{}。".format(
                enemy.name,
                real_heal,
                enemy.hp,
                enemy.max_hp
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
    
    if op == "enemy_summon_fixed_enemies":
        enemy_ids = list(action.get("enemy_ids", []) or [])
        count = int(action.get("count", 0) or 0)

        if count > 0:
            enemy_ids = enemy_ids[:count]

        if not enemy_ids:
            logs.append("{} 试图召唤，但没有配置召唤物。".format(enemy.name))
            return

        max_enemies = int(action.get("max_enemies", 5))
        alive_count = sum(1 for e in getattr(game_state, "enemies", []) or [] if e.is_alive())
        slots = max_enemies - alive_count

        if slots <= 0:
            logs.append("{} 试图召唤，但场上已经没有位置。".format(enemy.name))
            return

        enemy_ids = enemy_ids[:slots]

        from data.enemy.AAAregistry import create_enemy

        summoned = []
        for enemy_id in enemy_ids:
            new_enemy = create_enemy(enemy_id)
            new_enemy.is_minion = True
            game_state.enemies.append(new_enemy)
            summoned.append(new_enemy)

        if summoned:
            logs.append("{} 召唤了 {}。".format(
                enemy.name,
                "、".join(e.name for e in summoned)
            ))
        return

    if op == "enemy_champ_burst":
        removed = []

        from game.status.status_defs import get_status_def, get_status_name
        active = list(getattr(enemy.statuses, "values", {}).items())

        for status_key, value in active:
            status_def = get_status_def(status_key)
            category = getattr(status_def, "category", "") if status_def is not None else ""

            should_remove = False

            if category == "debuff":
                should_remove = True

            # 负力量 / 负敏捷也按负面效果移除。
            if status_key in ("strength", "dexterity") and int(value) < 0:
                should_remove = True

            if should_remove:
                enemy.statuses.remove(status_key)
                removed.append(get_status_name(status_key))

        if removed:
            logs.append("{} 移除了所有负面效果：{}。".format(
                enemy.name,
                "、".join(removed)
            ))
        else:
            logs.append("{} 试图移除负面效果，但没有可移除的负面效果。".format(enemy.name))

        result = enemy.gain_status_with_result("strength", 6)
        from game.status.status_gain import format_status_gain_log
        logs.append(format_status_gain_log(enemy, "strength", 6, result))
        return

    if op == "enemy_bronze_orb_capture_card":
        player = game_state.player

        if bool(getattr(enemy, "_bronze_orb_capture_used", False)):
            logs.append("{} 已经使用过夺牌。".format(enemy.name))
            return

        setattr(enemy, "_bronze_orb_capture_used", True)

        rarity_rank = {
            "curse": 0,
            "status": 0,
            "starting": 1,
            "common": 2,
            "event": 2,
            "uncommon": 3,
            "rare": 4,
            "myth": 5,
        }

        source_pile = player.draw_pile
        source_name = "抽牌堆"

        if not source_pile:
            source_pile = player.discard_pile
            source_name = "弃牌堆"

        if not source_pile:
            logs.append("{} 试图夺取卡牌，但你的抽牌堆和弃牌堆都没有牌。".format(enemy.name))
            return

        max_rank = max(rarity_rank.get(getattr(card, "quantity", ""), 1) for card in source_pile)
        candidates = [
            card for card in source_pile
            if rarity_rank.get(getattr(card, "quantity", ""), 1) == max_rank
        ]

        captured = random.choice(candidates)
        source_pile.remove(captured)

        setattr(enemy, "_captured_card", captured)

        logs.append("{} 从你的{}中夺走了【{}】。击杀它即可取回。".format(
            enemy.name,
            source_name,
            captured.name
        ))
        return

    if op == "enemy_block_bronze_automaton":
        block = int(action.get("block", 0))
        if block <= 0:
            logs.append("{} 试图给予格挡，但数值无效。".format(enemy.name))
            return

        target = None
        for candidate in getattr(game_state, "enemies", []) or []:
            if not candidate.is_alive():
                continue
            if getattr(candidate, "enemy_id", "") == "enemy.bronze_automaton":
                target = candidate
                break

        if target is None:
            target = enemy

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=enemy,
            target=target,
            amount=block,
            block_source=BLOCK_SOURCE_ENEMY_ACTION,
            card=None
        ))
        return

    if op == "enemy_collector_buff":
        strength = int(action.get("strength", 3))
        block = int(action.get("block", 15))

        from game.status.status_gain import format_status_gain_log

        for target in getattr(game_state, "enemies", []) or []:
            if not target.is_alive():
                continue
            if target is enemy or getattr(target, "enemy_id", "") == "enemy.torch_head":
                result = target.gain_status_with_result("strength", strength)
                logs.append(format_status_gain_log(target, "strength", strength, result))

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=enemy,
            target=enemy,
            amount=block,
            block_source=BLOCK_SOURCE_ENEMY_ACTION,
            card=None
        ))
        return

    if op == "enemy_collector_summon_torch_heads":
        target_count = int(action.get("target_count", 2))
        current_count = sum(
            1 for e in getattr(game_state, "enemies", []) or []
            if e.is_alive() and getattr(e, "enemy_id", "") == "enemy.torch_head"
        )
        need = max(0, target_count - current_count)

        if need <= 0:
            logs.append("{} 试图召唤火炬头，但火炬头数量已经达到 {}。".format(
                enemy.name,
                target_count
            ))
            return

        max_enemies = int(action.get("max_enemies", 5))
        alive_count = sum(1 for e in getattr(game_state, "enemies", []) or [] if e.is_alive())
        slots = max(0, max_enemies - alive_count)
        need = min(need, slots)

        if need <= 0:
            logs.append("{} 试图召唤火炬头，但场上已经没有位置。".format(enemy.name))
            return

        from data.enemy.AAAregistry import create_enemy

        summoned = []
        for _ in range(need):
            torch = create_enemy("enemy.torch_head")
            torch.is_minion = True
            game_state.enemies.append(torch)
            summoned.append(torch)

        logs.append("{} 召唤了 {}。".format(
            enemy.name,
            "、".join(e.name for e in summoned)
        ))
        return

    if op == "enemy_summon_gremlins":
        count = int(action.get("count", 2))
        if count <= 0:
            logs.append("{} 试图召唤地精，但数量无效。".format(enemy.name))
            return

        max_enemies = int(action.get("max_enemies", 5))
        alive_count = sum(1 for e in getattr(game_state, "enemies", []) or [] if e.is_alive())
        slots = max_enemies - alive_count

        if slots <= 0:
            logs.append("{} 试图召唤地精，但场上已经没有位置。".format(enemy.name))
            return

        summon_count = min(count, slots)

        from data.route.encounters import build_random_gremlin_ids
        from data.enemy.AAAregistry import create_enemy

        gremlin_ids = build_random_gremlin_ids(random, summon_count)

        summoned = []
        for enemy_id in gremlin_ids:
            new_enemy = create_enemy(enemy_id)
            new_enemy.is_minion = True
            game_state.enemies.append(new_enemy)
            summoned.append(new_enemy)

        if summoned:
            logs.append("{} 召唤了 {}。".format(
                enemy.name,
                "、".join(e.name for e in summoned)
            ))
        else:
            logs.append("{} 试图召唤地精，但没有召唤成功。".format(enemy.name))

        return

    if op == "enemy_gremlin_leader_rally":
        strength = int(action.get("strength", 3))
        minion_block = int(action.get("minion_block", 6))

        from game.status.status_gain import format_status_gain_log

        alive_enemies = [
            e for e in getattr(game_state, "enemies", []) or []
            if e.is_alive()
        ]

        for target in alive_enemies:
            result = target.gain_status_with_result("strength", strength)
            logs.append(format_status_gain_log(target, "strength", strength, result))

        for target in alive_enemies:
            if not bool(getattr(target, "is_minion", False)):
                continue

            logs.extend(gain_block_without_modifiers(
                game_state=game_state,
                source=enemy,
                target=target,
                amount=minion_block,
                block_source=BLOCK_SOURCE_ENEMY_ACTION,
                card=None
            ))

        return
    
    if op == "enemy_heal_all_allies":
        heal = int(action.get("heal", 0))
        if heal <= 0:
            logs.append("{} 试图治疗己方，但治疗量无效。".format(enemy.name))
            return

        healed_any = False
        for target in getattr(game_state, "enemies", []) or []:
            if not target.is_alive():
                continue

            old_hp = int(getattr(target, "hp", 0))
            max_hp = int(getattr(target, "max_hp", old_hp))
            target.hp = min(max_hp, old_hp + heal)
            real_heal = int(target.hp) - old_hp

            if real_heal > 0:
                healed_any = True
                logs.append("{} 回复 {} 点生命。当前 HP：{}/{}。".format(
                    target.name,
                    real_heal,
                    target.hp,
                    target.max_hp
                ))

        if not healed_any:
            logs.append("{} 试图治疗己方，但没有成员需要治疗。".format(enemy.name))

        return

    if op == "enemy_status_all_allies":
        status_key = action.get("status", "")
        amount = int(action.get("amount", 0))

        if not status_key:
            logs.append("敌人全员状态行动缺少 status。")
            return

        if amount == 0:
            logs.append("敌人全员状态行动数值为 0。")
            return

        from game.zone_utils import apply_zone_amount_modifier, apply_zone_source_hp_loss_if_needed
        amount = apply_zone_amount_modifier(amount, game_state, zone_element)

        for target in getattr(game_state, "enemies", []) or []:
            if not target.is_alive():
                continue

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

    if op == "enemy_block_mystic_or_self":
        block = int(action.get("block", 0))
        if block <= 0:
            logs.append("{} 试图给予格挡，但数值无效。".format(enemy.name))
            return

        target = None
        for candidate in getattr(game_state, "enemies", []) or []:
            if candidate is enemy:
                continue
            if not candidate.is_alive():
                continue
            if getattr(candidate, "enemy_id", "") == "enemy.mystic":
                target = candidate
                break

        if target is None:
            target = enemy

        block = apply_modifier_profile(
            value=block,
            modifier_profile="block",
            game_state=game_state,
            source=enemy,
            target=target,
            card=None,
            block_source=BLOCK_SOURCE_ENEMY_ACTION,
            zone_element=zone_element
        )

        from game.zone_utils import (
            apply_zone_amount_modifier,
            apply_earth_zone_temp_thorns,
            apply_zone_source_hp_loss_if_needed,
        )

        block = apply_zone_amount_modifier(block, game_state, zone_element)
        if block < 0:
            block = 0

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=enemy,
            target=target,
            amount=block,
            block_source=BLOCK_SOURCE_ENEMY_ACTION,
            card=None
        ))

        apply_earth_zone_temp_thorns(
            game_state=game_state,
            target=target,
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
    
    if op == "enemy_gain_block":
        block = int(action.get("block", 0))
        block = apply_modifier_profile(
            value=block,
            modifier_profile="block",
            game_state=game_state,
            source=enemy,
            target=enemy,
            card=None,
            block_source=BLOCK_SOURCE_ENEMY_ACTION,
            zone_element=zone_element
        )
        from game.zone_utils import (
            apply_zone_amount_modifier,
            apply_earth_zone_temp_thorns,
            apply_zone_source_hp_loss_if_needed,
        )
        block = apply_zone_amount_modifier(block, game_state, zone_element)
        if block < 0:
            block = 0
        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=enemy,
            target=enemy,
            amount=block,
            block_source=BLOCK_SOURCE_ENEMY_ACTION,
            card=None
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
    
    if op == "enemy_smart_ally_block_or_attack":
        allies = [
            e for e in game_state.enemies
            if e is not enemy and e.is_alive()
        ]

        if allies:
            target = random.choice(allies)
            block = int(action.get("block", 0))
            logs.extend(gain_block_without_modifiers(
                game_state=game_state,
                source=enemy,
                target=target,
                amount=block,
                block_source=BLOCK_SOURCE_ENEMY_ACTION,
                card=None
            ))
            return

        damage = int(action.get("damage", 0))
        logs.extend(deal_damage(
            game_state=game_state,
            source=enemy,
            target=game_state.player,
            amount=damage,
            damage_kind="attack",
            attack_type=action.get("attack_type", ""),
            attack_element=action.get("attack_element", ""),
            card=None,
        ))
        return
    
    if op == "enemy_split":
        resolver = getattr(enemy, "resolve_split", None)
        if resolver is None:
            logs.append("{} 想要分裂，但没有实现分裂逻辑。".format(enemy.name))
            return
        logs.extend(resolver(game_state))
        return
    
    if op == "enemy_wait":
        return

    if op in ("enemy_add_card_to_discard", "enemy_add_card_to_draw", "enemy_add_card_to_hand"):
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
        added_to_hand = 0
        added_to_discard = 0
        added_to_draw = 0

        for _ in range(count):
            new_card = create_card(card_id)

            # 战斗内生成牌标记。
            setattr(new_card, "temporary", True)
            setattr(new_card, "created_in_battle", True)

            if op == "enemy_add_card_to_draw":
                game_state.player.draw_pile.append(new_card)
                added_to_draw += 1
            elif op == "enemy_add_card_to_hand":
                if len(game_state.player.hand) < getattr(game_state.player, "max_hand_size", 10):
                    game_state.player.hand.append(new_card)
                    added_to_hand += 1
                else:
                    game_state.player.discard_pile.append(new_card)
                    added_to_discard += 1
            else:
                game_state.player.discard_pile.append(new_card)
                added_to_discard += 1

            added_cards.append(new_card)

        card_name = added_cards[0].name if added_cards else card_id

        if added_to_draw > 0:
            logs.append("{} 向你的抽牌堆加入 {} 张【{}】。".format(
                enemy.name,
                added_to_draw,
                card_name
            ))

        if added_to_hand > 0:
            logs.append("{} 向你的手牌加入 {} 张【{}】。".format(
                enemy.name,
                added_to_hand,
                card_name
            ))

        if added_to_discard > 0:
            if op == "enemy_add_card_to_hand":
                logs.append("手牌已满，{} 将 {} 张【{}】加入你的弃牌堆。".format(
                    enemy.name,
                    added_to_discard,
                    card_name
                ))
            else:
                logs.append("{} 向你的弃牌堆加入 {} 张【{}】。".format(
                    enemy.name,
                    added_to_discard,
                    card_name
                ))

        return

    if op == "enemy_add_curse_to_master_deck":
        card_id = action.get("card_id", "") or "card.curse.parasite"
        count = int(action.get("count", 1) or 1)

        if count <= 0:
            return

        run_state = getattr(game_state, "run_state", None)
        if run_state is None:
            logs.append("{} 试图将诅咒加入你的牌组，但当前战斗没有绑定 RunState。".format(enemy.name))
            return

        from data.card.AAAregistry import create_card
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics

        # 战斗中长期牌组发生变化前，先把当前玩家生命/遗物同步到 RunState，
        # 避免黑石护符等获得诅咒触发按战斗开始时的旧 HP 结算。
        run_state.hp = game_state.player.hp
        run_state.max_hp = game_state.player.max_hp
        run_state.relics = game_state.player.relics
        run_state.potions = game_state.player.potions

        for _ in range(count):
            card = create_card(card_id)
            logs.extend(add_card_to_master_deck_with_relics(
                run_state,
                card,
                source=enemy.name
            ))

        # 如果御守未抵消且黑石护符等修改了生命上限/生命值，同步回当前战斗。
        game_state.player.max_hp = run_state.max_hp
        game_state.player.hp = min(run_state.hp, game_state.player.max_hp)
        game_state.player.relics = run_state.relics
        game_state.player.potions = run_state.potions

        return

    if op == "enemy_steal_gold":
        amount = int(action.get("amount", 0))

        if amount <= 0:
            logs.append("{} 试图偷金币，但数量无效。".format(enemy.name))
            return
        run_state = getattr(game_state, "run_state", None)
        if run_state is None:
            logs.append("{} 试图偷金币，但当前战斗没有绑定 RunState。".format(enemy.name))
            return
        current_gold = int(getattr(run_state, "gold", 0))
        stolen = min(amount, current_gold)
        if stolen < 0:
            stolen = 0
        run_state.gold -= stolen
        old_stolen = int(getattr(enemy, "_stolen_gold", 0))
        enemy._stolen_gold = old_stolen + stolen
        if stolen > 0:
            logs.append("{} 偷走了 {} 金币。当前金币：{}。".format(
                enemy.name,
                stolen,
                run_state.gold
            ))
        else:
            logs.append("{} 想偷金币，但你已经没有金币了。".format(enemy.name))
        return

    if op == "enemy_escape":
        stolen = int(getattr(enemy, "_stolen_gold", 0))

        setattr(enemy, "_escaped", True)

        enemy.hp = 0
        enemy.block = 0

        if stolen > 0:
            logs.append("{} 带着偷走的 {} 金币逃离了战斗。".format(
                enemy.name,
                stolen
            ))
        else:
            logs.append("{} 逃离了战斗。".format(enemy.name))

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
        before_status_value = 0
        if hasattr(target, "get_status_value"):
            before_status_value = int(target.get_status_value(status_key))
        status_applied = False
        if hasattr(target, "gain_status_with_result"):
            result = target.gain_status_with_result(status_key, amount)
            from game.status.status_gain import format_status_gain_log
            logs.append(format_status_gain_log(target, status_key, amount, result))
            status_applied = bool(result.get("applied")) and int(result.get("current", 0)) > 0
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
            status_applied = int(current) > before_status_value
        defer_player_turn_end_decay_from_enemy_action(
            game_state=game_state,
            target=target,
            status_key=status_key,
            amount=amount,
            before_value=before_status_value,
            applied=status_applied
        )
        if (
            status_key == "ritual"
            and target is not game_state.player
            and before_status_value <= 0
            and amount > 0
        ):
            setattr(target, "_ritual_skip_turn_end_once", True)
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
    if enemy.get_status_value("flinch") > 0:
        current_flinch = enemy.gain_status("flinch", -1)
        logs.append("{} 畏缩了，无法行动。剩余畏缩：{}。".format(
            enemy.name,
            current_flinch
        ))
        return logs
    setattr(enemy, "_current_game_state", game_state)
    result = enemy.act()
    for log in result.logs:
        logs.append(log)

    before_enemy_action = getattr(enemy, "before_enemy_action", None)
    if before_enemy_action is not None:
        before_logs = before_enemy_action(game_state)
        if before_logs:
            logs.extend(before_logs)
    process_enemy_action_payload(
        game_state=game_state,
        enemy=enemy,
        action=result.action,
        logs=logs
    )
    after_enemy_action = getattr(enemy, "after_enemy_action", None)
    if after_enemy_action is not None:
        after_logs = after_enemy_action(game_state)
        if after_logs:
            logs.extend(after_logs)

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
    clear_pending_choice(game_state)
    game_state.pending_discard_selection = False
    game_state.pending_discard_source = ""
    clear_pending_discard_to_draw_top(game_state)
    clear_pending_exhaust_hand_selection(game_state)
    clear_pending_hand_to_draw_top_selection(game_state)
    clear_pending_upgrade_hand_selection(game_state)
    clear_pending_exhume_selection(game_state)
    clear_pending_potion_card_selection(game_state)
    clear_pending_elixir_selection(game_state)

    player_turn_end_context = BattleContext(
        game_state=game_state,
        player=player,
        source=player
    )

    player_turn_end_logs = dispatch_event(
        game_state,
        EVENT_PLAYER_TURN_END,
        player_turn_end_context
    )

    if player_turn_end_logs:
        logs.append("")
        logs.append("玩家回合结束状态结算：")
        logs.extend(player_turn_end_logs)

    result = check_battle_result(game_state)
    if result:
        logs.append(result)
        return "\n".join(logs)

    logs.extend(end_player_turn_hand_cleanup(game_state))
    result = check_battle_result(game_state)
    if result:
        logs.append(result)
        return "\n".join(logs)
    logs.append("")
    logs.append("敌人行动：")

    # 使用快照遍历，避免史莱姆分裂后新生成的小史莱姆在同一轮立刻行动。
    for enemy in list(game_state.enemies):
        if enemy not in game_state.enemies:
            continue
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
    game_state.player_card_type_played_counts_this_turn = make_empty_player_card_type_played_counts()
    game_state.player_lost_hp_this_turn = False
    game_state.player_lost_hp_total_this_turn = 0
    cleared_temp_costs = clear_turn_temporary_card_costs(player)
    start_turn_block_logs = player.start_turn(game_state)
    if start_turn_block_logs:
        logs.extend(start_turn_block_logs)
    if cleared_temp_costs:
        logs.append("临时费用变化已清除：{} 张牌。".format(cleared_temp_costs))
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
    draw_reduction = get_turn_draw_reduction(game_state)
    turn_draw_count = 5 + get_turn_draw_bonus(game_state) - draw_reduction

    if turn_draw_count < 0:
        turn_draw_count = 0

    if draw_reduction > 0:
        logs.append("抽牌减少：本回合少抽 1 张牌。")

    logs.extend(player.draw_cards(
        turn_draw_count,
        game_state=game_state,
        draw_source="turn_start"
    ))
    logs.extend(apply_turn_start_hand_ready_effects(game_state))
    logs.append(player.status_text())
    logs.append(format_enemy_current_status(game_state))
    logs.append("")
    logs.append(player.hand_text(game_state))

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
        if bool(getattr(game_state.enemies[target_index], "_unselectable", False)):
            return "目标敌人当前无法被选择。"
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

    from game.display_names import format_relic_display_name

    for relic_id, relic in relic_map.items():
        count = relic_count_map[relic_id]

        if count > 1:
            name_text = "{}（{}）".format(format_relic_display_name(relic), count)
        else:
            name_text = format_relic_display_name(relic)

        lines.append("{}：{}".format(
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

# =========================
# 工具箱：战斗内开局选无色牌
# =========================

def _get_toolbox_colorless_pool():
    from data.card.AAAregistry import CARD_REGISTRY, create_card
    from data.content_gate import is_content_enabled
    result = []
    for card_id in CARD_REGISTRY.keys():
        if not is_content_enabled("card", card_id):
            continue
        try:
            card = create_card(card_id)
        except Exception:
            continue
        if getattr(card, "owner_character_id", "") != "":
            continue
        if getattr(card, "card_type", "") in ("status", "curse"):
            continue
        if getattr(card, "quantity", "") in ("starting", "status", "curse", "test"):
            continue
        result.append(card_id)
    return result


def queue_toolbox_selection(game_state, source_name="工具箱"):
    from data.card.AAAregistry import create_card
    pool = _get_toolbox_colorless_pool()
    if not pool:
        return ["【{}】触发，但没有可选择的无色牌。".format(source_name)]
    seed = int(getattr(getattr(game_state, "run_state", None), "run_seed", 0) or 0) + 5321 + int(getattr(game_state, "turn_count", 1))
    rng = random.Random(seed)
    ids = rng.sample(pool, 3) if len(pool) >= 3 else [rng.choice(pool) for _ in range(3)]
    options = []
    for card_id in ids:
        card = create_card(card_id)
        setattr(card, "temporary", True)
        setattr(card, "created_in_battle", True)
        options.append(card)
    game_state.pending_toolbox_selection = True
    game_state.pending_toolbox_source = source_name
    game_state.pending_toolbox_options = options
    return [format_pending_toolbox_selection(game_state)]


def format_pending_toolbox_selection(game_state):
    if not getattr(game_state, "pending_toolbox_selection", False):
        return "当前没有需要处理的【工具箱】选择。"
    source = getattr(game_state, "pending_toolbox_source", "工具箱")
    options = getattr(game_state, "pending_toolbox_options", []) or []
    lines = ["=== {}：选择 1 张无色牌加入手牌 ===".format(source), ""]
    for index, card in enumerate(options):
        try:
            text = card.summary_text()
        except Exception:
            text = "【{}】".format(getattr(card, "name", "未知卡牌"))
        lines.append("[{}] {}".format(index, text))
    lines.append("")
    lines.append("使用 /card toolbox 0 选择。")
    return "\n".join(lines)


def clear_pending_toolbox_selection(game_state):
    game_state.pending_toolbox_selection = False
    game_state.pending_toolbox_source = ""
    game_state.pending_toolbox_options = []
    game_state.pending_toolbox_mode = ""
    game_state.pending_toolbox_temp_cost_zero = False


def choose_pending_toolbox_card(game_state, choice_index):
    import copy
    if not getattr(game_state, "pending_toolbox_selection", False):
        return "当前没有需要处理的【工具箱】选择。"
    options = getattr(game_state, "pending_toolbox_options", []) or []
    if choice_index < 0 or choice_index >= len(options):
        return "选择编号无效。"
    source = getattr(game_state, "pending_toolbox_source", "工具箱")
    mode = getattr(game_state, "pending_toolbox_mode", "") or "add_choice_to_hand"
    selected = options[choice_index]
    card = copy.deepcopy(selected)
    if bool(getattr(game_state, "pending_toolbox_temp_cost_zero", False)):
        try:
            card.cost = 0
        except Exception:
            setattr(card, "temporary_cost_override", 0)
    player = game_state.player
    clear_pending_toolbox_selection(game_state)
    if mode == "draw_pile_to_hand":
        if selected not in player.draw_pile:
            return "所选牌已经不在抽牌堆中，选择已取消。"
        player.draw_pile.remove(selected)
        card = selected
    if player.is_hand_full():
        player.discard_pile.append(card)
        return "【{}】选择【{}】，但手牌已满，进入弃牌堆。".format(source, getattr(card, "name", "未知卡牌"))
    player.hand.append(card)
    return "【{}】选择【{}】，加入手牌。".format(source, getattr(card, "name", "未知卡牌"))
