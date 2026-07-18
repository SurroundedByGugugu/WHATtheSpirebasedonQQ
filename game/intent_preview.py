# -*- coding: utf-8 -*-

from game.constants import (
    DAMAGE_SOURCE_ENEMY_ACTION,
    BLOCK_SOURCE_ENEMY_ACTION,
)
from game.modifiers import apply_modifier_profile
from data.enemy.base_enemy import get_attack_type_display_name
from data.zones.element_zones import get_element_display_name


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

def _format_attack_text(
        prefix,
        value,
        base_value,
        repeat=1,
        value_suffix=""
    ):
    value = int(value)
    base_value = int(base_value)
    repeat = max(1, int(repeat))

    if repeat > 1:
        text = "{} {} ×{}".format(
            prefix,
            value,
            repeat
        )

        if value_suffix:
            text += " {}".format(value_suffix)

        if value != base_value:
            text += "（基础 {} ×{}）".format(
                base_value,
                repeat
            )

        return text

    text = "{} {}".format(prefix, value)

    if value_suffix:
        text += " {}".format(value_suffix)

    if value != base_value:
        text += "（基础 {}）".format(base_value)

    return text


def _get_attack_prefix(intent, verb="攻击"):
    tag_parts = []
    attack_element = getattr(intent, "attack_element", "")
    attack_type = getattr(intent, "attack_type", "")

    if attack_element:
        tag_parts.append(get_element_display_name(attack_element))
    if attack_type:
        tag_parts.append(get_attack_type_display_name(attack_type))

    if not tag_parts:
        return verb
    return "{} {}".format("/".join(tag_parts), verb)


def _format_one_intent_text(game_state, enemy, intent):
    if intent.kind == "multi":
        parts = []

        for child in getattr(intent, "actions", []):
            text = _format_one_intent_text(
                game_state,
                enemy,
                child
            )

            if text:
                parts.append(text)

        return "；".join(parts)

    if intent.kind == "attack":
        value = preview_enemy_attack_damage(
            game_state=game_state,
            enemy=enemy,
            base_damage=intent.value,
            target_key=getattr(intent, "target", "player"),
            attack_type=getattr(intent, "attack_type", ""),
            attack_element=getattr(intent, "attack_element", "")
        )

        # 没有发生数值修正时沿用 EnemyIntent.to_text()，
        # 保留攻击属性、攻击类型和吸血说明。
        if value == int(intent.value):
            return intent.to_text()

        text = _format_attack_text(
            prefix=_get_attack_prefix(intent),
            value=value,
            base_value=intent.value,
            repeat=getattr(intent, "repeat", 1)
        )

        if getattr(intent, "heal_unblocked", False):
            text += "，回复未被格挡伤害等量生命"

        return text

    if intent.kind == "attack_gain_block_equal_output":
        value = preview_enemy_attack_damage(
            game_state=game_state,
            enemy=enemy,
            base_damage=intent.value,
            target_key=getattr(intent, "target", "player"),
            attack_type=getattr(intent, "attack_type", ""),
            attack_element=getattr(intent, "attack_element", "")
        )

        damage_text = _format_attack_text(
            prefix=_get_attack_prefix(intent, verb="造成"),
            value=value,
            base_value=intent.value,
            repeat=getattr(intent, "repeat", 1),
            value_suffix="点伤害"
        )

        return "{}，获得等同于本次伤害输出的格挡".format(
            damage_text
        )

    if intent.kind == "smart_ally_block_or_attack":
        value = preview_enemy_attack_damage(
            game_state=game_state,
            enemy=enemy,
            base_damage=intent.count,
            target_key="player",
            attack_type=getattr(intent, "attack_type", ""),
            attack_element=getattr(intent, "attack_element", "")
        )

        attack_text = _format_attack_text(
            prefix=_get_attack_prefix(intent),
            value=value,
            base_value=intent.count,
            repeat=1
        )

        return "给予随机队友 {} 点格挡；若无队友则{}".format(
            int(intent.value),
            attack_text
        )

    if intent.kind == "block":
        value = preview_enemy_block(
            game_state=game_state,
            enemy=enemy,
            base_block=intent.value
        )

        if value != int(intent.value):
            return "获得 {} 点格挡（基础 {}）".format(
                value,
                intent.value
            )

        return intent.to_text()

    return intent.to_text()


def format_enemy_intent_text(game_state, enemy):
    if not enemy.is_alive():
        return "已经走了有一会了。"

    intent = enemy.get_current_intent()
    return _format_one_intent_text(game_state, enemy, intent)
