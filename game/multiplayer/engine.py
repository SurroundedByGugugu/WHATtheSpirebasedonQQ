# -*- coding: utf-8 -*-

import random

from data.card.AAAregistry import create_card, create_deck
from data.character.AAAregistry import create_character
from data.enemy.AAAregistry import create_enemy
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from data.content_gate import filter_relic_ids
from data.route.encounters import (
    STARTING_ENCOUNTER_POOL_1_1,
    filter_encounter_pool,
    pick_weighted,
    resolve_encounter_enemy_ids,
)
from game.constants import KEYWORD_EXHAUST
from game.display_names import format_potion_display_name, format_relic_display_name
from game.player_state import PlayerState
from game.reward import (
    RELIC_REWARD_POOL,
    FALLBACK_RELIC_ID,
    roll_gold_reward,
    roll_potion_id_by_rarity,
)
from game.relic_logic.run_relic_utils import is_relic_available_by_floor
from game.multiplayer.state import (
    MultiBattleState,
    MultiPlayerSlot,
    MultiRewardState,
    ROOM_STATUS_BATTLE,
    ROOM_STATUS_COMPLETE,
    ROOM_STATUS_DEFEAT,
    ROOM_STATUS_LOBBY,
    ROOM_STATUS_REWARD,
)


def create_player_slot(user_id, character_id):
    character = create_character(character_id)
    max_potion_slots = int(getattr(character, "max_potion_slots", 3) or 3)
    starting_potions = [
        create_potion(potion_id)
        for potion_id in getattr(character, "starting_potion_ids", []) or []
    ][:max_potion_slots]
    return MultiPlayerSlot(
        user_id=str(user_id),
        character_id=character.character_id,
        character_name=character.name,
        max_hp=character.max_hp,
        hp=character.max_hp,
        max_cost=character.max_cost,
        gold=int(getattr(character, "starting_gold", 0) or 0),
        max_potion_slots=max_potion_slots,
        master_deck=create_deck(getattr(character, "starting_deck_ids", []) or []),
        relics=[
            create_relic(relic_id)
            for relic_id in getattr(character, "starting_relic_ids", []) or []
        ],
        potions=starting_potions,
    )


def _make_player_state(slot):
    player = PlayerState(
        character_id=slot.character_id,
        name=slot.character_name,
        max_hp=slot.max_hp,
        hp=slot.hp,
        max_cost=slot.max_cost,
        cost=slot.max_cost,
        relics=slot.relics,
        max_potion_slots=slot.max_potion_slots,
        potions=slot.potions,
        draw_pile=list(slot.master_deck),
        discard_pile=[],
        exhaust_pile=[],
        hand=[],
    )
    return player


def _sync_slot_from_player(slot):
    player = slot.player_state
    if player is None:
        return
    slot.hp = int(getattr(player, "hp", slot.hp) or 0)
    slot.max_hp = int(getattr(player, "max_hp", slot.max_hp) or 0)
    slot.relics = getattr(player, "relics", []) or []
    slot.potions = getattr(player, "potions", []) or []


def _status_value(entity, key):
    statuses = getattr(entity, "statuses", None)
    if statuses is None:
        return 0
    try:
        return int(statuses.get(key) or 0)
    except Exception:
        return 0


def _scale_enemy_hp(enemy, player_count):
    multiplier = max(1, int(player_count))
    old_max_hp = int(getattr(enemy, "max_hp", 0) or 0)
    old_hp = int(getattr(enemy, "hp", old_max_hp) or old_max_hp)
    enemy.max_hp = old_max_hp * multiplier
    enemy.hp = old_hp * multiplier


def start_test_battle(room):
    if room.status != ROOM_STATUS_LOBBY:
        return "当前多人房间已经不在大厅。"
    if not room.players:
        return "当前多人房间还没有玩家。"

    rng = random.Random(int(room.seed))
    encounter_id = pick_weighted(filter_encounter_pool(STARTING_ENCOUNTER_POOL_1_1), rng)
    enemy_ids = resolve_encounter_enemy_ids(encounter_id, rng)
    enemies = [create_enemy(enemy_id) for enemy_id in enemy_ids]
    for enemy in enemies:
        _scale_enemy_hp(enemy, room.player_count())

    for slot in room.players:
        player = _make_player_state(slot)
        rng.shuffle(player.draw_pile)
        player.draw_cards(5, game_state=None, draw_source="multi_opening")
        slot.player_state = player
        slot.ended_turn = False

    battle = MultiBattleState(
        session_id=room.session_id,
        encounter_id=encounter_id,
        enemies=enemies,
        active_user_id=room.players[0].user_id,
        turn_count=1,
    )
    room.battle = battle
    room.status = ROOM_STATUS_BATTLE

    return "\n".join([
        "多人测试房间开战。",
        "遭遇：{}。敌人 HP 已按人数 x{}。".format(encounter_id, room.player_count()),
        "",
        format_battle(room),
    ])


