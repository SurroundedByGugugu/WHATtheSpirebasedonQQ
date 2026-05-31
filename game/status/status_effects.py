# -*- coding: utf-8 -*-

from game.constants import EVENT_DAMAGE_AFTER
from game.modifiers import get_status_value


STATUS_EVENT_PRIORITY = {
    "thorns": 50,
}


def get_status_event_priority(status_key):
    return STATUS_EVENT_PRIORITY.get(status_key, 0)


def iter_status_entities(game_state):
    """
    当前参与状态事件结算的实体。
    后续如果有召唤物、队友，也可以从这里扩展。
    """
    entities = []

    if game_state.player is not None:
        entities.append(game_state.player)

    entities.extend(game_state.enemies)

    return entities


def dispatch_status_event(game_state, event_name, context):
    """
    分发状态事件。
    """
    logs = []

    status_items = []

    for entity in iter_status_entities(game_state):
        statuses = getattr(entity, "statuses", None)

        if statuses is None:
            continue

        for status_key, value in statuses.all_active().items():
            status_items.append((
                get_status_event_priority(status_key),
                entity,
                status_key,
                value
            ))

    status_items.sort(key=lambda item: item[0], reverse=True)

    for _, owner, status_key, value in status_items:
        handler = STATUS_EVENT_HANDLERS.get(status_key)

        if handler is None:
            continue

        result = handler(
            event_name=event_name,
            context=context,
            owner=owner,
            value=value
        )

        if result:
            logs.extend(result)

    return logs


def handle_thorns(event_name, context, owner, value):
    """
    荆棘：
    owner 被攻击后，对攻击来源造成荆棘层数的伤害。

    当前规则：
    1. 只响应 attack 类型伤害
    2. 荆棘反伤不会继续触发荆棘
    3. 只要攻击伤害结算值 amount > 0，就触发荆棘
    4. 荆棘伤害可以被攻击者自己的格挡抵消
    """
    logs = []

    if event_name != EVENT_DAMAGE_AFTER:
        return logs

    if context.target is not owner:
        return logs

    if context.extra.get("damage_kind") != "attack":
        return logs

    if context.extra.get("is_reaction_damage"):
        return logs

    amount = int(context.extra.get("amount", 0))
    if amount <= 0:
        return logs

    source = context.source

    if source is None:
        return logs

    if source is owner:
        return logs

    if not source.is_alive():
        return logs

    thorns = int(value)

    if thorns <= 0:
        return logs

    logs.append("{} 的荆棘对 {} 造成 {} 点伤害。".format(
        owner.name,
        source.name,
        thorns
    ))

    old_alive = source.is_alive()
    logs.append(source.take_damage(thorns))

    if old_alive and not source.is_alive():
        if hasattr(source, "enemy_id"):
            from data.enemy.death_messages import get_enemy_death_message
            logs.append(get_enemy_death_message(source))

    return logs


STATUS_EVENT_HANDLERS = {
    "thorns": handle_thorns,
}