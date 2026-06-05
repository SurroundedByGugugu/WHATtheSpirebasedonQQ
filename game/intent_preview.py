# -*- coding: utf-8 -*-

from game.constants import (
    DAMAGE_SOURCE_ENEMY_ACTION,
    BLOCK_SOURCE_ENEMY_ACTION,
)
from game.modifiers import apply_modifier_profile


def find_first_alive_enemy_by_id(game_state, enemy_id, exclude_enemy=None):
    for target in getattr(game_state, "enemies", []):
        if target is exclude_enemy:
            continue
        if not target.is_alive():
            continue
        if getattr(target, "enemy_id", "") == enemy_id:
            return target
    return None


def get_enemy_preview_target(game_state, enemy, target_key):
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


def preview_enemy_attack_damage(game_state, enemy, base_damage, target_key="player", attack_type="", attack_element=""):
    target = get_enemy_preview_target(game_state, enemy, target_key)
    if target is None:
        return int(base_damage)

    return apply_modifier_profile(
        value=int(base_damage),
        modifier_profile="attack_damage",
        game_state=game_state,
        source=enemy,
        target=target,
        card=None,
        damage_source=DAMAGE_SOURCE_ENEMY_ACTION,
        attack_type=attack_type,
        attack_element=attack_element
    )


def preview_enemy_block(game_state, enemy, base_block):
    return apply_modifier_profile(
        value=int(base_block),
        modifier_profile="block",
        game_state=game_state,
        source=enemy,
        target=enemy,
        card=None,
        block_source=BLOCK_SOURCE_ENEMY_ACTION
    )


def format_enemy_intent_text(game_state, enemy):
    if not enemy.is_alive():
        return "已经走了有一会了。"

    intent = enemy.get_current_intent()

    if intent.kind == "attack":
        value = preview_enemy_attack_damage(
            game_state=game_state,
            enemy=enemy,
            base_damage=intent.value,
            target_key=getattr(intent, "target", "player"),
            attack_type=getattr(intent, "attack_type", ""),
            attack_element=getattr(intent, "attack_element", "")
        )
        if value != intent.value:
            return "攻击 {}（基础 {}）".format(value, intent.value)
        return intent.to_text()

    if intent.kind == "block":
        value = preview_enemy_block(
            game_state=game_state,
            enemy=enemy,
            base_block=intent.value
        )
        if value != intent.value:
            return "获得 {} 点格挡（基础 {}）".format(value, intent.value)
        return intent.to_text()

    return intent.to_text()