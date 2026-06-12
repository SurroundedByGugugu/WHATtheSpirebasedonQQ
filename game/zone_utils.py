# -*- coding: utf-8 -*-

from game.battle_context import BattleContext
from data.zones.element_zones import ElementZone, ELEMENT_NAME_MAP, get_element_display_name


EXTREME_ZONE_DURATION = 3


def normalize_element(element):
    if element is None:
        return ""
    return str(element).strip().lower()


def is_valid_element(element):
    return element in ELEMENT_NAME_MAP


def collect_zone_deploy_modifiers(game_state, source=None, card=None, element=""):
    """
    收集展开 Zone 时的修正。

    当前支持遗物方法：
        modify_zone_deploy(context) -> dict

    返回 dict 可包含：
        force_extreme: bool
        logs: list[str]
    """
    result = {
        "force_extreme": False,
        "logs": []
    }

    player = getattr(game_state, "player", None)
    if player is None:
        return result

    context = BattleContext(
        game_state=game_state,
        player=player,
        source=source,
        card=card,
        extra={
            "element": element
        }
    )

    for relic in getattr(player, "relics", []):
        modifier = getattr(relic, "modify_zone_deploy", None)
        if modifier is None:
            continue

        relic_result = modifier(context)
        if not relic_result:
            continue

        if relic_result.get("force_extreme", False):
            result["force_extreme"] = True

        for log in relic_result.get("logs", []):
            result["logs"].append(log)

    return result


def deploy_element_zone(game_state, element, source=None, card=None, force_extreme=False):
    """
    展开属性 Zone。

    规则：
    1. 普通 Zone 持续到战斗结束或被覆盖。
    2. 已有同属性普通 Zone 时，再次展开会升级为极 Zone。
    3. 极 Zone 持续 3 回合，持续期间不可覆盖。
    4. 遗物 / 卡牌可以强制使本次展开变为极 Zone。
    """
    logs = []
    element = normalize_element(element)

    if not element:
        return ["展开 Zone 失败：缺少元素。"]

    if not is_valid_element(element):
        return ["展开 Zone 失败：未知元素 {}。".format(element)]

    current_zone = getattr(game_state, "active_zone", None)

    if current_zone is not None and getattr(current_zone, "is_extreme", False):
        if not current_zone.is_expired():
            logs.append("当前为极 Zone，持续期间不可覆盖：{}。".format(current_zone.summary_text()))
            return logs

    modifier_result = collect_zone_deploy_modifiers(
        game_state=game_state,
        source=source,
        card=card,
        element=element
    )

    force_extreme = force_extreme or modifier_result.get("force_extreme", False)
    logs.extend(modifier_result.get("logs", []))

    same_normal_zone = (
        current_zone is not None
        and not getattr(current_zone, "is_extreme", False)
        and getattr(current_zone, "element", "") == element
    )

    make_extreme = bool(force_extreme or same_normal_zone)

    if make_extreme:
        game_state.active_zone = ElementZone(
            element=element,
            is_extreme=True,
            duration=EXTREME_ZONE_DURATION
        )

        if same_normal_zone and not force_extreme:
            logs.append("再次展开同属性 Zone，Zone 升级为极 Zone。")

        logs.append(game_state.active_zone.prompt_text())
        return logs

    if current_zone is not None:
        logs.append("原有 Zone 被覆盖：{}。".format(current_zone.name))

    game_state.active_zone = ElementZone(
        element=element,
        is_extreme=False,
        duration=0
    )

    logs.append(game_state.active_zone.prompt_text())
    return logs


def get_zone_damage_multiplier(game_state, attack_element):
    """
    兼容旧接口。
    新版 Zone 不再提供通用同属性伤害倍率，具体效果由元素能力表处理。
    """
    return 1.0


def apply_zone_damage_modifier(value, game_state, attack_element):
    multiplier = get_zone_damage_multiplier(game_state, attack_element)

    if multiplier == 1.0:
        return int(value)

    return int(value * multiplier)



# =========================
# Zone ability helpers
# =========================

ZONE_REPLAY_EXTRA = {
    "crystal": (1, 2),
    "thunder": (0, 1),
}

ZONE_SHADE_MULTIPLIER = {
    "shade": (1.5, 2.0),
}

ZONE_FIRE_BURN = {
    "fire": (1, 2),
}

ZONE_EARTH_TEMP_THORNS_RATIO = {
    "earth": (0.5, 0.8),
}

ZONE_WATER_REGEN = {
    "water": (2, 3),
}

ZONE_WIND_BLOCK_EFFECT = {
    "wind": (1.3, 1.5),
}


def get_zone_value(zone, table, default=0):
    if zone is None:
        return default
    element = getattr(zone, "element", "")
    if element not in table:
        return default
    normal_value, extreme_value = table[element]
    if getattr(zone, "is_extreme", False):
        return extreme_value
    return normal_value


def has_relic(player, relic_id):
    if player is None:
        return False
    for relic in getattr(player, "relics", []):
        if getattr(relic, "relic_id", "") == relic_id:
            return True
    return False


