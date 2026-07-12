# -*- coding: utf-8 -*-

import random

from data.card.AAAregistry import create_deck
from data.character.AAAregistry import create_character
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from game.constants import KEYWORD_EXHAUST
from game.display_names import format_relic_display_name
from game.player_state import PlayerState
from game.pvp.state import (
    PVP_BASE_MAX_COST,
    PVP_STATUS_BATTLE,
    PVP_STATUS_COMPLETE,
    PVP_STATUS_LOBBY,
    PvpBattleState,
    PvpPlayerSlot,
)
from game.status.status_defs import get_status_name
from game.status.status_display import get_status_display_text


def create_player_slot(user_id, character_id, side):
    character = create_character(character_id)
    max_potion_slots = int(getattr(character, "max_potion_slots", 3) or 3)
    starting_potions = [
        create_potion(potion_id)
        for potion_id in getattr(character, "starting_potion_ids", []) or []
    ][:max_potion_slots]
    return PvpPlayerSlot(
        user_id=str(user_id),
        character_id=character.character_id,
        character_name=character.name,
        side=side,
        max_hp=character.max_hp,
        hp=character.max_hp,
        max_cost=PVP_BASE_MAX_COST,
        master_deck=create_deck(getattr(character, "starting_deck_ids", []) or []),
        relics=[
            create_relic(relic_id)
            for relic_id in getattr(character, "starting_relic_ids", []) or []
        ],
        potions=starting_potions,
    )


def _rules(room):
    return room.rules


def _sync_slot_from_player(slot):
    player = slot.player_state
    if player is None:
        return
    slot.hp = int(getattr(player, "hp", slot.hp) or 0)
    slot.max_hp = int(getattr(player, "max_hp", slot.max_hp) or 0)
    slot.relics = getattr(player, "relics", []) or []
    slot.potions = getattr(player, "potions", []) or []


def _ensure_card_uid(card):
    uid = getattr(card, "pvp_card_uid", "")
    if uid:
        return str(uid)
    uid = "pvp_card_{}".format(id(card))
    setattr(card, "pvp_card_uid", uid)
    return uid


def _ensure_slot_card_uids(slot):
    for card in list(getattr(slot, "master_deck", []) or []):
        _ensure_card_uid(card)


def _make_player_state(room, slot):
    rules = _rules(room)
    player = PlayerState(
        character_id=slot.character_id,
        name=slot.character_name,
        max_hp=slot.max_hp,
        hp=slot.hp,
        max_cost=int(rules.base_cost),
        cost=int(rules.base_cost),
        relics=slot.relics,
        max_potion_slots=3,
        potions=slot.potions,
        draw_pile=list(slot.master_deck),
        discard_pile=[],
        exhaust_pile=[],
        hand=[],
    )
    for card in player.draw_pile:
        _ensure_card_uid(card)
    return player


def start_pvp_battle(room):
    if room.status != PVP_STATUS_LOBBY:
        return "当前 PVP 房间已经不在大厅。"
    if len(room.players) != 2:
        return "当前 PVP 第一版需要正好 2 名玩家。当前人数：{}。".format(len(room.players))

    rng = random.Random(int(room.seed))
    for slot in room.players:
        if not getattr(slot, "master_deck", None):
            return "{} 的牌库为空，不能开始 PVP。".format(slot.label())
        _ensure_slot_card_uids(slot)
        player = _make_player_state(room, slot)
        rng.shuffle(player.draw_pile)
        player.draw_cards(5, game_state=None, draw_source="pvp_opening")
        slot.player_state = player
        slot.overheated_cards = []

    room.battle = PvpBattleState(active_user_id=room.players[0].user_id)
    room.status = PVP_STATUS_BATTLE
    return "\n".join([
        "PVP 演绎房开战。",
        _format_rule_summary(room),
        "PVP 专用控制台仍可使用：/card pvp ctrl ...",
        "",
        format_room(room, viewer_user_id=room.players[0].user_id),
    ])


def _active_slot(room):
    battle = room.battle
    if battle is None:
        return None
    return room.get_player(battle.active_user_id)


def _card_cost(player, card):
    raw_cost = getattr(card, "cost", 0)
    if str(raw_cost).upper() == "X":
        return max(0, int(getattr(player, "cost", 0) or 0))
    try:
        return int(raw_cost)
    except (TypeError, ValueError):
        return 0


