# -*- coding: utf-8 -*-

from game.modifiers import apply_modifier_profile, get_status_value
from game.status.status_defs import get_status_name
from game.damage import deal_damage
import random

from game.zone.zone_utils import (
    get_effective_zone_element_for_card,
    get_zone_replay_extra,
    apply_zone_source_hp_loss_if_needed,
    apply_water_zone_regeneration_on_card_play,
    record_player_card_played_this_turn
)
from game.block import gain_block_without_modifiers, gain_block
from game.pending_choice import PendingChoice, set_pending_choice


EFFECT_HANDLERS = {}


def register_effect(op):
    def decorator(func):
        EFFECT_HANDLERS[op] = func
        return func
    return decorator


def is_player_attack_card(card):
    return getattr(card, "card_type", "") == "attack"


def should_apply_abyssal_form_effect(game_state, card, zone_element=""):
    player = getattr(game_state, "player", None)
    if player is None:
        return False
    if not is_player_attack_card(card):
        return False
    if get_status_value(player, "abyssal_form") <= 0:
        return False
    # 深渊形态现在只强化晶属性攻击牌。(热修复是否只强化shade改这里)
    card_element = str(getattr(card, "attack_element", "") or "").strip().lower()
    if card_element != "crystal":
        return False
    # 已经通过真实阴 Zone / 以太介质 / 薄雾等吃到阴 Zone 时，不重复叠加深渊形态的虚拟极阴效果。
    # 注意：真实晶 Zone 不会阻止深渊形态；晶攻击牌可以同时吃晶 Zone 和深渊形态的虚拟极阴。
    if str(zone_element).strip().lower() == "shade":
        return False

    return True


def apply_abyssal_form_amount_modifier(value, game_state, card, zone_element=""):
    if not should_apply_abyssal_form_effect(game_state, card, zone_element):
        return int(value)
    # 按当前极阴 Zone 的实际实现折算：基础数值乘区 1.3 × 阴特殊效果 2.0。
    return int(int(value) * 1.3 * 2.0)


def apply_abyssal_form_hp_loss_if_needed(game_state, card, zone_element, logs):
    if not should_apply_abyssal_form_effect(game_state, card, zone_element):
        return

    logs.append("深渊形态使【{}】额外视为有极阴 Zone 效果。".format(card.name))
    apply_zone_source_hp_loss_if_needed(
        game_state=game_state,
        source=game_state.player,
        zone_element="shade",
        logs=logs,
        label="深渊形态",
        card=card,
        count_as_player_self_action_hp_loss=True
    )

def iter_player_cards_by_piles(player, pile_names):
    """
    按指定牌堆遍历玩家当前战斗中的卡牌。

    pile_names 示例：
    ["draw_pile", "hand", "discard_pile"]
    """
    for pile_name in pile_names:
        pile = getattr(player, pile_name, [])
        for pile_card in pile:
            yield pile_card

def count_cards_by_name_contains(game_state, card, rule):
    """
    统计当前战斗中名称包含指定文本的牌数量。

    rule 示例：
    {
        "name_contains": "打击",
        "piles": ["draw_pile", "hand", "discard_pile"],
        "include_self": True
    }

    include_self=True 用于处理：
    play_card() 会先把正在打出的牌从 hand 移除，再执行效果。
    如果不额外计入 self，完美打击不会为自身加伤。
    """
    player = game_state.player
    name_contains = rule.get("name_contains", "")
    if not name_contains:
        return 0
    pile_names = rule.get("piles", ["draw_pile", "hand", "discard_pile"])
    count = 0
    found_self_in_piles = False
    for pile_card in iter_player_cards_by_piles(player, pile_names):
        if pile_card is card:
            found_self_in_piles = True
        if name_contains in getattr(pile_card, "name", ""):
            count += 1
    if rule.get("include_self", False):
        if not found_self_in_piles and name_contains in getattr(card, "name", ""):
            count += 1
    return count

def move_specific_draw_card_to_hand_or_discard(game_state, card, logs, draw_source="special_draw"):
    player = game_state.player

    if card not in player.draw_pile:
        return

    player.draw_pile.remove(card)

    if player.is_hand_full():
        player.discard_pile.append(card)
        logs.append("抽到【{}】，但手牌已满，进入弃牌堆。".format(card.name))
        return

    player.hand.append(card)
    logs.append("抽到【{}】。".format(card.name))

    try:
        from data.card.enchantment_rules import get_card_enchantment_stacks

        index_plus = get_card_enchantment_stacks(card, "index_shade_plus")
        if index_plus > 0:
            player.cost += index_plus
            logs.append("【索引·阴+】触发：抽到【{}】，获得 {} 点费用。当前费用：{}。".format(
                card.name,
                index_plus,
                player.cost
            ))
    except Exception:
        pass

    if getattr(card, "card_id", "") == "card.status.void":
        old_cost = int(getattr(player, "cost", 0))
        player.cost = max(0, old_cost - 1)
        logs.append("【虚空】触发：失去 1 点能量。当前费用：{}。".format(player.cost))

    from game.battle_context import BattleContext
    from game.event_bus import dispatch_event
    from game.constants import EVENT_DRAW_CARD_AFTER

    context = BattleContext(
        game_state=game_state,
        player=player,
        source=player,
        card=card,
        extra={
            "drawn_card": card,
            "draw_source": draw_source
        }
    )

    logs.extend(dispatch_event(
        game_state,
        EVENT_DRAW_CARD_AFTER,
        context
    ))

    from game.zone.resonance import trigger_resonance_on_draw
    logs.extend(trigger_resonance_on_draw(
        game_state=game_state,
        card=card
    ))
    
def get_real_active_shade_zone_info(game_state):
    zone = getattr(game_state, "active_zone", None)
    if zone is None:
        return False, False
    try:
        if zone.is_expired():
            return False, False
    except Exception:
        pass
    if str(getattr(zone, "element", "") or "").strip().lower() != "shade":
        return False, False
    return True, bool(getattr(zone, "is_extreme", False))


def is_real_active_shade_zone(game_state):
    active, _ = get_real_active_shade_zone_info(game_state)
    return active


def lose_1_hp_for_shade_bonus(game_state, card, logs, label):
    player = game_state.player

    logs.append("【{}】触发阴 Zone 额外效果：{} 失去 1 点生命。".format(
        card.name,
        player.name
    ))

    from game.damage import deal_damage

    logs.extend(deal_damage(
        game_state=game_state,
        source=player,
        target=player,
        amount=1,
        damage_kind="card_hp_loss",
        card=card,
        is_reaction_damage=False,
        ignore_block=True,
        count_as_player_self_action_hp_loss=True
    ))

def resolve_amount(
    game_state,
    card,
    amount_spec,
    target=None,
    source=None,
    damage_source=None,
    block_source=None,
    effect_context=None,
    attack_type="",
    attack_element=""
):
    """
    解析卡牌效果中的数值。

    支持：
    1. 直接整数：
       "amount": 6

    2. 从 card_vars 取值：
       "amount": {"var": "block"}

    3. 基础值 + 修正：
       "amount": {
           "base_var": "damage",
           "modifier_profile": "attack_damage"
       }

    4. 根据状态缩放：
       "amount": {
           "base_var": "damage",
           "scaling": [
               {"stat": "strength", "multiplier_var": "strength_scale"}
           ]
       }
    """
    if isinstance(amount_spec, int):
        return amount_spec

    if amount_spec is None:
        return 0

    if source is None:
        source = game_state.player

    if effect_context is None:
        effect_context = {}

    if not isinstance(amount_spec, dict):
        return 0

    card_vars = getattr(card, "card_vars", None)

    if card_vars is None:
        card_vars = getattr(card, "effect_vars", {})

    value = 0

    base_var = amount_spec.get("base_var")
    if base_var:
        value += int(card_vars.get(base_var, 0))

    var_name = amount_spec.get("var")
    if var_name:
        value += int(card_vars.get(var_name, 0))

    if amount_spec.get("current_block", False):
        value += int(getattr(source, "block", 0))
    if amount_spec.get("draw_pile_count", False):
        player = getattr(game_state, "player", None)
        draw_pile = getattr(player, "draw_pile", []) if player is not None else []
        value += len(draw_pile)
    if amount_spec.get("player_self_action_hp_loss_total_this_battle", False):
        loss_total = int(getattr(
            game_state,
            "player_self_action_hp_loss_total_this_battle",
            0
        ))
        multiplier = int(amount_spec.get("multiplier", 1) or 1)
        multiplier_var = amount_spec.get("multiplier_var")
        if multiplier_var:
            multiplier = int(card_vars.get(multiplier_var, multiplier))
        value += loss_total * multiplier

    scaling_list = amount_spec.get("scaling", [])
    for scaling in scaling_list:
        stat = scaling.get("stat")
        multiplier_var = scaling.get("multiplier_var")

        if not stat or not multiplier_var:
            continue
        stat_value = get_status_value(source, stat)
        multiplier = int(card_vars.get(multiplier_var, 0))
        value += stat_value * multiplier

    name_count_bonus = amount_spec.get("name_count_bonus")
    if name_count_bonus:
        matched_count = count_cards_by_name_contains(
            game_state=game_state,
            card=card,
            rule=name_count_bonus
        )

        bonus_var = name_count_bonus.get("bonus_var")
        bonus = int(name_count_bonus.get("bonus", 0))

        if bonus_var:
            bonus = int(card_vars.get(bonus_var, 0))

        value += matched_count * bonus

    x_var_name = amount_spec.get("x_var")
    if x_var_name:
        x_value = int(effect_context.get(x_var_name, 0) or 0)
        x_multiplier = int(amount_spec.get("multiplier", 1) or 1)
        x_add = int(amount_spec.get("add", 0) or 0)
        value += x_value * x_multiplier + x_add

    context_var_name = amount_spec.get("context_var")
    if context_var_name:
        context_value = int(effect_context.get(context_var_name, 0) or 0)

        divisor = int(amount_spec.get("divisor", 1) or 1)
        if divisor != 1:
            context_value = int(context_value // divisor)

        multiplier = int(amount_spec.get("multiplier", 1) or 1)
        context_value = context_value * multiplier

        add_value = int(amount_spec.get("add", 0) or 0)
        add_var = amount_spec.get("add_var")
        if add_var:
            add_value += int(card_vars.get(add_var, 0) or 0)

        value += context_value + add_value

    x_conditional_var = amount_spec.get("x_conditional_var")
    if x_conditional_var:
        x_value = int(effect_context.get("x", 0))
        threshold = int(x_conditional_var.get("x_gte", 0))
        then_var = x_conditional_var.get("then_var")
        else_var = x_conditional_var.get("else_var")

        if x_value >= threshold:
            value += int(card_vars.get(then_var, 0))
        else:
            value += int(card_vars.get(else_var, 0))
    potion_amount_multiplier = float(effect_context.get("potion_amount_multiplier", 1.0) or 1.0)
    if potion_amount_multiplier != 1.0:
        value = int(value * potion_amount_multiplier)
    modifier_profile = amount_spec.get("modifier_profile")

    zone_element = ""
    if effect_context is not None:
        zone_element = effect_context.get("zone_element", "")

    value = apply_modifier_profile(
        value=value,
        modifier_profile=modifier_profile,
        game_state=game_state,
        source=source,
        target=target,
        card=card,
        damage_source=damage_source,
        block_source=block_source,
        attack_type=attack_type,
        attack_element=attack_element,
        zone_element=zone_element
    )

    if zone_element:
        from game.zone.zone_utils import apply_zone_amount_modifier
        value = apply_zone_amount_modifier(
            value=value,
            game_state=game_state,
            zone_element=zone_element
        )

    if modifier_profile == "attack_damage":
        value = apply_abyssal_form_amount_modifier(
            value=value,
            game_state=game_state,
            card=card,
            zone_element=zone_element
        )

    status_conditional_multiplier = amount_spec.get("status_conditional_multiplier")
    if status_conditional_multiplier:
        status_key = str(status_conditional_multiplier.get("status", "") or "")
        status_target_key = str(status_conditional_multiplier.get("target", "self") or "self")

        if status_target_key in ("self", "player"):
            status_target = source
        elif status_target_key in ("target", "selected_enemy", "enemy"):
            status_target = target
        else:
            status_target = source

        current_status = get_status_value(status_target, status_key)

        matched = True

        if "gt" in status_conditional_multiplier:
            matched = matched and current_status > int(status_conditional_multiplier.get("gt", 0))
        if "gte" in status_conditional_multiplier:
            matched = matched and current_status >= int(status_conditional_multiplier.get("gte", 0))
        if "lt" in status_conditional_multiplier:
            matched = matched and current_status < int(status_conditional_multiplier.get("lt", 0))
        if "lte" in status_conditional_multiplier:
            matched = matched and current_status <= int(status_conditional_multiplier.get("lte", 0))

        if matched:
            multiplier = float(status_conditional_multiplier.get("multiplier", 1.0) or 1.0)
            value = int(value * multiplier)
    status_step_multiplier = amount_spec.get("status_step_multiplier")
    if status_step_multiplier:
        status_key = str(status_step_multiplier.get("status", "") or "")
        status_target_key = str(status_step_multiplier.get("target", "self") or "self")

        if status_target_key in ("self", "player"):
            status_target = source
        elif status_target_key in ("target", "selected_enemy", "enemy"):
            status_target = target
        else:
            status_target = source

        current_status = get_status_value(status_target, status_key)
        step = int(status_step_multiplier.get("step", 1) or 1)

        if step > 0 and current_status > 0:
            step_count = current_status // step
            if step_count > 0:
                multiplier_per_step = float(status_step_multiplier.get("multiplier_per_step", 0.0) or 0.0)
                final_multiplier = 1.0 + step_count * multiplier_per_step
                value = int(value * final_multiplier)
    return int(value)

def is_enemy_selectable(enemy):
    if enemy is None:
        return False
    if not enemy.is_alive():
        return False
    if bool(getattr(enemy, "_unselectable", False)):
        return False
    return True


def get_target_enemy(game_state, target_index):
    enemies = game_state.enemies

    if target_index < 0 or target_index >= len(enemies):
        return None

    enemy = enemies[target_index]

    if not is_enemy_selectable(enemy):
        return None

    return enemy


def get_alive_enemies(game_state):
    alive_enemies = []

    for enemy in game_state.enemies:
        if is_enemy_selectable(enemy):
            alive_enemies.append(enemy)

    return alive_enemies

def get_effect_target_entity(game_state, target_key, target_index):
    if target_key in (None, "self"):
        return game_state.player
    if target_key in ("selected_enemy", "enemy"):
        return get_target_enemy(game_state, target_index)
    return None

def get_effect_attack_tags(card, effect):
    attack_type = effect.get("attack_type", getattr(card, "attack_type", ""))

    if "attack_element" in effect and str(effect.get("attack_element", "") or "").strip():
        attack_element = effect.get("attack_element", "")
    else:
        attack_element = getattr(card, "attack_element", "")

    return attack_type, attack_element

def get_effect_zone_element(game_state, card, effect, effect_context):
    from game.zone.zone_utils import get_effective_zone_element_for_card
    return get_effective_zone_element_for_card(
        game_state=game_state,
        card=card,
        effect=effect,
        effect_context=effect_context
    )

def make_zone_effect_context(effect_context, zone_element):
    if effect_context is None:
        effect_context = {}
    new_context = dict(effect_context)
    new_context["zone_element"] = zone_element
    return new_context

def resolve_effect_times(game_state, card, effect, effect_context):
    """
    解析效果重复次数。

    支持：
    "times": 3
    "times": {"var": "repeat"}
    "times": {"x_var": "x"}
    没写 times 时，兼容读取 count。
    都没写时，默认为 1。
    """
    times_spec = effect.get("times", None)

    if times_spec is None:
        times_spec = effect.get("count", 1)

    times = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=times_spec,
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context
    )

    return int(times)

def get_all_alive_enemies(game_state):
    return [enemy for enemy in game_state.enemies if is_enemy_selectable(enemy)]

def should_convert_enemy_target_to_all(game_state, zone_element, target_key):
    from game.zone.zone_utils import should_zone_thunder_make_all
    if target_key not in ("selected_enemy", "enemy", "random_enemy"):
        return False
    return should_zone_thunder_make_all(game_state, zone_element)

def deal_card_attack_damage_to_target(game_state, card, effect, target_entity, effect_context, attack_type, attack_element, zone_element, logs, prefix):
    from game.zone.zone_utils import apply_fire_zone_burn

    damage = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=game_state.player,
        target=target_entity,
        damage_source="played_card",
        effect_context=effect_context,
        attack_type=attack_type,
        attack_element=attack_element
    )

    if prefix:
        logs.append(prefix.format(
            card=card,
            target=target_entity,
            damage=damage
        ))

    logs.extend(deal_damage(
        game_state=game_state,
        source=game_state.player,
        target=target_entity,
        amount=damage,
        damage_kind="attack",
        card=card,
        attack_type=attack_type,
        attack_element=attack_element,
        zone_element=zone_element
    ))

    apply_fire_zone_burn(
        game_state=game_state,
        source=game_state.player,
        target=target_entity,
        card=card,
        zone_element=zone_element,
        logs=logs
    )

def reshuffle_discard_into_draw_if_needed(player, logs, game_state=None):
    """
    抽牌堆为空时，将弃牌堆洗回抽牌堆。
    用于破灭：打出时抽牌堆为空，也要先进行一轮洗牌。
    """
    if player.draw_pile:
        return True

    if not player.discard_pile:
        return False

    player.draw_pile = player.discard_pile
    player.discard_pile = []
    random.shuffle(player.draw_pile)
    logs.append("抽牌堆为空，弃牌堆洗回抽牌堆。")
    if game_state is not None:
        for relic in getattr(player, "relics", []) or []:
            handler = getattr(relic, "on_shuffle", None)
            if handler is None:
                continue
            result = handler(game_state, player)
            if result:
                logs.extend(result)
    return bool(player.draw_pile)

def get_auto_play_target_index(game_state, card):
    """
    自动打出牌时选择目标。

    enemy 目标：优先锁定目标；否则选择第一个存活敌人。
    all_enemies / random_enemy / self / none：target_index 使用 0 即可。
    """
    card_target = getattr(card, "target", "none")

    if card_target != "enemy":
        return 0

    if getattr(card, "card_type", "") == "attack":
        from game.target_lock import get_locked_attack_target_index
        locked_index = get_locked_attack_target_index(game_state)

        if locked_index is not None:
            if 0 <= locked_index < len(game_state.enemies):
                if game_state.enemies[locked_index].is_alive():
                    return locked_index

    for index, enemy in enumerate(game_state.enemies):
        if enemy.is_alive():
            return index

    return 0

def play_card_from_effect_and_exhaust(
        game_state,
        source_card,
        played_card,
        reason="havoc",
        force_exhaust=True,
        effect_context_extra=None,
        source_label=None
    ):
    """
    被其他效果自动打出的牌。

    当前用于破灭：
    - 从抽牌堆顶取出一张牌。
    - 尝试免费打出。
    - 无论是否成功打出，最后都进入消耗堆。
    """
    logs = []

    from data.card.keyword_rules import can_play_card
    from game.engine import (
        validate_card_target,
        move_card_to_exhaust_pile,
        move_played_card_to_destination,
        resolve_abyss_index_after_shade_card_play,
    )
    from game.x_value import is_x_cost_card, calculate_card_x_value
    from game.zone.zone_utils import (
        is_card_first_play_this_battle,
        mark_card_played_this_battle
    )
    from game.event_bus import dispatch_event
    from game.battle_context import BattleContext
    from game.constants import EVENT_CARD_PLAY_AFTER

    can_play, cannot_play_reason = can_play_card(
        game_state=game_state,
        card=played_card,
        play_reason="effect_auto_play"
    )

    if not can_play:
        logs.append("【{}】尝试打出【{}】，但失败：{}".format(
            source_card.name,
            played_card.name,
            cannot_play_reason
        ))
        if force_exhaust:
            logs.extend(move_card_to_exhaust_pile(
                game_state=game_state,
                card=played_card,
                reason=reason
            ))
        else:
            logs.extend(move_played_card_to_destination(game_state, played_card))
        return logs

    target_index = get_auto_play_target_index(game_state, played_card)
    target_error = validate_card_target(game_state, played_card, target_index)

    if target_error:
        logs.append("【{}】尝试打出【{}】，但目标无效：{}".format(
            source_card.name,
            played_card.name,
            target_error
        ))
        logs.extend(move_card_to_exhaust_pile(
            game_state=game_state,
            card=played_card,
            reason=reason
        ))
        return logs

    effect_context = {
        "card_first_play_this_battle": is_card_first_play_this_battle(
            game_state,
            played_card
        ),
        "played_by_effect": True,
        "source_card_id": getattr(source_card, "card_id", ""),
    }

    if effect_context_extra:
        effect_context.update(effect_context_extra)
    if is_x_cost_card(played_card):
        raw_x = 0
        x_value, x_logs = calculate_card_x_value(
            game_state=game_state,
            card=played_card,
            raw_x=raw_x
        )
        effect_context["raw_x"] = raw_x
        effect_context["x"] = x_value
        effect_context["spent_cost"] = 0

        if source_label:
            logs.append("【{}】自动打出【{}】，最终 X = {}。".format(
                source_label,
                played_card.name,
                x_value
            ))
        else:
            logs.append("【{}】免费打出抽牌堆顶的【{}】，最终 X = {}。".format(
                source_card.name,
                played_card.name,
                x_value
            ))
        logs.extend(x_logs)
    else:
        if source_label:
            logs.append("【{}】自动打出【{}】。".format(
                source_label,
                played_card.name
            ))
        else:
            logs.append("【{}】免费打出抽牌堆顶的【{}】。".format(
                source_card.name,
                played_card.name
            ))
    from game.engine import apply_next_card_replay_statuses
    apply_next_card_replay_statuses(
        game_state=game_state,
        card=played_card,
        effect_context=effect_context,
        logs=logs
    )
    logs.extend(apply_card_effects(
        game_state=game_state,
        card=played_card,
        target_index=target_index,
        effect_context=effect_context
    ))

    mark_card_played_this_battle(game_state, played_card)
    record_player_card_played_this_turn(
        game_state,
        played_card,
        game_state.player
    )

    context = BattleContext(
        game_state=game_state,
        player=game_state.player,
        source=game_state.player,
        card=played_card
    )
    logs.extend(dispatch_event(game_state, EVENT_CARD_PLAY_AFTER, context))
    logs.extend(resolve_abyss_index_after_shade_card_play(game_state, played_card))

    logs.extend(move_card_to_exhaust_pile(
        game_state=game_state,
        card=played_card,
        reason=reason
    ))

    return logs

