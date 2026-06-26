# -*- coding: utf-8 -*-
from game.zone_utils import (
    apply_zone_damage_modifier,
    get_zone_damage_multiplier,
    get_zone_base_amount_multiplier
)

from game.constants import (
    DAMAGE_SOURCE_ENEMY_ACTION,
    DAMAGE_SOURCE_PLAYED_CARD,
    BLOCK_SOURCE_ENEMY_ACTION,
    BLOCK_SOURCE_PLAYED_CARD,
    VULNERABLE_ENEMY_ATTACK_DAMAGE_MULT,
    VULNERABLE_PLAYER_CARD_DAMAGE_MULT,
    WEAK_ENEMY_ATTACK_DAMAGE_MULT,
    WEAK_PLAYER_CARD_DAMAGE_MULT,
    FRAIL_ENEMY_ACTION_BLOCK_MULT,
    FRAIL_PLAYER_CARD_BLOCK_MULT,
)



def entity_has_relic(entity, relic_id):
    for relic in getattr(entity, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False

def get_status_value(entity, key):
    if entity is None:
        return 0
    statuses = getattr(entity, "statuses", None)
    if statuses is None:
        return 0
    value = statuses.get(key)
    if value is None:
        return 0
    return int(value)

def apply_block_modifiers(
        value,
        game_state,
        source,
        target,
        card=None,
        block_source=None,
        zone_element=""
    ):
    value = int(value)
    if block_source is None:
        block_source = BLOCK_SOURCE_PLAYED_CARD
    value += get_status_value(source, "dexterity")
    if get_status_value(source, "frail") > 0:
        if block_source == BLOCK_SOURCE_PLAYED_CARD:
            value = int(value * FRAIL_PLAYER_CARD_BLOCK_MULT)
        elif block_source == BLOCK_SOURCE_ENEMY_ACTION:
            value = int(value * FRAIL_ENEMY_ACTION_BLOCK_MULT)
    value = int(value * get_zone_base_amount_multiplier(
        game_state=game_state,
        zone_element=zone_element
    ))
    if value < 0:
        value = 0
    return value

def get_attack_status_multiplier(source, target, damage_source):
    """
    攻击状态乘区。

    当前包括：
    - 虚弱 weak
    - 易伤 vulnerable

    注意：
    力量 strength 是加算，不放在这里。
    Zone / Field 是环境乘区，也不放在这里。
    """
    multiplier = 1.0

    if get_status_value(source, "weak") > 0:
        if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
            multiplier *= WEAK_PLAYER_CARD_DAMAGE_MULT
        elif damage_source == DAMAGE_SOURCE_ENEMY_ACTION:
            if entity_has_relic(target, "relic.paper_crane"):
                multiplier *= 0.60
            else:
                multiplier *= WEAK_ENEMY_ATTACK_DAMAGE_MULT

    if get_status_value(source, "burn") > 0:
        multiplier *= 0.5

    if get_status_value(target, "vulnerable") > 0:
        if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
            if entity_has_relic(source, "relic.paper_frog"):
                multiplier *= 1.75
            else:
                multiplier *= VULNERABLE_PLAYER_CARD_DAMAGE_MULT
        elif damage_source == DAMAGE_SOURCE_ENEMY_ACTION:
            if entity_has_relic(target, "relic.odd_mushroom"):
                multiplier *= 1.25
            else:
                multiplier *= VULNERABLE_ENEMY_ATTACK_DAMAGE_MULT
        # 飞行：只影响 attack_damage 乘区；荆棘/中毒/效果伤害不会进入这里。
    if get_status_value(target, "flying") > 0:
        multiplier *= 0.5
    return multiplier


def get_attack_environment_multiplier(game_state, attack_element="", zone_element=""):
    """
    攻击环境乘区。

    当前包括：
    - Zone 基础数值乘区

    attack_element 保留给后续 Field / 类型修正使用；
    Zone 是否生效以 zone_element 为准，避免以太介质等覆盖 tag 的效果失效。
    """
    multiplier = 1.0

    multiplier *= get_zone_base_amount_multiplier(
        game_state=game_state,
        zone_element=zone_element
    )

    return multiplier


def apply_attack_damage_modifiers(
        value,
        game_state,
        source,
        target,
        card=None,
        damage_source=None,
        attack_type="",
        attack_element="",
        zone_element=""
    ):
    """
    攻击伤害通用修正。

    结算顺序：
    1. 基础值
    2. 力量加算
    3. 状态乘区：虚弱 / 易伤
    4. 环境乘区：Zone / Field
    5. 小于 0 归 0
    """
    value = int(value)
    if damage_source is None:
        damage_source = DAMAGE_SOURCE_PLAYED_CARD
    # 1. 力量属于攻击基础区的加算修正。
    value += get_status_value(source, "strength")

    if (
        damage_source == DAMAGE_SOURCE_PLAYED_CARD
        and card is not None
        and entity_has_relic(source, "relic.strike_dummy")
        and "打击" in getattr(card, "name", "")
    ):
        value += 3

    # 活力也是攻击基础区的加算修正；赤牛的多段攻击每段均吃到加成。
    if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
        value += get_status_value(source, "vigor")

    # 袖剑：费用为 0 的攻击牌额外造成 4 点伤害。战斗中临时变 0 费也生效。
    if (
        damage_source == DAMAGE_SOURCE_PLAYED_CARD
        and card is not None
        and getattr(card, "card_type", "") == "attack"
        and entity_has_relic(source, "relic.wrist_blade")
    ):
        try:
            from game.card_cost import get_card_current_cost
            current_cost = int(get_card_current_cost(game_state, card))
        except Exception:
            current_cost = int(getattr(card, "cost", 0) or 0)
        if current_cost == 0:
            value += 4

    # 2. 状态乘区
    status_multiplier = get_attack_status_multiplier(
        source=source,
        target=target,
        damage_source=damage_source
    )
    value = int(value * status_multiplier)
    # 3. 锁定目标乘区：好，下一个
    if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
        from game.target_lock import get_next_target_damage_multiplier
        value = int(value * get_next_target_damage_multiplier(target))
    # 4. 环境乘区
    environment_multiplier = get_attack_environment_multiplier(
        game_state=game_state,
        attack_element=attack_element,
        zone_element=zone_element
    )
    value = int(value * environment_multiplier)

    # 5. 钢笔尖：大多数伤害修正之后翻倍。
    if damage_source == DAMAGE_SOURCE_PLAYED_CARD and getattr(source, "_pen_nib_active_card", None) is card:
        value = int(value * 2)

    if value < 0:
        value = 0
    return int(value)



def apply_modifier_profile(
        value,
        modifier_profile,
        game_state,
        source,
        target,
        card=None,
        damage_source=None,
        block_source=None,
        attack_type="",
        attack_element="",
        zone_element=""
    ):
    if modifier_profile is None:
        return int(value)
    if modifier_profile == "attack_damage":
        return apply_attack_damage_modifiers(
            value=value,
            game_state=game_state,
            source=source,
            target=target,
            card=card,
            damage_source=damage_source,
            attack_type=attack_type,
            attack_element=attack_element,
            zone_element=zone_element
        )
    if modifier_profile == "block":
        return apply_block_modifiers(
            value=value,
            game_state=game_state,
            source=source,
            target=target,
            card=card,
            block_source=block_source,
            zone_element=zone_element
        )
    return int(value)