def _active_slot(room):
    battle = room.battle
    if battle is None:
        return None
    return room.get_player(battle.active_user_id)


def _first_alive_enemy_index(battle):
    for index, enemy in enumerate(battle.enemies):
        if enemy.is_alive():
            return index
    return None


def _get_enemy(battle, target_index):
    if target_index is None:
        target_index = _first_alive_enemy_index(battle)
    if target_index is None:
        return None
    if target_index < 0 or target_index >= len(battle.enemies):
        return None
    enemy = battle.enemies[target_index]
    if not enemy.is_alive():
        return None
    return enemy


def _card_cost(player, card):
    raw_cost = getattr(card, "cost", 0)
    if str(raw_cost).upper() == "X":
        return max(0, int(getattr(player, "cost", 0) or 0))
    try:
        return int(raw_cost)
    except (TypeError, ValueError):
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


def _deal_damage(source, target, amount):
    amount = max(0, int(amount))
    if target is None:
        return "伤害目标无效。"
    return target.take_damage(amount)


def _effect_targets(room, player, effect, selected_enemy):
    target_key = effect.get("target", getattr(effect, "target", "self"))
    battle = room.battle
    if target_key in ("self", "player"):
        return [player]
    if target_key in ("selected_enemy", "enemy"):
        return [selected_enemy] if selected_enemy is not None else []
    if target_key == "all_enemies":
        return battle.get_alive_enemies()
    if target_key == "random_enemy":
        alive = battle.get_alive_enemies()
        if not alive:
            return []
        rng = random.Random(int(room.seed) + int(battle.turn_count) * 3001 + len(alive))
        return [rng.choice(alive)]
    return [player]


def _apply_card_effect(room, slot, card, effect, selected_enemy):
    player = slot.player_state
    op = effect.get("op")
    logs = []

    if op == "deal_damage":
        targets = _effect_targets(room, player, effect, selected_enemy)
        for target in targets:
            amount = _resolve_amount(
                player=player,
                target=target,
                card=card,
                spec=effect.get("amount", 0),
                modifier_profile="attack_damage",
            )
            logs.append(_deal_damage(player, target, amount))
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
        logs.extend(player.draw_cards(amount, game_state=None, draw_source=getattr(card, "card_id", "multi_card")))
        return logs

    if op == "gain_energy":
        amount = _resolve_amount(player, player, card, effect.get("amount", 0))
        player.cost = int(getattr(player, "cost", 0) or 0) + amount
        logs.append("{} 获得 {} 点能量。当前费用：{}。".format(player.name, amount, player.cost))
        return logs

    if op in ("gain_status", "apply_status"):
        status_key = effect.get("status", "")
        amount = _resolve_amount(player, selected_enemy, card, effect.get("amount", 0))
        targets = _effect_targets(room, player, effect, selected_enemy)
        for target in targets:
            current = target.gain_status(status_key, amount)
            logs.append("{} 获得 {} 点{}。当前：{}。".format(
                target.name,
                amount,
                status_key,
                current,
            ))
        return logs

    logs.append("多人测试房暂未处理卡牌效果：{}。".format(op))
    return logs