def upgrade_card_for_this_combat(card):
    """
    返回本场战斗内临时升级后的牌。
    不修改原对象。
    """
    if getattr(card, "upgraded", False):
        return None

    from data.card.upgrade_rules import upgrade_card

    upgraded_card = upgrade_card(card)

    if getattr(upgraded_card, "upgrade_unavailable", False):
        return None

    if not getattr(upgraded_card, "upgraded", False):
        return None

    setattr(upgraded_card, "temporary_upgraded", True)

    return upgraded_card

def collect_upgradeable_cards_from_pile(pile):
    options = []

    for pile_card in pile:
        upgraded_card = upgrade_card_for_this_combat(pile_card)

        if upgraded_card is None:
            continue

        options.append(pile_card)

    return options

def replace_card_in_pile(pile, old_card, new_card):
    for index, pile_card in enumerate(pile):
        if pile_card is old_card:
            pile[index] = new_card
            return True

    return False

def upgrade_all_cards_in_pile_for_this_combat(pile):
    logs = []
    upgraded_count = 0

    for index, pile_card in enumerate(list(pile)):
        upgraded_card = upgrade_card_for_this_combat(pile_card)

        if upgraded_card is None:
            continue

        pile[index] = upgraded_card
        upgraded_count += 1
        logs.append("【{}】临时升级为【{}】。".format(
            pile_card.name,
            upgraded_card.name
        ))

    return upgraded_count, logs

def draw_cards_with_no_draw_check(game_state, count, draw_source="card_effect"):
    player = game_state.player

    if get_status_value(player, "no_draw") > 0:
        return ["{} 受到不能抽牌影响，无法抽牌。".format(player.name)]

    return player.draw_cards(
        count,
        game_state=game_state,
        draw_source=draw_source
    )

def is_enemy_intent_attack(intent):
    if intent is None:
        return False
    if getattr(intent, "kind", "") == "attack":
        return True
    if getattr(intent, "kind", "") == "multi":
        for child in getattr(intent, "actions", []):
            if is_enemy_intent_attack(child):
                return True
    return False

def any_alive_enemy_intends_attack(game_state):
    for enemy in getattr(game_state, "enemies", []) or []:
        if not enemy.is_alive():
            continue
        intent = enemy.get_current_intent()
        if is_enemy_intent_attack(intent):
            return True
    return False

@register_effect("gain_status_all_enemies_if_any_enemy_intent_attack")
def handle_gain_status_all_enemies_if_any_enemy_intent_attack(game_state, card, effect, target_index, effect_context):
    logs = []
    if not any_alive_enemy_intends_attack(game_state):
        logs.append("没有敌人的意图是攻击，【{}】没有施加状态。".format(card.name))
        return logs
    status_key = effect.get("status", "weak")
    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 1),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context
    )
    amount = int(amount)
    from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
    logs.append("有敌人的意图是攻击，【{}】对全体敌人施加状态。".format(card.name))
    for enemy in get_all_alive_enemies(game_state):
        logs.extend(apply_status_with_player_relics(
            game_state=game_state,
            source=game_state.player,
            target=enemy,
            status_key=status_key,
            amount=amount
        ))
    return logs

@register_effect("gain_block_if_enemy_attack_or_self_action_hp_loss_this_turn")
def handle_gain_block_if_enemy_attack_or_self_action_hp_loss_this_turn(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    enemy_attack = any_alive_enemy_intends_attack(game_state)
    self_hurt = int(getattr(game_state, "player_self_action_hp_loss_count_this_turn", 0) or 0) > 0

    if not enemy_attack and not self_hurt:
        logs.append("没有敌人的意图是攻击，且本回合没有触发过自伤，【{}】没有获得格挡。".format(
            card.name
        ))
        return logs

    if get_status_value(player, "no_card_block") > 0:
        logs.append("{} 受到不能从卡牌获得格挡影响，【{}】没有获得格挡。".format(
            player.name,
            card.name
        ))
        return logs

    zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
    local_context = make_zone_effect_context(effect_context, zone_element)

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=player,
        target=player,
        block_source="played_card",
        effect_context=local_context
    )
    amount = int(amount)

    if enemy_attack and self_hurt:
        logs.append("有敌人的意图是攻击，且本回合触发过自伤，【{}】触发。".format(card.name))
    elif enemy_attack:
        logs.append("有敌人的意图是攻击，【{}】触发。".format(card.name))
    else:
        logs.append("本回合触发过自伤，【{}】触发。".format(card.name))

    logs.extend(gain_block_without_modifiers(
        game_state=game_state,
        source=player,
        target=player,
        amount=amount,
        block_source="played_card",
        card=card
    ))

    from game.zone.zone_utils import apply_earth_zone_temp_thorns
    apply_earth_zone_temp_thorns(
        game_state=game_state,
        target=player,
        zone_element=zone_element,
        block_amount=amount,
        logs=logs
    )

    return logs
@register_effect("mirror_target_positive_buffs")
def handle_mirror_target_positive_buffs(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    target_entity = get_effect_target_entity(
        game_state=game_state,
        target_key=effect.get("target", "selected_enemy"),
        target_index=target_index
    )

    if target_entity is None:
        return ["【{}】目标无效。".format(card.name)]

    excluded_statuses = set(effect.get("exclude_statuses", []) or [])

    copied = 0

    from game.status.status_defs import get_status_def
    from game.status.status_gain import format_status_gain_log

    active_statuses = getattr(target_entity, "statuses", None)
    if active_statuses is None:
        return ["【{}】目标没有可复制的状态。".format(card.name)]

    for status_key, amount in active_statuses.all_active().items():
        amount = int(amount)

        if amount <= 0:
            continue

        if status_key in excluded_statuses:
            continue

        status_def = get_status_def(status_key)
        if status_def is None:
            continue

        if getattr(status_def, "category", "") != "buff":
            continue

        if hasattr(player, "gain_status_with_result"):
            result = player.gain_status_with_result(status_key, amount)
            if bool(result.get("applied", False)):
                logs.append(format_status_gain_log(
                    player,
                    status_key,
                    amount,
                    result
                ))
                copied += 1
        else:
            current = player.gain_status(status_key, amount)
            logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
                player.name,
                amount,
                status_def.name,
                status_def.name,
                current
            ))
            copied += 1

    if copied <= 0:
        logs.append("【{}】没有从 {} 身上复制到正面增益。".format(
            card.name,
            target_entity.name
        ))
    else:
        logs.insert(0, "【{}】复制 {} 身上的正面增益。".format(
            card.name,
            target_entity.name
        ))

    return logs

@register_effect("draw_cards")
def handle_draw_cards(game_state, card, effect, target_index, effect_context):
    logs = []
    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context
    )

    logs.extend(draw_cards_with_no_draw_check(
        game_state,
        amount,
        draw_source="card_effect"
    ))
    return logs


@register_effect("draw_to_full")
def handle_draw_to_full(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    logs = []
    if get_status_value(player, "no_draw") > 0:
        logs.append("{} 受到不能抽牌影响，无法抽牌。".format(player.name))
        return logs
    logs.extend(player.draw_to_full(
        game_state=game_state,
        draw_source="card_effect"
    ))
    return logs


@register_effect("gain_energy")
def handle_gain_energy(game_state, card, effect, target_index, effect_context):
    logs = []
    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    )

    game_state.player.cost += amount

    logs.append("{} 获得 {} 点费用。当前费用：{}。".format(
        game_state.player.name,
        amount,
        game_state.player.cost
    ))

    return logs


@register_effect("heal_player")
def handle_heal_player(game_state, card, effect, target_index, effect_context):
    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    )
    from game.relic_logic.combat_relic_utils import heal_player_in_combat
    return heal_player_in_combat(game_state, amount, getattr(card, "name", "卡牌"))

