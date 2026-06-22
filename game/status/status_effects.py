# -*- coding: utf-8 -*-

from game.constants import (
    EVENT_CARD_PLAY_AFTER,
    EVENT_DAMAGE_AFTER,
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

STATUS_EVENT_PRIORITY = {
    "thorns": 50,
    "temporary_thorns": 50,
    "poison_thorns": 49,
    "curl_up": 48,
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
    "entangled": 13,
    "rage": 12,
    "anger": 12,
    "enrage": 12,
    "sharp_hide": 12,
    "flex": 11,
    "temporary_dexterity_loss": 10,
    "crystal_cocoon": 10,
    "abyssal_form": 10,
    "phantom_form": 10,
    "no_draw": 9,
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

def deal_status_damage_all_enemies(context, owner, amount, status_key):
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

    logs.extend(deal_status_damage_all_enemies(
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

    logs.extend(deal_status_damage_all_enemies(
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

        logs.extend(deal_status_damage_all_enemies(
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

    logs.append("{} 的狂暴触发，本场战斗费用上限增加 {}。当前费用：{}/{}。".format(
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
    gain_amount = current_block * layers
    if hasattr(owner, "statuses"):
        owner.statuses.remove("crystal_cocoon")
    if gain_amount <= 0:
        logs.append("{} 的晶茧裂开，但当前没有格挡可转化为力量。".format(owner.name))
        return logs
    current_strength = owner.gain_status("strength", gain_amount)
    logs.append("{} 的晶茧裂开，获得 {} 点力量。当前力量：{}。".format(
        owner.name,
        gain_amount,
        current_strength
    ))

    return logs

STATUS_EVENT_HANDLERS = {
    "thorns": handle_thorns,
    "temporary_thorns": handle_temporary_thorns,
    "poison_thorns": handle_poison_thorns,
    "curl_up": handle_curl_up,
    "spore_cloud": handle_spore_cloud,
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
    "berserk": handle_berserk,
    "entangled": handle_entangled,
    "brutality": handle_brutality,
    "anger": handle_anger,
    "enrage": handle_enrage,
    "sharp_hide": handle_sharp_hide,
    "crystal_cocoon": handle_crystal_cocoon,
}