def play_card(room, user_id, hand_index, target_index=None):
    if room.status != ROOM_STATUS_BATTLE or room.battle is None:
        return "当前多人房间不在战斗中。"
    battle = room.battle
    slot = _active_slot(room)
    if slot is None or str(slot.user_id) != str(user_id):
        return "还没轮到你行动。当前行动者：{}。".format(battle.active_user_id)
    player = slot.player_state
    if player is None or not player.is_alive():
        return "当前行动者已经无法行动。"
    if hand_index < 0 or hand_index >= len(player.hand):
        return "手牌编号无效。"

    card = player.hand[hand_index]
    cost = _card_cost(player, card)
    if cost > int(getattr(player, "cost", 0) or 0):
        return "费用不足：需要 {}，当前 {}。".format(cost, player.cost)

    selected_enemy = None
    if getattr(card, "target", "") == "enemy":
        selected_enemy = _get_enemy(battle, target_index)
        if selected_enemy is None:
            return "目标敌人编号无效。"
    elif target_index is not None:
        selected_enemy = _get_enemy(battle, target_index)

    player.cost -= cost
    player.hand.pop(hand_index)
    logs = ["{} 打出【{}】。".format(slot.label(), getattr(card, "name", "未知卡牌"))]

    for effect in getattr(card, "effects", []) or []:
        logs.extend(_apply_card_effect(room, slot, card, effect, selected_enemy))

    if card.has_keyword(KEYWORD_EXHAUST):
        player.exhaust_pile.append(card)
        logs.append("【{}】进入消耗堆。".format(card.name))
    else:
        player.discard_pile.append(card)

    _sync_slot_from_player(slot)
    result = _check_battle_result(room)
    if result:
        logs.append("")
        logs.append(result)
    else:
        logs.append("")
        logs.append(format_battle(room))
    return "\n".join(logs)


def _next_living_unended_slot(room, after_user_id=None):
    players = room.players
    if not players:
        return None
    start = 0
    if after_user_id is not None:
        for index, slot in enumerate(players):
            if str(slot.user_id) == str(after_user_id):
                start = index + 1
                break
    for offset in range(len(players)):
        slot = players[(start + offset) % len(players)]
        if slot.is_alive() and not slot.ended_turn:
            return slot
    return None


def _start_player_turn(slot):
    player = slot.player_state
    if player is None or not player.is_alive():
        return []
    logs = player.start_turn(game_state=None)
    draw_count = max(0, 5 - len(player.hand))
    if draw_count:
        logs.extend(player.draw_cards(draw_count, game_state=None, draw_source="multi_turn_start"))
    return logs


def end_player_turn(room, user_id):
    if room.status != ROOM_STATUS_BATTLE or room.battle is None:
        return "当前多人房间不在战斗中。"
    battle = room.battle
    slot = _active_slot(room)
    if slot is None or str(slot.user_id) != str(user_id):
        return "还没轮到你结束回合。当前行动者：{}。".format(battle.active_user_id)
    player = slot.player_state
    logs = ["{} 结束回合。".format(slot.label())]
    if player is not None:
        logs.append(player.discard_hand())
    slot.ended_turn = True
    _sync_slot_from_player(slot)

    next_slot = _next_living_unended_slot(room, after_user_id=slot.user_id)
    if next_slot is not None:
        battle.active_user_id = next_slot.user_id
        logs.append("轮到 {}。".format(next_slot.label()))
        logs.append("")
        logs.append(format_battle(room))
        return "\n".join(logs)

    logs.append("")
    logs.extend(_process_enemy_turn(room))
    result = _check_battle_result(room)
    if result:
        logs.append("")
        logs.append(result)
        return "\n".join(logs)

    battle.turn_count += 1
    for player_slot in room.players:
        if player_slot.is_alive():
            player_slot.ended_turn = False
            logs.extend(_start_player_turn(player_slot))
            _sync_slot_from_player(player_slot)
    next_slot = _next_living_unended_slot(room)
    if next_slot is not None:
        battle.active_user_id = next_slot.user_id
        logs.append("")
        logs.append("第 {} 回合开始。轮到 {}。".format(battle.turn_count, next_slot.label()))
        logs.append(format_battle(room))
    return "\n".join(logs)


def _enemy_attack_amount(enemy, target, base_amount):
    amount = int(base_amount)
    amount += _status_value(enemy, "strength")
    if _status_value(enemy, "weak") > 0:
        amount = int(amount * 0.75)
    if _status_value(target, "vulnerable") > 0:
        amount = int(amount * 1.5)
    return max(0, amount)


