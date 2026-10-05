from game.resolution import resumable
# -*- coding: utf-8 -*-

from game.battle_context import BattleContext


def notify_enemy_removed(game_state, enemy, reason):
    from game.constants import EVENT_ENEMY_REMOVED
    return dispatch_event(game_state, EVENT_ENEMY_REMOVED, BattleContext(
        game_state=game_state, player=game_state.player, target=enemy,
        extra={"reason": reason},
    ))


@resumable(text=False)
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
            yield logs
            logs = []

    if finished():
        return logs + context.logs
    from game.watcher import on_event as watcher_event
    logs.extend(watcher_event(game_state, event_name, context))
    yield logs
    logs = []
    if finished():
        return logs + context.logs
    from game.defect import on_event as defect_event
    logs.extend(defect_event(game_state, event_name, context))
    yield logs
    logs = []
    if finished():
        return logs + context.logs
    from game.status.status_effects import dispatch_status_event
    logs.extend(dispatch_status_event(game_state, event_name, context))
    yield logs
    logs = []

    for enemy in list(getattr(game_state, "enemies", [])):
        if finished():
            return logs + context.logs
        on_event = getattr(enemy, "on_event", None)
        if on_event is None:
            continue
        result = on_event(event_name, context)
        if result:
            logs.extend(result)
            yield logs
            logs = []

    if finished():
        return logs + context.logs
    active_zone = getattr(game_state, "active_zone", None)
    
    if active_zone is not None:
        on_event = getattr(active_zone, "on_event", None)
        if on_event is not None:
            result = on_event(event_name, context)
            if result:
                logs.extend(result)
                yield logs
                logs = []

    for active_field in getattr(game_state, "active_fields", []):
        if finished():
            return logs + context.logs
        on_event = getattr(active_field, "on_event", None)
        if on_event is None:
            continue
        result = on_event(event_name, context)
        if result:
            logs.extend(result)
            yield logs
            logs = []

    if context.logs:
        logs.extend(context.logs)
        yield logs
        logs = []

    return logs
