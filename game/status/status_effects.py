# -*- coding: utf-8 -*-

import random
from game.constants import (
    EVENT_CARD_PLAY_AFTER,
    EVENT_DAMAGE_AFTER,
    EVENT_DAMAGE_BEFORE,
    EVENT_ENEMY_DEATH,
    EVENT_CARD_EXHAUST,
    EVENT_DRAW_CARD_AFTER,
    EVENT_GAIN_BLOCK_AFTER,
    EVENT_PLAYER_TURN_END,
    EVENT_TURN_END,
    EVENT_TURN_START,
    BLOCK_SOURCE_PLAYED_CARD,
)
from game.modifiers import get_status_value, apply_block_modifiers
from game.status.status_defs import get_status_name
from game.block import gain_block_without_modifiers
from game.pending_choice import PendingChoice, set_pending_choice

STATUS_EVENT_PRIORITY = {
    "thorns": 50,
    "temporary_thorns": 50,
    "poison_thorns": 49,
    "curl_up": 48,
    "flying": 47,
    "plated_armor": 46,
    "spore_cloud": 45,
    "god_in_hand": 40,
    "mirage_shadows": 35,
    "demon_form": 30,
    "ritual": 30,
    "combust": 29,
    "fire_breathing_history": 28,
    "dark_embrace": 27,
    "evolve": 26,
    "fire_breathing": 25,
    "feel_no_pain": 24,
    "metallicize": 23,
    "rupture": 22,
    "poison": 20,
    "burn": 19,
    "regeneration": 18,
    "confusion": 14,
    "hex": 14,
    "entangled": 13,
    "pain_stab": 12,
    "rage": 12,
    "anger": 12,
    "enrage": 12,
    "sharp_hide": 12,
    "vigor": 12,
    "malleable": 12,
    "slow": 12,
    "curious": 12,
    "time_warp": 12,
    "magma_layer": 12,
    "sedimentation": 12,
    "heavy_rock": 12,
    "rock_polishing_9": 12,
    "rock_polishing_6": 12,
    "flex": 11,
    "temporary_dexterity_loss": 10,
    "temporary_dexterity_gain": 10,
    "crystal_cocoon": 10,
    "reminiscence": 10,
    "abyssal_form": 10,
    "phantom_form": 10,
    "crystal_mist": 10,
    "abyss_mist": 10,
    "next_turn_energy": 10,
    "next_turn_block": 10,
    "temporary_strength_loss": 10,
    "abyss_mist_extreme": 10,
    "tailwind": 10,
    "flinch": 10,
    "stun": 10,
    "insatiable_abyss": 10,
    "no_draw": 9,
    "phantasmal_killer": 10,
    "phantasmal_killer_next": 10,
    "corpse_explosion": 24,
    "wraith_form": 10,
    "tools_of_the_trade": 10,
    "envenom": 24,
    "after_image": 24,
    "a_thousand_cuts": 24,
    "next_turn_draw": 10,
    "choked": 11,
    "well_laid_plans": 10,
    "noxious_fumes": 10,
    "infinite_blades": 10,
    "accuracy": 12,
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

def handle_constricted(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_PLAYER_TURN_END:
        return logs

    if owner is None or owner is not context.game_state.player or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    logs.append("{} 受到 {} 层缠绕影响。".format(owner.name, amount))

    from game.damage import deal_damage

    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=amount,
        damage_kind="status",
        card=None,
        is_reaction_damage=False,
        ignore_block=True
    ))

    return logs

def deal_effect_damage_all_enemies(context, owner, amount, status_key):
    """
    能力 / 状态造成的全体伤害。

    规则：
    - damage_kind="effect"
    - 可被格挡抵消
    - 不吃力量、虚弱、易伤
    - 不吃 Zone
    - 不触发荆棘
    """
    logs = []

    amount = int(amount)
    if amount <= 0:
        return logs

    game_state = context.game_state

    from game.damage import deal_damage

    status_name = get_status_name(status_key)

    alive_enemies = [
        enemy for enemy in game_state.enemies
        if enemy.is_alive()
    ]

    if not alive_enemies:
        logs.append("没有可攻击的敌人。")
        return logs

    for enemy in alive_enemies:
        if game_state.battle_over:
            break

        if not enemy.is_alive():
            continue

        logs.append("{} 对 {} 造成 {} 点效果伤害。".format(
            status_name,
            enemy.name,
            amount
        ))

        logs.extend(deal_damage(
            game_state=game_state,
            source=owner,
            target=enemy,
            amount=amount,
            damage_kind="effect",
            card=None,
            is_reaction_damage=False,
            ignore_block=False
        ))

    return logs

def enemy_action_contains_attack(game_state, enemy, action):
    if action is None:
        return False

    op = action.get("op", "")

    if op == "enemy_attack":
        return True

    if op == "enemy_multi_action":
        for child_action in list(action.get("actions", []) or []):
            if enemy_action_contains_attack(game_state, enemy, child_action):
                return True
        return False

    # 持盾地精这类：有队友时是格挡意图，无队友时实际攻击。
    if op == "enemy_smart_ally_block_or_attack":
        allies = [
            other for other in getattr(game_state, "enemies", []) or []
            if other is not enemy and other.is_alive()
        ]
        return not bool(allies)

    return False


def resolve_hidden_gravel_before_enemy_action(game_state, enemy, action):
    logs = []

    player = getattr(game_state, "player", None)
    if player is None or not player.is_alive():
        return logs

    if enemy is None or not enemy.is_alive():
        return logs

    amount = get_status_value(player, "hidden_gravel")
    if amount <= 0:
        return logs

    if enemy_action_contains_attack(game_state, enemy, action):
        return logs

    logs.append("{} 的隐蔽石砾刺向 {}，造成 {} 点伤害。".format(
        player.name,
        enemy.name,
        amount
    ))

    from game.damage import deal_damage

    logs.extend(deal_damage(
        game_state=game_state,
        source=player,
        target=enemy,
        amount=amount,
        damage_kind="effect",
        card=None,
        is_reaction_damage=True,
        ignore_block=False
    ))

    return logs

def draw_cards_from_status(context, owner, count, status_key):
    """
    状态触发抽牌。
    会受到 no_draw 限制。
    """
    logs = []

    count = int(count)
    if count <= 0:
        return logs

    if get_status_value(owner, "no_draw") > 0:
        logs.append("{} 受到不能抽牌影响，{} 没有抽牌。".format(
            owner.name,
            get_status_name(status_key)
        ))
        return logs

    logs.extend(owner.draw_cards(
        count,
        game_state=context.game_state,
        draw_source=status_key
    ))

    return logs


#handle
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
    from game.damage import deal_damage
    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=source,
        amount=thorns,
        damage_kind="thorns",
        card=None,
        is_reaction_damage=True,
        ignore_block=False
    ))
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
    if owner is context.game_state.player:
        from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
        logs.append("{} 的毒荆棘触发。".format(owner.name))
        logs.extend(apply_status_with_player_relics(
            game_state=context.game_state,
            source=owner,
            target=source,
            status_key="poison",
            amount=poison
        ))
        return logs

    current = source.gain_status("poison", poison)
    logs.append("{} 的毒荆棘使 {} 获得 {} 层中毒。当前中毒：{}。".format(
        owner.name,
        source.name,
        poison,
        current
    ))
    return logs

def queue_pending_curl_up(game_state, owner, block, card):
    """
    记录“本张牌结算结束后”才触发的蜷缩。
    同一张牌的多段攻击只记录一次。
    """
    pending = getattr(game_state, "pending_curl_up_targets", None)
    if pending is None:
        pending = []
        setattr(game_state, "pending_curl_up_targets", pending)

    for item in pending:
        if item.get("owner") is owner:
            return

    pending.append({
        "owner": owner,
        "block": int(block),
        "card": card,
    })