def _status_value(entity, key):
    statuses = getattr(entity, "statuses", None)
    if statuses is None:
        return 0
    try:
        return int(statuses.get(key) or 0)
    except Exception:
        return 0


def _resolve_amount(player, target, card, spec, modifier_profile=None):
    if isinstance(spec, dict):
        if "value" in spec:
            amount = int(spec.get("value") or 0)
        elif "base_var" in spec:
            amount = int(getattr(card, "card_vars", {}).get(spec.get("base_var"), 0) or 0)
        elif "var" in spec:
            amount = int(getattr(card, "card_vars", {}).get(spec.get("var"), 0) or 0)
        else:
            amount = int(spec.get("amount", 0) or 0)

        for scaling in spec.get("scaling", []) or []:
            stat = scaling.get("stat")
            if stat == "strength":
                multiplier_var = scaling.get("multiplier_var")
                multiplier = int(getattr(card, "card_vars", {}).get(multiplier_var, 1) or 1)
                amount += _status_value(player, "strength") * multiplier

        modifier_profile = spec.get("modifier_profile", modifier_profile)
    else:
        amount = int(spec or 0)

    if modifier_profile == "attack_damage":
        amount += _status_value(player, "strength")
        if _status_value(player, "weak") > 0:
            amount = int(amount * 0.75)
        if target is not None and _status_value(target, "vulnerable") > 0:
            amount = int(amount * 1.5)

    if modifier_profile == "block":
        amount += _status_value(player, "dexterity")
        if _status_value(player, "frail") > 0:
            amount = int(amount * 0.75)

    return max(0, int(amount))


def _gain_block(entity, amount):
    amount = max(0, int(amount))
    entity.block = int(getattr(entity, "block", 0) or 0) + amount
    return "{} 获得 {} 点格挡。当前格挡：{}。".format(entity.name, amount, entity.block)


def _selected_opponent(room, source_slot, target_index=None):
    opponents = room.opponents_of(source_slot.user_id)
    opponents = [slot for slot in opponents if slot.player_state is not None]
    if not opponents:
        return None
    if target_index is None:
        return opponents[0]
    if target_index < 0 or target_index >= len(room.players):
        return None
    target = room.players[target_index]
    if str(target.user_id) == str(source_slot.user_id):
        return None
    if target.player_state is None:
        return None
    return target


def _effect_target_slots(room, source_slot, effect, selected_opponent):
    target_key = effect.get("target", getattr(effect, "target", "self"))
    if target_key in ("self", "player"):
        return [source_slot]
    if target_key in ("selected_enemy", "enemy", "selected_opponent", "opponent"):
        return [selected_opponent] if selected_opponent is not None else []
    if target_key in ("all_enemies", "all_opponents"):
        return [
            slot for slot in room.opponents_of(source_slot.user_id)
            if slot.player_state is not None
        ]
    if target_key in ("random_enemy", "random_opponent"):
        opponents = [
            slot for slot in room.opponents_of(source_slot.user_id)
            if slot.player_state is not None
        ]
        if not opponents:
            return []
        rng = random.Random(int(room.seed) + int(room.battle.turn_count) * 7717 + len(opponents))
        return [rng.choice(opponents)]
    return [source_slot]


def _queue_attack(room, source_slot, target_slot, amount, card):
    if target_slot is None or target_slot.player_state is None:
        return "攻击目标无效。"
    amount = max(0, int(amount))
    room.battle.pending_attacks.append({
        "source_user_id": source_slot.user_id,
        "target_user_id": target_slot.user_id,
        "amount": amount,
        "card_name": getattr(card, "name", "未知卡牌"),
    })
    return "{} 对 {} 施加 {} 点待结算攻击伤害。".format(
        source_slot.label(),
        target_slot.label(),
        amount,
    )


