# -*- coding: utf-8 -*-

from game.status.status_defs import get_status_name
from game.status.status_gain import format_status_gain_log


def player_has_relic(game_state, relic_id):
    player = getattr(game_state, "player", None)
    for relic in getattr(player, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def apply_status_with_player_relics(game_state, source, target, status_key, amount):
    """施加状态，并处理“玩家给予敌人状态”相关遗物。返回日志列表。"""
    logs = []
    amount = int(amount)
    player = getattr(game_state, "player", None)
    target_is_enemy = hasattr(target, "enemy_id")

    if status_key == "poison" and source is player and target_is_enemy and amount > 0:
        if player_has_relic(game_state, "relic.snake_skull"):
            amount += 1
            logs.append("【异蛇头骨】触发：中毒层数额外 +1。")
    if status_key == "abyss_gaze" and source is player and target_is_enemy and amount > 0:
        if player_has_relic(game_state, "relic.matte_false_eye"):
            amount += 2
            logs.append("【灰暗的假眼】触发：深渊凝视层数额外 +2。")

    applied = True
    if hasattr(target, "gain_status_with_result"):
        result = target.gain_status_with_result(status_key, amount)
        applied = bool(result.get("applied", False))
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

    if (
        applied
        and status_key == "vulnerable"
        and amount > 0
        and source is player
        and target_is_enemy
        and player_has_relic(game_state, "relic.champion_belt")
    ):
        logs.append("【冠军腰带】触发：给予易伤时，同时给予 1 层虚弱。")
        if hasattr(target, "gain_status_with_result"):
            result = target.gain_status_with_result("weak", 1)
            logs.append(format_status_gain_log(target, "weak", 1, result))
        else:
            current = target.gain_status("weak", 1)
            logs.append("{} 获得 1 点虚弱。当前虚弱：{}。".format(target.name, current))

    return logs


def _entity_has_relic(entity, relic_id):
    for relic in getattr(entity, "relics", []) or []:
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def apply_magic_flower_heal_amount(entity, amount):
    amount = int(amount)
    if amount <= 0:
        return 0
    if _entity_has_relic(entity, "relic.magic_flower"):
        return int(amount * 1.5)
    return amount


def heal_player_in_combat(game_state, amount, source_name="回复"):
    player = getattr(game_state, "player", None)
    if player is None:
        return []
    base_amount = int(amount)
    if _entity_has_relic(player, "relic.mark_of_the_bloom"):
        return ["【绽放印记】阻止了【{}】的回复生命。".format(source_name)]
    heal_amount = apply_magic_flower_heal_amount(player, base_amount)
    old_hp = int(getattr(player, "hp", 0))
    max_hp = int(getattr(player, "max_hp", old_hp))
    player.hp = min(max_hp, old_hp + heal_amount)
    real = player.hp - old_hp
    flower_text = ""
    if heal_amount != base_amount:
        flower_text = "【魔法花】使回复量 {} -> {}。".format(base_amount, heal_amount)
    if real > 0:
        return ["【{}】触发：{}回复 {} 点生命。HP：{} -> {}。".format(source_name, flower_text, real, old_hp, player.hp)]
    return ["【{}】触发：{}HP 已满，没有恢复。".format(source_name, flower_text)]