def get_card_battle_key(card):
    # 同一场战斗内，同一张牌对象在手牌/弃牌/抽牌堆之间移动时 id 不变。
    return id(card)


def is_card_first_play_this_battle(game_state, card):
    played = getattr(game_state, "played_card_keys_this_battle", None)
    if played is None:
        played = set()
        setattr(game_state, "played_card_keys_this_battle", played)
    return get_card_battle_key(card) not in played


def mark_card_played_this_battle(game_state, card):
    played = getattr(game_state, "played_card_keys_this_battle", None)
    if played is None:
        played = set()
        setattr(game_state, "played_card_keys_this_battle", played)
    played.add(get_card_battle_key(card))


def card_has_ether_medium_override(game_state, effect_context=None):
    player = getattr(game_state, "player", None)
    if not has_relic(player, "relic.ether_medium"):
        return False
    if effect_context is None:
        return False
    return bool(effect_context.get("card_first_play_this_battle", False))


def get_active_zone(game_state):
    return getattr(game_state, "active_zone", None)


def get_card_or_effect_element(card=None, effect=None):
    if effect is not None:
        effect_element = effect.get("attack_element", None)
        if effect_element is not None:
            return normalize_element(effect_element)
    return normalize_element(getattr(card, "attack_element", ""))


def get_effective_zone_element_for_card(game_state, card=None, effect=None, effect_context=None):
    """
    返回本次卡牌/效果实际吃到的 Zone 元素。

    正常规则：卡牌/效果元素 tag 必须与当前 Zone 元素一致。
    以太介质：该场战斗中第一次打出该牌时，无视 tag，直接吃当前 Zone。
    """
    zone = get_active_zone(game_state)
    if zone is None:
        return ""

    zone_element = normalize_element(getattr(zone, "element", ""))
    if not zone_element:
        return ""

    if card_has_ether_medium_override(game_state, effect_context):
        return zone_element

    element = get_card_or_effect_element(card=card, effect=effect)
    if element == zone_element:
        return zone_element

    return ""


def is_zone_effect_active_for_card(game_state, card=None, effect=None, effect_context=None, element=""):
    zone_element = get_effective_zone_element_for_card(
        game_state=game_state,
        card=card,
        effect=effect,
        effect_context=effect_context
    )
    if not element:
        return bool(zone_element)
    return zone_element == normalize_element(element)


def get_effective_zone_element_for_enemy_action(game_state, attack_element=""):
    zone = get_active_zone(game_state)
    if zone is None:
        return ""
    zone_element = normalize_element(getattr(zone, "element", ""))
    action_element = normalize_element(attack_element)
    if zone_element and action_element == zone_element:
        return zone_element
    return ""


def apply_zone_amount_modifier(value, game_state, zone_element):
    zone = get_active_zone(game_state)
    zone_element = normalize_element(zone_element)
    if zone is None or zone_element != "shade":
        return int(value)
    multiplier = get_zone_value(zone, ZONE_SHADE_MULTIPLIER, 1.0)
    return int(int(value) * float(multiplier))


def get_zone_replay_extra(game_state, zone_element):
    zone = get_active_zone(game_state)
    zone_element = normalize_element(zone_element)
    # 必须以调用方传入的“已判定可吃 Zone 的元素”为准。
    # 如果 zone_element 为空或不等于当前 Zone 元素，说明本次效果没有吃到 Zone。
    if zone is None or not zone_element:
        return 0
    current_zone_element = normalize_element(getattr(zone, "element", ""))
    if zone_element != current_zone_element:
        return 0
    if zone_element not in ZONE_REPLAY_EXTRA:
        return 0
    return int(get_zone_value(zone, ZONE_REPLAY_EXTRA, 0))


def get_zone_burn_amount(game_state, zone_element):
    zone = get_active_zone(game_state)
    zone_element = normalize_element(zone_element)
    if zone is None or zone_element != "fire":
        return 0
    return int(get_zone_value(zone, ZONE_FIRE_BURN, 0))


def get_zone_temp_thorns_amount(game_state, zone_element, block_amount):
    zone = get_active_zone(game_state)
    zone_element = normalize_element(zone_element)
    if zone is None or zone_element != "earth":
        return 0
    ratio = float(get_zone_value(zone, ZONE_EARTH_TEMP_THORNS_RATIO, 0.0))
    return int(int(block_amount) * ratio)


def get_zone_regeneration_amount(game_state, zone_element):
    zone = get_active_zone(game_state)
    zone_element = normalize_element(zone_element)
    if zone is None or zone_element != "water":
        return 0
    return int(get_zone_value(zone, ZONE_WATER_REGEN, 0))


def get_zone_wind_block_effect_multiplier(game_state, zone_element):
    zone = get_active_zone(game_state)
    zone_element = normalize_element(zone_element)
    if zone is None or zone_element != "wind":
        return 1.0
    return float(get_zone_value(zone, ZONE_WIND_BLOCK_EFFECT, 1.0))