def _apply_card_effect(room, source_slot, card, effect, selected_opponent):
    player = source_slot.player_state
    op = effect.get("op")
    logs = []

    if op == "deal_damage":
        for target_slot in _effect_target_slots(room, source_slot, effect, selected_opponent):
            target = target_slot.player_state if target_slot is not None else None
            amount = _resolve_amount(
                player=player,
                target=target,
                card=card,
                spec=effect.get("amount", 0),
                modifier_profile="attack_damage",
            )
            logs.append(_queue_attack(room, source_slot, target_slot, amount, card))
        return logs

    if op == "gain_block":
        amount = _resolve_amount(
            player=player,
            target=player,
            card=card,
            spec=effect.get("amount", 0),
            modifier_profile="block",
        )
        logs.append(_gain_block(player, amount))
        return logs

    if op == "draw_cards":
        amount = _resolve_amount(player, player, card, effect.get("amount", effect.get("count", 0)))
        logs.extend(player.draw_cards(amount, game_state=None, draw_source=getattr(card, "card_id", "pvp_card")))
        return logs

    if op == "gain_energy":
        amount = _resolve_amount(player, player, card, effect.get("amount", 0))
        player.cost = int(getattr(player, "cost", 0) or 0) + amount
        logs.append("{} 获得 {} 点能量。当前费用：{}。".format(player.name, amount, player.cost))
        return logs

    if op in ("gain_status", "apply_status"):
        status_key = effect.get("status", "")
        amount = _resolve_amount(player, selected_opponent.player_state if selected_opponent else None, card, effect.get("amount", 0))
        for target_slot in _effect_target_slots(room, source_slot, effect, selected_opponent):
            target = target_slot.player_state
            current = target.gain_status(status_key, amount)
            logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
                target_slot.label(),
                amount,
                get_status_name(status_key),
                get_status_name(status_key),
                current,
            ))
        return logs

    logs.append("PVP 暂未处理卡牌效果：{}。".format(op))
    return logs


def _record_card_play(room, card):
    battle = room.battle
    uid = _ensure_card_uid(card)
    count = int(battle.card_play_counts_this_turn.get(uid, 0) or 0) + 1
    battle.card_play_counts_this_turn[uid] = count
    battle.cards_played_this_turn += 1
    return count, battle.cards_played_this_turn


def play_card(room, user_id, hand_index, target_index=None):
    if room.status != PVP_STATUS_BATTLE or room.battle is None:
        return "当前 PVP 房间不在战斗中。"
    battle = room.battle
    slot = _active_slot(room)
    if slot is None or str(slot.user_id) != str(user_id):
        return "还没轮到你行动。当前行动者：{}。".format(battle.active_user_id)
    player = slot.player_state
    if player is None or not player.is_alive():
        return "当前行动者已经无法行动。可以由任意参战者使用 /card pvp finish 结束战斗。"
    if hand_index < 0 or hand_index >= len(player.hand):
        return "手牌编号无效。"
    rules = _rules(room)
    max_cards = int(rules.max_cards_per_turn)
    if battle.cards_played_this_turn >= max_cards:
        return "本回合出牌数已经达到上限。"

    card = player.hand[hand_index]
    cost = _card_cost(player, card)
    if cost > int(getattr(player, "cost", 0) or 0):
        return "费用不足：需要 {}，当前 {}。".format(cost, player.cost)

    selected_opponent = _selected_opponent(room, slot, target_index)
    if getattr(card, "target", "") == "enemy" and selected_opponent is None:
        return "目标玩家编号无效。"

    player.cost -= cost
    player.hand.pop(hand_index)
    card_play_count, total_count = _record_card_play(room, card)
    logs = [
        "{} 打出【{}】。".format(slot.label(), getattr(card, "name", "未知卡牌")),
        "PVP 出牌计数：{}/{}；本张牌本回合第 {} 次。".format(
            total_count,
            max_cards,
            card_play_count,
        ),
    ]

    for effect in getattr(card, "effects", []) or []:
        logs.extend(_apply_card_effect(room, slot, card, effect, selected_opponent))

    natural_exhaust = bool(card.has_keyword(KEYWORD_EXHAUST))
    overheated = (not natural_exhaust) and card_play_count > int(rules.overheat_threshold)

    if natural_exhaust:
        player.exhaust_pile.append(card)
        logs.append("【{}】进入消耗堆。".format(card.name))
    elif overheated:
        player.exhaust_pile.append(card)
        slot.overheated_cards.append(card)
        logs.append("【{}】过热：暂入消耗堆，下个自己的回合进入弃牌堆。".format(card.name))
    else:
        player.discard_pile.append(card)

    _sync_slot_from_player(slot)

    if battle.cards_played_this_turn >= max_cards:
        logs.append("")
        logs.extend(_end_active_turn(room, forced=True))
        return "\n".join(logs)

    logs.append("")
    logs.append(format_room(room, viewer_user_id=user_id))
    return "\n".join(logs)