@register_effect("heal_player_by_max_hp_percent")
def handle_heal_player_by_max_hp_percent(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    percent = float(effect.get("percent", 0.0) or 0.0)
    percent *= float(effect_context.get("potion_amount_multiplier", 1.0) or 1.0)

    amount = int(int(getattr(player, "max_hp", 0)) * percent)
    if amount <= 0 and percent > 0:
        amount = 1

    from game.relic_logic.combat_relic_utils import heal_player_in_combat
    return heal_player_in_combat(game_state, amount, getattr(card, "name", "卡牌"))

@register_effect("roost_heal_by_flying_state")
def handle_roost_heal_by_flying_state(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    from game.modifiers import get_status_value

    flying = get_status_value(player, "flying")

    if flying > 0:
        percent = float(effect.get("with_flying_percent", 0.0) or 0.0)
        label = "有飞行"
    else:
        percent = float(effect.get("without_flying_percent", 0.0) or 0.0)
        label = "没有飞行"

    amount = int(int(getattr(player, "max_hp", 0)) * percent)
    if amount <= 0 and percent > 0:
        amount = 1

    logs.append("【{}】{}，恢复 {}% 最大生命值。".format(
        card.name,
        label,
        int(percent * 100)
    ))

    from game.relic_logic.combat_relic_utils import heal_player_in_combat
    logs.extend(heal_player_in_combat(
        game_state,
        amount,
        getattr(card, "name", "卡牌")
    ))

    return logs

@register_effect("brave_bird_self_cost")
def handle_brave_bird_self_cost(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    from game.modifiers import get_status_value

    flying = get_status_value(player, "flying")
    if flying > 0:
        logs.append("【{}】受到飞行保护，消去了自伤。当前飞行：{}。".format(
            card.name,
            flying
        ))
        return logs

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    amount = int(amount)

    if amount <= 0:
        logs.append("【{}】没有造成自伤。".format(card.name))
        return logs

    logs.append("【{}】没有飞行保护，失去 {} 点生命。".format(
        card.name,
        amount
    ))

    logs.extend(deal_damage(
        game_state=game_state,
        source=player,
        target=player,
        amount=amount,
        damage_kind="card_hp_loss",
        card=card,
        is_reaction_damage=False,
        ignore_block=True,
        count_as_player_self_action_hp_loss=True
    ))

    return logs

@register_effect("deal_damage_heal_on_full_hp_kill")
def handle_deal_damage_heal_on_full_hp_kill(game_state, card, effect, target_index, effect_context):
    logs = []

    attack_type, attack_element = get_effect_attack_tags(card, effect)
    zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
    local_context = make_zone_effect_context(effect_context, zone_element)

    target_key = effect.get("target", "selected_enemy")
    target_entity = get_effect_target_entity(
        game_state=game_state,
        target_key=target_key,
        target_index=target_index
    )

    if target_entity is None:
        logs.append("目标敌人无效。")
        return logs

    damage = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=game_state.player,
        target=target_entity,
        damage_source="played_card",
        effect_context=local_context,
        attack_type=attack_type,
        attack_element=attack_element
    )

    was_alive = target_entity.is_alive()
    was_full_hp = int(getattr(target_entity, "hp", 0)) >= int(getattr(target_entity, "max_hp", 0))

    logs.append("【{}】造成 {} 点攻击伤害。".format(
        card.name,
        damage
    ))

    logs.extend(deal_damage(
        game_state=game_state,
        source=game_state.player,
        target=target_entity,
        amount=damage,
        damage_kind="attack",
        card=card,
        attack_type=attack_type,
        attack_element=attack_element,
        zone_element=zone_element
    ))

    from game.zone.zone_utils import apply_fire_zone_burn
    apply_fire_zone_burn(
        game_state=game_state,
        source=game_state.player,
        target=target_entity,
        card=card,
        zone_element=zone_element,
        logs=logs
    )

    if was_alive and was_full_hp and not target_entity.is_alive():
        heal_amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("heal"),
            source=game_state.player,
            target=game_state.player,
            effect_context=local_context
        )
        heal_amount = int(heal_amount)

        if heal_amount > 0:
            from game.relic_logic.combat_relic_utils import heal_player_in_combat
            logs.extend(heal_player_in_combat(
                game_state,
                heal_amount,
                "【{}】满血斩杀".format(card.name)
            ))

    return logs

@register_effect("draw_gain_energy_if_player_lost_hp_this_battle")
def handle_draw_gain_energy_if_player_lost_hp_this_battle(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    base_draw = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("base_draw"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    base_draw = int(base_draw)

    if base_draw > 0:
        logs.extend(draw_cards_with_no_draw_check(
            game_state,
            base_draw,
            draw_source="card_effect"
        ))

    if int(getattr(game_state, "player_life_loss_count_this_battle", 0) or 0) <= 0:
        logs.append("本场战斗中还没有失去过生命，【{}】没有触发额外效果。".format(card.name))
        return logs

    extra_draw = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("extra_draw"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    energy = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("energy"),
        source=player,
        target=player,
        effect_context=effect_context
    )

    extra_draw = int(extra_draw)
    energy = int(energy)

    logs.append("本场战斗中已经失去过生命，【{}】触发额外效果。".format(card.name))

    if extra_draw > 0:
        logs.extend(draw_cards_with_no_draw_check(
            game_state,
            extra_draw,
            draw_source="card_effect"
        ))

    if energy > 0:
        player.cost += energy
        logs.append("{} 获得 {} 点费用。当前费用：{}。".format(
            player.name,
            energy,
            player.cost
        ))

    return logs

@register_effect("trigger_shade_hp_loss_then_draw")
def handle_trigger_shade_hp_loss_then_draw(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    from game.zone.zone_utils import apply_zone_source_hp_loss_if_needed

    apply_zone_source_hp_loss_if_needed(
        game_state=game_state,
        source=player,
        zone_element="shade",
        logs=logs,
        label="唤渊",
        card=card,
        count_as_player_self_action_hp_loss=True
    )

    if game_state.battle_over or not player.is_alive():
        logs.append("【{}】的反噬已经使玩家无法继续抽牌。".format(card.name))
        return logs

    draw = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("draw"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    draw = int(draw)

    if draw > 0:
        logs.extend(draw_cards_with_no_draw_check(
            game_state,
            draw,
            draw_source="card_effect"
        ))

    return logs

@register_effect("apply_flinch_if_flying_gt")
def handle_apply_flinch_if_flying_gt(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    threshold = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("threshold"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    threshold = int(threshold)

    flinch_amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    flinch_amount = int(flinch_amount)

    flying = get_status_value(player, "flying")

    if flying <= threshold:
        logs.append("【{}】判定：当前飞行 {} 层，未大于 {}，没有赋予畏缩。".format(
            card.name,
            flying,
            threshold
        ))
        return logs

    target_key = effect.get("target", "selected_enemy")
    target_entity = get_effect_target_entity(
        game_state=game_state,
        target_key=target_key,
        target_index=target_index
    )

    if target_entity is None:
        logs.append("【{}】畏缩目标无效。".format(card.name))
        return logs

    if flinch_amount <= 0:
        logs.append("【{}】畏缩层数为 0。".format(card.name))
        return logs

    from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
    logs.append("【{}】判定：当前飞行 {} 层，大于 {}，赋予畏缩。".format(
        card.name,
        flying,
        threshold
    ))
    logs.extend(apply_status_with_player_relics(
        game_state=game_state,
        source=player,
        target=target_entity,
        status_key="flinch",
        amount=flinch_amount
    ))

    return logs

@register_effect("abyss_mire_damage_by_gaze")
def handle_abyss_mire_damage_by_gaze(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    attack_type, attack_element = get_effect_attack_tags(card, effect)
    zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
    local_context = make_zone_effect_context(effect_context, zone_element)

    alive_enemies = get_all_alive_enemies(game_state)

    attempted = False
    total_real_damage = 0

    for enemy in alive_enemies:
        if game_state.battle_over:
            break

        if not enemy.is_alive():
            continue

        gaze = int(get_status_value(enemy, "abyss_gaze"))
        if gaze <= 0:
            continue

        attempted = True

        damage = int(gaze)

        # 渊淖是阴属性攻击，基础值来自目标身上的深渊凝视层数。
        damage = apply_modifier_profile(
            value=damage,
            modifier_profile="attack_damage",
            game_state=game_state,
            source=player,
            target=enemy,
            card=card,
            damage_source="played_card",
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        )

        if zone_element:
            from game.zone.zone_utils import apply_zone_amount_modifier
            damage = apply_zone_amount_modifier(
                value=damage,
                game_state=game_state,
                zone_element=zone_element
            )

        # 若深渊形态存在，且渊淖本身是阴属性攻击牌，则吃深渊形态的极阴效果。
        damage = apply_abyssal_form_amount_modifier(
            value=damage,
            game_state=game_state,
            card=card,
            zone_element=zone_element
        )

        damage = int(damage)

        if damage <= 0:
            logs.append("【{}】试图依据 {} 的 {} 层深渊凝视造成伤害，但最终伤害为 0。".format(
                card.name,
                enemy.name,
                gaze
            ))
            continue

        before_hp = int(getattr(enemy, "hp", 0))

        logs.append("【{}】依据 {} 的 {} 层深渊凝视，对其造成 {} 点阴属性攻击伤害。".format(
            card.name,
            enemy.name,
            gaze,
            damage
        ))

        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=enemy,
            amount=damage,
            damage_kind="attack",
            card=card,
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        ))

        after_hp = int(getattr(enemy, "hp", 0))
        real_damage = max(0, before_hp - after_hp)
        total_real_damage += real_damage

    if not attempted:
        logs.append("【{}】没有找到带有深渊凝视的敌人，无法造成伤害。".format(card.name))

    if total_real_damage <= 0:
        energy_gain = int(effect.get("energy_if_no_damage", 2) or 2)
        player.cost += energy_gain

        logs.append("【{}】没有造成实际生命伤害，获得 {} 点费用。当前费用：{}。".format(
            card.name,
            energy_gain,
            player.cost
        ))

        from data.card.AAAregistry import create_card
        from data.card.upgrade_rules import upgrade_card

        prayer = create_card("card.lightless_prayer")

        if getattr(card, "upgraded", False):
            prayer = upgrade_card(prayer)

        setattr(prayer, "temporary", True)
        setattr(prayer, "created_in_battle", True)

        player.draw_pile.append(prayer)
        random.shuffle(player.draw_pile)

        logs.append("将 1 张【{}】加入抽牌堆，并重洗抽牌堆。".format(
            prayer.name
        ))

    return logs

@register_effect("play_all_lightless_prayers_from_exhaust")
def handle_play_all_lightless_prayers_from_exhaust(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    prayers = [
        pile_card
        for pile_card in list(player.exhaust_pile)
        if getattr(pile_card, "card_id", "") == "card.lightless_prayer"
    ]

    if not prayers:
        return ["【{}】没有在消耗堆中找到无光祷言。".format(card.name)]

    from game.effects import play_card_from_effect_and_exhaust

    echo_upgraded = bool(getattr(card, "upgraded", False))

    logs.append("【{}】将打出消耗堆中的 {} 张无光祷言。".format(
        card.name,
        len(prayers)
    ))

    for prayer in prayers:
        if game_state.battle_over:
            break

        if prayer not in player.exhaust_pile:
            continue

        player.exhaust_pile.remove(prayer)

        logs.extend(play_card_from_effect_and_exhaust(
            game_state=game_state,
            source_card=card,
            played_card=prayer,
            reason="prayer_echo",
            force_exhaust=True,
            source_label=card.name
        ))

        if (
            echo_upgraded
            and getattr(prayer, "upgraded", False)
            and prayer in player.exhaust_pile
            and not game_state.battle_over
        ):
            player.exhaust_pile.remove(prayer)
            logs.append("【{}】升级效果：再次打出【{}】。".format(
                card.name,
                prayer.name
            ))
            logs.extend(play_card_from_effect_and_exhaust(
                game_state=game_state,
                source_card=card,
                played_card=prayer,
                reason="prayer_echo",
                force_exhaust=True,
                source_label=card.name
            ))

    return logs

@register_effect("gain_abyss_hunt")
def handle_gain_abyss_hunt(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    heal = int(effect.get("heal", 4) or 4)

    zone_element = ""
    if effect_context is not None:
        zone_element = effect_context.get("zone_element", "")

    if zone_element == "shade":
        from game.zone.zone_utils import apply_zone_amount_modifier
        old_heal = heal
        heal = apply_zone_amount_modifier(
            value=heal,
            game_state=game_state,
            zone_element="shade"
        )
        logs.append("【{}】恢复值受到阴 Zone 修正：{} -> {}。".format(
            card.name,
            old_heal,
            heal
        ))

    status_key = "abyss_hunt_plus" if getattr(card, "upgraded", False) else "abyss_hunt"
    current = player.gain_status(status_key, heal)

    logs.append("【{}】生效：渊猎触发时恢复 {} HP。当前层数：{}。".format(
        card.name,
        heal,
        current
    ))

    return logs

@register_effect("gain_abyss_symbiosis")
def handle_gain_abyss_symbiosis(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=player,
        target=player,
        effect_context=effect_context
    )
    amount = int(amount)

    if amount <= 0:
        logs.append("【{}】没有获得深渊共生层数。".format(card.name))
        return logs

    current = player.gain_status("abyss_symbiosis", amount)

    logs.append("【{}】生效：攻击有深渊凝视的敌人时恢复 {} HP。当前深渊共生：{}。".format(
        card.name,
        amount,
        current
    ))

    return logs

@register_effect("abyss_wail_damage_by_exhaust_count")
def handle_abyss_wail_damage_by_exhaust_count(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    target_entity = get_effect_target_entity(
        game_state=game_state,
        target_key=effect.get("target", "selected_enemy"),
        target_index=target_index
    )

    if target_entity is None:
        return ["目标敌人无效。"]

    count = len(getattr(player, "exhaust_pile", []) or [])

    if count <= 0:
        logs.append("【{}】消耗堆没有牌，造成 0 点伤害。".format(card.name))
    else:
        logs.append("【{}】依据消耗堆牌数，对 {} 造成 {} 点阴属性攻击伤害。".format(
            card.name,
            target_entity.name,
            count
        ))

    logs.extend(deal_damage(
        game_state=game_state,
        source=player,
        target=target_entity,
        amount=count,
        damage_kind="attack",
        card=card,
        attack_type=getattr(card, "attack_type", ""),
        attack_element="shade",
        zone_element=effect_context.get("zone_element", "") if effect_context else ""
    ))

    if getattr(card, "upgraded", False):
        import copy
        copied = copy.deepcopy(card)
        setattr(copied, "temporary", True)
        setattr(copied, "created_in_battle", True)
        player.draw_pile.append(copied)
        random.shuffle(player.draw_pile)
        logs.append("【{}】升级效果：将 1 张当前【{}】的复制品加入抽牌堆，并重洗抽牌堆。".format(
            card.name,
            card.name
        ))

    return logs

@register_effect("draw_from_draw_pile_bottom")
def handle_draw_from_draw_pile_bottom(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player
    count = int(effect.get("count", 2) or 2)
    shade_active, shade_extreme = get_real_active_shade_zone_info(game_state)
    if shade_active:
        if shade_extreme:
            bonus = int(effect.get("extreme_bonus", effect.get("shade_bonus", 1)) or 0)
        else:
            bonus = int(effect.get("shade_bonus", 1) or 0)
        count += bonus
        if bonus > 0:
            lose_1_hp_for_shade_bonus(game_state, card, logs, "沉渊")
            if game_state.battle_over or not player.is_alive():
                return logs
    if count <= 0:
        return logs

    if not player.draw_pile:
        return ["【{}】抽牌堆为空。".format(card.name)]
    selected = list(player.draw_pile[:count])
    logs.append("【{}】从抽牌堆底端取出 {} 张牌。".format(
        card.name,
        len(selected)
    ))
    for pile_card in selected:
        move_specific_draw_card_to_hand_or_discard(
            game_state=game_state,
            card=pile_card,
            logs=logs,
            draw_source="sink_into_abyss"
        )
        if game_state.battle_over:
            break

    return logs

@register_effect("shuffle_draw_pile_draw_middle")
def handle_shuffle_draw_pile_draw_middle(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    count = int(effect.get("count", 2) or 2)

    shade_active, shade_extreme = get_real_active_shade_zone_info(game_state)
    if shade_active:
        if shade_extreme:
            bonus = int(effect.get("extreme_bonus", effect.get("shade_bonus", 1)) or 0)
        else:
            bonus = int(effect.get("shade_bonus", 1) or 0)

        count += bonus

        if bonus > 0:
            lose_1_hp_for_shade_bonus(game_state, card, logs, "深渊混沌")

            if game_state.battle_over or not player.is_alive():
                return logs

    if not player.draw_pile:
        return ["【{}】抽牌堆为空，无法重洗并抽取。".format(card.name)]

    random.shuffle(player.draw_pile)
    logs.append("【{}】重洗抽牌堆。".format(card.name))

    total = len(player.draw_pile)
    count = min(count, total)

    start = (total - count) // 2
    selected = list(player.draw_pile[start:start + count])

    logs.append("【{}】抽出洗后正中的 {} 张牌。".format(
        card.name,
        len(selected)
    ))

    for pile_card in selected:
        move_specific_draw_card_to_hand_or_discard(
            game_state=game_state,
            card=pile_card,
            logs=logs,
            draw_source="abyss_chaos"
        )

        if game_state.battle_over:
            break

    return logs

@register_effect("gain_insatiable_abyss")
def handle_gain_insatiable_abyss(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    base_percent = int(effect.get("base_percent", 50) or 50)
    upgraded_percent = int(effect.get("upgraded_percent", base_percent) or base_percent)

    percent = upgraded_percent if getattr(card, "upgraded", False) else base_percent

    zone = getattr(game_state, "active_zone", None)
    zone_element = ""
    is_extreme = False

    if zone is not None:
        try:
            if not zone.is_expired():
                zone_element = str(getattr(zone, "element", "") or "").strip().lower()
                is_extreme = bool(getattr(zone, "is_extreme", False))
        except Exception:
            zone_element = str(getattr(zone, "element", "") or "").strip().lower()
            is_extreme = bool(getattr(zone, "is_extreme", False))

    if zone_element == "shade":
        if getattr(card, "upgraded", False):
            if is_extreme:
                percent = 200
            else:
                percent = 120
        else:
            if is_extreme:
                percent = 100
            else:
                percent = 75

    current = player.gain_status("insatiable_abyss", percent)

    logs.append("【{}】生效：无厌之渊返还比例为 {}%。当前无厌之渊：{}%。".format(
        card.name,
        percent,
        current
    ))

    return logs

def _select_abyss_manifestation_target(game_state):
    candidates = [
        enemy
        for enemy in getattr(game_state, "enemies", []) or []
        if enemy.is_alive()
    ]

    if not candidates:
        return None

    candidates.sort(key=lambda enemy: (
        -int(get_status_value(enemy, "abyss_gaze")),
        int(getattr(enemy, "hp", 0)),
        getattr(enemy, "_battle_order", 0)
    ))

    target = candidates[0]

    if int(get_status_value(target, "abyss_gaze")) <= 0:
        return None

    return target


@register_effect("abyss_manifestation_damage")
def handle_abyss_manifestation_damage(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    target = _select_abyss_manifestation_target(game_state)

    if target is None:
        return ["【{}】没有找到带有深渊凝视的敌人。".format(card.name)]

    gaze = int(get_status_value(target, "abyss_gaze"))
    damage = gaze

    use_shade_zone_when_upgraded = bool(effect.get("use_shade_zone_when_upgraded", False))
    zone_element = ""

    if use_shade_zone_when_upgraded and getattr(card, "upgraded", False):
        zone = getattr(game_state, "active_zone", None)
        if zone is not None:
            try:
                if not zone.is_expired():
                    zone_element = str(getattr(zone, "element", "") or "").strip().lower()
            except Exception:
                zone_element = str(getattr(zone, "element", "") or "").strip().lower()

        if zone_element == "shade":
            from game.zone.zone_utils import apply_zone_amount_modifier
            old_damage = damage
            damage = apply_zone_amount_modifier(damage, game_state, "shade")
            logs.append("【{}】受到阴 Zone 修正：{} -> {}。".format(
                card.name,
                old_damage,
                damage
            ))

            from game.zone.zone_utils import apply_zone_source_hp_loss_if_needed
            apply_zone_source_hp_loss_if_needed(
                game_state=game_state,
                source=player,
                zone_element="shade",
                logs=logs,
                label=card.name,
                card=card,
                count_as_player_self_action_hp_loss=True
            )

            if game_state.battle_over or not player.is_alive():
                return logs

    logs.append("【{}】锁定深渊凝视最高的敌人：{}，造成 {} 点无来源环境伤害。".format(
        card.name,
        target.name,
        damage
    ))

    logs.extend(deal_damage(
        game_state=game_state,
        source=None,
        target=target,
        amount=damage,
        damage_kind="environment",
        card=card,
        is_reaction_damage=True,
        ignore_block=False,
        attack_type="",
        attack_element="",
        zone_element=""
    ))

    return logs


def _find_and_move_upgraded_crystal_zone_to_draw_top(game_state, logs, source_name):
    """
    找到当前战斗中的【辉晶领域】，升级后放到抽牌堆顶。

    选择优先级：
    1. 未升级优先于已升级
    2. 同升级状态下：弃牌堆 > 手牌 > 抽牌堆 > 消耗堆

    抽牌堆顶在当前工程中是 list 末尾，因为抽牌使用 draw_pile.pop()。
    """
    player = game_state.player

    pile_specs = [
        ("discard_pile", "弃牌堆"),
        ("hand", "手牌"),
        ("draw_pile", "抽牌堆"),
        ("exhaust_pile", "消耗堆"),
    ]

    candidates = []

    for pile_priority, (pile_attr, pile_label) in enumerate(pile_specs):
        pile = getattr(player, pile_attr, []) or []
        for card_index, pile_card in enumerate(list(pile)):
            if getattr(pile_card, "card_id", "") != "card.crystal_zone":
                continue

            upgraded_priority = 1 if getattr(pile_card, "upgraded", False) else 0

            candidates.append({
                "card": pile_card,
                "pile": pile,
                "pile_attr": pile_attr,
                "pile_label": pile_label,
                "pile_priority": pile_priority,
                "upgraded_priority": upgraded_priority,
                "card_index": card_index,
            })

    if not candidates:
        logs.append("【{}】没有找到【辉晶领域】，无法将其升级并放回抽牌堆顶。".format(
            source_name
        ))
        return

    candidates.sort(key=lambda item: (
        item["upgraded_priority"],
        item["pile_priority"],
        item["card_index"],
    ))

    selected = candidates[0]
    found_card = selected["card"]
    found_pile = selected["pile"]
    found_pile_label = selected["pile_label"]

    from data.card.upgrade_rules import upgrade_card

    found_pile.remove(found_card)

    old_name = found_card.name
    upgraded_card = upgrade_card(found_card)
    setattr(upgraded_card, "temporary_combat_upgrade", True)

    player.draw_pile.append(upgraded_card)

    logs.append("【{}】找到{}中的【{}】，将其升级为【{}】并放回抽牌堆顶。".format(
        source_name,
        found_pile_label,
        old_name,
        upgraded_card.name
    ))

@register_effect("crystal_dust_explosion")
def handle_crystal_dust_explosion(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    zone = getattr(game_state, "active_zone", None)

    if zone is None:
        logs.append("【{}】没有当前晶 Zone，无法引爆。".format(card.name))
        return logs

    try:
        if zone.is_expired():
            logs.append("【{}】当前 Zone 已失效，无法引爆。".format(card.name))
            return logs
    except Exception:
        pass

    zone_element = str(getattr(zone, "element", "") or "").strip().lower()
    if zone_element != "crystal":
        logs.append("【{}】当前 Zone 不是晶 Zone，无法引爆。".format(card.name))
        return logs

    is_extreme = bool(getattr(zone, "is_extreme", False))

    normal_times = int(effect.get("normal_times", 1) or 1)
    normal_damage = int(effect.get("normal_damage", 8) or 8)
    extreme_times = int(effect.get("extreme_times", 2) or 2)
    extreme_damage = int(effect.get("extreme_damage", 12) or 12)

    if is_extreme:
        hit_times = extreme_times
        hit_damage = extreme_damage
        zone_name = getattr(zone, "name", "极·辉晶")
    else:
        hit_times = normal_times
        hit_damage = normal_damage
        zone_name = getattr(zone, "name", "辉晶")

    game_state.active_zone = None

    logs.append("【{}】破坏了当前 Zone：{}。".format(
        card.name,
        zone_name
    ))
    logs.append("晶尘爆炸将对全体敌人造成 {} 次 {} 点伤害。".format(
        hit_times,
        hit_damage
    ))

    for hit_index in range(hit_times):
        if game_state.battle_over:
            logs.append("战斗已经结束，后续晶尘爆炸不再结算。")
            break

        alive_enemies = get_all_alive_enemies(game_state)
        if not alive_enemies:
            logs.append("没有可攻击的敌人。")
            break

        if hit_times > 1:
            logs.append("晶尘爆炸第 {}/{} 次：".format(
                hit_index + 1,
                hit_times
            ))

        for enemy in alive_enemies:
            if game_state.battle_over:
                break

            if not enemy.is_alive():
                continue

            logs.append("晶尘爆炸对 {} 造成 {} 点伤害。".format(
                enemy.name,
                hit_damage
            ))

            logs.extend(deal_damage(
                game_state=game_state,
                source=None,
                target=enemy,
                amount=hit_damage,
                damage_kind="zone_burst",
                card=card,
                is_reaction_damage=True,
                ignore_block=False,
                attack_type="",
                attack_element="crystal",
                zone_element=""
            ))

    if getattr(card, "upgraded", False):
        _find_and_move_upgraded_crystal_zone_to_draw_top(
            game_state=game_state,
            logs=logs,
            source_name=card.name
        )

    return logs

@register_effect("request_abyss_index_choice")
def handle_request_abyss_index_choice(
        game_state,
        card,
        effect,
        target_index,
        effect_context
    ):
    player = game_state.player
    options = list(getattr(player, "draw_pile", []) or [])

    if not options:
        return [
            "【{}】触发，但抽牌堆中没有可选择的牌。".format(
                card.name
            )
        ]

    enchantment_id = str(
        effect.get("enchantment", "index_shade")
        or "index_shade"
    ).strip().lower()

    from data.card.enchantment_rules import (
        get_enchantment_display_name
    )

    enchantment_name = get_enchantment_display_name(
        enchantment_id
    )

    set_pending_choice(game_state, PendingChoice(
        kind="abyss_index",
        source=card.name,
        prompt=(
            "=== {}：选择抽牌堆中 1 张牌"
            "添加附魔【{}】 ==="
        ).format(
            card.name,
            enchantment_name
        ),
        command_hint="用法：/card abyss_index 0。",
        block_message=(
            "当前需要先处理深渊索引选择。"
            "用法：/card abyss_index 0。"
        ),
        options=options,
        payload={
            "enchantment": enchantment_id,
        }
    ))

    logs = [
        (
            "=== {}：选择抽牌堆中 1 张牌"
            "添加附魔【{}】 ==="
        ).format(
            card.name,
            enchantment_name
        )
    ]

    for index, target_card in enumerate(options):
        logs.append("[{}] {}".format(
            index,
            target_card.summary_text()
        ))

    logs.append("")
    logs.append("用法：/card abyss_index 0。")

    return logs

@register_effect("request_synchronization_choice")
def handle_request_synchronization_choice(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    add_exhaust = bool(effect.get("add_exhaust", True))

    from game.zone.resonance import collect_non_exhaust_pile_cards
    from game.pending_choice import PendingChoice, set_pending_choice

    options = collect_non_exhaust_pile_cards(player)

    if not options:
        return ["【{}】没有可选择的消耗堆以外卡牌。".format(card.name)]

    set_pending_choice(game_state, PendingChoice(
        kind="synchronization",
        source=card.name,
        prompt="=== {}：选择 1 张消耗堆以外的牌添加共鸣{} ===".format(
            card.name,
            "和消耗" if add_exhaust else ""
        ),
        command_hint="用法：/card sync 0。",
        block_message="当前需要先处理同调选择。用法：/card sync 0。",
        options=options,
        payload={
            "add_exhaust": add_exhaust,
        }
    ))

    logs = [
        "=== {}：选择 1 张消耗堆以外的牌添加共鸣{} ===".format(
            card.name,
            "和消耗" if add_exhaust else ""
        )
    ]

    for index, item in enumerate(options):
        pile_label = item.get("pile_label", "")
        target_card = item.get("card")
        logs.append("[{}] {}：{}".format(index, pile_label, target_card.summary_text()))

    logs.append("")
    logs.append("用法：/card sync 0。")

    return logs

@register_effect("precipitate_zone_to_plating")
def handle_precipitate_zone_to_plating(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    zone = getattr(game_state, "active_zone", None)
    if zone is None:
        logs.append("【{}】没有已展开的晶或阴 Zone，无法析出。".format(card.name))
        return logs

    try:
        if zone.is_expired():
            logs.append("【{}】当前 Zone 已失效，无法析出。".format(card.name))
            return logs
    except Exception:
        pass

    element = str(getattr(zone, "element", "") or "").strip().lower()
    if element not in ("crystal", "shade"):
        logs.append("【{}】只能破坏晶或阴 Zone，当前 Zone 为 {}。".format(
            card.name,
            element or "无"
        ))
        return logs

    is_extreme = bool(getattr(zone, "is_extreme", False))
    zone_name = getattr(zone, "name", "Zone")

    card_id_by_element = {
        "crystal": "card.crystal_plating",
        "shade": "card.abyss_plating",
    }
    element_name = {
        "crystal": "晶",
        "shade": "阴",
    }.get(element, element)

    plating_card_id = card_id_by_element[element]

    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card

    plating = create_card(plating_card_id)
    if is_extreme:
        plating = upgrade_card(plating)

    setattr(plating, "temporary", True)
    setattr(plating, "created_in_battle", True)

    game_state.active_zone = None

    player.draw_pile.append(plating)
    random.shuffle(player.draw_pile)

    if is_extreme:
        logs.append("【{}】破坏了当前极{} Zone：{}。".format(
            card.name,
            element_name,
            zone_name
        ))
        logs.append("将 1 张【{}】加入抽牌堆，并重洗抽牌堆。".format(
            plating.name
        ))
    else:
        logs.append("【{}】破坏了当前{} Zone：{}。".format(
            card.name,
            element_name,
            zone_name
        ))
        logs.append("将 1 张【{}】加入抽牌堆，并重洗抽牌堆。".format(
            plating.name
        ))

    return logs

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

@register_effect("choose_non_exhaust_pile_card_add_replay")
def handle_choose_non_exhaust_pile_card_add_replay(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    count = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("count", 1),
        source=player,
        target=player,
        effect_context=effect_context
    )
    count = int(count)

    if count <= 0:
        return ["【{}】不需要选择映照目标。".format(card.name)]

    total_times = int(effect_context.get("_total_replay_times", 1) or 1)

    # 被重放时，把多次选择合并成一次 pending，避免后续重放覆盖前一次 pending。
    if effect_context.get("_radiant_reflection_pending_created", False):
        return []

    effect_context["_radiant_reflection_pending_created"] = True

    max_count = count * max(1, total_times)

    options = []

    pile_specs = [
        ("hand", "手牌", getattr(player, "hand", []) or []),
        ("draw_pile", "抽牌堆", getattr(player, "draw_pile", []) or []),
        ("discard_pile", "弃牌堆", getattr(player, "discard_pile", []) or []),
    ]

    for pile_name, pile_label, pile_cards in pile_specs:
        for pile_card in list(pile_cards):
            options.append({
                "pile_name": pile_name,
                "pile_label": pile_label,
                "card": pile_card,
            })

    if not options:
        return ["【{}】没有可选择的非消耗堆卡牌。".format(card.name)]

    if max_count > len(options):
        max_count = len(options)

    from game.pending_choice import PendingChoice, set_pending_choice

    set_pending_choice(game_state, PendingChoice(
        kind="radiant_reflection",
        source=card.name,
        prompt="=== {}：选择至多 {} 张消耗堆以外的牌添加重放 1 ===".format(card.name, max_count),
        command_hint="用法：/card reflect 0 或 /card reflect 0,1。",
        block_message="当前需要先处理辉晶映照选择。用法：/card reflect 0 或 /card reflect 0,1。",
        options=options,
        payload={
            "max_count": max_count,
        }
    ))

    logs = [
        "=== {}：选择至多 {} 张消耗堆以外的牌添加重放 1 ===".format(card.name, max_count)
    ]

    for index, item in enumerate(options):
        pile_label = item.get("pile_label", "")
        pile_card = item.get("card")
        logs.append("[{}] {}：{}".format(index, pile_label, pile_card.summary_text()))

    logs.append("")
    logs.append("用法：/card reflect 0 或 /card reflect 0,1。")

    return logs

@register_effect("choose_hand_attack_without_element_apply_plating")
def handle_choose_hand_attack_without_element_apply_plating(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    element = str(effect.get("element", "") or "").strip().lower()
    suffix = str(effect.get("suffix", "") or "")
    allowed_card_types = effect.get("allowed_card_types", ["attack"])
    allowed_card_types = [str(t) for t in allowed_card_types if str(t)]
    if not allowed_card_types:
        allowed_card_types = ["attack"]

    type_text_map = {
        ("attack",): "攻击牌",
        ("skill",): "技能牌",
        ("attack", "skill"): "攻击牌或技能牌",
    }
    type_text = type_text_map.get(tuple(allowed_card_types), " / ".join(allowed_card_types))

    if not element:
        return ["【{}】镀层失败：缺少属性。".format(card.name)]

    if not suffix:
        suffix = {
            "shade": "·阴",
            "crystal": "·晶",
        }.get(element, "·{}".format(element))

    require_gain_block = bool(effect.get("require_gain_block", False))

    options = [
        hand_card
        for hand_card in list(getattr(player, "hand", []) or [])
        if getattr(hand_card, "card_type", "") in allowed_card_types
        and not str(getattr(hand_card, "attack_element", "") or "").strip()
        and (not require_gain_block or card_has_gain_block_effect(hand_card))
    ]

    if not options:
        return ["【{}】没有可添加镀层的无属性{}。".format(card.name, type_text)]

    from game.pending_choice import PendingChoice, set_pending_choice

    set_pending_choice(game_state, PendingChoice(
        kind="element_plating",
        source=card.name,
        prompt="=== {}：选择 1 张无属性{}添加镀层 ===".format(card.name, type_text),
        command_hint="用法：/card plate 0\nplate 等效 plating，镀层，选择镀层。",
        block_message="当前需要先处理镀层选择。用法：/card plate 0。",
        options=options,
        payload={
            "element": element,
            "suffix": suffix,
            "allowed_card_types": allowed_card_types,
            "type_text": type_text,
            "require_gain_block": require_gain_block,
        }
    ))

    logs = [
        "=== {}：选择 1 张无属性{}添加{}镀层 ===".format(
            card.name,
            type_text,
            {
                "shade": "阴",
                "crystal": "晶",
                "earth": "地",
            }.get(element, element)
        )
    ]

    for index, hand_card in enumerate(options):
        logs.append("[{}] {}".format(index, hand_card.summary_text()))

    logs.append("")
    logs.append("用法：/card plate 0")

    return logs

@register_effect("shuffle_discard_into_draw")
def handle_shuffle_discard_into_draw(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    logs = []
    if not player.discard_pile:
        logs.append("弃牌堆为空，没有牌洗入抽牌堆。")
        return logs
    player.draw_pile.extend(player.discard_pile)
    count = len(player.discard_pile)
    player.discard_pile = []
    random.shuffle(player.draw_pile)
    logs.append("将弃牌堆的 {} 张牌洗入抽牌堆。".format(count))
    for relic in getattr(player, "relics", []) or []:
        handler = getattr(relic, "on_shuffle", None)
        if handler is None:
            continue
        result = handler(game_state, player)
        if result:
            logs.extend(result)
    return logs


@register_effect("draw_if_no_attack_in_hand")
def handle_draw_if_no_attack_in_hand(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    for hand_card in getattr(player, "hand", []) or []:
        if getattr(hand_card, "card_type", "") == "attack":
            return ["手牌中有攻击牌，【{}】没有抽牌。".format(card.name)]
    return handle_draw_cards(game_state, card, effect, target_index, effect_context)


def get_random_card_candidates(card_type=None, colorless_only=False, exclude_card_ids=None):
    from data.card.AAAregistry import CARD_REGISTRY, create_card
    from data.content_gate import is_content_enabled
    exclude_card_ids = set(exclude_card_ids or [])
    candidates = []
    for candidate_card_id in CARD_REGISTRY:
        if candidate_card_id in exclude_card_ids:
            continue
        if not is_content_enabled("card", candidate_card_id):
            continue
        try:
            candidate = create_card(candidate_card_id)
        except Exception:
            continue
        if colorless_only and getattr(candidate, "owner_character_id", "") != "":
            continue
        if getattr(candidate, "card_type", "") in ("status", "curse"):
            continue
        if getattr(candidate, "quantity", "") in ("starting", "status", "curse", "test"):
            continue
        if card_type and getattr(candidate, "card_type", "") != card_type:
            continue
        candidates.append(candidate_card_id)
    return candidates


def prepare_generated_card(card, temp_cost_zero=False, upgrade=False):
    setattr(card, "temporary", True)
    setattr(card, "created_in_battle", True)
    if upgrade:
        from data.card.upgrade_rules import upgrade_card
        card = upgrade_card(card)
        setattr(card, "temporary", True)
        setattr(card, "created_in_battle", True)
    if temp_cost_zero and getattr(card, "card_type", "") not in ("status", "curse"):
        try:
            card.cost = 0
        except Exception:
            setattr(card, "temporary_cost_override", 0)
    return card


def add_card_to_hand_or_discard(player, card, logs, source_name):
    if player.is_hand_full():
        player.discard_pile.append(card)
        logs.append("【{}】生成【{}】，但手牌已满，进入弃牌堆。".format(source_name, card.name))
        return
    player.hand.append(card)
    logs.append("【{}】生成【{}】，加入手牌。".format(source_name, card.name))


@register_effect("add_random_cards_to_draw_pile_temp_cost_zero")
def handle_add_random_cards_to_draw_pile_temp_cost_zero(game_state, card, effect, target_index, effect_context):
    from data.card.AAAregistry import create_card
    count = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 1),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    )
    count = int(count)
    card_type = effect.get("card_type")
    candidates = get_random_card_candidates(
        card_type=card_type,
        colorless_only=bool(effect.get("colorless_only", False)),
        exclude_card_ids=effect.get("exclude_card_ids", [])
    )
    if count <= 0 or not candidates:
        return ["【{}】没有生成卡牌。".format(card.name)]
    logs = []
    added = []
    for _ in range(count):
        new_card = prepare_generated_card(
            create_card(random.choice(candidates)),
            temp_cost_zero=True,
            upgrade=bool(effect.get("upgrade", False))
        )
        game_state.player.draw_pile.append(new_card)
        added.append(new_card.name)
    random.shuffle(game_state.player.draw_pile)
    logs.append("【{}】将 {} 张随机{}牌加入抽牌堆，它们在本场战斗中耗能为 0。".format(
        card.name,
        len(added),
        {"attack": "攻击", "skill": "技能", "power": "能力"}.get(card_type, "")
    ))
    return logs


@register_effect("add_random_colorless_to_hand_temp_cost_zero")
def handle_add_random_colorless_to_hand_temp_cost_zero(game_state, card, effect, target_index, effect_context):
    from data.card.AAAregistry import create_card
    count = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 1),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    )
    count = int(count)
    candidates = get_random_card_candidates(
        colorless_only=True,
        exclude_card_ids=effect.get("exclude_card_ids", [])
    )
    if count <= 0 or not candidates:
        return ["【{}】没有生成无色牌。".format(card.name)]
    logs = []
    for _ in range(count):
        new_card = prepare_generated_card(
            create_card(random.choice(candidates)),
            temp_cost_zero=bool(effect.get("temp_cost_zero", False)),
            upgrade=bool(effect.get("upgrade", False))
        )
        add_card_to_hand_or_discard(game_state.player, new_card, logs, card.name)
    return logs


@register_effect("request_discovery_card")
def handle_request_discovery_card(game_state, card, effect, target_index, effect_context):
    from data.card.AAAregistry import create_card
    candidates = get_random_card_candidates(exclude_card_ids=effect.get("exclude_card_ids", []))
    if not candidates:
        return ["【{}】没有可发现的卡牌。".format(card.name)]
    option_count = int(effect.get("option_count", 3))
    selected_ids = random.sample(candidates, option_count) if len(candidates) >= option_count else [
        random.choice(candidates) for _ in range(option_count)
    ]
    options = [
        prepare_generated_card(create_card(card_id), temp_cost_zero=True)
        for card_id in selected_ids
    ]
    game_state.pending_toolbox_selection = True
    game_state.pending_toolbox_source = card.name
    game_state.pending_toolbox_options = options
    game_state.pending_toolbox_mode = "add_choice_to_hand"
    game_state.pending_toolbox_temp_cost_zero = True
    logs = ["=== {}：选择 1 张牌加入手牌，本回合耗能为 0 ===".format(card.name)]
    for index, option in enumerate(options):
        logs.append("[{}] {}".format(index, option.summary_text()))
    logs.append("使用 /card toolbox 0 选择。")
    return logs


@register_effect("reduce_hand_costs_to")
def handle_reduce_hand_costs_to(game_state, card, effect, target_index, effect_context):
    target_cost = int(effect.get("cost", 1))
    duration = effect.get("duration", "turn")
    changed = 0
    for hand_card in getattr(game_state.player, "hand", []) or []:
        if getattr(hand_card, "card_type", "") in ("status", "curse"):
            continue
        try:
            current_cost = int(getattr(hand_card, "cost", 0))
        except (TypeError, ValueError):
            continue
        if current_cost <= target_cost:
            continue
        if duration == "combat":
            hand_card.cost = target_cost
        else:
            setattr(hand_card, "temporary_cost_override", target_cost)
        changed += 1
    if changed <= 0:
        return ["【{}】没有降低任何手牌费用。".format(card.name)]
    return ["【{}】使 {} 张手牌的耗能降低到 {}。".format(card.name, changed, target_cost)]


@register_effect("random_hand_card_cost_zero")
def handle_random_hand_card_cost_zero(game_state, card, effect, target_index, effect_context):
    options = [
        hand_card for hand_card in getattr(game_state.player, "hand", []) or []
        if getattr(hand_card, "card_type", "") not in ("status", "curse")
    ]
    if not options:
        return ["【{}】没有可降费的手牌。".format(card.name)]
    chosen = random.choice(options)
    chosen.cost = 0
    return ["【{}】使【{}】在本场战斗中耗能变为 0。".format(card.name, chosen.name)]


@register_effect("request_hand_to_draw_bottom_temp_cost_zero")
def handle_request_hand_to_draw_bottom_temp_cost_zero(game_state, card, effect, target_index, effect_context):
    options = [
        hand_card for hand_card in getattr(game_state.player, "hand", []) or []
        if hand_card is not card
    ]
    if not options:
        return ["手牌中没有可以放到抽牌堆底的牌。"]
    from game.pending_choice import PendingChoice, set_pending_choice
    set_pending_choice(game_state, PendingChoice(
        kind="hand_to_draw_top",
        source=card.name,
        prompt="请选择 1 张手牌放到抽牌堆底并使其耗能变为 0：/card handtop 0。",
        command_hint="handtop 等效 hand_top，warcry，置顶手牌，手牌置顶。",
        block_message="当前需要先处理手牌放回抽牌堆选择。用法：/card handtop 0。",
        options=options,
        payload={"destination": "bottom", "set_cost_zero": True}
    ))
    logs = ["请选择 1 张手牌放到抽牌堆底并使其耗能变为 0：/card handtop 0。", "可选牌："]
    for index, hand_card in enumerate(options):
        logs.append("[{}] {}".format(index, hand_card.summary_text()))
    return logs


@register_effect("request_draw_pile_card_to_hand")
def handle_request_draw_pile_card_to_hand(game_state, card, effect, target_index, effect_context):
    required_type = effect.get("card_type")
    options = [
        pile_card for pile_card in getattr(game_state.player, "draw_pile", []) or []
        if not required_type or getattr(pile_card, "card_type", "") == required_type
    ]
    if not options:
        return ["抽牌堆中没有可选择的{}牌。".format({"attack": "攻击", "skill": "技能"}.get(required_type, ""))]
    game_state.pending_toolbox_selection = True
    game_state.pending_toolbox_source = card.name
    game_state.pending_toolbox_options = options
    game_state.pending_toolbox_mode = "draw_pile_to_hand"
    logs = ["=== {}：选择 1 张{}牌加入手牌 ===".format(card.name, {"attack": "攻击", "skill": "技能"}.get(required_type, ""))]
    for index, option in enumerate(options):
        logs.append("[{}] {}".format(index, option.summary_text()))
    logs.append("使用 /card toolbox 0 选择。")
    return logs


@register_effect("request_exhaust_multiple_hand_cards")
def handle_request_exhaust_multiple_hand_cards(game_state, card, effect, target_index, effect_context):
    options = list(enumerate(getattr(game_state.player, "hand", []) or []))
    if not options:
        return ["手牌为空，没有可以消耗的牌。"]
    max_count = int(resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("max_count", 1),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    ))
    game_state.pending_elixir_selection = True
    game_state.pending_elixir_source = card.name
    game_state.pending_elixir_options = options
    game_state.pending_elixir_max_count = max_count
    logs = ["=== {}：选择最多 {} 张手牌消耗 ===".format(card.name, max_count), ""]
    for index, hand_card in options:
        logs.append("[{}] {}".format(index, hand_card.summary_text()))
    logs.append("")
    logs.append("使用 /card elixir 0,1,2；不消耗则 /card elixir none。")
    return logs


@register_effect("move_random_draw_pile_cards_to_hand")
def handle_move_random_draw_pile_cards_to_hand(game_state, card, effect, target_index, effect_context):
    count = int(resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 1),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    ))
    card_type = effect.get("card_type")
    player = game_state.player
    options = [
        pile_card for pile_card in list(getattr(player, "draw_pile", []) or [])
        if not card_type or getattr(pile_card, "card_type", "") == card_type
    ]
    if count <= 0 or not options:
        return ["抽牌堆中没有可加入手牌的{}牌。".format({"attack": "攻击", "skill": "技能"}.get(card_type, ""))]
    random.shuffle(options)
    logs = []
    for chosen in options[:count]:
        if chosen not in player.draw_pile:
            continue
        player.draw_pile.remove(chosen)
        add_card_to_hand_or_discard(player, chosen, logs, card.name)
    return logs


@register_effect("gain_bomb")
def handle_gain_bomb(game_state, card, effect, target_index, effect_context):
    damage = int(resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("damage", 40),
        source=game_state.player,
        target=game_state.player,
        effect_context=effect_context,
    ))
    game_state.player.gain_status("the_bomb", damage)
    setattr(game_state.player, "_the_bomb_turns", int(effect.get("turns", 3)))
    return ["【{}】已设置炸弹：{} 回合后对所有敌人造成 {} 点伤害。".format(card.name, int(effect.get("turns", 3)), damage)]


@register_effect("gain_rock_layer")
def handle_gain_rock_layer(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    target_key = effect.get("target", "self")
    target_entity = get_effect_target_entity(
        game_state=game_state,
        target_key=target_key,
        target_index=target_index
    )

    if target_entity is None:
        return ["【{}】岩层目标无效。".format(card.name)]

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 0),
        source=player,
        target=target_entity,
        effect_context=effect_context
    )

    from game.suzuri_rock import gain_rock_layer

    return gain_rock_layer(
        game_state=game_state,
        target=target_entity,
        amount=amount,
        source_name=card.name
    )


@register_effect("consume_rock_layer_to_context")
def handle_consume_rock_layer_to_context(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    context_key = str(effect.get("context_key", "consumed_rock") or "consumed_rock")
    mode = str(effect.get("mode", "amount") or "amount")

    from game.suzuri_rock import consume_rock_layer, calculate_ratio_rock_consume

    current = get_status_value(player, "rock_layer")

    if mode == "all":
        consume_amount = current
    elif mode == "ratio":
        ratio = float(effect.get("ratio", 1.0) or 1.0)
        rounding = str(effect.get("rounding", "ceil") or "ceil")
        consume_amount = calculate_ratio_rock_consume(current, ratio, rounding=rounding)
    else:
        consume_amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 0),
            source=player,
            target=player,
            effect_context=effect_context
        )

    consumed, logs = consume_rock_layer(
        game_state=game_state,
        target=player,
        amount=consume_amount,
        source_name=card.name
    )

    effect_context[context_key] = consumed

    return logs


@register_effect("request_fossil_exhaust_hand_gain_rock_layer")
def handle_request_fossil_exhaust_hand_gain_rock_layer(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    options = list(enumerate(getattr(player, "hand", []) or []))

    draw_after = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("draw_after", 0),
        source=player,
        target=player,
        effect_context=effect_context
    )
    draw_after = int(draw_after)

    if not options:
        logs = ["【{}】当前没有可消耗的手牌。".format(card.name)]
        if draw_after > 0:
            logs.extend(player.draw_cards(draw_after, game_state=game_state, draw_source=card.card_id))
        return logs

    from game.pending_choice import PendingChoice, set_pending_choice

    set_pending_choice(game_state, PendingChoice(
        kind="fossil_exhaust_hand",
        source=card.name,
        prompt="=== {}：选择任意数量手牌消耗 ===".format(card.name),
        command_hint="用法：/card fossil 0,1,2；不消耗则 /card fossil none。",
        block_message="当前需要先处理化石选择。用法：/card fossil 0,1,2；不消耗则 /card fossil none。",
        options=options,
        payload={
            "draw_after": draw_after,
        }
    ))

    logs = [
        "=== {}：选择任意数量手牌消耗 ===".format(card.name),
        "每消耗 1 张手牌，获得 1 层岩层。",
        ""
    ]

    for index, hand_card in options:
        logs.append("[{}] {}".format(index, hand_card.summary_text()))

    logs.append("")
    logs.append("用法：/card fossil 0,1,2；不消耗则 /card fossil none。")

    return logs

@register_effect("consume_status_gain_energy_if_present")
def handle_consume_status_gain_energy_if_present(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    status_key = str(effect.get("status", "") or "")
    if not status_key:
        return ["【{}】效果失败：缺少要消耗的状态。".format(card.name)]

    current = get_status_value(player, status_key)
    if current <= 0:
        from game.status.status_defs import get_status_name
        logs.append("{} 没有{}，【{}】未获得额外费用。".format(
            player.name,
            get_status_name(status_key),
            card.name
        ))
        return logs

    energy = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("energy", 0),
        source=player,
        target=player,
        effect_context=effect_context
    )
    energy = int(energy)

    from game.status.status_defs import get_status_name

    if status_key == "rock_layer":
        from game.suzuri_rock import consume_rock_layer
        consumed, rock_logs = consume_rock_layer(
            game_state=game_state,
            target=player,
            amount=current,
            source_name=card.name
        )
        logs.extend(rock_logs)
    else:
        player.statuses.remove(status_key)
        logs.append("【{}】消耗 {} 层{}。".format(
            card.name,
            current,
            get_status_name(status_key)
        ))

    if energy > 0:
        player.cost += energy
        logs.append("{} 获得 {} 点费用。当前费用：{}。".format(
            player.name,
            energy,
            player.cost
        ))

    return logs

@register_effect("gain_status_with_zone_bonus")
def handle_gain_status_with_zone_bonus(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    status_key = str(effect.get("status", "") or "")
    if not status_key:
        return ["【{}】效果失败：缺少状态。".format(card.name)]

    target_key = effect.get("target", "self")
    target_entity = get_effect_target_entity(
        game_state=game_state,
        target_key=target_key,
        target_index=target_index
    )

    if target_entity is None:
        return ["【{}】状态目标无效。".format(card.name)]

    zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
    local_context = make_zone_effect_context(effect_context, zone_element)

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 0),
        source=player,
        target=target_entity,
        effect_context=local_context
    )
    amount = int(amount)

    required_zone_element = str(effect.get("zone_element", "") or "").strip().lower()
    bonus = 0

    if required_zone_element and zone_element == required_zone_element:
        bonus = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("zone_bonus", 0),
            source=player,
            target=target_entity,
            effect_context=local_context
        )
        bonus = int(bonus)

    total_amount = amount + bonus

    if bonus > 0:
        logs.append("地 Zone 使【{}】额外获得 {} 层隐蔽石砾。".format(
            card.name,
            bonus
        ))

    if target_entity is not player and hasattr(target_entity, "enemy_id"):
        from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
        logs.extend(apply_status_with_player_relics(
            game_state=game_state,
            source=player,
            target=target_entity,
            status_key=status_key,
            amount=total_amount
        ))
        return logs

    if hasattr(target_entity, "gain_status_with_result"):
        result = target_entity.gain_status_with_result(status_key, total_amount)

        from game.status.status_gain import format_status_gain_log
        logs.append(format_status_gain_log(
            target_entity,
            status_key,
            total_amount,
            result
        ))
        return logs

    current = target_entity.gain_status(status_key, total_amount)

    from game.status.status_defs import get_status_name
    logs.append("{} 获得 {} 层{}。当前{}：{}。".format(
        target_entity.name,
        total_amount,
        get_status_name(status_key),
        get_status_name(status_key),
        current
    ))

    return logs

@register_effect("consume_status_amount")
def handle_consume_status_amount(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    status_key = str(effect.get("status", "") or "")
    if not status_key:
        return ["【{}】效果失败：缺少要消耗的状态。".format(card.name)]

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount", 1),
        source=player,
        target=player,
        effect_context=effect_context
    )
    amount = int(amount)

    if amount <= 0:
        return logs

    current = get_status_value(player, status_key)

    from game.status.status_defs import get_status_name
    status_name = get_status_name(status_key)

    if current < amount:
        logs.append("【{}】需要消耗 {} 层{}，当前只有 {} 层，效果未发动。".format(
            card.name,
            amount,
            status_name,
            current
        ))
        return logs

    if status_key == "rock_layer":
        from game.suzuri_rock import consume_rock_layer

        consumed, rock_logs = consume_rock_layer(
            game_state=game_state,
            target=player,
            amount=amount,
            source_name=card.name
        )
        logs.extend(rock_logs)
        return logs

    remaining = player.statuses.add(status_key, -amount)

    logs.append("【{}】消耗 {} 层{}。当前{}：{}。".format(
        card.name,
        amount,
        status_name,
        status_name,
        remaining
    ))

    return logs

@register_effect("choose_hand_add_retain")
def handle_choose_hand_add_retain(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    count = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("count", 1),
        source=player,
        target=player,
        effect_context=effect_context
    )
    count = int(count)

    if count <= 0:
        return ["【{}】不需要选择保留牌。".format(card.name)]

    from game.constants import KEYWORD_RETAIN

    hand = list(getattr(player, "hand", []) or [])

    selectable_indices = [
        index
        for index, hand_card in enumerate(hand)
        if KEYWORD_RETAIN not in getattr(hand_card, "keywords", [])
    ]

    if not selectable_indices:
        return ["【{}】没有可添加保留的手牌。".format(card.name)]

    from game.pending_choice import PendingChoice, set_pending_choice

    set_pending_choice(game_state, PendingChoice(
        kind="retain_hand",
        source=card.name,
        prompt="=== {}：选择至多 {} 张手牌添加保留 ===".format(card.name, count),
        command_hint="用法：/card retain 手牌编号，例如 /card retain 4 或 /card retain 4,6；跳过则 /card retain skip。",
        block_message="当前需要先处理保留选择。用法：/card retain 手牌编号，或 /card retain skip。",
        options=[],
        payload={
            "max_count": count,
        }
    ))

    logs = [
        "=== {}：选择至多 {} 张手牌添加保留 ===".format(card.name, count),
        "编号使用当前手牌编号。"
    ]

    for index, hand_card in enumerate(hand):
        if KEYWORD_RETAIN in getattr(hand_card, "keywords", []):
            logs.append("[{}] {}（已有保留）".format(index, hand_card.summary_text()))
        else:
            logs.append("[{}] {}".format(index, hand_card.summary_text()))

    logs.append("")
    logs.append("用法：/card retain 手牌编号，例如 /card retain 4 或 /card retain 4,6；跳过则 /card retain skip。")

    return logs

@register_effect("gain_rock_polishing_counter")
def handle_gain_rock_polishing_counter(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    threshold = int(effect.get("threshold", 9) or 9)

    from game.suzuri_rock import add_rock_polishing_counter

    return add_rock_polishing_counter(
        game_state=game_state,
        target=player,
        threshold=threshold,
        source_name=card.name
    )

@register_effect("gain_living_soil_counter")
def handle_gain_living_soil_counter(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    threshold = int(effect.get("threshold", 9) or 9)

    from game.suzuri_rock import add_living_soil_counter

    return add_living_soil_counter(
        game_state=game_state,
        target=player,
        threshold=threshold,
        source_name=card.name
    )

def trigger_beat_of_death_after_card_resolution(
        game_state,
        card
    ):
    logs = []
    if game_state is None:
        return logs
    # apply_card_effects 同时被药水复用。
    # 药水没有 card_id，不触发死亡律动。
    if not getattr(card, "card_id", ""):
        return logs
    player = getattr(game_state, "player", None)
    if player is None or not player.is_alive():
        return logs
    for enemy in getattr(game_state, "enemies", []) or []:
        if not enemy.is_alive():
            continue
        amount = get_status_value(
            enemy,
            "beat_of_death"
        )
        if amount <= 0:
            continue
        logs.append(
            "{}的死亡律动触发，造成 {} 点伤害。".format(
                enemy.name,
                amount
            )
        )
        logs.extend(deal_damage(
            game_state=game_state,
            source=enemy,
            target=player,
            amount=amount,
            damage_kind="effect",
            card=card,
            is_reaction_damage=True,
            ignore_block=False
        ))
        if not player.is_alive():
            break
    return logs

def apply_card_effect(game_state, card, effect, target_index, effect_context=None):
    """
    执行单个卡牌效果。
    返回 logs。
    """
    if effect_context is None:
        effect_context = {}
    logs = []

    op = effect.get("op")
    handler = EFFECT_HANDLERS.get(op)
    if handler is not None:
        return handler(
            game_state=game_state,
            card=card,
            effect=effect,
            target_index=target_index,
            effect_context=effect_context
        )

    if op == "deal_damage":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)
        target_key = effect.get("target", "selected_enemy")

        times = resolve_effect_times(
            game_state=game_state,
            card=card,
            effect=effect,
            effect_context=local_context
        )

        if times <= 0:
            logs.append("伤害次数为 0，【{}】没有造成伤害。".format(card.name))
            return logs

        if should_convert_enemy_target_to_all(game_state, zone_element, target_key):
            logs.append("雷 Zone 使【{}】的目标变为全体。".format(card.name))

            for hit_index in range(times):
                if game_state.battle_over:
                    logs.append("战斗已经结束，后续全体伤害不再结算。")
                    break

                alive_enemies = get_all_alive_enemies(game_state)
                if not alive_enemies:
                    logs.append("没有可攻击的敌人。")
                    break

                if times > 1:
                    logs.append("全体伤害第 {}/{} 次：".format(
                        hit_index + 1,
                        times
                    ))

                for target_entity in alive_enemies:
                    if game_state.battle_over:
                        break

                    if not target_entity.is_alive():
                        continue

                    deal_card_attack_damage_to_target(
                        game_state=game_state,
                        card=card,
                        effect=effect,
                        target_entity=target_entity,
                        effect_context=local_context,
                        attack_type=attack_type,
                        attack_element=attack_element,
                        zone_element=zone_element,
                        logs=logs,
                        prefix="【{card.name}】对 {target.name} 造成 {damage} 点攻击伤害。"
                    )

            return logs

        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs

        compact_fixed_target_multi_hit = (
            times > 1
            and target_key in ("selected_enemy", "enemy")
            and target_entity is not None
        )

        if compact_fixed_target_multi_hit:
            logs.append("【{}】对 {} 连续结算 {} 次攻击。".format(
                card.name,
                target_entity.name,
                times
            ))

        for hit_index in range(times):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续伤害不再结算。")
                break

            if not target_entity.is_alive():
                logs.append("目标已被击败，后续伤害不再结算。")
                break

            if times > 1 and not compact_fixed_target_multi_hit:
                logs.append("【{}】第 {}/{} 次伤害：".format(
                    card.name,
                    hit_index + 1,
                    times
                ))

            deal_card_attack_damage_to_target(
                game_state=game_state,
                card=card,
                effect=effect,
                target_entity=target_entity,
                effect_context=local_context,
                attack_type=attack_type,
                attack_element=attack_element,
                zone_element=zone_element,
                logs=logs,
                prefix=(
                    ""
                    if compact_fixed_target_multi_hit
                    else "【{card.name}】造成 {damage} 点攻击伤害。"
                )
            )

        return logs
    
    if op == "deal_damage_random_enemies":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)
        times = resolve_effect_times(
            game_state=game_state,
            card=card,
            effect=effect,
            effect_context=local_context
        )
        if times <= 0:
            logs.append("随机伤害次数为 0，【{}】没有造成伤害。".format(card.name))
            return logs

        if should_convert_enemy_target_to_all(game_state, zone_element, "random_enemy"):
            logs.append("雷 Zone 使【{}】的随机目标变为全体。".format(card.name))
            for hit_index in range(times):
                alive_enemies = get_all_alive_enemies(game_state)
                if not alive_enemies:
                    logs.append("没有可攻击的敌人。")
                    break
                logs.append("全体随机替代效果第 {}/{} 次：".format(hit_index + 1, times))
                for target_entity in alive_enemies:
                    if game_state.battle_over:
                        break
                    deal_card_attack_damage_to_target(
                        game_state=game_state,
                        card=card,
                        effect=effect,
                        target_entity=target_entity,
                        effect_context=local_context,
                        attack_type=attack_type,
                        attack_element=attack_element,
                        zone_element=zone_element,
                        logs=logs,
                        prefix="【{card.name}】对 {target.name} 造成 {damage} 点攻击伤害。"
                    )
                if game_state.battle_over:
                    break
            return logs

        unique_targets = bool(effect.get("unique_targets", False))

        compact_random_single_target_multi_hit = False
        compact_random_target = None

        if times > 1 and not unique_targets:
            alive_enemies_for_log = get_alive_enemies(game_state)
            if len(alive_enemies_for_log) == 1:
                compact_random_single_target_multi_hit = True
                compact_random_target = alive_enemies_for_log[0]
                logs.append("【{}】随机目标仅有 {}，连续结算 {} 次攻击。".format(
                    card.name,
                    compact_random_target.name,
                    times
                ))

        if unique_targets:
            candidate_pool = get_alive_enemies(game_state)
        else:
            candidate_pool = None

        for hit_index in range(times):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续随机伤害不再结算。")
                break
            if game_state.is_all_enemies_dead():
                logs.append("所有敌人已被击败，后续随机伤害不再结算。")
                break
            if unique_targets:
                candidate_pool = [enemy for enemy in candidate_pool if enemy.is_alive()]
                if not candidate_pool:
                    logs.append("没有更多可随机命中的敌人。")
                    break
                target_entity = random.choice(candidate_pool)
                candidate_pool.remove(target_entity)
            else:
                alive_enemies = get_alive_enemies(game_state)
                if not alive_enemies:
                    logs.append("没有可攻击的敌人。")
                    break
                target_entity = random.choice(alive_enemies)

            damage = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("amount"),
                source=game_state.player,
                target=target_entity,
                damage_source="played_card",
                effect_context=local_context,
                attack_type=attack_type,
                attack_element=attack_element
            )
            if not compact_random_single_target_multi_hit:
                logs.append("【{}】随机命中 {}，造成 {} 点攻击伤害。第 {}/{} 次。".format(
                    card.name,
                    target_entity.name,
                    damage,
                    hit_index + 1,
                    times
                ))
            logs.extend(deal_damage(
                game_state=game_state,
                source=game_state.player,
                target=target_entity,
                amount=damage,
                damage_kind="attack",
                card=card,
                attack_type=attack_type,
                attack_element=attack_element,
                zone_element=zone_element
            ))
            from game.zone.zone_utils import apply_fire_zone_burn
            apply_fire_zone_burn(
                game_state=game_state,
                source=game_state.player,
                target=target_entity,
                card=card,
                zone_element=zone_element,
                logs=logs
            )
        return logs

    if op == "deal_damage_all_enemies":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        times = resolve_effect_times(
            game_state=game_state,
            card=card,
            effect=effect,
            effect_context=local_context
        )

        if times <= 0:
            logs.append("全体伤害次数为 0，【{}】没有造成伤害。".format(card.name))
            return logs

        for hit_index in range(times):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续全体伤害不再结算。")
                break

            alive_enemies = get_all_alive_enemies(game_state)
            if not alive_enemies:
                logs.append("没有可攻击的敌人。")
                break

            if times > 1:
                logs.append("全体伤害第 {}/{} 次：".format(
                    hit_index + 1,
                    times
                ))

            for target_entity in alive_enemies:
                if game_state.battle_over:
                    break

                if not target_entity.is_alive():
                    continue

                deal_card_attack_damage_to_target(
                    game_state=game_state,
                    card=card,
                    effect=effect,
                    target_entity=target_entity,
                    effect_context=local_context,
                    attack_type=attack_type,
                    attack_element=attack_element,
                    zone_element=zone_element,
                    logs=logs,
                    prefix="【{card.name}】对 {target.name} 造成 {damage} 点攻击伤害。"
                )
        return logs

    if op == "deal_damage_gain_max_hp_on_non_minion_kill":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs

        damage = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            damage_source="played_card",
            effect_context=local_context,
            attack_type=attack_type,
            attack_element=attack_element
        )

        was_alive = target_entity.is_alive()
        was_minion = bool(getattr(target_entity, "is_minion", False))

        logs.append("【{}】造成 {} 点攻击伤害。".format(
            card.name,
            damage
        ))

        logs.extend(deal_damage(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            amount=damage,
            damage_kind="attack",
            card=card,
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        ))

        from game.zone.zone_utils import apply_fire_zone_burn
        apply_fire_zone_burn(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            card=card,
            zone_element=zone_element,
            logs=logs
        )

        if was_alive and not target_entity.is_alive() and bool(getattr(target_entity, "_suppress_non_minion_kill_reward_once", False)):
            logs.append("目标受生命链接保护，【{}】不触发斩杀。".format(card.name))

        elif was_alive and not target_entity.is_alive() and not was_minion:
            max_hp_gain = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("max_hp_gain"),
                source=game_state.player,
                target=game_state.player,
                effect_context=local_context
            )
            max_hp_gain = int(max_hp_gain)

            if max_hp_gain > 0:
                player = game_state.player
                player.max_hp += max_hp_gain
                player.hp += max_hp_gain

                if player.hp > player.max_hp:
                    player.hp = player.max_hp

                logs.append("【{}】击杀了非爪牙敌人，{} 获得 {} 点最大生命。当前 HP：{}/{}。".format(
                    card.name,
                    player.name,
                    max_hp_gain,
                    player.hp,
                    player.max_hp
                ))

        elif was_alive and not target_entity.is_alive() and was_minion:
            logs.append("目标是爪牙，【{}】不获得最大生命。".format(card.name))

        return logs
    if op == "deal_damage_gain_gold_on_non_minion_kill":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs

        damage = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            damage_source="played_card",
            effect_context=local_context,
            attack_type=attack_type,
            attack_element=attack_element
        )

        was_alive = target_entity.is_alive()
        was_minion = bool(getattr(target_entity, "is_minion", False))

        logs.append("【{}】造成 {} 点攻击伤害。".format(
            card.name,
            damage
        ))

        logs.extend(deal_damage(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            amount=damage,
            damage_kind="attack",
            card=card,
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        ))

        from game.zone.zone_utils import apply_fire_zone_burn
        apply_fire_zone_burn(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            card=card,
            zone_element=zone_element,
            logs=logs
        )

        if was_alive and not target_entity.is_alive() and bool(getattr(target_entity, "_suppress_non_minion_kill_reward_once", False)):
            logs.append("目标受生命链接保护，【{}】不触发斩杀。".format(card.name))

        elif was_alive and not target_entity.is_alive() and not was_minion:
            gold_gain = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("gold_gain"),
                source=game_state.player,
                target=game_state.player,
                effect_context=local_context
            )
            gold_gain = int(gold_gain)

            if gold_gain > 0:
                run_state = getattr(game_state, "run_state", None)

                if run_state is None:
                    logs.append("【{}】触发斩杀，但当前战斗没有绑定 RunState，无法获得金币。".format(card.name))
                else:
                    from game.relic_logic.run_relic_utils import gain_gold_with_relics
                    logs.extend(gain_gold_with_relics(
                        run_state,
                        gold_gain,
                        source="【{}】斩杀".format(card.name)
                    ))

        elif was_alive and not target_entity.is_alive() and was_minion:
            logs.append("目标是爪牙，【{}】不获得金币。".format(card.name))

        return logs

    if op == "deal_damage_increase_card_var_on_non_minion_kill":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs

        damage = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            damage_source="played_card",
            effect_context=local_context,
            attack_type=attack_type,
            attack_element=attack_element
        )

        was_alive = target_entity.is_alive()
        was_minion = bool(getattr(target_entity, "is_minion", False))

        logs.append("【{}】造成 {} 点攻击伤害。".format(card.name, damage))

        logs.extend(deal_damage(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            amount=damage,
            damage_kind="attack",
            card=card,
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        ))

        from game.zone.zone_utils import apply_fire_zone_burn
        apply_fire_zone_burn(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            card=card,
            zone_element=zone_element,
            logs=logs
        )

        if was_alive and not target_entity.is_alive() and bool(getattr(target_entity, "_suppress_non_minion_kill_reward_once", False)):
            logs.append("目标受生命链接保护，【{}】不触发斩杀。".format(card.name))

        elif was_alive and not target_entity.is_alive() and not was_minion:
            var_name = effect.get("var", "damage")
            increase = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("increase", 0),
                source=game_state.player,
                target=game_state.player,
                effect_context=effect_context
            )
            old_value = int(card.card_vars.get(var_name, 0))
            new_value = old_value + int(increase)
            card.card_vars[var_name] = new_value
            run_state = getattr(game_state, "run_state", None)
            uid = getattr(card, "_master_deck_uid", None)

            if run_state is not None and uid:
                for master_card in getattr(run_state, "master_deck", []) or []:
                    if getattr(master_card, "_master_deck_uid", None) == uid:
                        master_card.card_vars[var_name] = new_value
                        break
            logs.append("【{}】斩杀成功：{} 从 {} 增加到 {}。".format(
                card.name,
                var_name,
                old_value,
                new_value
            ))
        elif was_alive and not target_entity.is_alive() and was_minion:
            logs.append("目标是爪牙，【{}】不成长。".format(card.name))

        return logs

    if op == "deal_damage_all_enemies_heal_unblocked":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        alive_enemies = get_all_alive_enemies(game_state)
        if not alive_enemies:
            logs.append("没有可攻击的敌人。")
            return logs

        total_real_damage = 0

        for target_entity in alive_enemies:
            if game_state.battle_over:
                break

            if not target_entity.is_alive():
                continue

            damage = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("amount"),
                source=game_state.player,
                target=target_entity,
                damage_source="played_card",
                effect_context=local_context,
                attack_type=attack_type,
                attack_element=attack_element
            )

            old_hp = target_entity.hp

            logs.append("【{}】对 {} 造成 {} 点攻击伤害。".format(
                card.name,
                target_entity.name,
                damage
            ))

            logs.extend(deal_damage(
                game_state=game_state,
                source=game_state.player,
                target=target_entity,
                amount=damage,
                damage_kind="attack",
                card=card,
                attack_type=attack_type,
                attack_element=attack_element,
                zone_element=zone_element
            ))

            real_damage = old_hp - target_entity.hp
            if real_damage < 0:
                real_damage = 0

            total_real_damage += real_damage

            from game.zone.zone_utils import apply_fire_zone_burn
            apply_fire_zone_burn(
                game_state=game_state,
                source=game_state.player,
                target=target_entity,
                card=card,
                zone_element=zone_element,
                logs=logs
            )

        if total_real_damage <= 0:
            logs.append("没有造成未被格挡的伤害，未回复生命。")
            return logs

        player = game_state.player
        from game.relic_logic.combat_relic_utils import apply_magic_flower_heal_amount
        heal_amount = apply_magic_flower_heal_amount(player, total_real_damage)
        old_hp = player.hp
        player.hp += heal_amount
        if player.hp > player.max_hp:
            player.hp = player.max_hp

        real_heal = player.hp - old_hp
        flower_text = ""
        if heal_amount != total_real_damage:
            flower_text = "【魔法花】使回复量 {} -> {}。".format(total_real_damage, heal_amount)

        if real_heal > 0:
            logs.append("{} {}根据未被格挡的伤害回复 {} 点生命。当前 HP：{}/{}。".format(
                player.name,
                flower_text,
                real_heal,
                player.hp,
                player.max_hp
            ))
        else:
            logs.append("{} {}生命已满，没有实际回复。".format(player.name, flower_text))

        return logs

    if op == "gain_block":
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)
        target_key = effect.get("target", "self")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("格挡目标无效。")
            return logs
        if get_status_value(target_entity, "no_card_block") > 0:
            logs.append("{} 受到不能从卡牌获得格挡影响，【{}】没有获得格挡。".format(
                target_entity.name,
                card.name
            ))
            return logs
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            block_source="played_card",
            effect_context=local_context
        )
        if amount < 0:
            amount = 0

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            amount=amount,
            block_source="played_card",
            card=card
        ))
        from game.zone.zone_utils import apply_earth_zone_temp_thorns
        apply_earth_zone_temp_thorns(
            game_state=game_state,
            target=target_entity,
            zone_element=zone_element,
            block_amount=amount,
            logs=logs
        )
        return logs
    
    if op == "double_block":
        player = game_state.player
        old_block = int(getattr(player, "block", 0))

        if old_block <= 0:
            logs.append("{} 没有格挡可以翻倍。".format(player.name))
            return logs

    if op == "double_status":
        target_key = effect.get("target", "self")
        status_key = effect.get("status", "")

        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("状态翻倍目标无效。")
            return logs

        if not status_key:
            logs.append("double_status 缺少 status。")
            return logs

        current = get_status_value(target_entity, status_key)
        new_value = target_entity.gain_status(status_key, current)

        logs.append("{} 的{}翻倍：{} -> {}。".format(
            target_entity.name,
            get_status_name(status_key),
            current,
            new_value
        ))

        return logs

    if op == "lose_hp":
        target_key = effect.get("target", "self")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("失去生命目标无效。")
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            logs.append("{} 没有失去生命。".format(target_entity.name))
            return logs

        logs.extend(deal_damage(
            game_state=game_state,
            source=game_state.player,
            target=target_entity,
            amount=amount,
            damage_kind="life_loss",
            card=card,
            is_reaction_damage=False,
            ignore_block=True,
            count_as_player_self_action_hp_loss=(
                target_entity is game_state.player
                and bool(effect.get("count_as_player_self_action_hp_loss", True))
            )
        ))

        return logs

    if op == "if_target_has_status":
        target_key = effect.get("target", "selected_enemy")
        status_key = effect.get("status", "")

        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("条件判断目标无效。")
            return logs

        if not status_key:
            logs.append("if_target_has_status 缺少 status。")
            return logs

        status_value = get_status_value(target_entity, status_key)

        if status_value <= 0:
            logs.append("{} 没有{}，【{}】的附加效果未触发。".format(
                target_entity.name,
                get_status_name(status_key),
                card.name
            ))
            return logs

        logs.append("{} 拥有{}，【{}】的附加效果触发。".format(
            target_entity.name,
            get_status_name(status_key),
            card.name
        ))

        for child_effect in effect.get("effects", []):
            logs.extend(apply_card_effect(
                game_state=game_state,
                card=card,
                effect=child_effect,
                target_index=target_index,
                effect_context=effect_context
            ))

            if game_state.battle_over:
                break

        return logs

    if op == "gain_status":
        status_key = effect.get("status")
        target_key = effect.get("target", "self")
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        if bool(effect.get("ignore_zone_amount_modifier", False)):
            local_context = make_zone_effect_context(effect_context, "")
        else:
            local_context = make_zone_effect_context(effect_context, zone_element)
        if not status_key:
            logs.append("gain_status 缺少 status。")
            return logs

        target_entities = []
        if target_key in ("all_enemies", "all_enemy", "enemies"):
            target_entities = get_all_alive_enemies(game_state)
        elif should_convert_enemy_target_to_all(game_state, zone_element, target_key):
            target_entities = get_all_alive_enemies(game_state)
            logs.append("雷 Zone 使【{}】的状态目标变为全体。".format(card.name))
        else:
            target_entity = get_effect_target_entity(
                game_state=game_state,
                target_key=target_key,
                target_index=target_index
            )
            if target_entity is not None:
                target_entities = [target_entity]

        if not target_entities:
            logs.append("状态目标无效。")
            return logs

        for target_entity in target_entities:
            amount = resolve_amount(
                game_state=game_state,
                card=card,
                amount_spec=effect.get("amount"),
                source=game_state.player,
                target=target_entity,
                effect_context=local_context
            )

            status_applied = True

            # 统一走状态施加工具，以便异蛇头骨、冠军腰带等遗物能修正“玩家给予敌人状态”的来源。
            if target_entity is not game_state.player and hasattr(target_entity, "enemy_id"):
                from game.relic_logic.combat_relic_utils import apply_status_with_player_relics

                before_value = get_status_value(target_entity, status_key)
                logs.extend(apply_status_with_player_relics(
                    game_state=game_state,
                    source=game_state.player,
                    target=target_entity,
                    status_key=status_key,
                    amount=amount
                ))
                after_value = get_status_value(target_entity, status_key)
                status_applied = after_value != before_value or int(amount) == 0
            elif hasattr(target_entity, "gain_status_with_result"):
                result = target_entity.gain_status_with_result(status_key, amount)
                status_applied = bool(result.get("applied", False))

                from game.status.status_gain import format_status_gain_log
                logs.append(format_status_gain_log(
                    target_entity,
                    status_key,
                    amount,
                    result
                ))
                if (
                    status_applied
                    and status_key in ("berserk", "quartz_ritual")
                    and target_entity is game_state.player
                    and int(amount) > 0
                ):
                    target_entity.max_cost += int(amount)

                    source_name = {
                        "berserk": "狂暴",
                        "quartz_ritual": "石英祭仪",
                    }[status_key]

                    logs.append(
                        "{} 的{}生效，本场战斗费用上限增加 {}。当前费用：{}/{}。".format(
                            target_entity.name,
                            source_name,
                            int(amount),
                            target_entity.cost,
                            target_entity.max_cost
                        )
                    )
            else:
                current = target_entity.gain_status(status_key, amount)
                status_name = get_status_name(status_key)
                logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
                    target_entity.name,
                    amount,
                    status_name,
                    status_name,
                    current
                ))

            if (
                status_applied
                and target_entity is not game_state.player
                and hasattr(target_entity, "enemy_id")
                and int(amount) > 0
            ):
                from game.status.status_defs import get_status_def
                status_def = get_status_def(status_key)
                if getattr(status_def, "category", "") == "debuff":
                    sadistic_damage = get_status_value(game_state.player, "sadistic_nature")
                    if sadistic_damage > 0 and target_entity.is_alive():
                        logs.append("【残虐天性】触发：对【{}】造成 {} 点伤害。".format(
                            target_entity.name,
                            sadistic_damage
                        ))
                        logs.extend(deal_damage(
                            game_state=game_state,
                            source=game_state.player,
                            target=target_entity,
                            amount=sadistic_damage,
                            damage_kind="status",
                            card=None,
                            is_reaction_damage=False,
                            ignore_block=False
                        ))

            if (
                status_applied
                and status_key == "fire_breathing_history"
                and target_entity is game_state.player
            ):
                from game.zone.zone_utils import get_player_attack_cards_played_this_turn

                current_attack_count = get_player_attack_cards_played_this_turn(game_state)

                old_attack_count = int(getattr(
                    target_entity,
                    "_fire_breathing_history_attack_count",
                    0
                ))

                if current_attack_count > old_attack_count:
                    setattr(
                        target_entity,
                        "_fire_breathing_history_attack_count",
                        current_attack_count
                    )
                    logs.append("火焰吐息·旧记录本回合此前已打出的 {} 张攻击牌。".format(
                        current_attack_count
                    ))

        return logs
    
    if op == "gain_status_by_target_status":
        gain_status_key = effect.get("status", "strength")
        gain_target_key = effect.get("target", "self")
        count_target_key = effect.get("count_target", "selected_enemy")
        count_status_key = effect.get("count_status", "vulnerable")

        gain_target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=gain_target_key,
            target_index=target_index
        )
        count_target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=count_target_key,
            target_index=target_index
        )

        if gain_target_entity is None:
            logs.append("获得状态目标无效。")
            return logs

        if count_target_entity is None:
            logs.append("计数状态目标无效。")
            return logs

        if not gain_status_key:
            logs.append("gain_status_by_target_status 缺少 status。")
            return logs

        if not count_status_key:
            logs.append("gain_status_by_target_status 缺少 count_status。")
            return logs

        stack_count = int(get_status_value(count_target_entity, count_status_key))
        if stack_count < 0:
            stack_count = 0

        per_stack = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 1),
            source=game_state.player,
            target=count_target_entity,
            effect_context=effect_context
        )
        per_stack = int(per_stack)

        amount = stack_count * per_stack

        if amount == 0:
            logs.append("{} 身上没有可结算的{}，【{}】没有获得{}。".format(
                count_target_entity.name,
                get_status_name(count_status_key),
                card.name,
                get_status_name(gain_status_key)
            ))
            return logs

        if hasattr(gain_target_entity, "gain_status_with_result"):
            result = gain_target_entity.gain_status_with_result(gain_status_key, amount)

            from game.status.status_gain import format_status_gain_log

            logs.append("{} 身上有 {} 层{}。".format(
                count_target_entity.name,
                stack_count,
                get_status_name(count_status_key)
            ))
            logs.append(format_status_gain_log(
                gain_target_entity,
                gain_status_key,
                amount,
                result
            ))
        else:
            current = gain_target_entity.gain_status(gain_status_key, amount)
            logs.append("{} 身上有 {} 层{}，{} 获得 {} 点{}。当前{}：{}。".format(
                count_target_entity.name,
                stack_count,
                get_status_name(count_status_key),
                gain_target_entity.name,
                amount,
                get_status_name(gain_status_key),
                get_status_name(gain_status_key),
                current
            ))

        return logs

    if op == "gain_status_if_enemy_intent_attack":
        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("观察目标无效。")
            return logs

        intent = target_entity.get_current_intent()

        if not is_enemy_intent_attack(intent):
            logs.append("{} 的意图不是攻击，【{}】没有获得力量。".format(
                target_entity.name,
                card.name
            ))
            return logs

        status_key = effect.get("status", "strength")
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)

        current = game_state.player.gain_status(status_key, amount)
        logs.append("{} 的意图是攻击，{} 获得 {} 点{}。当前{}：{}。".format(
            target_entity.name,
            game_state.player.name,
            amount,
            get_status_name(status_key),
            get_status_name(status_key),
            current
        ))

        return logs

    if op == "gain_mirage_shadows":
        target_key = effect.get("target", "self")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("蜃楼复影目标无效。")
            return logs
        x = int(effect_context.get("x", 0))
        threshold = int(effect.get("threshold", 0))
        if x < threshold:
            logs.append("X = {}，未达到蜃楼复影触发条件 {}。".format(
                x,
                threshold
            ))
            return logs
        duration_add = int(effect.get("duration_add", 0))
        duration = x + duration_add
        if duration <= 0:
            logs.append("蜃楼复影持续时间为 0，没有获得延迟格挡状态。")
            return logs
        block_amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        if block_amount <= 0:
            logs.append("蜃楼复影的延迟格挡数值为 0，没有获得状态。")
            return logs
        entries = getattr(target_entity, "_mirage_shadow_entries", None)
        if entries is None:
            entries = []
        entries.append({
            "remaining": int(duration),
            "block": int(block_amount)
        })
        setattr(target_entity, "_mirage_shadow_entries", entries)
        if hasattr(target_entity, "statuses"):
            target_entity.statuses.set("mirage_shadows", len(entries))
        logs.append("{} 获得蜃楼复影：接下来 {} 个回合开始时，获得 {} 点格挡。".format(
            target_entity.name,
            duration,
            block_amount
        ))
        return logs
    
    if op == "gain_god_in_hand":
        target_key = effect.get("target", "self")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("手中上帝目标无效。")
            return logs
        hp_loss = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("hp_loss"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        energy_loss = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("energy_loss"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        duration = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("duration"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        final_hp_loss = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("final_hp_loss"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        entries = getattr(target_entity, "_god_in_hand_entries", None)
        if entries is None:
            entries = []
        entries.append({
            "remaining": int(duration),
            "hp_loss": int(hp_loss),
            "energy_loss": int(energy_loss),
            "final_hp_loss": int(final_hp_loss),
        })
        setattr(target_entity, "_god_in_hand_entries", entries)
        if hasattr(target_entity, "statuses"):
            target_entity.statuses.set("god_in_hand", len(entries))
        logs.append("{} 获得手中上帝：接下来 {} 个回合开始时，失去 {} 点生命、{} 点能量；随后失去 {} 点生命。".format(
            target_entity.name,
            duration,
            hp_loss,
            energy_loss,
            final_hp_loss
        ))
        return logs

    if op == "force_end_turn":
        setattr(game_state, "force_end_turn_after_card", True)
        logs.append("本张牌结算后将结束你的回合。")
        return logs

    if op == "move_exhaust_cards_by_name":
        player = game_state.player
        name_contains = effect.get("name_contains", "")
        destination = effect.get("destination", "draw_pile_shuffle")
        if not name_contains:
            logs.append("move_exhaust_cards_by_name 缺少 name_contains。")
            return logs
        matched_cards = []
        remaining_cards = []
        for pile_card in player.exhaust_pile:
            if name_contains in pile_card.name:
                matched_cards.append(pile_card)
            else:
                remaining_cards.append(pile_card)
        player.exhaust_pile = remaining_cards
        if not matched_cards:
            logs.append("消耗牌堆中没有名称包含“{}”的牌。".format(name_contains))
            return logs
        if destination == "hand":
            moved_to_hand = 0
            moved_to_draw = 0
            for pile_card in matched_cards:
                if len(player.hand) < player.max_hand_size:
                    player.hand.append(pile_card)
                    moved_to_hand += 1
                else:
                    # 手牌满时兜底放入抽牌堆，并重洗抽牌堆
                    player.draw_pile.append(pile_card)
                    moved_to_draw += 1
            if moved_to_hand:
                logs.append("将 {} 张名称包含“{}”的牌从消耗牌堆放入手牌。".format(
                    moved_to_hand,
                    name_contains
                ))
            if moved_to_draw:
                random.shuffle(player.draw_pile)
                logs.append("手牌已满，将 {} 张名称包含“{}”的牌放入抽牌堆，并重洗抽牌堆。".format(
                    moved_to_draw,
                    name_contains
                ))
            return logs
        if destination == "draw_pile_top":
            for pile_card in matched_cards:
                player.draw_pile.append(pile_card)
            logs.append("将 {} 张名称包含“{}”的牌从消耗牌堆放到抽牌堆顶。".format(
                len(matched_cards),
                name_contains
            ))
            return logs
        if destination in ("draw_pile", "draw_pile_shuffle"):
            player.draw_pile.extend(matched_cards)
            random.shuffle(player.draw_pile)
            logs.append("将 {} 张名称包含“{}”的牌从消耗牌堆放入抽牌堆，并重洗抽牌堆。".format(
                len(matched_cards),
                name_contains
            ))
            return logs
        logs.append("未知目的地：{}。".format(destination))
        return logs

    if op == "transform_hand_skills_to_card":
        from data.card.AAAregistry import create_card
        from data.card.upgrade_rules import upgrade_card
        player = game_state.player
        new_card_id = effect.get("new_card_id")
        new_card_upgraded = bool(effect.get("new_card_upgraded", False))
        if not new_card_id:
            logs.append("transform_hand_skills_to_card 缺少 new_card_id。")
            return logs
        transformed_count = 0
        for index, hand_card in enumerate(list(player.hand)):
            if getattr(hand_card, "card_type", "") != "skill":
                continue
            new_card = create_card(new_card_id)
            if new_card_upgraded:
                new_card = upgrade_card(new_card)
            player.hand[index] = new_card
            transformed_count += 1
        if transformed_count <= 0:
            logs.append("手牌中没有技能牌可转化。")
        else:
            suffix = "+" if new_card_upgraded else ""
            logs.append("将手牌中 {} 张技能牌变为【转移{}】。".format(
                transformed_count,
                suffix
            ))
        return logs

    if op == "gain_temporary_status_delta":
        target_key = effect.get("target", "self")
        status_key = effect.get("status")
        temporary_status_key = effect.get("temporary_status")
        block_policy = effect.get("block_policy", "skip_delta_if_temporary_blocked")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("临时状态变化目标无效。")
            return logs
        if not status_key:
            logs.append("gain_temporary_status_delta 缺少 status。")
            return logs
        delta = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("delta"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        delta_multiplier = int(effect.get("delta_multiplier", 1))
        delta = int(delta) * delta_multiplier
        temporary_amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("temporary_amount"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        temporary_amount = int(temporary_amount)
        if temporary_status_key and temporary_amount > 0:
            if hasattr(target_entity, "gain_status_with_result"):
                temporary_result = target_entity.gain_status_with_result(
                    temporary_status_key,
                    temporary_amount
                )
                from game.status.status_gain import format_status_gain_log
                logs.append(format_status_gain_log(
                    target_entity,
                    temporary_status_key,
                    temporary_amount,
                    temporary_result
                ))

                if temporary_result.get("blocked") and block_policy == "skip_delta_if_temporary_blocked":
                    logs.append("由于临时状态被抵挡，本次{}变化未发生。".format(
                        get_status_name(status_key)
                    ))
                    return logs
            else:
                current_temp = target_entity.gain_status(
                    temporary_status_key,
                    temporary_amount
                )
                logs.append("{} 获得 {} 点{}。当前{}：{}。".format(
                    target_entity.name,
                    temporary_amount,
                    get_status_name(temporary_status_key),
                    get_status_name(temporary_status_key),
                    current_temp
                ))
        if delta == 0:
            logs.append("{} 的{}没有变化。".format(
                target_entity.name,
                get_status_name(status_key)
            ))
            return logs
        current = target_entity.gain_status(status_key, delta)
        status_name = get_status_name(status_key)
        if delta > 0:
            logs.append("{} 临时获得 {} 点{}。当前{}：{}。".format(
                target_entity.name,
                delta,
                status_name,
                status_name,
                current
            ))
        else:
            logs.append("{} 临时失去 {} 点{}。当前{}：{}。".format(
                target_entity.name,
                -delta,
                status_name,
                status_name,
                current
            ))
        return logs

    if op == "gain_energy_if_discarded_this_turn":
        discarded_count = int(getattr(game_state, "player_discarded_cards_this_turn", 0) or 0)

        if discarded_count <= 0:
            logs.append("本回合没有丢弃过牌，【{}】未获得额外费用。".format(card.name))
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            return logs

        game_state.player.cost += amount

        logs.append("本回合已丢弃过牌，【{}】获得 {} 点费用。当前费用：{}。".format(
            card.name,
            amount,
            game_state.player.cost
        ))

        return logs

    if op == "gain_next_turn_block":
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            block_source="played_card",
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            return logs

        result = game_state.player.gain_status_with_result("next_turn_block", amount)

        from game.status.status_gain import format_status_gain_log

        logs.append(format_status_gain_log(
            game_state.player,
            "next_turn_block",
            amount,
            result
        ))

        return logs

    if op == "gain_temporary_strength_loss_all_enemies":
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            return logs

        from game.status.status_gain import format_status_gain_log

        alive_enemies = get_all_alive_enemies(game_state)
        if not alive_enemies:
            logs.append("没有敌人受到力量降低。")
            return logs

        for enemy in alive_enemies:
            temp_result = enemy.gain_status_with_result("temporary_strength_loss", amount)
            logs.append(format_status_gain_log(
                enemy,
                "temporary_strength_loss",
                amount,
                temp_result
            ))

            if temp_result.get("blocked"):
                continue

            strength_result = enemy.gain_status_with_result("strength", -amount)
            logs.append(format_status_gain_log(
                enemy,
                "strength",
                -amount,
                strength_result
            ))

        return logs

    if op == "lose_dexterity_this_turn":
        compatibility_effect = {
            "op": "gain_temporary_status_delta",
            "target": "self",
            "status": "dexterity",
            "delta": effect.get("amount"),
            "delta_multiplier": -1,
            "temporary_status": "temporary_dexterity_loss",
            "temporary_amount": effect.get("amount"),
            "block_policy": "skip_delta_if_temporary_blocked"
        }

        logs.extend(apply_card_effect(
            game_state=game_state,
            card=card,
            effect=compatibility_effect,
            target_index=target_index,
            effect_context=effect_context
        ))

        return logs

    if op == "gain_status_if_target_has_block":
        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("条件状态目标无效。")
            return logs
        if getattr(target_entity, "block", 0) <= 0:
            logs.append("{} 没有格挡，未施加额外状态。".format(target_entity.name))
            return logs
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        statuses = effect.get("statuses", [])
        for status_key in statuses:
            current = target_entity.gain_status(status_key, amount)
            status_name = get_status_name(status_key)

            logs.append("{} 有格挡，获得 {} 层{}。当前{}：{}。".format(
                target_entity.name,
                amount,
                status_name,
                status_name,
                current
            ))
        return logs

    if op == "gain_status_if_target_has_no_artifact":
        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("条件状态目标无效。")
            return logs
        artifact = 0
        if hasattr(target_entity, "statuses"):
            artifact = target_entity.statuses.get("artifact")
        status_key = effect.get("status", "")
        if not status_key:
            logs.append("gain_status_if_target_has_no_artifact 缺少 status。")
            return logs
        if artifact > 0:
            logs.append("{} 拥有人工制品，未被{}影响。".format(
                target_entity.name,
                get_status_name(status_key)
            ))
            return logs
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        current = target_entity.gain_status(status_key, amount)
        status_name = get_status_name(status_key)
        logs.append("{} 没有人工制品，获得 {} 点{}。当前{}：{}。".format(
            target_entity.name,
            amount,
            status_name,
            status_name,
            current
        ))
        return logs

    if op == "lock_next_target":
        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("锁定目标无效。")
            return logs
        duration = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("duration", 3),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        initial_bonus = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("initial_bonus_percent", 100),
            source=game_state.player,
            target=target_entity,
            effect_context=effect_context
        )
        from game.target_lock import lock_attack_target
        logs.extend(lock_attack_target(
            game_state=game_state,
            enemy=target_entity,
            duration=duration,
            initial_bonus_percent=initial_bonus
        ))
        return logs

    if op == "increase_card_var":
        var_name = effect.get("var")
        if not var_name:
            logs.append("increase_card_var 缺少 var。")
            return logs
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        old_value = int(card.card_vars.get(var_name, 0))
        new_value = old_value + int(amount)
        card.card_vars[var_name] = new_value
        logs.append("【{}】的 {} 从 {} 增加到 {}。".format(
            card.name,
            var_name,
            old_value,
            new_value
        ))
        return logs
    
    if op == "add_copy_to_discard":
        import copy
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 1),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)
        if amount <= 0:
            logs.append("【{}】没有生成复制品。".format(card.name))
            return logs
        for _ in range(amount):
            copied_card = copy.deepcopy(card)
            # 标记为战斗内临时生成牌。
            # 当前逻辑下战斗结束不会同步弃牌堆到 master_deck，
            # 这个标记主要是给以后显示、过滤、特殊机制预留。
            setattr(copied_card, "temporary", True)
            setattr(copied_card, "created_in_battle", True)
            game_state.player.discard_pile.append(copied_card)
        if amount == 1:
            logs.append("在弃牌堆放入 1 张【{}】的复制品。".format(card.name))
        else:
            logs.append("在弃牌堆放入 {} 张【{}】的复制品。".format(
                amount,
                card.name
            ))
        return logs

    if op == "add_card_to_draw_pile":
        card_id = effect.get("card_id", "")
        if not card_id:
            logs.append("add_card_to_draw_pile 缺少 card_id。")
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 1),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            logs.append("没有向抽牌堆加入卡牌。")
            return logs

        from data.card.AAAregistry import create_card

        make_upgraded = bool(effect.get("upgraded", False))

        added_cards = []
        for _ in range(amount):
            new_card = create_card(card_id)

            if make_upgraded:
                from data.card.upgrade_rules import upgrade_card
                new_card = upgrade_card(new_card)

            # 战斗内生成牌标记。
            # 当前战斗结束不会把战斗牌堆写回长期 deck，这里主要给后续显示/过滤/特殊机制预留。
            setattr(new_card, "temporary", True)
            setattr(new_card, "created_in_battle", True)

            game_state.player.draw_pile.append(new_card)
            added_cards.append(new_card)

        should_shuffle = effect.get("shuffle", True)
        if should_shuffle:
            random.shuffle(game_state.player.draw_pile)

        card_name = added_cards[0].name if added_cards else card_id

        if should_shuffle:
            logs.append("将 {} 张【{}】加入抽牌堆，并重洗抽牌堆。".format(
                amount,
                card_name
            ))
        else:
            logs.append("将 {} 张【{}】加入抽牌堆顶。".format(
                amount,
                card_name
            ))

        return logs

    if op == "add_card_to_discard_pile":
        card_id = effect.get("card_id", "")
        if not card_id:
            logs.append("add_card_to_discard_pile 缺少 card_id。")
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 1),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            logs.append("没有向弃牌堆加入卡牌。")
            return logs

        from data.card.AAAregistry import create_card

        added_cards = []
        for _ in range(amount):
            new_card = create_card(card_id)
            setattr(new_card, "temporary", True)
            setattr(new_card, "created_in_battle", True)

            game_state.player.discard_pile.append(new_card)
            added_cards.append(new_card)

        card_name = added_cards[0].name if added_cards else card_id

        logs.append("将 {} 张【{}】加入弃牌堆。".format(
            amount,
            card_name
        ))

        return logs

    if op == "add_card_to_hand":
        card_id = effect.get("card_id", "")
        if not card_id:
            logs.append("add_card_to_hand 缺少 card_id。")
            return logs

        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 1),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)

        if amount <= 0:
            logs.append("没有向手牌加入卡牌。")
            return logs

        from data.card.AAAregistry import create_card

        added_to_hand = 0
        added_to_discard = 0
        card_name = ""
        for _ in range(amount):
            new_card = create_card(card_id)
            setattr(new_card, "temporary", True)
            setattr(new_card, "created_in_battle", True)
            card_name = new_card.name

            if game_state.player.is_hand_full():
                game_state.player.discard_pile.append(new_card)
                added_to_discard += 1
            else:
                game_state.player.hand.append(new_card)
                added_to_hand += 1

        if added_to_hand > 0:
            logs.append("将 {} 张【{}】加入手牌。".format(
                added_to_hand,
                card_name
            ))
        if added_to_discard > 0:
            logs.append("手牌已满，{} 张【{}】进入弃牌堆。".format(
                added_to_discard,
                card_name
            ))

        return logs

    if op == "add_random_attack_to_hand_temp_cost_zero":
        owner_character_id = effect.get(
            "owner_character_id",
            getattr(card, "owner_character_id", "")
        )
        exclude_card_ids = set(effect.get("exclude_card_ids", []))

        from data.card.AAAregistry import CARD_REGISTRY, create_card
        from data.content_gate import is_content_enabled

        candidates = []

        for candidate_card_id in CARD_REGISTRY.keys():
            if not is_content_enabled("card", candidate_card_id):
                continue
            if candidate_card_id in exclude_card_ids:
                continue

            try:
                candidate = create_card(candidate_card_id)
            except Exception:
                continue

            if getattr(candidate, "card_type", "") != "attack":
                continue

            if getattr(candidate, "quantity", "") in ("starting", "status", "curse", "test"):
                continue

            if getattr(candidate, "owner_character_id", "") != owner_character_id:
                continue

            # X 费牌不加入这里，避免“本回合费用变 0”与 X 费用规则冲突。
            if getattr(candidate, "cost", None) == "X":
                continue

            candidates.append(candidate_card_id)

        if not candidates:
            logs.append("没有可生成的随机攻击牌。")
            return logs

        selected_card_id = random.choice(candidates)
        new_card = create_card(selected_card_id)

        setattr(new_card, "temporary", True)
        setattr(new_card, "created_in_battle", True)

        # 本回合费用变为 0。
        # 即使进入弃牌堆，也保留这个临时费用变化。
        # 之后如果本回合内被捞回手牌，仍然是 0 费。
        setattr(new_card, "temporary_cost_override", 0)

        if game_state.player.is_hand_full():
            game_state.player.discard_pile.append(new_card)
            logs.append("手牌已满，随机攻击牌【{}】进入弃牌堆。本回合其费用变为 0。".format(
                new_card.name
            ))
        else:
            game_state.player.hand.append(new_card)
            logs.append("将随机攻击牌【{}】加入手牌。本回合其费用变为 0。".format(
                new_card.name
            ))

        return logs

    if op == "play_draw_pile_top_and_exhaust":
        player = game_state.player

        has_draw_card = reshuffle_discard_into_draw_if_needed(player, logs, game_state=game_state)

        if not has_draw_card:
            logs.append("抽牌堆和弃牌堆都为空，【{}】没有可打出的牌。".format(card.name))
            return logs

        top_card = player.draw_pile.pop()

        logs.append("抽牌堆顶牌为【{}】。".format(top_card.name))
        logs.extend(play_card_from_effect_and_exhaust(
            game_state=game_state,
            source_card=card,
            played_card=top_card,
            reason="havoc"
        ))

        return logs

    if op == "exhaust_random_hand_card":
        player = game_state.player
        options = list(player.hand)

        if not options:
            logs.append("手牌为空，没有可以随机消耗的牌。")
            return logs

        chosen_card = random.choice(options)
        player.hand.remove(chosen_card)

        from game.engine import move_card_to_exhaust_pile

        logs.append("随机选择手牌【{}】消耗。".format(chosen_card.name))
        logs.extend(move_card_to_exhaust_pile(
            game_state=game_state,
            card=chosen_card,
            reason="true_grit"
        ))

        return logs

    if op == "exhaust_non_attack_hand_cards":
        player = game_state.player
        cards_to_exhaust = []

        for hand_card in list(player.hand):
            if getattr(hand_card, "card_type", "") != "attack":
                cards_to_exhaust.append(hand_card)

        if not cards_to_exhaust:
            logs.append("手牌中没有需要消耗的非攻击牌。")
            return logs

        from game.engine import move_card_to_exhaust_pile

        for hand_card in cards_to_exhaust:
            if hand_card not in player.hand:
                continue

            player.hand.remove(hand_card)
            logs.append("消耗非攻击牌【{}】。".format(hand_card.name))
            logs.extend(move_card_to_exhaust_pile(
                game_state=game_state,
                card=hand_card,
                reason="sever_soul"
            ))

        return logs

    if op == "exhaust_all_hand_cards_then_attack_per_card":
        player = game_state.player
        target_key = effect.get("target", "selected_enemy")
        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )

        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs

        cards_to_exhaust = list(player.hand)

        from game.engine import move_card_to_exhaust_pile

        exhausted_count = 0
        for hand_card in cards_to_exhaust:
            if hand_card not in player.hand:
                continue

            player.hand.remove(hand_card)
            logs.append("消耗手牌【{}】。".format(hand_card.name))
            logs.extend(move_card_to_exhaust_pile(
                game_state=game_state,
                card=hand_card,
                reason="fiend_fire"
            ))
            exhausted_count += 1

        if exhausted_count <= 0:
            logs.append("没有消耗任何手牌，【{}】没有造成伤害。".format(card.name))
            return logs

        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        for hit_index in range(exhausted_count):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续伤害不再结算。")
                break

            if not target_entity.is_alive():
                logs.append("目标已被击败，后续伤害不再结算。")
                break

            logs.append("【{}】第 {}/{} 次伤害：".format(
                card.name,
                hit_index + 1,
                exhausted_count
            ))

            deal_card_attack_damage_to_target(
                game_state=game_state,
                card=card,
                effect=effect,
                target_entity=target_entity,
                effect_context=local_context,
                attack_type=attack_type,
                attack_element=attack_element,
                zone_element=zone_element,
                logs=logs,
                prefix="【{card.name}】造成 {damage} 点攻击伤害。"
            )

        return logs

    if op == "exhaust_non_attack_hand_cards_gain_block_per_card":
        player = game_state.player
        cards_to_exhaust = []

        for hand_card in list(player.hand):
            if getattr(hand_card, "card_type", "") != "attack":
                cards_to_exhaust.append(hand_card)

        if not cards_to_exhaust:
            logs.append("手牌中没有需要消耗的非攻击牌。")
            return logs

        from game.engine import move_card_to_exhaust_pile
        from game.zone.zone_utils import apply_earth_zone_temp_thorns

        exhausted_count = 0

        for hand_card in cards_to_exhaust:
            if hand_card not in player.hand:
                continue

            player.hand.remove(hand_card)
            logs.append("消耗非攻击牌【{}】。".format(hand_card.name))
            logs.extend(move_card_to_exhaust_pile(
                game_state=game_state,
                card=hand_card,
                reason="second_wind"
            ))
            exhausted_count += 1

        if exhausted_count <= 0:
            logs.append("没有实际消耗任何牌。")
            return logs

        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)

        block_per_card = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("block_per_card"),
            source=game_state.player,
            target=game_state.player,
            block_source="played_card",
            effect_context=local_context
        )

        total_block = int(block_per_card) * exhausted_count
        if total_block < 0:
            total_block = 0

        old_block = int(getattr(player, "block", 0))

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=game_state.player,
            target=player,
            amount=total_block,
            block_source="second_wind",
            card=card,
            message="{} 消耗了 {} 张非攻击牌，获得 {} 点格挡。当前格挡：{}。".format(
                player.name,
                exhausted_count,
                total_block,
                old_block + total_block
            )
        ))

        apply_earth_zone_temp_thorns(
            game_state=game_state,
            target=player,
            zone_element=zone_element,
            block_amount=total_block,
            logs=logs
        )

        return logs

    if op == "request_discard_to_draw_top":
        player = game_state.player
        # 如果伤害已经解决了所有敌人，就不再要求选择。
        if game_state.is_all_enemies_dead():
            logs.append("敌人已被击败，不再选择弃牌堆置顶。")
            return logs

        options = list(player.discard_pile)

        if not options:
            logs.append("弃牌堆为空，没有可以放到抽牌堆顶的牌。")
            return logs

        from game.pending_choice import PendingChoice, set_pending_choice

        set_pending_choice(game_state, PendingChoice(
            kind="discard_to_draw_top",
            source=card.name,
            prompt="请选择弃牌堆中的 1 张牌放到抽牌堆顶：/card top 0。",
            command_hint="top 等效 headbutt，置顶，选择弃牌置顶。",
            block_message="当前需要先处理弃牌堆置顶选择。用法：/card top 0。\ntop 等效 headbutt，置顶，选择弃牌置顶。",
            options=options
        ))

        logs.append("请选择弃牌堆中的 1 张牌放到抽牌堆顶：/card top 0。")
        logs.append("可选牌：")

        for index, pile_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                pile_card.summary_text()
            ))

        return logs

    if op == "request_exhaust_hand_card":
        player = game_state.player
        options = list(player.hand)

        if not options:
            logs.append("手牌为空，没有可以消耗的牌。")
            return logs

        game_state.pending_exhaust_hand_selection = True
        game_state.pending_exhaust_hand_source = card.name
        game_state.pending_exhaust_hand_options = options

        logs.append("请选择 1 张手牌消耗：/card exhaust_hand 0。")
        logs.append("可选牌：")

        for index, hand_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                hand_card.summary_text()
            ))

        return logs

    if op == "request_exhaust_hand_card_then_if_type":
        player = game_state.player
        options = list(player.hand)

        if not options:
            logs.append("手牌为空，没有可以消耗的牌。")
            return logs

        game_state.pending_exhaust_hand_selection = True
        game_state.pending_exhaust_hand_source = card.name
        game_state.pending_exhaust_hand_options = options
        game_state.pending_exhaust_hand_source_card = card
        game_state.pending_exhaust_hand_target_index = int(target_index)
        game_state.pending_exhaust_hand_required_card_types = list(
            effect.get("card_types", [])
        )
        game_state.pending_exhaust_hand_after_effects = list(
            effect.get("effects", [])
        )

        logs.append("请选择 1 张手牌消耗：/card exhaust_hand 0。")
        logs.append("如果被消耗的是指定类型，将触发后续效果。")
        logs.append("可选牌：")

        for index, hand_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                hand_card.summary_text()
            ))

        return logs

    if op == "request_hand_to_draw_top":
        player = game_state.player
        options = list(player.hand)

        if not options:
            logs.append("手牌为空，没有可以放到抽牌堆顶的牌。")
            return logs

        from game.pending_choice import PendingChoice, set_pending_choice

        set_pending_choice(game_state, PendingChoice(
            kind="hand_to_draw_top",
            source=card.name,
            prompt="请选择 1 张手牌放到抽牌堆顶：/card handtop 0。",
            command_hint="handtop 等效 hand_top，warcry，置顶手牌，手牌置顶。",
            block_message="当前需要先处理手牌置顶选择。用法：/card handtop 0。\nhandtop 等效 hand_top，warcry，置顶手牌，手牌置顶。",
            options=options
        ))

        logs.append("请选择 1 张手牌放到抽牌堆顶：/card handtop 0。")
        logs.append("可选牌：")

        for index, hand_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                hand_card.summary_text()
            ))

        return logs

    if op == "request_upgrade_hand_card":
        player = game_state.player
        options = collect_upgradeable_cards_from_pile(player.hand)

        if not options:
            logs.append("手牌中没有可以升级的牌。")
            return logs

        from game.pending_choice import PendingChoice, set_pending_choice

        set_pending_choice(game_state, PendingChoice(
            kind="upgrade_hand",
            source=card.name,
            prompt="请选择 1 张手牌在本场战斗中临时升级：/card upgrade_hand 0。",
            command_hint="upgrade_hand 等效 upgradehand，armaments，选择升级，升级手牌。",
            block_message="当前需要先处理手牌升级选择。用法：/card upgrade_hand 0。\nupgrade_hand 等效 upgradehand，armaments，选择升级，升级手牌。",
            options=options
        ))

        logs.append("请选择 1 张手牌在本场战斗中临时升级：/card upgrade_hand 0。")
        logs.append("可选牌：")

        for index, hand_card in enumerate(options):
            upgraded_preview = upgrade_card_for_this_combat(hand_card)

            if upgraded_preview is None:
                continue

            logs.append("[{}] {} -> {}".format(
                index,
                hand_card.summary_text(),
                upgraded_preview.summary_text()
            ))

        return logs

    if op == "request_exhaust_hand_card_then_effects":
        player = game_state.player
        options = list(player.hand)

        if not options:
            logs.append("手牌为空，没有可以消耗的牌。")
            return logs

        game_state.pending_exhaust_hand_selection = True
        game_state.pending_exhaust_hand_source = card.name
        game_state.pending_exhaust_hand_options = options
        game_state.pending_exhaust_hand_source_card = card
        game_state.pending_exhaust_hand_target_index = int(target_index)
        game_state.pending_exhaust_hand_required_card_types = []
        game_state.pending_exhaust_hand_after_effects = list(
            effect.get("effects", [])
        )

        logs.append("请选择 1 张手牌消耗：/card exhaust_hand 0。")
        logs.append("可选牌：")

        for index, hand_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                hand_card.summary_text()
            ))

        return logs

    if op == "request_duplicate_hand_card":
        player = game_state.player
        allowed_types = effect.get("card_types", ["attack", "power"])
        count = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount", 1),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        count = int(count)

        options = []
        for hand_card in player.hand:
            if getattr(hand_card, "card_type", "") in allowed_types:
                options.append(hand_card)

        if not options:
            logs.append("手牌中没有可以复制的攻击牌或能力牌。")
            return logs

        if count <= 0:
            logs.append("复制数量为 0，没有添加复制品。")
            return logs

        game_state.pending_duplicate_hand_selection = True
        game_state.pending_duplicate_hand_source = card.name
        game_state.pending_duplicate_hand_options = options
        game_state.pending_duplicate_hand_count = count

        logs.append("请选择 1 张攻击牌或能力牌复制到手牌：/card duplicate_hand 0。")
        logs.append("可选牌：")

        for index, hand_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                hand_card.summary_text()
            ))

        return logs

    if op == "request_exhume_card":
        player = game_state.player
        options = list(player.exhaust_pile)

        if not options:
            logs.append("消耗堆为空，没有可以发掘的牌。")
            return logs

        game_state.pending_exhume_selection = True
        game_state.pending_exhume_source = card.name
        game_state.pending_exhume_options = options

        logs.append("请选择 1 张消耗堆中的牌加入手牌：/card exhume 0。")
        logs.append("可选牌：")

        for index, exhaust_card in enumerate(options):
            logs.append("[{}] {}".format(
                index,
                exhaust_card.summary_text()
            ))

        return logs

    if op == "upgrade_cards":
        player = game_state.player
        scope = effect.get("scope", "hand")
        mode = effect.get("mode", "all")

        if mode != "all":
            logs.append("upgrade_cards 暂不支持 mode={}。".format(mode))
            return logs

        if scope == "hand":
            upgraded_count, upgrade_logs = upgrade_all_cards_in_pile_for_this_combat(player.hand)
            logs.extend(upgrade_logs)

            if upgraded_count <= 0:
                logs.append("手牌中没有可以升级的牌。")
            else:
                logs.append("本场战斗中，手牌里的 {} 张牌被临时升级。".format(
                    upgraded_count
                ))

            return logs

        if scope in ("combat", "all_combat"):
            total_upgraded = 0
            pile_labels = [
                ("draw_pile", "抽牌堆"),
                ("hand", "手牌"),
                ("discard_pile", "弃牌堆"),
                ("exhaust_pile", "消耗堆"),
            ]
            for pile_name, pile_label in pile_labels:
                pile = getattr(player, pile_name, [])
                upgraded_count, upgrade_logs = upgrade_all_cards_in_pile_for_this_combat(pile)
                total_upgraded += upgraded_count
                logs.extend(upgrade_logs)
                if upgraded_count > 0:
                    logs.append("{}中 {} 张牌被临时升级。".format(pile_label, upgraded_count))

            if total_upgraded <= 0:
                logs.append("本场战斗中没有可以升级的牌。")
            else:
                logs.append("本场战斗中，共 {} 张牌被临时升级。".format(total_upgraded))

            return logs

        logs.append("upgrade_cards 暂不支持 scope={}。".format(scope))
        return logs

    if op == "request_discard_any":
        player = game_state.player
        available_count = len(getattr(player, "hand", []) or [])
        min_count = int(resolve_amount(game_state, card, effect.get("min_count", 0), source=player, target=player, effect_context=effect_context) or 0)
        max_count_raw = effect.get("max_count", None)
        max_count = None if max_count_raw is None else int(resolve_amount(game_state, card, max_count_raw, source=player, target=player, effect_context=effect_context))

        if available_count <= 0:
            return logs

        if max_count is not None and max_count <= 0:
            logs.append("无需丢弃手牌。")
            return logs

        # 强制丢弃 X 张：若当前手牌数 <= X，自动全部丢弃。
        # 这里按“主动丢弃”结算，能触发奇巧。
        if min_count > 0 and max_count is not None and min_count == max_count and available_count <= max_count:
            indexed_cards = list(enumerate(list(player.hand)))
            player.hand = []

            logs.append("需要丢弃 {} 张牌，当前手牌只有 {} 张，自动全部丢弃。".format(
                min_count,
                available_count
            ))

            from game.engine import resolve_discarded_card

            for index, discard_card in indexed_cards:
                logs.append("选择丢弃手牌 [{}] 【{}】。".format(index, discard_card.name))
                logs.extend(resolve_discarded_card(
                    game_state,
                    discard_card,
                    reason="主动丢弃",
                    trigger_clever=True
                ))

            for after_effect in list(effect.get("after_effects", []) or []):
                logs.extend(apply_card_effect(
                    game_state=game_state,
                    card=card,
                    effect=after_effect,
                    target_index=target_index,
                    effect_context=effect_context
                ))

            return logs

        game_state.pending_discard_selection = True
        game_state.pending_discard_source = card.name
        game_state.pending_discard_min_count = min_count
        game_state.pending_discard_max_count = max_count
        game_state.pending_discard_source_card = card
        game_state.pending_discard_target_index = int(target_index)
        game_state.pending_discard_after_effects = list(effect.get("after_effects", []) or [])

        if min_count == 1 and max_count == 1:
            logs.append("请选择 1 张手牌丢弃：/card drop 0。")
        elif max_count is not None:
            logs.append("请选择 {} 到 {} 张手牌丢弃：/card drop 0 2 3。".format(min_count, max_count))
        elif min_count > 0:
            logs.append("请选择至少 {} 张手牌丢弃：/card drop 0 2 3。".format(min_count))
        else:
            logs.append("请选择任意张手牌丢弃：/card drop 0 2 3。若不丢弃，使用 /card drop none。")
        return logs
    
    if op == "repeat_x":
        x = int(effect_context.get("x", 0))

        if x <= 0:
            logs.append("X 为 0，【{}】没有触发重复效果。".format(card.name))
            return logs

        child_effects = effect.get("effects", [])

        if not child_effects:
            logs.append("repeat_x 缺少 effects。")
            return logs

        for index in range(x):
            if game_state.battle_over:
                logs.append("战斗已经结束，后续 X 次数不再结算。")
                break

            logs.append("X 效果第 {}/{} 次：".format(index + 1, x))

            for child_effect in child_effects:
                logs.extend(apply_card_effect(
                    game_state=game_state,
                    card=card,
                    effect=child_effect,
                    target_index=target_index,
                    effect_context=effect_context
                ))

                if game_state.battle_over:
                    break

        return logs

    if op in ("set_zone", "deploy_zone"):
        from game.zone.zone_utils import deploy_element_zone
        element = effect.get("element", getattr(card, "attack_element", ""))
        force_extreme = bool(effect.get("force_extreme", False))
        logs.extend(deploy_element_zone(
            game_state=game_state,
            element=element,
            source=game_state.player,
            card=card,
            force_extreme=force_extreme
        ))
        return logs

    logs.append("未知效果：{}".format(op))
    return logs