def _process_enemy_action(room, enemy, action):
    op = action.get("op")
    logs = []

    message = action.get("message", "")
    if message:
        logs.append("{}：{}".format(enemy.name, message))

    if op == "enemy_multi_action":
        for child in action.get("actions", []) or []:
            logs.extend(_process_enemy_action(room, enemy, child))
        return logs

    if op == "enemy_attack":
        base_damage = int(action.get("damage", 0) or 0)
        for slot in room.living_players():
            player = slot.player_state
            amount = _enemy_attack_amount(enemy, player, base_damage)
            logs.append("{} -> {}：{}".format(
                enemy.name,
                slot.label(),
                player.take_damage(amount),
            ))
            _sync_slot_from_player(slot)
        return logs

    if op == "enemy_gain_block":
        block = int(action.get("block", 0) or 0) + _status_value(enemy, "dexterity")
        logs.append(_gain_block(enemy, block))
        return logs

    if op == "enemy_gain_status":
        status_key = action.get("status", "")
        amount = int(action.get("amount", 0) or 0)
        if action.get("target") == "self":
            current = enemy.gain_status(status_key, amount)
            logs.append("{} 获得 {} 点{}。当前：{}。".format(enemy.name, amount, status_key, current))
        else:
            for slot in room.living_players():
                current = slot.player_state.gain_status(status_key, amount)
                logs.append("{} 获得 {} 点{}。当前：{}。".format(
                    slot.label(),
                    amount,
                    status_key,
                    current,
                ))
        return logs

    if op in ("enemy_add_card_to_discard", "enemy_add_card_to_draw", "enemy_add_card_to_hand"):
        card_id = action.get("card_id", "")
        count = int(action.get("count", 1) or 1)
        pile_name = {
            "enemy_add_card_to_discard": "discard_pile",
            "enemy_add_card_to_draw": "draw_pile",
            "enemy_add_card_to_hand": "hand",
        }.get(op, "discard_pile")
        for slot in room.living_players():
            pile = getattr(slot.player_state, pile_name)
            for _ in range(count):
                pile.append(create_card(card_id))
            logs.append("{} 的{}加入 {} 张{}。".format(
                slot.label(),
                {
                    "discard_pile": "弃牌堆",
                    "draw_pile": "抽牌堆",
                    "hand": "手牌",
                }.get(pile_name, pile_name),
                count,
                card_id,
            ))
            if (
                pile_name == "draw_pile"
                and bool(action.get("shuffle_draw_pile", False))
            ):
                random.shuffle(pile)
        return logs

    if op == "enemy_wait":
        logs.append("{} 正在蓄力。".format(enemy.name))
        return logs

    if op == "enemy_escape":
        enemy.hp = 0
        logs.append("{} 逃离了战斗。".format(enemy.name))
        return logs

    logs.append("多人测试房暂未处理敌人行动：{}。".format(op))
    return logs


def _process_enemy_turn(room):
    battle = room.battle
    logs = ["敌人回合。"]
    for enemy in list(battle.enemies):
        if not enemy.is_alive():
            continue
        old_block = enemy.clear_block()
        if old_block > 0:
            logs.append("{} 的 {} 点格挡消失。".format(enemy.name, old_block))
        action_result = enemy.act()
        logs.extend(action_result.logs)
        logs.extend(_process_enemy_action(room, enemy, action_result.action))
    return logs


def _check_battle_result(room):
    battle = room.battle
    if battle is None or battle.battle_over:
        return ""
    if battle.is_all_enemies_dead():
        battle.battle_over = True
        battle.victory = True
        room.status = ROOM_STATUS_REWARD
        room.reward = create_reward(room)
        return "\n".join([
            "战斗胜利，进入多人奖励选择。",
            "",
            format_reward(room),
        ])
    if not room.living_players():
        battle.battle_over = True
        battle.victory = False
        room.status = ROOM_STATUS_DEFEAT
        return "全员倒下，多人测试房间失败。"
    return ""


def _fake_run_for_character(character_id):
    class FakeRunState(object):
        pass
    fake = FakeRunState()
    fake.character_id = character_id
    fake.relics = []
    fake.completed_node_ids = []
    fake.reward_count = 1
    return fake


def _character_counts(room):
    result = {}
    for slot in room.players:
        result[slot.character_id] = result.get(slot.character_id, 0) + 1
    return result


def _owned_relic_ids(room):
    result = set()
    for slot in room.players:
        for relic in getattr(slot, "relics", []) or []:
            result.add(getattr(relic, "relic_id", ""))
    return result


