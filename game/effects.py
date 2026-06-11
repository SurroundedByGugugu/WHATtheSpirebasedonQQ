# -*- coding: utf-8 -*-

from game.modifiers import apply_modifier_profile, get_status_value
from game.status.status_defs import get_status_name
from game.damage import deal_damage
import random

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

    scaling_list = amount_spec.get("scaling", [])
    for scaling in scaling_list:
        stat = scaling.get("stat")
        multiplier_var = scaling.get("multiplier_var")

        if not stat or not multiplier_var:
            continue
        stat_value = get_status_value(source, stat)
        multiplier = int(card_vars.get(multiplier_var, 0))
        value += stat_value * multiplier

    x_var_name = amount_spec.get("x_var")
    if x_var_name:
        value += int(effect_context.get(x_var_name, 0))

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

    modifier_profile = amount_spec.get("modifier_profile")

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
        attack_element=attack_element
    )

    zone_element = ""
    if effect_context is not None:
        zone_element = effect_context.get("zone_element", "")
    if zone_element:
        from game.zone_utils import apply_zone_amount_modifier
        value = apply_zone_amount_modifier(
            value=value,
            game_state=game_state,
            zone_element=zone_element
        )

    return int(value)


def get_target_enemy(game_state, target_index):
    enemies = game_state.enemies
    if target_index < 0 or target_index >= len(enemies):
        return None
    enemy = enemies[target_index]
    if not enemy.is_alive():
        return None
    return enemy

def get_alive_enemies(game_state):
    alive_enemies = []
    for enemy in game_state.enemies:
        if enemy.is_alive():
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
    attack_element = effect.get("attack_element", getattr(card, "attack_element", ""))
    return attack_type, attack_element


def get_effect_zone_element(game_state, card, effect, effect_context):
    from game.zone_utils import get_effective_zone_element_for_card
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


def get_all_alive_enemies(game_state):
    return [enemy for enemy in game_state.enemies if enemy.is_alive()]


def should_convert_enemy_target_to_all(game_state, zone_element, target_key):
    from game.zone_utils import should_zone_thunder_make_all
    if target_key not in ("selected_enemy", "enemy", "random_enemy"):
        return False
    return should_zone_thunder_make_all(game_state, zone_element)


def deal_card_attack_damage_to_target(game_state, card, effect, target_entity, effect_context, attack_type, attack_element, zone_element, logs, prefix):
    from game.zone_utils import apply_fire_zone_burn

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