@register_effect("exhaust_status_and_curse_hand_gain_stats")
def handle_exhaust_status_and_curse_hand_gain_stats(game_state, card, effect, target_index, effect_context):
    logs = []
    player = game_state.player

    def is_status_or_curse(target_card):
        return getattr(target_card, "card_type", "") in ("status", "curse")

    pile_specs = [
        ("hand", "手牌"),
        ("draw_pile", "抽牌堆"),
        ("discard_pile", "弃牌堆"),
    ]

    cards_to_exhaust = []
    for pile_attr, pile_name in pile_specs:
        pile = getattr(player, pile_attr, None)
        if pile is None:
            continue
        for pile_card in list(pile):
            if is_status_or_curse(pile_card):
                cards_to_exhaust.append((pile_attr, pile_name, pile_card))

    from game.engine import move_card_to_exhaust_pile

    exhausted_count = 0
    exhausted_names = []
    exhausted_by_pile = {}

    if not cards_to_exhaust:
        logs.append("没有可消耗的状态牌或诅咒牌。")
    else:
        for pile_attr, pile_name, pile_card in cards_to_exhaust:
            pile = getattr(player, pile_attr, None)
            if pile is None or pile_card not in pile:
                continue

            pile.remove(pile_card)
            exhausted_names.append(pile_card.name)
            exhausted_by_pile.setdefault(pile_name, []).append(pile_card.name)
            exhausted_count += 1

            logs.extend(move_card_to_exhaust_pile(
                game_state=game_state,
                card=pile_card,
                reason="rockbound_wish"
            ))

            if game_state.battle_over:
                return logs

    hp_divisor = int(effect.get("hp_divisor", 2) or 2)
    stat_divisor = int(effect.get("stat_divisor", 4) or 4)

    if hp_divisor <= 0:
        hp_divisor = 2
    if stat_divisor <= 0:
        stat_divisor = 4

    hp_loss = exhausted_count // hp_divisor

    # 力量和敏捷保底 1：即使没有实际消耗牌，也获得 1 点力量和 1 点敏捷。
    stat_gain = exhausted_count // stat_divisor
    if stat_gain < 1:
        stat_gain = 1

    if exhausted_count > 0:
        pile_summaries = []
        for _, pile_name in pile_specs:
            names = exhausted_by_pile.get(pile_name, [])
            if names:
                pile_summaries.append("{}：{}".format(pile_name, "、".join(names)))

        logs.append("【{}】消耗了 {} 张状态牌/诅咒牌：{}。".format(
            card.name,
            exhausted_count,
            "；".join(pile_summaries) if pile_summaries else "、".join(exhausted_names)
        ))
    else:
        logs.append("【{}】没有实际消耗任何状态牌或诅咒牌。".format(card.name))

    if hp_loss > 0:
        from game.damage import deal_damage

        logs.append("【{}】使 {} 失去 {} 点生命。".format(
            card.name,
            player.name,
            hp_loss
        ))

        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=player,
            amount=hp_loss,
            damage_kind="life_loss",
            card=card,
            is_reaction_damage=False,
            ignore_block=True,
            count_as_player_self_action_hp_loss=True
        ))

        if game_state.battle_over or not player.is_alive():
            return logs
    else:
        logs.append("【{}】本次生命损失为 0。".format(card.name))

    current_strength = player.gain_status("strength", stat_gain)
    current_dexterity = player.gain_status("dexterity", stat_gain)

    logs.append("【{}】获得 {} 点力量和 {} 点敏捷。当前力量：{}，敏捷：{}。".format(
        card.name,
        stat_gain,
        stat_gain,
        current_strength,
        current_dexterity
    ))

    return logs