def should_zone_thunder_make_all(game_state, zone_element):
    return normalize_element(zone_element) == "thunder" and get_active_zone(game_state) is not None


def apply_zone_source_hp_loss_if_needed(game_state, source, zone_element, logs, label="Zone"):
    zone_element = normalize_element(zone_element)
    if zone_element != "shade":
        return
    if source is None or not source.is_alive():
        return
    amount = int(source.hp * 0.05)
    if amount <= 0:
        amount = 1
    logs.append("{} 受到{}反噬，失去当前生命 5%（{} 点）。".format(
        source.name,
        label,
        amount
    ))
    from game.damage import deal_damage
    logs.extend(deal_damage(
        game_state=game_state,
        source=source,
        target=source,
        amount=amount,
        damage_kind="hp_loss",
        card=None,
        ignore_block=True
    ))


def add_status_to_target(target, status_key, amount):
    if hasattr(target, "gain_status_with_result"):
        result = target.gain_status_with_result(status_key, amount)
        from game.status.status_gain import format_status_gain_log
        return format_status_gain_log(target, status_key, amount, result)
    current = target.gain_status(status_key, amount)
    from game.status.status_defs import get_status_name
    status_name = get_status_name(status_key)
    return "{} 获得 {} 点{}。当前{}：{}。".format(
        target.name,
        amount,
        status_name,
        status_name,
        current
    )


def apply_fire_zone_burn(game_state, source, target, card, zone_element, logs):
    if getattr(card, "card_type", "") != "attack":
        return
    burn = get_zone_burn_amount(game_state, zone_element)
    if burn <= 0 or target is None or not target.is_alive():
        return
    logs.append(add_status_to_target(target, "burn", burn))


def apply_earth_zone_temp_thorns(game_state, target, zone_element, block_amount, logs):
    thorns = get_zone_temp_thorns_amount(game_state, zone_element, block_amount)
    if thorns <= 0 or target is None or not target.is_alive():
        return
    logs.append(add_status_to_target(target, "temporary_thorns", thorns))


def apply_water_zone_regeneration_on_card_play(game_state, card, effect_context, logs):
    zone_element = get_effective_zone_element_for_card(
        game_state=game_state,
        card=card,
        effect=None,
        effect_context=effect_context
    )
    regen = get_zone_regeneration_amount(game_state, zone_element)
    if regen <= 0:
        return
    player = getattr(game_state, "player", None)
    if player is None or not player.is_alive():
        return
    logs.append(add_status_to_target(player, "regeneration", regen))

def tick_zone_turn_end(game_state):
    logs = []
    zone = getattr(game_state, "active_zone", None)

    if zone is None:
        return logs

    tick = getattr(zone, "tick_turn_end", None)
    if tick is None:
        return logs

    if not getattr(zone, "is_extreme", False):
        return logs

    zone.tick_turn_end()

    if zone.is_expired():
        logs.append("{} 消散了。".format(zone.name))
        game_state.active_zone = None
    else:
        logs.append("{} 剩余 {} 回合。".format(zone.name, zone.duration))

    return logs


def tick_fields_turn_end(game_state):
    logs = []
    fields = getattr(game_state, "active_fields", [])

    if not fields:
        return logs

    remaining_fields = []

    for field in fields:
        tick = getattr(field, "tick_turn_end", None)
        if tick is not None:
            field.tick_turn_end()

        is_expired = getattr(field, "is_expired", None)
        if is_expired is not None and field.is_expired():
            logs.append("{} 消散了。".format(field.name))
        else:
            remaining_fields.append(field)

    game_state.active_fields = remaining_fields
    return logs


def format_zone_field_detail(game_state):
    lines = []
    lines.append("=== Zone / Field ===")

    zone = getattr(game_state, "active_zone", None)

    lines.append("Zone：")
    if zone is None:
        lines.append("当前没有 Zone。")
    else:
        element = getattr(zone, "element", "")
        element_name = get_element_display_name(element) if element else "无属性"

        if getattr(zone, "is_extreme", False):
            lines.append("当前：{}".format(zone.name))
            lines.append("提示：场地上充满了{}元素。".format(element_name))
            lines.append("能力：{}".format(getattr(zone, "ability_text", "暂未定义")))
            lines.append("剩余：{} 回合".format(getattr(zone, "duration", 0)))
            lines.append("覆盖规则：极 Zone 持续期间不可覆盖。")
        else:
            lines.append("当前：{}".format(zone.name))
            lines.append("提示：场地上弥漫着{}元素。".format(element_name))
            lines.append("能力：{}".format(getattr(zone, "ability_text", "暂未定义")))
            lines.append("覆盖规则：持续到战斗结束或被覆盖；再次展开同属性 Zone 会升级为极 Zone。")

    lines.append("")
    lines.append("Field：")

    fields = getattr(game_state, "active_fields", [])

    if not fields:
        lines.append("当前没有 Field。")
    else:
        for index, field in enumerate(fields):
            summary = field.summary_text() if hasattr(field, "summary_text") else str(field)
            lines.append("[{}] {}".format(index, summary))

    return "\n".join(lines)