def resolve_pending_curl_up_after_card(game_state, card=None):
    """
    结算本张牌累计触发的蜷缩。
    """
    pending = list(getattr(game_state, "pending_curl_up_targets", []) or [])
    if not pending:
        return []

    logs = []
    remaining = []

    for item in pending:
        item_card = item.get("card")

        if card is not None and item_card is not card:
            remaining.append(item)
            continue

        owner = item.get("owner")
        block = int(item.get("block", 0))

        if owner is None:
            continue
        if not owner.is_alive():
            continue

        if block <= 0:
            logs.append("{} 的蜷缩消失了。".format(owner.name))
            continue

        old_block = int(getattr(owner, "block", 0))
        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=owner,
            target=owner,
            amount=block,
            block_source="curl_up",
            card=item_card,
            message="{} 的蜷缩触发，获得 {} 点格挡。蜷缩消失了。当前格挡：{}。".format(
                owner.name,
                block,
                old_block + block
            )
        ))

    setattr(game_state, "pending_curl_up_targets", remaining)
    return logs

def handle_curl_up(event_name, context, owner, value):
    """
    蜷缩：
    受到攻击伤害时触发；如果来源是玩家打出的牌，则在整张牌结算后获得格挡。
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
    if owner is None:
        return logs
    if not owner.is_alive():
        return logs

    amount = int(context.extra.get("amount", 0))
    if amount <= 0:
        return logs

    block = int(value)

    if hasattr(owner, "statuses"):
        owner.statuses.remove("curl_up")

    # 玩家打出的牌造成的攻击伤害：延迟到本张牌全部结算后触发。
    if context.card is not None and context.source is context.game_state.player:
        queue_pending_curl_up(
            game_state=context.game_state,
            owner=owner,
            block=block,
            card=context.card
        )
        return logs

    # 非卡牌来源保留即时结算，避免 pending 残留。
    if block <= 0:
        logs.append("{} 的蜷缩消失了。".format(owner.name))
        return logs

    old_block = int(getattr(owner, "block", 0))
    logs.extend(gain_block_without_modifiers(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=block,
        block_source="curl_up",
        card=context.card,
        message="{} 的蜷缩触发，获得 {} 点格挡。蜷缩消失了。当前格挡：{}。".format(
            owner.name,
            block,
            old_block + block
        )
    ))
    return logs

def _make_flying_pending_key(card=None, action_key=None):
    """
    flying 延迟结算 key。

    card:
        玩家打出的一整张牌。
    action_key:
        敌人一次复合行动 / 多段行动。
    """
    if card is not None:
        return ("card", id(card))
    if action_key is not None:
        return ("action", action_key)
    return None


def queue_pending_flying_hit(game_state, owner, card=None, action_key=None, hit_count=1):
    """
    记录飞行命中次数，并在“整张牌 / 整个敌人多段行动”结束后统一减少层数。
    """
    pending_key = _make_flying_pending_key(card=card, action_key=action_key)
    if pending_key is None:
        return False

    pending = getattr(game_state, "pending_flying_hit_targets", None)
    if pending is None:
        pending = []
        setattr(game_state, "pending_flying_hit_targets", pending)

    for item in pending:
        if item.get("owner") is owner and item.get("pending_key") == pending_key:
            item["hit_count"] = int(item.get("hit_count", 0)) + int(hit_count)
            return True

    pending.append({
        "owner": owner,
        "pending_key": pending_key,
        "card": card,
        "action_key": action_key,
        "hit_count": int(hit_count),
    })
    return True


def _apply_flying_hits(game_state, owner, hit_count, card=None):
    logs = []
    if owner is None or not owner.is_alive():
        return logs

    hit_count = int(hit_count)
    if hit_count <= 0:
        return logs

    current_flying = int(owner.statuses.get("flying"))
    if current_flying <= 0:
        return logs

    new_flying = current_flying - hit_count
    if new_flying > 0:
        owner.statuses.set("flying", new_flying)
        logs.append("{} 的飞行受到攻击影响，减少 {}，当前为 {}。".format(
            owner.name,
            hit_count,
            new_flying
        ))
        return logs

    owner.statuses.remove("flying")
    logs.append("{} 的飞行被打破。".format(owner.name))

    # 只有实现了 on_flying_broken 的实体才有坠落副作用。
    # 异鸟会眩晕；玩家没有这个方法，因此只会失去飞行。
    on_flying_broken = getattr(owner, "on_flying_broken", None)
    if on_flying_broken is not None:
        broken_logs = on_flying_broken(game_state=game_state, card=card)
        if broken_logs:
            logs.extend(broken_logs)

    return logs


def _resolve_pending_flying_by_key(game_state, pending_key):
    pending = list(getattr(game_state, "pending_flying_hit_targets", []) or [])
    if not pending:
        return []

    logs = []
    remaining = []

    for item in pending:
        if item.get("pending_key") != pending_key:
            remaining.append(item)
            continue

        logs.extend(_apply_flying_hits(
            game_state=game_state,
            owner=item.get("owner"),
            hit_count=int(item.get("hit_count", 0)),
            card=item.get("card")
        ))

    setattr(game_state, "pending_flying_hit_targets", remaining)
    return logs


def resolve_pending_flying_after_card(game_state, card=None):
    pending_key = _make_flying_pending_key(card=card)
    if pending_key is None:
        return []
    return _resolve_pending_flying_by_key(game_state, pending_key)


def resolve_pending_flying_after_action(game_state, action_key=None):
    pending_key = _make_flying_pending_key(action_key=action_key)
    if pending_key is None:
        return []
    return _resolve_pending_flying_by_key(game_state, pending_key)


def handle_flying(event_name, context, owner, value):
    logs = []

    if owner is None or not owner.is_alive():
        return logs

    if event_name != EVENT_DAMAGE_AFTER:
        return logs

    if context.target is not owner:
        return logs

    if context.extra.get("damage_kind") != "attack":
        return logs

    # 荆棘、毒荆棘、锋利外甲等反伤不影响飞行层数。
    if context.extra.get("is_reaction_damage"):
        return logs

    if context.source is owner:
        return logs

    # 建议用 real_damage 判断“是否真的受到了攻击伤害”。
    # 如果你希望被格挡完全抵消也减少飞行，就把这里改回 amount。
    real_damage = int(context.extra.get("real_damage", 0))
    if real_damage <= 0:
        return logs

    # 1. 玩家打出的牌：按整张牌延迟结算。
    if context.card is not None:
        queued = queue_pending_flying_hit(
            game_state=context.game_state,
            owner=owner,
            card=context.card,
            hit_count=1
        )
        if queued:
            return logs

    # 2. 敌人的多段 / 复合行动：按整个行动延迟结算。
    action_key = getattr(context.game_state, "_current_flying_action_key", None)
    if action_key is not None:
        queued = queue_pending_flying_hit(
            game_state=context.game_state,
            owner=owner,
            action_key=action_key,
            hit_count=1
        )
        if queued:
            return logs

    # 3. 其他单次攻击：即时结算。
    logs.extend(_apply_flying_hits(
        game_state=context.game_state,
        owner=owner,
        hit_count=1,
        card=context.card
    ))
    return logs

def handle_spore_cloud(event_name, context, owner, value):
    """
    孢子云：
    拥有者死亡时，使玩家获得等同于层数的易伤。
    当前规则：
    1. 只在伤害结算后检测。
    2. 只对敌人生效。
    3. 每个拥有者只触发一次。
    """
    logs = []
    if event_name != EVENT_DAMAGE_AFTER:
        return logs
    if context.target is not owner:
        return logs
    if owner is None:
        return logs
    if not hasattr(owner, "enemy_id"):
        return logs
    if owner.is_alive():
        return logs
    if getattr(owner, "_spore_cloud_triggered", False):
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    player = context.player
    if player is None:
        player = context.game_state.player
    if player is None or not player.is_alive():
        return logs
    owner._spore_cloud_triggered = True
    if hasattr(owner, "statuses"):
        owner.statuses.remove("spore_cloud")
    current = player.gain_status("vulnerable", amount)
    logs.append("{} 的孢子云爆开，使玩家获得 {} 层易伤。当前易伤：{}。".format(
        owner.name,
        amount,
        current
    ))
    return logs

def handle_poison(event_name, context, owner, value):
    """
    中毒：
    玩家回合结束、敌人行动前，拥有者失去等同于中毒层数的生命。
    毒伤结算后，中毒层数立刻减少 1。

    这比挂在 EVENT_TURN_END 更接近原作：
    敌人行动前先吃毒伤。
    """
    logs = []

    if event_name != EVENT_PLAYER_TURN_END:
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

    # 毒伤后立刻衰减 1 层。
    if hasattr(owner, "statuses"):
        new_poison = owner.statuses.add("poison", -1)
        logs.append("{} 的中毒减少 1，当前为 {}。".format(
            owner.name,
            new_poison
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

def handle_combust(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_PLAYER_TURN_END:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    damage = int(value)
    if damage <= 0:
        return logs

    from game.damage import deal_damage

    logs.append("{} 的自燃触发，先失去 1 点生命。".format(owner.name))
    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=1,
        damage_kind="power_hp_loss_from_card",
        card=None,
        is_reaction_damage=False,
        ignore_block=True
    ))

    if not owner.is_alive():
        return logs

    logs.extend(deal_effect_damage_all_enemies(
        context=context,
        owner=owner,
        amount=damage,
        status_key="combust"
    ))

    return logs

def handle_dark_embrace(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_CARD_EXHAUST:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if context.player is not owner:
        return logs

    draw_count = int(value)
    if draw_count <= 0:
        return logs

    logs.append("{} 的黑暗之拥触发，抽 {} 张牌。".format(
        owner.name,
        draw_count
    ))

    logs.extend(draw_cards_from_status(
        context=context,
        owner=owner,
        count=draw_count,
        status_key="dark_embrace"
    ))

    return logs

def handle_evolve(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_DRAW_CARD_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if context.player is not owner:
        return logs

    drawn_card = context.extra.get("drawn_card", context.card)
    if drawn_card is None:
        return logs

    if getattr(drawn_card, "card_type", "") != "status":
        return logs

    draw_count = int(value)
    if draw_count <= 0:
        return logs

    logs.append("{} 的进化触发，因为抽到了状态牌【{}】，抽 {} 张牌。".format(
        owner.name,
        drawn_card.name,
        draw_count
    ))

    logs.extend(draw_cards_from_status(
        context=context,
        owner=owner,
        count=draw_count,
        status_key="evolve"
    ))

    return logs

def handle_confusion(event_name, context, owner, value):
    """
    混乱：
    每当玩家抽到一张非 X 费用、非状态/诅咒牌时，
    将其本回合费用随机变为 0 到 3。
    """
    logs = []

    if event_name != EVENT_DRAW_CARD_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if owner is not context.game_state.player:
        return logs

    if int(value) <= 0:
        return logs

    drawn_card = context.extra.get("drawn_card", context.card)
    if drawn_card is None:
        return logs

    if getattr(drawn_card, "card_type", "") in ("status", "curse"):
        return logs

    if getattr(drawn_card, "cost", 0) == "X":
        return logs

    new_cost = random.randint(0, 3)
    setattr(drawn_card, "temporary_cost_override", new_cost)

    logs.append("【混乱】使抽到的【{}】费用随机变为 {}。".format(
        drawn_card.name,
        new_cost
    ))

    return logs

def handle_feel_no_pain(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_CARD_EXHAUST:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if context.player is not owner:
        return logs

    block = int(value)
    if block <= 0:
        return logs

    exhausted_card = context.card

    if exhausted_card is not None:
        message = "{} 的无惧疼痛触发，因为【{}】被消耗，获得 {} 点格挡。当前格挡：{}。".format(
            owner.name,
            exhausted_card.name,
            block,
            owner.block + block
        )
    else:
        message = "{} 的无惧疼痛触发，获得 {} 点格挡。当前格挡：{}。".format(
            owner.name,
            block,
            owner.block + block
        )
    logs.extend(gain_block_without_modifiers(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=block,
        block_source="feel_no_pain",
        card=exhausted_card,
        message=message
    ))
    return logs

def handle_fire_breathing(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_DRAW_CARD_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if context.player is not owner:
        return logs

    drawn_card = context.extra.get("drawn_card", context.card)
    if drawn_card is None:
        return logs

    card_type = getattr(drawn_card, "card_type", "")
    if card_type not in ("status", "curse"):
        return logs

    damage = int(value)
    if damage <= 0:
        return logs

    logs.append("{} 的火焰吐息触发，因为抽到了【{}】。".format(
        owner.name,
        drawn_card.name
    ))

    logs.extend(deal_effect_damage_all_enemies(
        context=context,
        owner=owner,
        amount=damage,
        status_key="fire_breathing"
    ))

    return logs

def handle_fire_breathing_history(event_name, context, owner, value):
    logs = []

    if owner is None or not owner.is_alive():
        return logs

    if event_name == EVENT_CARD_PLAY_AFTER:
        if context.player is not owner:
            return logs

        played_card = context.card
        if played_card is None:
            return logs

        if getattr(played_card, "card_type", "") != "attack":
            return logs

        current_count = int(getattr(owner, "_fire_breathing_history_attack_count", 0))
        setattr(owner, "_fire_breathing_history_attack_count", current_count + 1)

        return logs

    if event_name == EVENT_PLAYER_TURN_END:
        attack_count = int(getattr(owner, "_fire_breathing_history_attack_count", 0))
        setattr(owner, "_fire_breathing_history_attack_count", 0)

        if attack_count <= 0:
            logs.append("{} 的火焰吐息·旧没有检测到本回合打出的攻击牌。".format(
                owner.name
            ))
            return logs

        damage_per_attack = int(value)
        total_damage = attack_count * damage_per_attack

        logs.append("{} 的火焰吐息·旧触发，本回合打出了 {} 张攻击牌。".format(
            owner.name,
            attack_count
        ))

        logs.extend(deal_effect_damage_all_enemies(
            context=context,
            owner=owner,
            amount=total_damage,
            status_key="fire_breathing_history"
        ))

        return logs

    return logs

def handle_metallicize(event_name, context, owner, value):
    logs = []

    if owner is None or not owner.is_alive():
        return logs

    game_state = context.game_state

    # 玩家金属化：玩家回合结束结算。
    # 敌人金属化：整轮结束后结算，避免刚获得格挡就被敌人行动前的 clear_block 清掉。
    if owner is game_state.player:
        if event_name != EVENT_PLAYER_TURN_END:
            return logs
    else:
        if event_name != EVENT_TURN_END:
            return logs

    block = int(value)
    if block <= 0:
        return logs

    logs.extend(gain_block_without_modifiers(
        game_state=game_state,
        source=owner,
        target=owner,
        amount=block,
        block_source="metallicize",
        card=None,
        message="{} 的金属化触发，获得 {} 点格挡。当前格挡：{}。".format(
            owner.name,
            block,
            owner.block + block
        )
    ))
    return logs

def handle_enrage(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    # 激怒只给敌人用，避免以后玩家误挂 enrage 时触发奇怪逻辑。
    if owner is context.game_state.player:
        return logs

    played_card = context.card
    if played_card is None:
        return logs

    if getattr(played_card, "card_type", "") != "skill":
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    current = owner.gain_status("strength", amount)
    logs.append("{} 的激怒触发，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        amount,
        current
    ))
    return logs
def handle_rupture(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_DAMAGE_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if context.target is not owner:
        return logs

    real_damage = int(context.extra.get("real_damage", 0))
    if real_damage <= 0:
        return logs

    damage_kind = context.extra.get("damage_kind", "")

    # 这些类型视为“来自牌或能力牌效果的失去生命”。
    if damage_kind not in (
        "life_loss",
        "hp_loss",
        "card_hp_loss",
        "power_hp_loss_from_card"
    ):
        return logs

    strength = int(value)
    if strength <= 0:
        return logs

    current_strength = owner.gain_status("strength", strength)

    logs.append("{} 的撕裂触发，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        strength,
        current_strength
    ))

    return logs

def handle_sharp_hide(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs
    game_state = context.game_state
    player = game_state.player
    if owner is None or player is None:
        return logs

    # 锋利外甲是守护者效果；即使守护者刚被这张攻击牌击杀，
    # 只要状态在本次事件快照中存在，仍然会结算。
    if owner is player:
        return logs
    played_card = context.card
    if played_card is None:
        return logs
    if getattr(played_card, "card_type", "") != "attack":
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    if not player.is_alive():
        return logs
    logs.append("{} 的锋利外甲触发，因为你打出了攻击牌【{}】。".format(
        owner.name,
        played_card.name
    ))

    from game.damage import deal_damage
    logs.extend(deal_damage(
        game_state=game_state,
        source=owner,
        target=player,
        amount=amount,
        damage_kind="sharp_hide",
        card=None,
        is_reaction_damage=True,
        ignore_block=False
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
    try:
        from game.relic_logic.combat_relic_utils import apply_magic_flower_heal_amount
        heal_amount = apply_magic_flower_heal_amount(owner, amount)
    except Exception:
        heal_amount = amount
    old_hp = owner.hp
    owner.hp += heal_amount
    if owner.hp > owner.max_hp:
        owner.hp = owner.max_hp
    real_heal = owner.hp - old_hp
    flower_text = ""
    if heal_amount != amount:
        flower_text = "【魔法花】使回复量 {} -> {}。".format(amount, heal_amount)
    logs.append("{} 的再生触发，{}恢复 {} 点生命。当前 HP：{}/{}。".format(
        owner.name,
        flower_text,
        real_heal,
        owner.hp,
        owner.max_hp
    ))
    return logs

def handle_gain_strength_each_turn(event_name, context, owner, value, status_key):
    """
    通用：每个回合开始时，获得等同于状态层数的力量。
    用于：
    - 恶魔形态 demon_form
    - 仪式 ritual
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
    status_name = get_status_name(status_key)
    logs.append("{} 的{}触发，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        status_name,
        amount,
        current
    ))
    return logs