def apply_card_effect(game_state, card, effect, target_index, effect_context=None):
    """
    执行单个卡牌效果。
    返回 logs。
    """
    if effect_context is None:
        effect_context = {}
    logs = []

    op = effect.get("op")

    if op == "deal_damage":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)
        target_key = effect.get("target", "selected_enemy")

        if should_convert_enemy_target_to_all(game_state, zone_element, target_key):
            alive_enemies = get_all_alive_enemies(game_state)
            if not alive_enemies:
                logs.append("没有可攻击的敌人。")
                return logs
            logs.append("雷 Zone 使【{}】的目标变为全体。".format(card.name))
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
            return logs

        target_entity = get_effect_target_entity(
            game_state=game_state,
            target_key=target_key,
            target_index=target_index
        )
        if target_entity is None:
            logs.append("目标敌人无效。")
            return logs

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
    
    if op == "deal_damage_random_enemies":
        attack_type, attack_element = get_effect_attack_tags(card, effect)
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)
        times_spec = effect.get("times", None)
        if times_spec is None:
            times_spec = effect.get("count", 1)
        times = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=times_spec,
            source=game_state.player,
            target=game_state.player,
            effect_context=local_context
        )
        times = int(times)
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
            from game.zone_utils import apply_fire_zone_burn
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
        alive_enemies = []
        for enemy in game_state.enemies:
            if enemy.is_alive():
                alive_enemies.append(enemy)
        if not alive_enemies:
            logs.append("没有可攻击的敌人。")
            return logs
        for target_entity in alive_enemies:
            if game_state.battle_over:
                logs.append("战斗已经结束，后续全体伤害不再结算。")
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
            if game_state.battle_over:
                break
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
        target_entity.block += amount
        logs.append("{} 获得 {} 点格挡。".format(
            target_entity.name,
            amount
        ))
        from game.zone_utils import apply_earth_zone_temp_thorns
        apply_earth_zone_temp_thorns(
            game_state=game_state,
            target=target_entity,
            zone_element=zone_element,
            block_amount=amount,
            logs=logs
        )
        return logs

    if op == "gain_status":
        status_key = effect.get("status")
        target_key = effect.get("target", "self")
        zone_element = get_effect_zone_element(game_state, card, effect, effect_context)
        local_context = make_zone_effect_context(effect_context, zone_element)
        if not status_key:
            logs.append("gain_status 缺少 status。")
            return logs

        target_entities = []
        if should_convert_enemy_target_to_all(game_state, zone_element, target_key):
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
            if hasattr(target_entity, "gain_status_with_result"):
                result = target_entity.gain_status_with_result(status_key, amount)
                from game.status.status_gain import format_status_gain_log
                logs.append(format_status_gain_log(target_entity, status_key, amount, result))
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

    if op == "lose_dexterity_this_turn":
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )
        amount = int(amount)
        player = game_state.player
        current_dexterity = player.gain_status("dexterity", -amount)
        restore_value = player.gain_status("temporary_dexterity_loss", amount)
        logs.append("{} 本回合失去 {} 点敏捷。当前敏捷：{}。回合结束将恢复 {} 点。".format(
            player.name,
            amount,
            current_dexterity,
            restore_value
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
    
    if op == "draw_cards":
        amount = resolve_amount(
            game_state=game_state,
            card=card,
            amount_spec=effect.get("amount"),
            source=game_state.player,
            target=game_state.player,
            effect_context=effect_context
        )

        logs.extend(game_state.player.draw_cards(amount))
        return logs

    if op == "draw_to_full":
        logs.extend(game_state.player.draw_to_full())
        return logs

    if op == "request_discard_any":
        game_state.pending_discard_selection = True
        game_state.pending_discard_source = card.name
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
        from game.zone_utils import deploy_element_zone
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

    if op == "gain_energy":
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

    logs.append("未知效果：{}".format(op))
    return logs


def apply_card_effects(game_state, card, target_index, effect_context=None):
    logs = []

    if effect_context is None:
        effect_context = {}
    else:
        effect_context = dict(effect_context)

    from game.zone_utils import (
        get_effective_zone_element_for_card,
        get_zone_replay_extra,
        apply_zone_source_hp_loss_if_needed,
        apply_water_zone_regeneration_on_card_play,
    )

    card_zone_element = get_effective_zone_element_for_card(
        game_state=game_state,
        card=card,
        effect=None,
        effect_context=effect_context
    )

    # 打出牌时触发一次的 Zone 能力。重放不会重复触发这里。
    apply_water_zone_regeneration_on_card_play(
        game_state=game_state,
        card=card,
        effect_context=effect_context,
        logs=logs
    )
    apply_zone_source_hp_loss_if_needed(
        game_state=game_state,
        source=game_state.player,
        zone_element=card_zone_element,
        logs=logs,
        label="阴 Zone"
    )

    replay_extra = int(getattr(card, "replay_extra", 0))
    replay_extra += int(effect_context.get("replay_extra", 0))
    replay_extra += get_zone_replay_extra(game_state, card_zone_element)
    total_times = 1 + replay_extra
    if total_times < 1:
        total_times = 1

    if total_times > 1:
        logs.append("【{}】重放总次数：{}。".format(card.name, total_times))

    for play_index in range(total_times):
        if game_state.battle_over:
            logs.append("战斗已经结束，后续重放不再结算。")
            break

        if total_times > 1:
            logs.append("【{}】第 {}/{} 次结算：".format(
                card.name,
                play_index + 1,
                total_times
            ))

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

    return logs
