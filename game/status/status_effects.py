# -*- coding: utf-8 -*-

from game.constants import EVENT_DAMAGE_AFTER, EVENT_TURN_END, EVENT_TURN_START
from game.modifiers import get_status_value

STATUS_EVENT_PRIORITY = {
    "thorns": 50,
    "temporary_thorns": 50,
    "poison_thorns": 49,
    "god_in_hand": 40,
    "mirage_shadows": 35,
    "poison": 20,
    "burn": 19,
    "regeneration": 18,
    "temporary_dexterity_loss": 10,
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


def handle_temporary_thorns(event_name, context, owner, value):
    if event_name == EVENT_DAMAGE_AFTER:
        return handle_thorns(event_name, context, owner, value)

    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None:
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    if hasattr(owner, "statuses"):
        owner.statuses.remove("temporary_thorns")
    logs.append("{} 的临时荆棘消失了。".format(owner.name))
    return logs

def handle_poison_thorns(event_name, context, owner, value):
    """
    毒荆棘：
    owner 被攻击后，使攻击来源获得中毒。

    当前规则与荆棘保持一致：
    1. 只响应 attack 类型伤害
    2. 反应伤害不会继续触发毒荆棘
    3. 只要攻击伤害结算值 amount > 0，就触发毒荆棘
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

    poison = int(value)

    if poison <= 0:
        return logs

    current = source.gain_status("poison", poison)

    logs.append("{} 的毒荆棘使 {} 获得 {} 层中毒。当前中毒：{}。".format(
        owner.name,
        source.name,
        poison,
        current
    ))

    return logs

def handle_poison(event_name, context, owner, value):
    """
    中毒：
    回合结束时，拥有者失去等同于中毒层数的生命。

    当前规则：
    1. 在 EVENT_TURN_END 触发。
    2. 无视格挡。
    3. 先造成伤害，再由 engine.py 统一处理 turn_end 状态衰减。
    """
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None:
        return logs
    if not owner.is_alive():
        return logs
    poison = int(value)
    if poison <= 0:
        return logs
    logs.append("{} 受到 {} 层中毒影响。".format(
        owner.name,
        poison
    ))
    from game.damage import deal_damage
    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=poison,
        damage_kind="poison",
        card=None,
        is_reaction_damage=False,
        ignore_block=True
    ))
    return logs


def handle_burn(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    hp_loss = int(owner.hp / 8)
    if hp_loss <= 0:
        hp_loss = 1
    logs.append("{} 受到 {} 层烧伤影响，失去当前生命 1/8（{} 点）。".format(
        owner.name,
        amount,
        hp_loss
    ))
    from game.damage import deal_damage
    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=hp_loss,
        damage_kind="burn",
        card=None,
        is_reaction_damage=False,
        ignore_block=True
    ))
    return logs


def handle_regeneration(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    old_hp = owner.hp
    owner.hp += amount
    if owner.hp > owner.max_hp:
        owner.hp = owner.max_hp
    real_heal = owner.hp - old_hp
    logs.append("{} 的再生触发，恢复 {} 点生命。当前 HP：{}/{}。".format(
        owner.name,
        real_heal,
        owner.hp,
        owner.max_hp
    ))
    return logs

def handle_demon_form(event_name, context, owner, value):
    """
    恶魔形态：
    每个玩家回合开始时，拥有者获得等同于层数的力量。
    """
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None:
        return logs
    if not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    current = owner.gain_status("strength", amount)
    logs.append("{} 的恶魔形态触发，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        amount,
        current
    ))

    return logs

def handle_mirage_shadows(event_name, context, owner, value):
    """
    蜃楼复影：
    每个玩家回合开始时，根据记录的延迟格挡条目获得格挡。
    注意：
    这里直接修改 owner.block，不走 gain_block / modifier_profile="block"。
    所以该格挡不受敏捷、脆弱等格挡修正影响。
    """
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None:
        return logs
    if not owner.is_alive():
        return logs
    entries = getattr(owner, "_mirage_shadow_entries", None)
    if not entries:
        if hasattr(owner, "statuses"):
            owner.statuses.remove("mirage_shadows")
        return logs
    total_block = 0
    new_entries = []
    for entry in entries:
        remaining = int(entry.get("remaining", 0))
        block_amount = int(entry.get("block", 0))
        if remaining <= 0 or block_amount <= 0:
            continue
        total_block += block_amount
        remaining -= 1
        if remaining > 0:
            new_entries.append({
                "remaining": remaining,
                "block": block_amount
            })
    if total_block > 0:
        owner.block += total_block
        logs.append("{} 的蜃楼复影触发，获得 {} 点格挡。当前格挡：{}。".format(
            owner.name,
            total_block,
            owner.block
        ))
    setattr(owner, "_mirage_shadow_entries", new_entries)
    if hasattr(owner, "statuses"):
        if new_entries:
            owner.statuses.set("mirage_shadows", len(new_entries))
        else:
            owner.statuses.remove("mirage_shadows")
            logs.append("{} 的蜃楼复影消散了。".format(owner.name))
    return logs

def handle_temporary_dexterity_loss(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    current = owner.gain_status("dexterity", amount)
    if hasattr(owner, "statuses"):
        owner.statuses.remove("temporary_dexterity_loss")
    logs.append("{} 的临时敏捷降低结束，恢复 {} 点敏捷。当前敏捷：{}。".format(
        owner.name,
        amount,
        current
    ))
    return logs

def handle_god_in_hand(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    entries = getattr(owner, "_god_in_hand_entries", None)
    if not entries:
        if hasattr(owner, "statuses"):
            owner.statuses.remove("god_in_hand")
        return logs
    new_entries = []
    for entry in entries:
        remaining = int(entry.get("remaining", 0))
        hp_loss = int(entry.get("hp_loss", 0))
        energy_loss = int(entry.get("energy_loss", 0))
        final_hp_loss = int(entry.get("final_hp_loss", 0))
        if remaining > 0:
            if hp_loss > 0:
                from game.damage import deal_damage
                logs.append("{} 受到手中上帝影响，失去 {} 点生命。".format(
                    owner.name,
                    hp_loss
                ))
                logs.extend(deal_damage(
                    game_state=context.game_state,
                    source=owner,
                    target=owner,
                    amount=hp_loss,
                    damage_kind="hp_loss",
                    card=None,
                    is_reaction_damage=False,
                    ignore_block=True
                ))
            if energy_loss > 0:
                old_cost = owner.cost
                owner.cost -= energy_loss
                if owner.cost < 0:
                    owner.cost = 0
                logs.append("{} 受到手中上帝影响，失去 {} 点能量。当前能量：{}。".format(
                    owner.name,
                    old_cost - owner.cost,
                    owner.cost
                ))
            remaining -= 1
            if remaining <= 0:
                if final_hp_loss > 0 and owner.is_alive():
                    from game.damage import deal_damage
                    logs.append("{} 的手中上帝进入最终结算，失去 {} 点生命。".format(
                        owner.name,
                        final_hp_loss
                    ))
                    logs.extend(deal_damage(
                        game_state=context.game_state,
                        source=owner,
                        target=owner,
                        amount=final_hp_loss,
                        damage_kind="hp_loss",
                        card=None,
                        is_reaction_damage=False,
                        ignore_block=True
                    ))
                logs.append("{} 的手中上帝不再使其失去能量。".format(owner.name))
                continue
            new_entries.append({
                "remaining": remaining,
                "hp_loss": hp_loss,
                "energy_loss": energy_loss,
                "final_hp_loss": final_hp_loss,
            })
    setattr(owner, "_god_in_hand_entries", new_entries)
    if hasattr(owner, "statuses"):
        if new_entries:
            owner.statuses.set("god_in_hand", len(new_entries))
        else:
            owner.statuses.remove("god_in_hand")
    return logs

STATUS_EVENT_HANDLERS = {
    "thorns": handle_thorns,
    "temporary_thorns": handle_temporary_thorns,
    "poison_thorns": handle_poison_thorns,
    "poison": handle_poison,
    "burn": handle_burn,
    "regeneration": handle_regeneration,
    "mirage_shadows": handle_mirage_shadows,
    "temporary_dexterity_loss": handle_temporary_dexterity_loss,
    "god_in_hand": handle_god_in_hand,
}