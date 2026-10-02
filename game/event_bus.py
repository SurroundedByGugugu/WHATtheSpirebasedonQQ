# -*- coding: utf-8 -*-

from game.battle_context import BattleContext


def dispatch_event(game_state, event_name, context=None):
    """
    分发战斗事件。

    当前先接入玩家遗物。
    后续可以继续接：
    - 玩家状态
    - 敌人状态
    - Field
    - Zone
    - 敌人被动
    """

    if context is None:
        context = BattleContext(
            game_state=game_state,
            player=game_state.player,
            source=game_state.player
        )

    if context.player is None:
        context.player = game_state.player

    logs = []
    # These phases must not continue notifying listeners after battle completion.
    stop_on_finish = event_name in ("turn_start", "before_enemy_actions", "orb_channeled", "orb_passive", "orb_evoked")

    def finished():
        if not stop_on_finish:
            return False
        from game.orbs import finish_check
        return finish_check(game_state, logs)


    for relic in getattr(context.player, "relics", []):
        if finished():
            return logs + context.logs
        on_event = getattr(relic, "on_event", None)

        if on_event is None:
            continue

        result = on_event(event_name, context)

        if result:
            logs.extend(result)

    if finished():
        return logs + context.logs
    from game.defect import on_event as defect_event
    logs.extend(defect_event(game_state, event_name, context))
    if finished():
        return logs + context.logs
    from game.status.status_effects import dispatch_status_event
    logs.extend(dispatch_status_event(game_state, event_name, context))

    for enemy in list(getattr(game_state, "enemies", [])):
        if finished():
            return logs + context.logs
        on_event = getattr(enemy, "on_event", None)
        if on_event is None:
            continue
        result = on_event(event_name, context)
        if result:
            logs.extend(result)

    if finished():
        return logs + context.logs
    active_zone = getattr(game_state, "active_zone", None)
    
    if active_zone is not None:
        on_event = getattr(active_zone, "on_event", None)
        if on_event is not None:
            result = on_event(event_name, context)
            if result:
                logs.extend(result)

    for active_field in getattr(game_state, "active_fields", []):
        if finished():
            return logs + context.logs
        on_event = getattr(active_field, "on_event", None)
        if on_event is None:
            continue
        result = on_event(event_name, context)
        if result:
            logs.extend(result)

    if context.logs:
        logs.extend(context.logs)

    return logs