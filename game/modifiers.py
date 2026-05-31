# -*- coding: utf-8 -*-

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

def apply_attack_damage_modifiers(
        value,
        game_state,
        source,
        target,
        card=None,
        damage_source=None
    ):
    value = int(value)
    if damage_source is None:
        damage_source = "played_card"
    value += get_status_value(source, "strength")
    if get_status_value(source, "weak") > 0:
        if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
            value = int(value * WEAK_PLAYER_CARD_DAMAGE_MULT)
        elif damage_source == DAMAGE_SOURCE_ENEMY_ACTION:
            value = int(value * WEAK_ENEMY_ATTACK_DAMAGE_MULT)
    if get_status_value(target, "vulnerable") > 0:
        if damage_source == DAMAGE_SOURCE_PLAYED_CARD:
            value = int(value * VULNERABLE_PLAYER_CARD_DAMAGE_MULT)
        elif damage_source == DAMAGE_SOURCE_ENEMY_ACTION:
            value = int(value * VULNERABLE_ENEMY_ATTACK_DAMAGE_MULT)
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
        block_source=None
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
            damage_source=damage_source
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