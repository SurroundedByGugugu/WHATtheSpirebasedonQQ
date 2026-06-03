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
    获取当前 Zone 对指定元素攻击的伤害倍率。
    无 Zone / 无属性 / 属性不匹配时返回 1.0。
    """
    attack_element = normalize_element(attack_element)
    if not attack_element:
        return 1.0
    zone = getattr(game_state, "active_zone", None)
    if zone is None:
        return 1.0
    if getattr(zone, "element", "") != attack_element:
        return 1.0
    return float(getattr(zone, "damage_multiplier", 1.0))


def apply_zone_damage_modifier(value, game_state, attack_element):
    multiplier = get_zone_damage_multiplier(game_state, attack_element)

    if multiplier == 1.0:
        return int(value)

    return int(value * multiplier)


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
            lines.append("同属性伤害倍率：×{:.2f}".format(float(getattr(zone, "damage_multiplier", 1.0))))
            lines.append("剩余：{} 回合".format(getattr(zone, "duration", 0)))
            lines.append("覆盖规则：极 Zone 持续期间不可覆盖。")
        else:
            lines.append("当前：{}".format(zone.name))
            lines.append("提示：场地上弥漫着{}元素。".format(element_name))
            lines.append("同属性伤害倍率：×{:.2f}".format(float(getattr(zone, "damage_multiplier", 1.0))))
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