def _settle_pending_attacks(room, source_slot):
    battle = room.battle
    logs = []
    remaining = []
    for item in list(battle.pending_attacks):
        if str(item.get("source_user_id")) != str(source_slot.user_id):
            remaining.append(item)
            continue
        target_slot = room.get_player(item.get("target_user_id"))
        target = target_slot.player_state if target_slot is not None else None
        if target is None:
            logs.append("一段待结算攻击失去目标。")
            continue
        amount = int(item.get("amount", 0) or 0)
        card_name = item.get("card_name", "攻击")
        logs.append("待结算攻击【{}】命中 {}：{}".format(
            card_name,
            target_slot.label(),
            target.take_damage(amount),
        ))
        _sync_slot_from_player(target_slot)
    battle.pending_attacks = remaining
    if not logs:
        logs.append("没有待结算攻击。")
    return logs


def _return_overheated_cards(slot):
    player = slot.player_state
    if player is None:
        return []
    cards = list(getattr(slot, "overheated_cards", []) or [])
    if not cards:
        return []
    logs = []
    for card in cards:
        if card in player.exhaust_pile:
            player.exhaust_pile.remove(card)
        player.discard_pile.append(card)
    slot.overheated_cards = []
    logs.append("{} 的 {} 张过热牌进入弃牌堆。".format(slot.label(), len(cards)))
    return logs


def _start_turn_for_slot(slot, bonus_energy=0):
    player = slot.player_state
    if player is None:
        return []
    logs = []
    logs.extend(_return_overheated_cards(slot))
    logs.extend(player.start_turn(game_state=None))
    if bonus_energy:
        player.cost += int(bonus_energy)
        logs.append("{} 因对方强制换回合获得 {} 点费用。当前费用：{}/{}。".format(
            slot.label(),
            int(bonus_energy),
            player.cost,
            player.max_cost,
        ))
    draw_count = max(0, 5 - len(player.hand))
    if draw_count:
        logs.extend(player.draw_cards(draw_count, game_state=None, draw_source="pvp_turn_start"))
    _sync_slot_from_player(slot)
    return logs


def _next_slot(room, current_slot):
    if len(room.players) <= 1:
        return current_slot
    index = room.players.index(current_slot)
    return room.players[(index + 1) % len(room.players)]


def _end_active_turn(room, forced=False):
    battle = room.battle
    rules = _rules(room)
    slot = _active_slot(room)
    if slot is None:
        return ["当前没有行动者。"]
    player = slot.player_state
    logs = []
    if forced:
        logs.append("{} 打出第 {} 张牌，强制进入对方回合。".format(
            slot.label(),
            int(rules.max_cards_per_turn),
        ))
    else:
        logs.append("{} 结束回合。".format(slot.label()))
    logs.extend(_settle_pending_attacks(room, slot))
    if player is not None:
        logs.append(player.discard_hand())
    _sync_slot_from_player(slot)

    next_slot = _next_slot(room, slot)
    battle.active_user_id = next_slot.user_id
    battle.turn_count += 1
    battle.cards_played_this_turn = 0
    battle.card_play_counts_this_turn = {}

    logs.extend(_start_turn_for_slot(
        next_slot,
        bonus_energy=int(rules.forced_turn_bonus) if forced else 0
    ))
    logs.append("")
    logs.append("轮到 {}。".format(next_slot.label()))
    logs.append(format_room(room, viewer_user_id=next_slot.user_id))
    return logs


def end_turn(room, user_id):
    if room.status != PVP_STATUS_BATTLE or room.battle is None:
        return "当前 PVP 房间不在战斗中。"
    slot = _active_slot(room)
    if slot is None or str(slot.user_id) != str(user_id):
        return "还没轮到你结束回合。当前行动者：{}。".format(room.battle.active_user_id)
    return "\n".join(_end_active_turn(room, forced=False))