def _multi_relic_candidates(room):
    character_counts = _character_counts(room)
    owned = _owned_relic_ids(room)
    result = []
    fake = _fake_run_for_character("")
    for relic_id in filter_relic_ids(RELIC_REWARD_POOL):
        if relic_id == FALLBACK_RELIC_ID:
            continue
        relic = create_relic(relic_id)
        if getattr(relic, "quantity", "") in ("event", "shop", "test", "starting", "boss"):
            continue
        if not is_relic_available_by_floor(fake, relic):
            continue
        owner = getattr(relic, "owner_character_id", "")
        if owner and owner not in character_counts:
            continue
        if not getattr(relic, "allow_duplicate", False) and relic_id in owned:
            continue
        result.append(relic_id)
    return result


def _roll_multi_relic_options(room, rng, count):
    candidates = _multi_relic_candidates(room)
    character_counts = _character_counts(room)
    selected = []
    owner_selected_counts = {}
    while candidates and len(selected) < count:
        relic_id = rng.choice(candidates)
        candidates.remove(relic_id)
        relic = create_relic(relic_id)
        owner = getattr(relic, "owner_character_id", "")
        if owner:
            used = owner_selected_counts.get(owner, 0)
            if used >= character_counts.get(owner, 0):
                continue
            owner_selected_counts[owner] = used + 1
        selected.append(relic)
    if not selected:
        selected.append(create_relic(FALLBACK_RELIC_ID))
    return selected


def create_reward(room):
    rng = random.Random(int(room.seed) + 91001)
    gold_amount = roll_gold_reward("normal_enemy", rng)
    potion_by_user_id = {}
    for slot in room.players:
        slot.gold += gold_amount
        potion_id = roll_potion_id_by_rarity(
            rng,
            run_state=_fake_run_for_character(slot.character_id),
            include_event=False,
        )
        if potion_id is not None:
            potion = create_potion(potion_id)
            potion_by_user_id[slot.user_id] = potion
            if len(slot.potions) < slot.max_potion_slots:
                slot.potions.append(potion)

    return MultiRewardState(
        gold_amount=gold_amount,
        potion_by_user_id=potion_by_user_id,
        relic_options=_roll_multi_relic_options(room, rng, room.player_count()),
    )


def choose_relic(room, user_id, choice_index):
    if room.status != ROOM_STATUS_REWARD or room.reward is None:
        return "当前多人房间不在奖励选择阶段。"
    slot = room.get_player(user_id)
    if slot is None:
        return "你不在当前多人房间中。"
    reward = room.reward
    if reward.resolved:
        return format_reward(room)

    if choice_index is not None:
        if choice_index < 0 or choice_index >= len(reward.relic_options):
            return "遗物编号无效。"
    reward.relic_choices[str(user_id)] = choice_index

    living_user_ids = [slot.user_id for slot in room.living_players()]
    missing = [
        slot.label()
        for slot in room.living_players()
        if slot.user_id not in reward.relic_choices
    ]
    if missing:
        return "\n".join([
            "{} 已选择{}。".format(slot.label(), "跳过" if choice_index is None else "遗物 [{}]".format(choice_index)),
            "等待其他玩家决定：{}。".format("，".join(missing)),
            "",
            format_reward(room),
        ])

    logs = _resolve_relic_choices(room, living_user_ids)
    room.status = ROOM_STATUS_COMPLETE
    return "\n".join(logs + ["", format_reward(room)])


def _resolve_relic_choices(room, user_ids):
    reward = room.reward
    rng = random.Random(int(room.seed) + 92001)
    reward.resolved = True
    logs = ["多人遗物选择结算："]

    by_choice = {}
    for user_id in user_ids:
        choice = reward.relic_choices.get(user_id)
        if choice is None:
            logs.append("{} 跳过遗物。".format(room.get_player(user_id).label()))
            continue
        by_choice.setdefault(choice, []).append(user_id)

    for choice_index, claimers in sorted(by_choice.items()):
        relic = reward.relic_options[choice_index]
        if len(claimers) == 1:
            winner_id = claimers[0]
            roll_lines = []
        else:
            rolls = []
            for user_id in claimers:
                rolls.append((rng.randint(1, 100), user_id))
            rolls.sort(key=lambda item: (item[0], item[1]))
            winner_id = rolls[0][1]
            roll_lines = [
                "{} d100={}".format(room.get_player(user_id).label(), roll)
                for roll, user_id in rolls
            ]
        winner = room.get_player(winner_id)
        winner.relics.append(relic)
        if winner.player_state is not None:
            winner.player_state.relics = winner.relics
        if roll_lines:
            logs.append("争夺 {}：{}；{} 获得。".format(
                format_relic_display_name(relic),
                "，".join(roll_lines),
                winner.label(),
            ))
        else:
            logs.append("{} 获得 {}。".format(winner.label(), format_relic_display_name(relic)))

    reward.resolution_logs = list(logs)
    return logs


