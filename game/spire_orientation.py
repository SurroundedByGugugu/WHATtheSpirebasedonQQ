# -*- coding: utf-8 -*-

SPIRE_SHIELD_ID = "enemy.spire_shield"
SPIRE_SPEAR_ID = "enemy.spire_spear"

SPIRE_ELITE_ENEMY_IDS = {
    SPIRE_SHIELD_ID,
    SPIRE_SPEAR_ID,
}


def get_spire_elite_enemies(game_state, alive_only=False):
    result = []

    for enemy in getattr(game_state, "enemies", []) or []:
        if getattr(enemy, "enemy_id", "") not in SPIRE_ELITE_ENEMY_IDS:
            continue

        if alive_only and not enemy.is_alive():
            continue

        result.append(enemy)

    return result


def is_spire_elite_battle(game_state):
    enemy_ids = {
        getattr(enemy, "enemy_id", "")
        for enemy in getattr(game_state, "enemies", []) or []
    }

    return (
        SPIRE_SHIELD_ID in enemy_ids
        and SPIRE_SPEAR_ID in enemy_ids
    )


def find_spire_enemy(game_state, enemy_id, alive_only=True):
    for enemy in getattr(game_state, "enemies", []) or []:
        if getattr(enemy, "enemy_id", "") != enemy_id:
            continue

        if alive_only and not enemy.is_alive():
            continue

        return enemy

    return None


def refresh_spire_back_attack_statuses(game_state):
    facing_enemy_id = str(
        getattr(game_state, "spire_facing_enemy_id", "") or ""
    )

    for enemy in get_spire_elite_enemies(game_state, alive_only=False):
        enemy_id = getattr(enemy, "enemy_id", "")

        if not enemy.is_alive():
            enemy.statuses.remove("back_attack")
            continue

        if enemy_id == facing_enemy_id:
            enemy.statuses.remove("back_attack")
        else:
            enemy.statuses.set("back_attack", 1)


def set_spire_facing_enemy(
        game_state,
        target_enemy,
        source_text="你的行动"
    ):
    logs = []

    if not is_spire_elite_battle(game_state):
        return logs

    if target_enemy is None or not target_enemy.is_alive():
        return logs

    target_enemy_id = getattr(target_enemy, "enemy_id", "")

    if target_enemy_id not in SPIRE_ELITE_ENEMY_IDS:
        return logs

    old_facing_enemy_id = str(
        getattr(game_state, "spire_facing_enemy_id", "") or ""
    )

    game_state.spire_facing_enemy_id = target_enemy_id
    refresh_spire_back_attack_statuses(game_state)

    if old_facing_enemy_id == target_enemy_id:
        return logs

    rear_enemies = [
        enemy
        for enemy in get_spire_elite_enemies(game_state, alive_only=True)
        if getattr(enemy, "enemy_id", "") != target_enemy_id
    ]

    if rear_enemies:
        logs.append(
            "{}使你转向{}；{}获得后方攻击。".format(
                source_text,
                target_enemy.name,
                rear_enemies[0].name
            )
        )
    else:
        logs.append("{}使你转向{}。".format(
            source_text,
            target_enemy.name
        ))

    return logs


def initialize_spire_elite_orientation(game_state):
    logs = []

    if not is_spire_elite_battle(game_state):
        return logs

    if getattr(game_state, "spire_orientation_initialized", False):
        return logs

    spear = find_spire_enemy(
        game_state,
        SPIRE_SPEAR_ID,
        alive_only=True
    )

    shield = find_spire_enemy(
        game_state,
        SPIRE_SHIELD_ID,
        alive_only=True
    )

    if spear is None or shield is None:
        return logs

    game_state.spire_orientation_initialized = True
    game_state.spire_facing_enemy_id = SPIRE_SPEAR_ID

    refresh_spire_back_attack_statuses(game_state)

    logs.append(
        "战斗初始朝向高塔之矛；高塔之盾获得后方攻击。"
    )

    return logs


def normalize_spire_orientation_after_enemy_death(game_state):
    logs = []

    if not is_spire_elite_battle(game_state):
        return logs

    alive_enemies = get_spire_elite_enemies(
        game_state,
        alive_only=True
    )

    if len(alive_enemies) >= 2:
        refresh_spire_back_attack_statuses(game_state)
        return logs

    if len(alive_enemies) == 1:
        remaining_enemy = alive_enemies[0]

        had_back_attack = (
            remaining_enemy.get_status_value("back_attack") > 0
        )

        game_state.spire_facing_enemy_id = getattr(
            remaining_enemy,
            "enemy_id",
            ""
        )

        remaining_enemy.statuses.remove("back_attack")

        if had_back_attack:
            logs.append(
                "场上只剩{}，后方攻击失效。".format(
                    remaining_enemy.name
                )
            )

        return logs

    game_state.spire_facing_enemy_id = ""

    return logs