def finish_battle(room, user_id):
    if room.status != PVP_STATUS_BATTLE or room.battle is None:
        return "当前 PVP 房间不在战斗中。"
    if room.get_player(user_id) is None:
        return "只有参战者可以结束 PVP 战斗。"
    room.battle.battle_over = True
    room.status = PVP_STATUS_COMPLETE
    return "PVP 战斗已由 {} 结束。胜负与剧情结果请玩家自行结算。".format(user_id)


def _format_slot_line(slot, viewer_user_id=None):
    player = slot.player_state
    if player is None:
        return "{} HP：{}/{} 牌库：{} 遗物：{}".format(
            slot.label(),
            slot.hp,
            slot.max_hp,
            len(slot.master_deck),
            len(slot.relics),
        )
    return "{} HP：{}/{} 费用：{}/{} 格挡：{} 手牌：{} 抽/弃/耗：{}/{}/{} 过热：{} 状态：{}".format(
        slot.label(),
        player.hp,
        player.max_hp,
        player.cost,
        player.max_cost,
        player.block,
        len(player.hand),
        len(player.draw_pile),
        len(player.discard_pile),
        len(player.exhaust_pile),
        len(slot.overheated_cards),
        get_status_display_text(player.statuses),
    )


def _format_relics(relics):
    if not relics:
        return "无"
    return "，".join(format_relic_display_name(relic) for relic in relics)


def _format_rule_summary(room):
    rules = _rules(room)
    return "环境规则：基础 {} 费；每回合第 {} 张牌完整结算后强制换人；被强制换到的一方本回合 +{} 费；单张牌第 {} 次起过热；胜负由玩家自行判定。".format(
        int(rules.base_cost),
        int(rules.max_cards_per_turn),
        int(rules.forced_turn_bonus),
        int(rules.overheat_threshold) + 1,
    )


def format_lobby(room):
    lines = ["=== PVP 演绎房 ===", "状态：大厅", "房主：{}".format(room.host_user_id)]
    lines.append(_format_rule_summary(room))
    if not room.players:
        lines.append("玩家：无")
    else:
        lines.append("玩家：")
        for index, slot in enumerate(room.players):
            lines.append("[{}] {}".format(index, _format_slot_line(slot)))
            lines.append("    遗物：{}".format(_format_relics(slot.relics)))
    lines.append("")
    lines.append("使用 /card pvp join [角色编号] 加入/换角色；使用 /card pvp ctrl 配置资源和规则。")
    lines.append("房主使用 /card pvp start 开战；PVP 专用控制台开战后仍可用。")
    return "\n".join(lines)


def format_battle(room, viewer_user_id=None):
    battle = room.battle
    if battle is None:
        return format_lobby(room)
    lines = ["=== PVP 战斗 ==="]
    lines.append("行动序号：{}；当前行动：{}；本回合出牌：{}/{}".format(
        battle.turn_count,
        battle.active_user_id,
        battle.cards_played_this_turn,
        int(_rules(room).max_cards_per_turn),
    ))
    if battle.pending_attacks:
        hidden_count = len(battle.pending_attacks)
        mine = [
            item for item in battle.pending_attacks
            if str(item.get("target_user_id")) == str(viewer_user_id)
            or str(item.get("source_user_id")) == str(viewer_user_id)
        ]
        lines.append("待结算攻击：{} 段；与你相关：{} 段。".format(hidden_count, len(mine)))
    lines.append("玩家：")
    for index, slot in enumerate(room.players):
        lines.append("[{}] {}".format(index, _format_slot_line(slot, viewer_user_id=viewer_user_id)))

    viewer = room.get_player(viewer_user_id) if viewer_user_id is not None else None
    if viewer is not None and viewer.player_state is not None:
        lines.append("")
        lines.append("你的手牌：")
        lines.append(viewer.player_state.hand_text(None))
    else:
        lines.append("")
        lines.append("手牌详情仅对参战者自身显示。")
    return "\n".join(lines)


def format_room(room, viewer_user_id=None):
    if room.status == PVP_STATUS_LOBBY:
        return format_lobby(room)
    if room.status == PVP_STATUS_BATTLE:
        return format_battle(room, viewer_user_id=viewer_user_id)
    if room.status == PVP_STATUS_COMPLETE:
        return "PVP 战斗已结束。胜负与剧情结果由玩家自行结算。"
    return "未知 PVP 房间状态：{}。".format(room.status)