@register_effect("increase_player_max_hp")
def handle_increase_player_max_hp(game_state, card, effect, target_index, effect_context):
    player = game_state.player

    amount = resolve_amount(
        game_state=game_state,
        card=card,
        amount_spec=effect.get("amount"),
        source=player,
        target=player,
        effect_context=effect_context,
    )
    amount = int(amount)

    if amount <= 0:
        return ["【{}】没有提升最大生命。".format(getattr(card, "name", "效果"))]

    old_max = int(getattr(player, "max_hp", 0))
    old_hp = int(getattr(player, "hp", 0))

    player.max_hp = old_max + amount

    if any(getattr(relic, "relic_id", "") == "relic.mark_of_the_bloom" for relic in getattr(player, "relics", []) or []):
        player.hp = min(player.max_hp, old_hp)
    else:
        player.hp = min(player.max_hp, old_hp + amount)

    return ["【{}】生效：最大生命值 {} -> {}，HP {} -> {}。".format(
        getattr(card, "name", "效果"),
        old_max,
        player.max_hp,
        old_hp,
        player.hp
    )]


@register_effect("play_draw_pile_top_count")
def handle_play_draw_pile_top_count(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    logs = []

    times = resolve_effect_times(
        game_state=game_state,
        card=card,
        effect=effect,
        effect_context=effect_context,
    )
    times = int(times)

    if times <= 0:
        return ["【{}】没有打出抽牌堆顶牌。".format(card.name)]

    for index in range(times):
        if game_state.battle_over:
            logs.append("战斗已经结束，后续抽牌堆顶牌不再打出。")
            break

        has_draw_card = reshuffle_discard_into_draw_if_needed(
            player,
            logs,
            game_state=game_state
        )

        if not has_draw_card:
            logs.append("抽牌堆和弃牌堆都为空，【{}】停止结算。".format(card.name))
            break

        top_card = player.draw_pile.pop()

        logs.append("【{}】第 {}/{} 张：抽牌堆顶为【{}】。".format(
            card.name,
            index + 1,
            times,
            top_card.name
        ))

        logs.extend(play_card_from_effect_and_exhaust(
            game_state=game_state,
            source_card=card,
            played_card=top_card,
            reason="distilled_chaos",
            force_exhaust=False,
        ))

    return logs


@register_effect("randomize_hand_costs")
def handle_randomize_hand_costs(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    logs = []

    changed = 0
    skipped_corruption = 0

    from game.modifiers import get_status_value

    has_corruption = get_status_value(player, "corruption") > 0

    for hand_card in getattr(player, "hand", []) or []:
        if getattr(hand_card, "card_type", "") in ("status", "curse"):
            continue

        if getattr(hand_card, "cost", None) == "X":
            continue

        if has_corruption and getattr(hand_card, "card_type", "") == "skill":
            # 修复原版异蛇之油 + 腐化时技能牌可能被随机成 1~3 的问题。
            if hasattr(hand_card, "temporary_cost_override"):
                delattr(hand_card, "temporary_cost_override")
            skipped_corruption += 1
            continue

        new_cost = random.randint(0, 3)
        setattr(hand_card, "temporary_cost_override", new_cost)

        logs.append("【异蛇之油】使【{}】本回合费用随机变为 {}。".format(
            hand_card.name,
            new_cost
        ))
        changed += 1

    if skipped_corruption > 0:
        logs.append("【异蛇之油】检测到腐化：{} 张技能牌保持 0 费。".format(skipped_corruption))

    if changed <= 0 and skipped_corruption <= 0:
        logs.append("【{}】没有可随机化费用的手牌。".format(card.name))

    return logs

def apply_card_effects(game_state, card, target_index, effect_context=None):
    logs = []

    if effect_context is None:
        effect_context = {}
    else:
        effect_context = dict(effect_context)

    card_zone_element = get_effective_zone_element_for_card(
        game_state=game_state,
        card=card,
        effect=None,
        effect_context=effect_context
    )

    # 打出牌时触发一次的 Zone 能力。真实阴 Zone 的反噬仍按“打出牌”触发一次。
    # 深渊形态视为每次重放都重新结算一次虚拟极阴效果，所以放到重放循环内处理。
    apply_water_zone_regeneration_on_card_play(
        game_state=game_state,
        card=card,
        effect_context=effect_context,
        logs=logs
    )
    if not bool(getattr(card, "skip_auto_zone_hp_loss", False)):
        apply_zone_source_hp_loss_if_needed(
            game_state=game_state,
            source=game_state.player,
            zone_element=card_zone_element,
            logs=logs,
            label="阴 Zone",
            card=card,
            count_as_player_self_action_hp_loss=True
        )
    replay_extra = int(getattr(card, "replay_extra", 0))
    replay_extra += int(effect_context.get("replay_extra", 0))

    if not bool(getattr(card, "ignore_zone_replay", False)):
        replay_extra += get_zone_replay_extra(game_state, card_zone_element)
    total_times = 1 + replay_extra
    if total_times < 1:
        total_times = 1

    if total_times > 1:
        logs.append("【{}】重放总次数：{}。".format(card.name, total_times))

    for play_index in range(total_times):
        effect_context["_current_replay_index"] = play_index
        effect_context["_total_replay_times"] = total_times

        if game_state.battle_over:
            logs.append("战斗已经结束，后续重放不再结算。")
            break

        if total_times > 1:
            logs.append("【{}】第 {}/{} 次结算：".format(
                card.name,
                play_index + 1,
                total_times
            ))
        from game.status.status_effects import increment_slow_for_card_play
        increment_slow_for_card_play(game_state, logs)
        apply_abyssal_form_hp_loss_if_needed(
            game_state=game_state,
            card=card,
            zone_element=card_zone_element,
            logs=logs
        )

        if game_state.battle_over or not game_state.player.is_alive():
            logs.append("玩家已经倒下，后续结算不再执行。")
            break

        for effect in card.effects:
            logs.extend(apply_card_effect(
                game_state,
                card,
                effect,
                target_index,
                effect_context=effect_context
            ))
            if game_state.battle_over:
                break
        from game.status.status_effects import flush_pending_malleable_triggers
        logs.extend(flush_pending_malleable_triggers(game_state))
        logs.extend(
            trigger_beat_of_death_after_card_resolution(
                game_state=game_state,
                card=card
            )
        )
        if not game_state.player.is_alive():
            break
    from game.status.status_effects import (
        resolve_pending_curl_up_after_card,
        resolve_pending_flying_after_card,
    )
    logs.extend(resolve_pending_curl_up_after_card(
        game_state=game_state,
        card=card
    ))
    logs.extend(resolve_pending_flying_after_card(
        game_state=game_state,
        card=card
    ))
    return logs       


# =========================
# 静默猎手扩展效果
# =========================

def _discard_cards_direct(game_state, indexed_cards, logs, reason="主动丢弃", trigger_clever=True):
    from game.engine import resolve_discarded_card
    player = game_state.player
    for index, discard_card in indexed_cards:
        if discard_card in player.hand:
            player.hand.remove(discard_card)
        logs.append("选择丢弃手牌 [{}] 【{}】。".format(index, discard_card.name))
        logs.extend(resolve_discarded_card(game_state, discard_card, reason=reason, trigger_clever=trigger_clever))


@register_effect("discard_random_hand_cards")
def handle_discard_random_hand_cards(game_state, card, effect, target_index, effect_context):
    logs=[]
    player=game_state.player
    amount=resolve_amount(game_state, card, effect.get("amount",1), source=player, target=player, effect_context=effect_context)
    amount=int(amount)
    if amount<=0 or not player.hand:
        return logs
    hand=list(enumerate(player.hand))
    chosen=random.sample(hand, min(amount, len(hand)))
    _discard_cards_direct(game_state, chosen, logs, reason="主动丢弃", trigger_clever=True)
    return logs


@register_effect("discard_all_hand_then_draw_same")
def handle_discard_all_hand_then_draw_same(game_state, card, effect, target_index, effect_context):
    logs=[]
    player=game_state.player
    indexed=list(enumerate(list(player.hand)))
    count=len(indexed)
    if count<=0:
        logs.append("手牌为空，没有丢弃。")
        return logs
    _discard_cards_direct(game_state, indexed, logs, reason="主动丢弃", trigger_clever=True)
    logs.append("【{}】抽取与丢弃数量相同的牌：{} 张。".format(card.name, count))
    logs.extend(draw_cards_with_no_draw_check(game_state, count, draw_source="calculated_gamble"))
    return logs


@register_effect("discard_all_non_attack_hand_cards")
def handle_discard_all_non_attack_hand_cards(game_state, card, effect, target_index, effect_context):
    logs=[]
    player=game_state.player
    indexed=[(i,c) for i,c in enumerate(list(player.hand)) if getattr(c,"card_type","") != "attack"]
    if not indexed:
        logs.append("没有非攻击牌可丢弃。")
        return logs
    _discard_cards_direct(game_state, indexed, logs, reason="主动丢弃", trigger_clever=True)
    return logs


@register_effect("discard_all_hand_add_shivs")
def handle_discard_all_hand_add_shivs(game_state, card, effect, target_index, effect_context):
    logs=[]
    player=game_state.player
    indexed=list(enumerate(list(player.hand)))
    count=len(indexed)
    if count<=0:
        logs.append("手牌为空，没有丢弃，也没有增加小刀。")
        return logs
    _discard_cards_direct(game_state, indexed, logs, reason="主动丢弃", trigger_clever=True)
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card
    for _ in range(count):
        shiv=create_card("card.shiv")
        if bool(effect.get("upgrade_shiv", False)):
            shiv=upgrade_card(shiv)
        setattr(shiv,"temporary",True)
        setattr(shiv,"created_in_battle",True)
        add_card_to_hand_or_discard(player, shiv, logs, card.name)
    return logs


@register_effect("gain_status_all_enemies")
def handle_gain_status_all_enemies(game_state, card, effect, target_index, effect_context):
    logs=[]
    status_key=effect.get("status","")
    from game.status.status_gain import format_status_gain_log
    for enemy in get_all_alive_enemies(game_state):
        amount=resolve_amount(game_state, card, effect.get("amount"), source=game_state.player, target=enemy, effect_context=effect_context)
        result=enemy.gain_status_with_result(status_key, int(amount))
        logs.append(format_status_gain_log(enemy, status_key, int(amount), result))
    return logs


@register_effect("gain_status_random_enemies")
def handle_gain_status_random_enemies(game_state, card, effect, target_index, effect_context):
    logs=[]
    enemies=get_all_alive_enemies(game_state)
    if not enemies:
        return ["没有敌人可以获得状态。"]
    times=resolve_effect_times(game_state, card, effect, effect_context)
    status_key=effect.get("status","")
    from game.status.status_gain import format_status_gain_log
    for i in range(max(0,int(times))):
        enemies=get_all_alive_enemies(game_state)
        if not enemies:
            break
        enemy=random.choice(enemies)
        amount=resolve_amount(game_state, card, effect.get("amount"), source=game_state.player, target=enemy, effect_context=effect_context)
        result=enemy.gain_status_with_result(status_key, int(amount))
        logs.append("【{}】第 {}/{} 次命中 {}。".format(card.name, i+1, times, enemy.name))
        logs.append(format_status_gain_log(enemy, status_key, int(amount), result))
    return logs


@register_effect("multiply_status")
def handle_multiply_status(game_state, card, effect, target_index, effect_context):
    logs=[]
    target=get_effect_target_entity(game_state, effect.get("target","selected_enemy"), target_index)
    if target is None:
        return ["目标无效。"]
    status_key=effect.get("status","")
    current=get_status_value(target, status_key)
    multiplier=resolve_amount(game_state, card, effect.get("multiplier",2), source=game_state.player, target=target, effect_context=effect_context)
    new_value=int(current)*int(multiplier)
    if new_value<0:
        new_value=0
    if hasattr(target,"statuses"):
        target.statuses.set(status_key,new_value)
    logs.append("【{}】使 {} 的{}层数 {} -> {}。".format(card.name, target.name, get_status_name(status_key), current, new_value))
    return logs


@register_effect("deal_damage_times_by_attack_played_this_turn")
def handle_deal_damage_times_by_attack_played_this_turn(game_state, card, effect, target_index, effect_context):
    logs=[]
    counts=getattr(game_state,"player_card_type_played_counts_this_turn",{}) or {}
    times=int(counts.get("attack",0) or 0) + 1
    if times<=0:
        logs.append("本回合没有打出过攻击牌，【{}】没有造成伤害。".format(card.name))
        return logs
    child={"op":"deal_damage","target":effect.get("target","selected_enemy"),"amount":effect.get("amount"),"times":times}
    logs.append("【{}】按本回合攻击牌数结算 {} 次。".format(card.name,times))
    logs.extend(apply_card_effect(game_state, card, child, target_index, effect_context))
    return logs


@register_effect("deal_damage_times_by_hand_type")
def handle_deal_damage_times_by_hand_type(game_state, card, effect, target_index, effect_context):
    ctype=effect.get("card_type","skill")
    times=sum(1 for c in getattr(game_state.player,"hand",[]) if getattr(c,"card_type","")==ctype)
    logs=[]
    if times<=0:
        logs.append("手牌中没有{}牌，【{}】没有造成伤害。".format(ctype, card.name))
        return logs
    child={"op":"deal_damage","target":effect.get("target","selected_enemy"),"amount":effect.get("amount"),"times":times}
    logs.append("【{}】按手牌中{}牌数量结算 {} 次。".format(card.name,ctype,times))
    logs.extend(apply_card_effect(game_state, card, child, target_index, effect_context))
    return logs


@register_effect("draw_one_if_skill_gain_block")
def handle_draw_one_if_skill_gain_block(game_state, card, effect, target_index, effect_context):
    logs=[]
    player=game_state.player
    before=list(player.hand)
    logs.extend(draw_cards_with_no_draw_check(game_state,1,draw_source="escape_plan"))
    drawn=None
    for c in player.hand:
        if c not in before:
            drawn=c
            break
    if drawn is None:
        return logs
    if getattr(drawn,"card_type","") != "skill":
        logs.append("抽到的【{}】不是技能牌，未获得格挡。".format(drawn.name))
        return logs
    block=resolve_amount(game_state, card, effect.get("amount"), source=player, target=player, block_source="played_card", effect_context=effect_context)
    logs.extend(gain_block_without_modifiers(game_state, player, player, int(block), block_source="played_card", card=card, message="【{}】抽到技能牌，获得 {} 点格挡。当前格挡：{}。".format(card.name, int(block), player.block+int(block))))
    return logs


@register_effect("draw_until_hand_size")
def handle_draw_until_hand_size(game_state, card, effect, target_index, effect_context):
    target_size=resolve_amount(game_state, card, effect.get("amount"), source=game_state.player, target=game_state.player, effect_context=effect_context)
    target_size=int(target_size)
    count=max(0, target_size-len(getattr(game_state.player,"hand",[]) or []))
    if count<=0:
        return ["手牌数量已经达到 {}。".format(target_size)]
    return draw_cards_with_no_draw_check(game_state,count,draw_source="expertise")


@register_effect("add_random_skill_to_hand_temp_cost_zero")
def handle_add_random_skill_to_hand_temp_cost_zero(game_state, card, effect, target_index, effect_context):
    owner_character_id=effect.get("owner_character_id",getattr(card,"owner_character_id",""))
    exclude=set(effect.get("exclude_card_ids",[]))
    from data.card.AAAregistry import CARD_REGISTRY, create_card
    from data.content_gate import is_content_enabled
    candidates=[]
    for cid in CARD_REGISTRY.keys():
        if cid in exclude or not is_content_enabled("card",cid):
            continue
        try:
            c=create_card(cid)
        except Exception:
            continue
        if getattr(c,"card_type","")!="skill":
            continue
        if getattr(c,"quantity","") in ("starting","status","curse","test"):
            continue
        if getattr(c,"owner_character_id","") != owner_character_id:
            continue
        if getattr(c,"cost",None)=="X" or getattr(c,"cost",None)=="-":
            continue
        candidates.append(cid)
    if not candidates:
        return ["没有可生成的随机技能牌。"]
    new_card=create_card(random.choice(candidates))
    setattr(new_card,"temporary",True)
    setattr(new_card,"created_in_battle",True)
    setattr(new_card,"temporary_cost_override",0)
    add_card_to_hand_or_discard(game_state.player,new_card,logs:=[],card.name)
    if logs:
        logs[-1]=logs[-1]+"本回合其费用变为 0。"
    return logs


@register_effect("set_all_hand_cost_zero_this_turn")
def handle_set_all_hand_cost_zero_this_turn(game_state, card, effect, target_index, effect_context):
    count=0
    for hand_card in getattr(game_state.player,"hand",[]) or []:
        if getattr(hand_card,"card_type","") in ("status","curse"):
            continue
        if getattr(hand_card,"cost",None) in ("X","-"):
            continue
        setattr(hand_card,"temporary_cost_override",0)
        count+=1
    return ["【{}】使 {} 张手牌本回合耗能变为 0。".format(card.name,count)]


@register_effect("request_hand_to_draw_top_temp_cost_zero")
def handle_request_hand_to_draw_top_temp_cost_zero(game_state, card, effect, target_index, effect_context):
    player=game_state.player
    options=list(player.hand)
    if not options:
        return ["手牌为空，没有可以放到抽牌堆顶的牌。"]
    from game.pending_choice import PendingChoice, set_pending_choice
    set_pending_choice(game_state, PendingChoice(kind="hand_to_draw_top", source=card.name, prompt="请选择 1 张手牌放到抽牌堆顶，并使其耗能变为 0：/card handtop 0。", command_hint="handtop 等效 hand_top，warcry，置顶手牌，手牌置顶。", block_message="当前需要先处理手牌置顶选择。用法：/card handtop 0。", options=options, payload={"set_cost_zero": True, "destination":"top"}))
    logs=["请选择 1 张手牌放到抽牌堆顶，并使其耗能变为 0：/card handtop 0。","可选牌："]
    for i,c in enumerate(options):
        logs.append("[{}] {}".format(i,c.summary_text()))
    return logs


@register_effect("decrease_self_card_var")
def handle_decrease_self_card_var(game_state, card, effect, target_index, effect_context):
    var=effect.get("var","")
    if not var:
        return []
    amount=resolve_amount(game_state,card,effect.get("amount",1),source=game_state.player,target=game_state.player,effect_context=effect_context)
    min_value=int(effect.get("min_value",0))
    old=int(card.card_vars.get(var,0))
    new=max(min_value,old-int(amount))
    card.card_vars[var]=new
    return ["【{}】的基础{}降低：{} -> {}。".format(card.name,var,old,new)]


@register_effect("gain_random_potion")
def handle_gain_random_potion(game_state, card, effect, target_index, effect_context):
    try:
        from game.reward import roll_potion_id_by_rarity
        from data.potion.AAAregistry import create_potion
        from game.relic_logic.run_relic_utils import try_gain_potion_with_relics
        potion_id=roll_potion_id_by_rarity(random, run_state=getattr(game_state,"run_state",None), include_event=False)
        if potion_id is None:
            return ["没有可获得的随机药水。"]
        potion=create_potion(potion_id)
        return try_gain_potion_with_relics(game_state.player, potion, source=card.name)
    except Exception as exc:
        return ["获得随机药水失败：{}".format(exc)]


@register_effect("request_night_terror_card")
def handle_request_night_terror_card(game_state, card, effect, target_index, effect_context):
    player = game_state.player
    hand = list(getattr(player, "hand", []) or [])

    if not hand:
        return ["手牌为空，夜魇没有选择目标。"]

    lines = [
        "=== {}：选择 1 张手牌，下回合加入 3 张复制品 ===".format(card.name),
        "编号使用当前手牌编号。"
    ]
    for index, hand_card in enumerate(hand):
        lines.append("[{}] {}".format(index, hand_card.summary_text()))
    lines.append("")
    lines.append("用法：/card nightmare 0。")

    set_pending_choice(game_state, PendingChoice(
        kind="night_terror",
        source=card.name,
        prompt="\n".join(lines),
        command_hint="nightmare 等效 night_terror，night，夜魇。",
        block_message="当前需要先处理夜魇选择。用法：/card nightmare 0。",
        options=hand,
        payload={},
    ))

    return ["{}".format("\n".join(lines))]