def _format_player_line(slot):
    player = slot.player_state
    if player is None:
        return "{} HP：{}/{} 金币：{} 遗物：{} 药水：{}".format(
            slot.label(),
            slot.hp,
            slot.max_hp,
            slot.gold,
            len(slot.relics),
            len(slot.potions),
        )
    return "{} HP：{}/{} 费用：{}/{} 格挡：{} 金币：{} 手牌：{}".format(
        slot.label(),
        player.hp,
        player.max_hp,
        player.cost,
        player.max_cost,
        player.block,
        slot.gold,
        len(player.hand),
    )


def format_lobby(room):
    lines = ["=== 多人测试房间 ===", "状态：大厅", "房主：{}".format(room.host_user_id)]
    if not room.players:
        lines.append("玩家：无")
    else:
        lines.append("玩家：")
        for index, slot in enumerate(room.players):
            lines.append("[{}] {}".format(index, _format_player_line(slot)))
    lines.append("")
    lines.append("使用 /card multi join [角色编号] 加入，/card multi start 开战。")
    return "\n".join(lines)


def format_battle(room):
    battle = room.battle
    if battle is None:
        return format_lobby(room)
    lines = ["=== 多人战斗 ==="]
    lines.append("回合：{}；当前行动：{}".format(battle.turn_count, battle.active_user_id))
    lines.append("玩家：")
    for slot in room.players:
        lines.append("- {}".format(_format_player_line(slot)))
    lines.append("")
    lines.append("敌人：")
    for index, enemy in enumerate(battle.enemies):
        lines.append("[{}] {}".format(index, enemy.status_text(None)))
    active = _active_slot(room)
    if active is not None and active.player_state is not None:
        lines.append("")
        lines.append("当前行动者手牌：")
        lines.append(active.player_state.hand_text(None))
    return "\n".join(lines)


def format_reward(room):
    reward = room.reward
    if reward is None:
        return "当前没有多人奖励。"
    lines = ["=== 多人奖励 ==="]
    lines.append("每名玩家获得金币：{}。".format(reward.gold_amount))
    lines.append("个人药水：")
    for slot in room.players:
        potion = reward.potion_by_user_id.get(slot.user_id)
        if potion is None:
            lines.append("- {}：无".format(slot.label()))
        else:
            lines.append("- {}：{}".format(slot.label(), format_potion_display_name(potion)))
    lines.append("")
    lines.append("遗物池：")
    for index, relic in enumerate(reward.relic_options):
        owner = getattr(relic, "owner_character_id", "")
        owner_text = "；所属 {}".format(owner) if owner else ""
        lines.append("[{}] {}{}".format(index, relic.summary_text(), owner_text))
    lines.append("")
    if reward.resolved:
        lines.append("遗物选择已结算。")
        if reward.resolution_logs:
            lines.extend(reward.resolution_logs)
    else:
        lines.append("使用 /card multi relic 0 选择遗物；/card multi relic skip 跳过。")
        if reward.relic_choices:
            chosen = []
            for user_id, choice in reward.relic_choices.items():
                slot = room.get_player(user_id)
                label = slot.label() if slot is not None else user_id
                chosen.append("{}={}".format(label, "skip" if choice is None else choice))
            lines.append("已选择：{}。".format("，".join(chosen)))
    return "\n".join(lines)


def format_room(room):
    if room.status == ROOM_STATUS_LOBBY:
        return format_lobby(room)
    if room.status == ROOM_STATUS_BATTLE:
        return format_battle(room)
    if room.status in (ROOM_STATUS_REWARD, ROOM_STATUS_COMPLETE):
        return format_reward(room)
    if room.status == ROOM_STATUS_DEFEAT:
        return "多人测试房间已失败。"
    return "未知多人房间状态：{}。".format(room.status)

