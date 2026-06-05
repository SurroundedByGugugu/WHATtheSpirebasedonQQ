# -*- coding: utf-8 -*-

NEXT_TARGET_DAMAGE_STATUS = "next_target_damage_taken"


def _get_locked_enemy(game_state):
    enemy = getattr(game_state, "_locked_attack_target_enemy", None)
    turns_left = int(getattr(game_state, "_locked_attack_target_turns", 0))

    if enemy is None or turns_left <= 0:
        clear_attack_target_lock(game_state)
        return None

    if enemy not in getattr(game_state, "enemies", []):
        clear_attack_target_lock(game_state)
        return None

    if not enemy.is_alive():
        clear_attack_target_lock(game_state)
        return None

    return enemy


def clear_attack_target_lock(game_state):
    enemy = getattr(game_state, "_locked_attack_target_enemy", None)
    if enemy is not None and hasattr(enemy, "statuses"):
        enemy.statuses.remove(NEXT_TARGET_DAMAGE_STATUS)

    setattr(game_state, "_locked_attack_target_enemy", None)
    setattr(game_state, "_locked_attack_target_turns", 0)


def get_locked_attack_target_index(game_state):
    enemy = _get_locked_enemy(game_state)
    if enemy is None:
        return None

    try:
        return game_state.enemies.index(enemy)
    except ValueError:
        clear_attack_target_lock(game_state)
        return None


def get_locked_attack_target_text(game_state):
    index = get_locked_attack_target_index(game_state)
    if index is None:
        return ""

    enemy = game_state.enemies[index]
    turns_left = int(getattr(game_state, "_locked_attack_target_turns", 0))
    return "[{}] {}（剩余 {} 回合）".format(index, enemy.name, turns_left)


def lock_attack_target(game_state, enemy, duration=3, initial_bonus_percent=100):
    logs = []

    if enemy is None or not enemy.is_alive():
        logs.append("锁定目标无效。")
        return logs

    duration = int(duration)
    initial_bonus_percent = int(initial_bonus_percent)

    if duration <= 0:
        logs.append("锁定持续时间为 0。")
        return logs

    setattr(game_state, "_locked_attack_target_enemy", enemy)
    setattr(game_state, "_locked_attack_target_turns", duration)

    if hasattr(enemy, "statuses"):
        enemy.statuses.set(NEXT_TARGET_DAMAGE_STATUS, initial_bonus_percent)

    try:
        target_index = game_state.enemies.index(enemy)
    except ValueError:
        target_index = -1

    if target_index >= 0:
        logs.append("锁定攻击目标 [{}] {}，持续 {} 回合。".format(
            target_index,
            enemy.name,
            duration
        ))
    else:
        logs.append("锁定攻击目标 {}，持续 {} 回合。".format(
            enemy.name,
            duration
        ))

    logs.append("{} 受到的攻击牌伤害增加 {}%。".format(
        enemy.name,
        initial_bonus_percent
    ))
    return logs


def tick_attack_target_lock_turn_end(game_state, bonus_increment_percent=50):
    logs = []
    enemy = _get_locked_enemy(game_state)

    if enemy is None:
        return logs

    turns_left = int(getattr(game_state, "_locked_attack_target_turns", 0))
    turns_left -= 1
    setattr(game_state, "_locked_attack_target_turns", turns_left)

    if turns_left <= 0:
        enemy_name = enemy.name
        clear_attack_target_lock(game_state)
        logs.append("{} 的锁定攻击目标效果结束。".format(enemy_name))
        return logs

    if enemy.is_alive() and hasattr(enemy, "statuses"):
        current_bonus = enemy.statuses.add(
            NEXT_TARGET_DAMAGE_STATUS,
            int(bonus_increment_percent)
        )
        logs.append("{} 仍未死亡，受到的攻击牌伤害额外增加 {}%，当前增加 {}%。".format(
            enemy.name,
            int(bonus_increment_percent),
            current_bonus
        ))

    return logs


def get_next_target_damage_multiplier(target):
    if target is None:
        return 1.0

    statuses = getattr(target, "statuses", None)
    if statuses is None:
        return 1.0

    bonus = int(statuses.get(NEXT_TARGET_DAMAGE_STATUS))
    if bonus <= 0:
        return 1.0

    return 1.0 + bonus / 100.0