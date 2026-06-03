# -*- coding: utf-8 -*-
from game.zone_utils import (
    apply_zone_damage_modifier,
    get_zone_damage_multiplier
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
        block_source=None
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
            multiplier *= WEAK_ENEMY_ATTACK_DAMAGE_MULT

    if get_status_value(target, "vulnerable") > 0:
        if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
            multiplier *= VULNERABLE_PLAYER_CARD_DAMAGE_MULT
        elif damage_source == DAMAGE_SOURCE_ENEMY_ACTION:
            multiplier *= VULNERABLE_ENEMY_ATTACK_DAMAGE_MULT

    return multiplier


def get_attack_environment_multiplier(game_state, attack_element=""):
    """
    攻击环境乘区。

    当前包括：
    - Zone 同属性倍率

    后续可以继续加入：
    - Field 倍率
    - 特殊环境修正
    """
    multiplier = 1.0

    multiplier *= get_zone_damage_multiplier(
        game_state=game_state,
        attack_element=attack_element
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
        attack_element=""
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
    # 1. 力量属于攻击基础区的加算修正
    value += get_status_value(source, "strength")
    # 2. 状态乘区
    status_multiplier = get_attack_status_multiplier(
        source=source,
        target=target,
        damage_source=damage_source
    )
    value = int(value * status_multiplier)
    # 3. 环境乘区
    environment_multiplier = get_attack_environment_multiplier(
        game_state=game_state,
        attack_element=attack_element
    )
    value = int(value * environment_multiplier)
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
        attack_element=""
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
            attack_element=attack_element
        )
    if modifier_profile == "block":
        return apply_block_modifiers(
            value=value,
            game_state=game_state,
            source=source,
            target=target,
            card=card,
            block_source=block_source
        )
    return int(value)