def handle_demon_form(event_name, context, owner, value):
    return handle_gain_strength_each_turn(
        event_name=event_name,
        context=context,
        owner=owner,
        value=value,
        status_key="demon_form"
    )

def handle_ritual(event_name, context, owner, value):
    # 玩家仪式仍按“恶魔形态式”的回合开始触发。
    if owner is context.game_state.player:
        return handle_gain_strength_each_turn(
            event_name=event_name,
            context=context,
            owner=owner,
            value=value,
            status_key="ritual"
        )

    # 敌方仪式按原作节奏：敌方回合结束时获得力量；
    # 刚获得仪式的同一回合跳过一次，避免第二回合攻击已经吃到力量。
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None:
        return logs
    if not owner.is_alive():
        return logs
    if getattr(owner, "_ritual_skip_turn_end_once", False):
        owner._ritual_skip_turn_end_once = False
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    current = owner.gain_status("strength", amount)
    logs.append("{} 的仪式触发，获得 {} 点力量。当前力量：{}。".format(
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
    这里把记录的基础格挡重新走一次格挡修正。
    因此延迟格挡会受到敏捷、脆弱等状态影响。
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
        final_block = apply_block_modifiers(
            value=total_block,
            game_state=context.game_state,
            source=owner,
            target=owner,
            card=None,
            block_source=BLOCK_SOURCE_PLAYED_CARD
        )
        logs.extend(gain_block_without_modifiers(
            game_state=context.game_state,
            source=owner,
            target=owner,
            amount=final_block,
            block_source="mirage_shadows",
            card=None,
            message="{} 的蜃楼复影触发，获得 {} 点格挡。当前格挡：{}。".format(
                owner.name,
                final_block,
                owner.block + final_block
            )
        ))
    setattr(owner, "_mirage_shadow_entries", new_entries)
    if hasattr(owner, "statuses"):
        if new_entries:
            owner.statuses.set("mirage_shadows", len(new_entries))
        else:
            owner.statuses.remove("mirage_shadows")
            logs.append("{} 的蜃楼复影消散了。".format(owner.name))
    return logs

def handle_next_turn_energy(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    owner.cost += amount

    if hasattr(owner, "statuses"):
        owner.statuses.remove("next_turn_energy")

    logs.append("{} 获得 {} 点下回合费用。当前费用：{}。".format(
        owner.name,
        amount,
        owner.cost
    ))

    return logs


def handle_next_turn_block(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    logs.extend(gain_block_without_modifiers(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=amount,
        block_source="next_turn_block",
        card=None,
        message="{} 的下回合格挡触发，获得 {} 点格挡。当前格挡：{}。".format(
            owner.name,
            amount,
            owner.block + amount
        )
    ))

    if hasattr(owner, "statuses"):
        owner.statuses.remove("next_turn_block")

    return logs


def handle_temporary_strength_loss(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    current = owner.gain_status("strength", amount)

    if hasattr(owner, "statuses"):
        owner.statuses.remove("temporary_strength_loss")

    logs.append("{} 的临时力量降低结束，恢复 {} 点力量。当前力量：{}。".format(
        owner.name,
        amount,
        current
    ))

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
def handle_temporary_dexterity_gain(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_TURN_END:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    current = owner.gain_status("dexterity", -amount)

    if hasattr(owner, "statuses"):
        owner.statuses.remove("temporary_dexterity_gain")

    logs.append("{} 的临时敏捷提升结束，失去 {} 点敏捷。当前敏捷：{}。".format(
        owner.name,
        amount,
        current
    ))

    return logs
def handle_flex(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_END:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    current_strength = owner.gain_status("strength", -amount)
    if hasattr(owner, "statuses"):
        owner.statuses.remove("flex")
    logs.append("{} 的活动肌肉结束，失去 {} 点力量。当前力量：{}。".format(
        owner.name,
        amount,
        current_strength
    ))
    return logs

def handle_no_draw(event_name, context, owner, value):
    logs = []

    if event_name not in (EVENT_PLAYER_TURN_END, EVENT_TURN_END):
        return logs

    if owner is None:
        return logs

    if hasattr(owner, "statuses"):
        owner.statuses.remove("no_draw")

    logs.append("{} 的不能抽牌状态消失了。".format(owner.name))
    return logs

def handle_hex(event_name, context, owner, value):
    """
    邪咒：
    每当玩家打出一张非攻击牌时，将 X 张【眩晕】随机放入抽牌堆。
    X = 邪咒层数。
    """
    logs = []

    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    game_state = context.game_state
    player = game_state.player

    if owner is not player:
        return logs

    if context.player is not owner:
        return logs

    played_card = context.card
    if played_card is None:
        return logs

    if getattr(played_card, "card_type", "") == "attack":
        return logs

    count = int(value)
    if count <= 0:
        return logs

    from data.card.AAAregistry import create_card
    import random

    added = 0
    for _ in range(count):
        dazed = create_card("card.status.dazed")
        pos = random.randint(0, len(player.draw_pile))
        player.draw_pile.insert(pos, dazed)
        added += 1

    logs.append("{} 的邪咒触发，因为打出了非攻击牌【{}】，将 {} 张【眩晕】随机放入抽牌堆。".format(
        owner.name,
        getattr(played_card, "name", "牌"),
        added
    ))

    return logs

def handle_entangled(event_name, context, owner, value):
    """
    缠身：
    本回合不能打出攻击牌。
    在玩家回合结束时移除。

    由于红色奴隶主是在敌人行动阶段给予该状态，
    所以它会持续到玩家下一个回合结束。
    """
    logs = []

    if event_name != EVENT_PLAYER_TURN_END:
        return logs

    if owner is None:
        return logs

    if owner is not context.game_state.player:
        return logs

    if hasattr(owner, "statuses"):
        owner.statuses.remove("entangled")

    logs.append("{} 的缠身状态消失了。".format(owner.name))
    return logs

def handle_rage(event_name, context, owner, value):
    logs = []

    if owner is None or not owner.is_alive():
        return logs

    if event_name == EVENT_CARD_PLAY_AFTER:
        if context.player is not owner:
            return logs

        played_card = context.card
        if played_card is None:
            return logs

        if getattr(played_card, "card_type", "") != "attack":
            return logs

        block = int(value)
        if block <= 0:
            return logs

        logs.extend(gain_block_without_modifiers(
            game_state=context.game_state,
            source=owner,
            target=owner,
            amount=block,
            block_source="rage",
            card=played_card,
            message="{} 的愤怒触发，获得 {} 点格挡。当前格挡：{}。".format(
                owner.name,
                block,
                owner.block + block
            )
        ))
        return logs

    if event_name in (EVENT_PLAYER_TURN_END, EVENT_TURN_END):
        if hasattr(owner, "statuses"):
            owner.statuses.remove("rage")
        logs.append("{} 的愤怒消失了。".format(owner.name))
        return logs

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

def handle_turn_limited_replay_status(event_name, context, owner, value, status_key):
    logs = []

    if event_name not in (EVENT_PLAYER_TURN_END, EVENT_TURN_END):
        return logs

    if owner is None:
        return logs

    if int(value) <= 0:
        return logs

    if hasattr(owner, "statuses"):
        owner.statuses.remove(status_key)

    logs.append("{} 的{}效果消失了。".format(
        owner.name,
        get_status_name(status_key)
    ))

    return logs

def handle_double_tap(event_name, context, owner, value):
    return handle_turn_limited_replay_status(
        event_name,
        context,
        owner,
        value,
        "double_tap"
    )

def handle_burst(event_name, context, owner, value):
    return handle_turn_limited_replay_status(
        event_name,
        context,
        owner,
        value,
        "burst"
    )

def handle_amplify(event_name, context, owner, value):
    return handle_turn_limited_replay_status(
        event_name,
        context,
        owner,
        value,
        "amplify"
    )

def handle_duplication_potion_next_card(event_name, context, owner, value):
    return handle_turn_limited_replay_status(
        event_name,
        context,
        owner,
        value,
        "duplication_potion_next_card"
    )

def handle_juggernaut(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_GAIN_BLOCK_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if context.target is not owner:
        return logs

    gained_block = int(context.extra.get("amount", 0))
    if gained_block <= 0:
        return logs

    damage = int(value)
    if damage <= 0:
        return logs

    alive_enemies = [
        enemy for enemy in context.game_state.enemies
        if enemy.is_alive()
    ]

    if not alive_enemies:
        return logs

    import random
    target = random.choice(alive_enemies)

    from game.damage import deal_damage

    logs.append("{} 的势不可当触发，对随机敌人 {} 造成 {} 点效果伤害。".format(
        owner.name,
        target.name,
        damage
    ))

    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=target,
        amount=damage,
        damage_kind="effect",
        card=None,
        is_reaction_damage=False,
        ignore_block=False
    ))

    return logs

def handle_berserk(event_name, context, owner, value):
    # 狂暴的费用上限提升在获得状态时一次性处理，
    # 这里不再在每个回合开始叠加 max_cost。
    return []

def handle_deva_form(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_TURN_START:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    owner.max_cost += amount
    owner.cost += amount

    logs.append("{} 的天人形态触发，本场战斗费用上限增加 {}。当前费用：{}/{}。".format(
        owner.name,
        amount,
        owner.cost,
        owner.max_cost
    ))

    return logs

def handle_brutality(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    from game.damage import deal_damage
    logs.append("{} 的残暴触发，失去 {} 点生命并抽 {} 张牌。".format(
        owner.name,
        amount,
        amount
    ))
    logs.extend(deal_damage(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=amount,
        damage_kind="power_hp_loss_from_card",
        card=None,
        is_reaction_damage=False,
        ignore_block=True
    ))
    if owner.is_alive():
        logs.extend(owner.draw_cards(
            amount,
            game_state=context.game_state,
            draw_source="brutality"
        ))
    return logs

def handle_anger(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_DAMAGE_AFTER:
        return logs
    if context.target is not owner:
        return logs
    if context.extra.get("damage_kind") != "attack":
        return logs
    if owner is None or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    current = owner.gain_status("strength", amount)
    logs.append("{} 生气了，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        amount,
        current
    ))
    return logs

def _queue_pending_malleable_trigger(game_state, owner, base_amount):
    pending = getattr(game_state, "_pending_malleable_triggers", None)
    if not isinstance(pending, list):
        pending = []
        setattr(game_state, "_pending_malleable_triggers", pending)
    pending.append({
        "owner": owner,
        "base_amount": int(base_amount),
    })


def flush_pending_malleable_triggers(game_state):
    """
    结算玩家一张牌造成的柔韧触发。

    同一张牌内的多段攻击先累计触发次数，等这张牌本次结算结束后再统一给格挡；
    因此同一张牌的后续段数不会被前一段触发的柔韧格挡抵消。
    重放/双发会在每一次牌效果结束后各自结算一次。
    """
    pending = list(getattr(game_state, "_pending_malleable_triggers", []) or [])
    setattr(game_state, "_pending_malleable_triggers", [])

    logs = []
    for item in pending:
        owner = item.get("owner")
        if owner is None or not owner.is_alive():
            continue

        base_amount = int(item.get("base_amount", 0) or 0)
        if base_amount <= 0:
            continue

        current_block = int(getattr(owner, "_malleable_current_block", base_amount))
        if current_block <= 0:
            current_block = base_amount

        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=owner,
            target=owner,
            amount=current_block,
            block_source="malleable",
            card=None,
            message="{} 的柔韧触发，获得 {} 点格挡。当前格挡：{}。".format(
                owner.name,
                current_block,
                owner.block + current_block
            )
        ))

        setattr(owner, "_malleable_current_block", current_block + 1)

    return logs


def handle_malleable(event_name, context, owner, value):
    """
    柔韧：
    受到攻击时，获得 X 点格挡。
    每触发一次，下一次获得的格挡值 +1。
    在玩家回合开始时，当前触发值重置为基础值 X。

    玩家卡牌攻击造成的多段伤害会先累计柔韧触发，
    在该牌本次效果完全结束后再给格挡。
    """
    logs = []

    if owner is None or not owner.is_alive():
        return logs

    base_amount = int(value)
    if base_amount <= 0:
        return logs

    if event_name == EVENT_TURN_START:
        old_current = int(getattr(owner, "_malleable_current_block", base_amount))
        setattr(owner, "_malleable_current_block", base_amount)

        if old_current != base_amount:
            logs.append("{} 的柔韧重置为 {}。".format(
                owner.name,
                base_amount
            ))

        return logs

    if event_name != EVENT_DAMAGE_AFTER:
        return logs

    if context.target is not owner:
        return logs

    if context.extra.get("damage_kind") != "attack":
        return logs

    if context.extra.get("is_reaction_damage"):
        return logs

    source = getattr(context, "source", None)
    if source is None or source is owner:
        return logs

    real_damage = int(context.extra.get("real_damage", 0))
    if real_damage <= 0:
        return logs

    # 玩家打出的卡牌攻击：推迟到这张牌本次结算结束后统一加格挡。
    if source is getattr(context.game_state, "player", None) and getattr(context, "card", None) is not None:
        _queue_pending_malleable_trigger(context.game_state, owner, base_amount)
        return logs

    current_block = int(getattr(owner, "_malleable_current_block", base_amount))
    if current_block <= 0:
        current_block = base_amount

    logs.extend(gain_block_without_modifiers(
        game_state=context.game_state,
        source=owner,
        target=owner,
        amount=current_block,
        block_source="malleable",
        card=None,
        message="{} 的柔韧触发，获得 {} 点格挡。当前格挡：{}。".format(
            owner.name,
            current_block,
            owner.block + current_block
        )
    ))

    setattr(owner, "_malleable_current_block", current_block + 1)

    return logs

def handle_pain_stab(event_name, context, owner, value):
    """
    疼痛戳刺：
    每当 owner 对玩家造成未被格挡的攻击伤害时，
    向玩家弃牌堆加入 X 张【伤口】。
    X = 疼痛戳刺层数。
    """
    logs = []

    if event_name != EVENT_DAMAGE_AFTER:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    game_state = context.game_state
    player = game_state.player

    if context.source is not owner:
        return logs

    if context.target is not player:
        return logs

    if context.extra.get("damage_kind") != "attack":
        return logs

    if context.extra.get("is_reaction_damage"):
        return logs

    real_damage = int(context.extra.get("real_damage", 0))
    if real_damage <= 0:
        return logs

    count = int(value)
    if count <= 0:
        return logs
    from data.card.AAAregistry import create_card

    for _ in range(count):
        player.discard_pile.append(create_card("card.status.wound"))
    logs.append("{} 的疼痛戳刺触发，向你的弃牌堆加入 {} 张【伤口】。".format(
        owner.name,
        count
    ))
    return logs

def handle_rock_layer(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_GAIN_BLOCK_AFTER:
        return logs
    if owner is None or context.target is not owner:
        return logs

    extra = getattr(context, "extra", {}) or {}
    if extra.get("block_source") != BLOCK_SOURCE_PLAYED_CARD:
        return logs
    if int(extra.get("amount", 0) or 0) <= 0:
        return logs

    layers = int(value)
    if layers <= 0:
        return logs

    if hasattr(owner, "statuses"):
        owner.statuses.remove("rock_layer")

    logs.append("{} 的岩层被本次获得格挡消耗。".format(owner.name))
    return logs



def handle_sedimentation(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_PLAYER_TURN_END:
        return logs

    if owner is None or owner is not context.game_state.player or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    from game.suzuri_rock import gain_rock_layer

    logs.append("{} 的沉积作用触发。".format(owner.name))
    logs.extend(gain_rock_layer(
        game_state=context.game_state,
        target=owner,
        amount=amount,
        source_name="沉积作用"
    ))

    return logs


def handle_magma_layer(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_DAMAGE_AFTER:
        return logs
    if owner is None or context.target is not owner:
        return logs

    extra = getattr(context, "extra", {}) or {}
    if extra.get("damage_kind") != "attack":
        return logs
    if extra.get("is_reaction_damage"):
        return logs
    if int(extra.get("amount", 0) or 0) <= 0:
        return logs

    source = context.source
    if source is None or source is owner:
        return logs
    if not getattr(source, "is_alive", lambda: True)():
        return logs

    burn_amount = int(value)
    if burn_amount <= 0:
        return logs

    if hasattr(source, "gain_status_with_result"):
        result = source.gain_status_with_result("burn", burn_amount)
        from game.status.status_gain import format_status_gain_log
        logs.append("{} 的岩浆层触发。".format(owner.name))
        logs.append(format_status_gain_log(source, "burn", burn_amount, result))
    elif hasattr(source, "gain_status"):
        current = source.gain_status("burn", burn_amount)
        logs.append("{} 的岩浆层触发，使 {} 获得 {} 层烧伤。当前烧伤：{}。".format(
            owner.name,
            source.name,
            burn_amount,
            current
        ))

    return logs

def handle_vigor(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs
    if owner is None or context.player is not owner:
        return logs
    card = context.card
    if getattr(card, "card_type", "") != "attack":
        return logs
    if hasattr(owner, "statuses"):
        owner.statuses.remove("vigor")
    logs.append("{} 的活力被【{}】消耗。".format(owner.name, getattr(card, "name", "攻击牌")))
    return logs

def handle_crystal_cocoon(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_TURN_END:
        return logs
    if owner is None or not owner.is_alive():
        return logs
    if owner is not context.game_state.player:
        return logs
    layers = int(value)
    if layers <= 0:
        return logs
    current_block = int(getattr(owner, "block", 0))
    # 晶茧下修：保留原本“回合结束后读取当前格挡并乘以层数”的结构，
    # 但先将格挡值二值化。即：有格挡视为 1，无格挡视为 0。
    block_binary = 1 if current_block > 0 else 0
    gain_amount = block_binary * layers
    if hasattr(owner, "statuses"):
        owner.statuses.remove("crystal_cocoon")
    if gain_amount <= 0:
        logs.append("{} 的晶茧裂开，但当前没有格挡可转化为力量。".format(owner.name))
        return logs
    current_strength = owner.gain_status("strength", gain_amount)
    logs.append("{} 的晶茧裂开，当前有格挡，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        gain_amount,
        current_strength
    ))

    return logs

def handle_insatiable_abyss(event_name, context, owner, value):
    logs = []

    from game.constants import EVENT_ABYSS_GAZE_CLEARED_BY_SHADE_ATTACK

    if event_name != EVENT_ABYSS_GAZE_CLEARED_BY_SHADE_ATTACK:
        return logs

    game_state = context.game_state
    player = getattr(game_state, "player", None)

    if owner is not player:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    target = getattr(context, "target", None)
    if target is None or not hasattr(target, "enemy_id"):
        return logs

    if not target.is_alive():
        return logs

    cleared = int(context.extra.get("cleared_abyss_gaze", 0) or 0)
    if cleared <= 0:
        return logs

    percent = int(value)
    if percent <= 0:
        return logs

    reapply = int(cleared * percent / 100)
    if reapply <= 0:
        logs.append("【无厌之渊】触发，但 {} 层深渊凝视按 {}% 返还后为 0。".format(
            cleared,
            percent
        ))
        return logs

    from game.relic_logic.combat_relic_utils import apply_status_with_player_relics

    logs.append("【无厌之渊】触发：{} 未死亡，返还 {}% 的深渊凝视。".format(
        target.name,
        percent
    ))

    logs.extend(apply_status_with_player_relics(
        game_state=game_state,
        source=player,
        target=target,
        status_key="abyss_gaze",
        amount=reapply
    ))

    return logs

def handle_reminiscence(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_TURN_START:
        return logs

    if owner is None or not owner.is_alive():
        return logs

    if owner is not context.game_state.player:
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    zone = getattr(context.game_state, "active_zone", None)
    if zone is None:
        return logs

    from game.zone.zone_utils import normalize_element
    zone_element = normalize_element(getattr(zone, "element", ""))

    if zone_element != "crystal":
        return logs

    logs.append("{} 的追思触发，晶 Zone 下额外抽 {} 张牌。".format(
        owner.name,
        amount
    ))

    logs.extend(draw_cards_from_status(
        context=context,
        owner=owner,
        count=amount,
        status_key="reminiscence"
    ))

    return logs

def handle_plated_armor(event_name, context, owner, value):
    logs = []

    if owner is None or not owner.is_alive():
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    # 通用多层护甲：玩家和敌人在玩家回合开始时都获得等同于层数的格挡。
    if event_name == EVENT_TURN_START:
        logs.extend(gain_block_without_modifiers(
            game_state=context.game_state,
            source=owner,
            target=owner,
            amount=amount,
            block_source="plated_armor",
            card=None,
            message="{} 的多层护甲触发，获得 {} 点格挡。当前格挡：{}。".format(
                owner.name,
                amount,
                owner.block + amount
            )
        ))
        return logs

    # 受到未被格挡的攻击伤害后，多层护甲减少 1。
    if event_name == EVENT_DAMAGE_AFTER:
        if context.target is not owner:
            return logs

        if context.extra.get("damage_kind") != "attack":
            return logs

        if int(context.extra.get("real_damage", 0)) <= 0:
            return logs

        new_value = owner.statuses.add("plated_armor", -1)

        if new_value > 0:
            logs.append("{} 的多层护甲受到攻击后减少 1 层。当前多层护甲：{}。".format(
                owner.name,
                new_value
            ))
            return logs

        logs.append("{} 的多层护甲被全部击破。".format(owner.name))

        on_broken = getattr(owner, "on_plated_armor_broken", None)
        if on_broken is not None:
            broken_logs = on_broken(game_state=context.game_state)
            if broken_logs:
                logs.extend(broken_logs)

        return logs

    return logs

def handle_magnetism(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None or owner is not context.game_state.player or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    from game.effects import handle_add_random_colorless_to_hand_temp_cost_zero
    dummy = type("MagnetismCard", (), {
        "name": "磁力",
        "card_vars": {"amount": amount},
        "owner_character_id": ""
    })()
    logs.extend(handle_add_random_colorless_to_hand_temp_cost_zero(
        context.game_state,
        dummy,
        {"amount": {"var": "amount"}},
        0,
        {}
    ))
    return logs


def handle_mayhem(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_TURN_START:
        return logs
    if owner is None or owner is not context.game_state.player or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    from game.effects import reshuffle_discard_into_draw_if_needed, play_card_from_effect_and_exhaust
    for _ in range(amount):
        if not reshuffle_discard_into_draw_if_needed(owner, logs, game_state=context.game_state):
            logs.append("【乱战】触发，但抽牌堆没有可打出的牌。")
            break
        top_card = owner.draw_pile.pop()
        logs.extend(play_card_from_effect_and_exhaust(
            game_state=context.game_state,
            source_card=type("MayhemCard", (), {"name": "乱战", "card_id": "status.mayhem"})(),
            played_card=top_card,
            reason="mayhem"
        ))
        if context.game_state.battle_over:
            break
    return logs


def append_status_damage_all_enemies( game_state, owner, amount, source_name, logs ):
    from game.damage import deal_damage
    for enemy in list(getattr(game_state, "enemies", []) or []):
        if not enemy.is_alive():
            continue
        logs.extend(deal_damage(
            game_state=game_state,
            source=owner,
            target=enemy,
            amount=amount,
            damage_kind="status",
            card=None,
            is_reaction_damage=False,
            ignore_block=False
        ))
    if amount > 0:
        logs.insert(0, "【{}】触发：对所有敌人造成 {} 点伤害。".format(source_name, amount))


def handle_omega(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_PLAYER_TURN_END:
        return logs
    if owner is None or owner is not context.game_state.player or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    append_status_damage_all_enemies(context.game_state, owner, amount, "欧米伽", logs)
    return logs


def handle_panache(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs
    if owner is None or context.player is not owner or not owner.is_alive():
        return logs
    amount = int(value)
    if amount <= 0:
        return logs
    counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
    total = sum(int(v) for v in counts.values())
    if total <= 0 or total % 5 != 0:
        return logs
    append_status_damage_all_enemies(context.game_state, owner, amount, "神气制胜", logs)
    return logs


def handle_the_bomb(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_PLAYER_TURN_END:
        return logs
    if owner is None or owner is not context.game_state.player or not owner.is_alive():
        return logs
    amount = int(value)
    turns = int(getattr(owner, "_the_bomb_turns", 0))
    if amount <= 0 or turns <= 0:
        return logs
    turns -= 1
    setattr(owner, "_the_bomb_turns", turns)
    if turns > 0:
        logs.append("【炸弹】倒计时：剩余 {} 回合。".format(turns))
        return logs
    if hasattr(owner, "statuses"):
        owner.statuses.remove("the_bomb")
    append_status_damage_all_enemies(context.game_state, owner, amount, "炸弹", logs)
    return logs

def handle_slow(event_name, context, owner, value):
    logs = []

    if event_name == EVENT_TURN_START and owner is not context.game_state.player:
        setattr(owner, "_slow_cards_played_this_turn", 0)

    return logs


def increment_slow_for_card_play(game_state, logs=None):
    """
    大脑袋的缓慢：
    每次牌结算前增加 1 层。
    重放会多次进入 apply_card_effects 的结算循环，因此自然计作多张。
    """
    if logs is None:
        logs = []

    for enemy in getattr(game_state, "enemies", []) or []:
        if not enemy.is_alive():
            continue
        if int(enemy.get_status_value("slow")) <= 0:
            continue

        current = int(getattr(enemy, "_slow_cards_played_this_turn", 0) or 0) + 1
        setattr(enemy, "_slow_cards_played_this_turn", current)

        logs.append("{} 的缓慢增加：本回合已累计 {} 层。".format(
            enemy.name,
            current
        ))

    return logs


def handle_curious(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs
    if owner is context.game_state.player:
        return logs
    if context.player is not context.game_state.player:
        return logs
    if not owner.is_alive():
        return logs

    card = context.card
    if getattr(card, "card_type", "") != "power":
        return logs

    amount = int(value)
    if amount <= 0:
        return logs

    result = owner.gain_status_with_result("strength", amount)

    from game.status.status_gain import format_status_gain_log

    logs.append("{} 的好奇触发。".format(owner.name))
    logs.append(format_status_gain_log(owner, "strength", amount, result))

    return logs


def handle_time_warp(event_name, context, owner, value):
    logs = []

    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs

    game_state = context.game_state

    if owner is game_state.player:
        return logs
    if context.player is not game_state.player:
        return logs
    if not owner.is_alive():
        return logs

    threshold = int(value) if int(value) > 0 else 12
    count = int(getattr(game_state, "time_warp_card_count", 0) or 0) + 1

    if count < threshold:
        setattr(game_state, "time_warp_card_count", count)
        logs.append("时间扭曲：{}/{}。".format(count, threshold))
        return logs

    setattr(game_state, "time_warp_card_count", 0)
    setattr(game_state, "force_end_turn_after_card", True)

    result = owner.gain_status_with_result("strength", 2)

    from game.status.status_gain import format_status_gain_log

    logs.append("{} 的时间扭曲触发：强制结束你的回合。".format(owner.name))
    logs.append(format_status_gain_log(owner, "strength", 2, result))

    return logs



# =========================
# 静默猎手状态处理
# =========================
def _add_card_to_hand_or_discard_for_status(game_state, owner, card_id, source_name, count=1, upgrade=False):
    logs=[]
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card
    for _ in range(int(count)):
        new_card=create_card(card_id)
        if upgrade:
            new_card=upgrade_card(new_card)
        setattr(new_card,"temporary",True)
        setattr(new_card,"created_in_battle",True)
        if owner.is_hand_full():
            owner.discard_pile.append(new_card)
            logs.append("手牌已满，【{}】进入弃牌堆。".format(new_card.name))
        else:
            owner.hand.append(new_card)
            logs.append("{} 将【{}】加入手牌。".format(source_name,new_card.name))
    return logs


def handle_accuracy(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_DAMAGE_BEFORE:
        return logs
    if owner is not context.game_state.player:
        return logs
    card=context.card
    if getattr(card,"card_id","") != "card.shiv":
        return logs
    if context.source is not owner:
        return logs
    if context.extra.get("damage_kind") != "attack":
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    old=int(context.extra.get("amount",0))
    context.extra["amount"]=old+amount
    logs.append("精准使小刀伤害 {} -> {}。".format(old, old+amount))
    return logs


def handle_infinite_blades(event_name, context, owner, value):
    if event_name != EVENT_TURN_START or owner is not context.game_state.player:
        return []
    return _add_card_to_hand_or_discard_for_status(context.game_state, owner, "card.shiv", "无限刀刃", int(value))


def handle_noxious_fumes(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_TURN_START or owner is not context.game_state.player:
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    from game.status.status_gain import format_status_gain_log
    for enemy in context.game_state.enemies:
        if not enemy.is_alive():
            continue
        result=enemy.gain_status_with_result("poison", amount)
        logs.append(format_status_gain_log(enemy,"poison",amount,result))
    return logs


def handle_well_laid_plans(event_name, context, owner, value):
    logs = []
    if event_name != EVENT_PLAYER_TURN_END or owner is not context.game_state.player:
        return logs

    game_state = context.game_state
    count = int(value)
    if count <= 0:
        return logs

    hand = list(getattr(owner, "hand", []) or [])
    if not hand:
        logs.append("计划妥当触发，但当前没有手牌可保留。")
        return logs

    lines = [
        "=== 计划妥当：选择至多 {} 张手牌在本回合结束时保留 ===".format(count),
        "编号使用当前手牌编号。"
    ]
    for index, hand_card in enumerate(hand):
        lines.append("[{}] {}".format(index, hand_card.summary_text()))
    lines.append("")
    lines.append("用法：/card retain 0 或 /card retain 0,1；不保留则 /card retain skip。")

    set_pending_choice(game_state, PendingChoice(
        kind="well_laid_plans",
        source="计划妥当",
        prompt="\n".join(lines),
        command_hint="retain 等效 retain_hand，选择保留，保留。",
        block_message="当前需要先处理计划妥当的保留选择。用法：/card retain 0 或 /card retain skip。",
        options=hand,
        payload={"max_count": count},
    ))

    logs.append("计划妥当触发，需要选择保留手牌。")
    logs.append("\n".join(lines))
    return logs


def handle_choked(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_CARD_PLAY_AFTER:
        return logs
    if owner is context.game_state.player:
        return logs
    if context.player is not context.game_state.player:
        return logs
    if not owner.is_alive():
        return logs
    if getattr(context.card,"card_id","") == "card.choke":
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    from game.damage import deal_damage
    logs.append("{} 的勒脖触发，失去 {} 点生命。".format(owner.name, amount))
    logs.extend(deal_damage(context.game_state, context.game_state.player, owner, amount, damage_kind="hp_loss", card=context.card, ignore_block=True))
    return logs


def handle_next_turn_draw(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_TURN_START or owner is not context.game_state.player:
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    if hasattr(owner,"statuses"):
        owner.statuses.remove("next_turn_draw")
    logs.append("{} 的下回合抽牌触发，额外抽 {} 张牌。".format(owner.name, amount))
    logs.extend(draw_cards_from_status(context, owner, amount, "next_turn_draw"))
    return logs


def handle_a_thousand_cuts(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_CARD_PLAY_AFTER or owner is not context.game_state.player:
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    from game.damage import deal_damage
    for enemy in list(context.game_state.enemies):
        if not enemy.is_alive():
            continue
        logs.append("凌迟对 {} 造成 {} 点伤害。".format(enemy.name, amount))
        logs.extend(deal_damage(context.game_state, owner, enemy, amount, damage_kind="effect", card=context.card, ignore_block=False))
    return logs


def handle_after_image(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_CARD_PLAY_AFTER or owner is not context.game_state.player:
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    logs.extend(gain_block_without_modifiers(context.game_state, owner, owner, amount, block_source="after_image", card=context.card, message="余像触发，获得 {} 点格挡。当前格挡：{}。".format(amount, owner.block+amount)))
    return logs


def handle_envenom(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_DAMAGE_AFTER or owner is not context.game_state.player:
        return logs
    if context.source is not owner:
        return logs
    if context.extra.get("damage_kind") != "attack":
        return logs
    if int(context.extra.get("real_damage",0) or 0) <= 0:
        return logs
    target=context.target
    if target is None or not hasattr(target,"enemy_id") or not target.is_alive():
        return logs
    amount=int(value)
    from game.status.status_gain import format_status_gain_log
    result=target.gain_status_with_result("poison", amount)
    logs.append(format_status_gain_log(target,"poison",amount,result))
    return logs


def handle_tools_of_the_trade(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_TURN_START or owner is not context.game_state.player:
        return logs
    logs.extend(draw_cards_from_status(context, owner, int(value), "tools_of_the_trade"))
    if len(getattr(owner,"hand",[]) or []) <= 0:
        return logs
    # 使用旧式丢弃 pending，若只有 1 张会自动丢弃。
    context.game_state.pending_discard_selection = True
    context.game_state.pending_discard_source = "必备工具"
    context.game_state.pending_discard_min_count = 1
    context.game_state.pending_discard_max_count = 1
    logs.append("必备工具：请选择 1 张手牌丢弃：/card drop 0。")
    return logs


def handle_wraith_form(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_PLAYER_TURN_END or owner is not context.game_state.player:
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    current=owner.gain_status("dexterity", -amount)
    logs.append("幽魂形态：失去 {} 点敏捷。当前敏捷：{}。".format(amount,current))
    return logs


def handle_corpse_explosion(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_ENEMY_DEATH:
        return logs
    if context.target is not owner:
        return logs
    amount=int(getattr(owner,"max_hp",0) or 0)
    if amount<=0:
        return logs
    from game.damage import deal_damage
    logs.append("{} 的尸爆术触发，对所有敌人造成 {} 点伤害。".format(owner.name, amount))
    for enemy in list(context.game_state.enemies):
        if not enemy.is_alive():
            continue
        logs.extend(deal_damage(context.game_state, owner, enemy, amount, damage_kind="effect", card=context.card, ignore_block=False))
    return logs


def handle_phantasmal_killer_next(event_name, context, owner, value):
    logs=[]
    if event_name != EVENT_TURN_START or owner is not context.game_state.player:
        return logs
    amount=int(value)
    if amount<=0:
        return logs
    owner.statuses.remove("phantasmal_killer_next")
    owner.statuses.add("phantasmal_killer", amount)
    logs.append("幻影杀手生效：本回合攻击伤害翻倍。")
    return logs


def handle_phantasmal_killer(event_name, context, owner, value):
    logs=[]
    if event_name == EVENT_DAMAGE_BEFORE and owner is context.game_state.player:
        if context.source is owner and context.extra.get("damage_kind") == "attack":
            old=int(context.extra.get("amount",0) or 0)
            context.extra["amount"]=old*2
            logs.append("幻影杀手使攻击伤害 {} -> {}。".format(old, old*2))
    return logs


def resolve_night_terror_next_turn(game_state, player):
    logs=[]
    queue=list(getattr(game_state,"night_terror_next_turn_cards",[]) or [])
    if not queue:
        return logs
    import copy
    setattr(game_state,"night_terror_next_turn_cards",[])
    for source_card in queue:
        for _ in range(3):
            copied=copy.deepcopy(source_card)
            setattr(copied,"temporary",True)
            setattr(copied,"created_in_battle",True)
            if player.is_hand_full():
                player.discard_pile.append(copied)
                logs.append("手牌已满，夜魇复制品【{}】进入弃牌堆。".format(copied.name))
            else:
                player.hand.append(copied)
                logs.append("夜魇将复制品【{}】加入手牌。".format(copied.name))
    return logs

STATUS_EVENT_HANDLERS = {
    "thorns": handle_thorns,
    "temporary_thorns": handle_temporary_thorns,
    "poison_thorns": handle_poison_thorns,
    "curl_up": handle_curl_up,
    "flying": handle_flying,
    "spore_cloud": handle_spore_cloud,
    "plated_armor": handle_plated_armor,
    "poison": handle_poison,
    "burn": handle_burn,
    "demon_form": handle_demon_form,
    "combust": handle_combust,
    "dark_embrace": handle_dark_embrace,
    "evolve": handle_evolve,
    "feel_no_pain": handle_feel_no_pain,
    "fire_breathing": handle_fire_breathing,
    "fire_breathing_history": handle_fire_breathing_history,
    "metallicize": handle_metallicize,
    "rupture": handle_rupture,
    "no_draw": handle_no_draw,
    "rage": handle_rage,
    "ritual": handle_ritual,
    "regeneration": handle_regeneration,
    "mirage_shadows": handle_mirage_shadows,
    "temporary_dexterity_loss": handle_temporary_dexterity_loss,
    "flex": handle_flex,
    "god_in_hand": handle_god_in_hand,
    "double_tap": handle_double_tap,
    "burst": handle_burst,
    "amplify": handle_amplify,
    "duplication_potion_next_card": handle_duplication_potion_next_card,
    "juggernaut": handle_juggernaut,
    "deva_form": handle_deva_form,
    "confusion": handle_confusion,
    "entangled": handle_entangled,
    "hex": handle_hex,
    "malleable": handle_malleable,
    "brutality": handle_brutality,
    "anger": handle_anger,
    "enrage": handle_enrage,
    "sharp_hide": handle_sharp_hide,
    "vigor": handle_vigor,
    "crystal_cocoon": handle_crystal_cocoon,
    "insatiable_abyss": handle_insatiable_abyss,
    "reminiscence": handle_reminiscence,
    "magnetism": handle_magnetism,
    "mayhem": handle_mayhem,
    "omega": handle_omega,
    "panache": handle_panache,
    "the_bomb": handle_the_bomb,
    "pain_stab": handle_pain_stab,
    "constricted": handle_constricted,
    "slow": handle_slow,
    "curious": handle_curious,
    "time_warp": handle_time_warp,
    "magma_layer": handle_magma_layer,
    "sedimentation": handle_sedimentation,
    "temporary_dexterity_gain": handle_temporary_dexterity_gain,
    "next_turn_energy": handle_next_turn_energy,
    "next_turn_block": handle_next_turn_block,
    "temporary_strength_loss": handle_temporary_strength_loss,
    "phantasmal_killer": handle_phantasmal_killer,
    "phantasmal_killer_next": handle_phantasmal_killer_next,
    "corpse_explosion": handle_corpse_explosion,
    "wraith_form": handle_wraith_form,
    "tools_of_the_trade": handle_tools_of_the_trade,
    "envenom": handle_envenom,
    "after_image": handle_after_image,
    "a_thousand_cuts": handle_a_thousand_cuts,
    "next_turn_draw": handle_next_turn_draw,
    "choked": handle_choked,
    "well_laid_plans": handle_well_laid_plans,
    "noxious_fumes": handle_noxious_fumes,
    "infinite_blades": handle_infinite_blades,
    "accuracy": handle_accuracy,
}
