# -*- coding: utf-8 -*-

import copy
import re

from data.card.AAAregistry import CARD_REGISTRY, create_card
from data.card.upgrade_rules import has_upgrade, upgrade_card
from data.potion.AAAregistry import POTION_REGISTRY, create_potion
from data.relic.AAAregistry import RELIC_REGISTRY, create_relic
from data.zones.element_zones import ELEMENT_NAME_MAP, ElementZone, get_element_display_name
from game.display_names import format_card_display_name, format_potion_display_name, format_relic_display_name
from game.relic_logic.run_relic_utils import assign_new_card_master_uid
from game.status.status_defs import get_status_name, has_status_def, iter_status_defs
from game.target_lock import clear_attack_target_lock
from game.test_room import enter_test_room, get_test_room_usage
from game.zone.zone_utils import EXTREME_ZONE_DURATION


def normalize_lookup_key(value):
    text = str(value or "").strip().lower()
    return re.sub(r"[\s_\-\.·・]+", "", text)


def _register_alias(mapping, alias, value):
    key = normalize_lookup_key(alias)
    if key and key not in mapping:
        mapping[key] = value


def build_status_alias_map():
    mapping = {}
    for status_def in iter_status_defs():
        _register_alias(mapping, status_def.key, status_def.key)
        _register_alias(mapping, status_def.name, status_def.key)

    extras = {
        "str": "strength",
        "力": "strength",
        "dex": "dexterity",
        "敏": "dexterity",
        "vul": "vulnerable",
        "易损": "vulnerable",
        "regen": "regeneration",
        "再生": "regeneration",
        "无形": "intangible",
        "人工": "artifact",
        "橙色人工": "artifact",
        "火毒": "burn",
        "临时荆棘": "temporary_thorns",
        "临敏降": "temporary_dexterity_loss",
        "好下一个": "next_target_damage_taken",
        "极深渊薄雾": "abyss_mist_extreme",
    }
    for alias, status_key in extras.items():
        if has_status_def(status_key):
            _register_alias(mapping, alias, status_key)
    return mapping


STATUS_ALIAS_MAP = build_status_alias_map()


def resolve_status_key(raw_name):
    raw_text = str(raw_name or "").strip()
    if has_status_def(raw_text):
        return raw_text
    return STATUS_ALIAS_MAP.get(normalize_lookup_key(raw_text))


def build_element_alias_map():
    mapping = {}
    for element, name in ELEMENT_NAME_MAP.items():
        _register_alias(mapping, element, element)
        _register_alias(mapping, name, element)

    extras = {
        "烈火": "fire",
        "地裂": "earth",
        "风王": "wind",
        "水天": "water",
        "招雷": "thunder",
        "刻阴": "shade",
        "辉晶": "crystal",
        "深渊": "shade",
        "晶体": "crystal",
    }
    for alias, element in extras.items():
        _register_alias(mapping, alias, element)
    return mapping


ELEMENT_ALIAS_MAP = build_element_alias_map()


def resolve_zone_spec(raw_name):
    key = normalize_lookup_key(raw_name)
    key = key.replace("zone", "")
    is_extreme = False

    for prefix in ("extreme", "ext", "极"):
        if key.startswith(prefix):
            is_extreme = True
            key = key[len(prefix):]
            break

    element = ELEMENT_ALIAS_MAP.get(key)
    if element is None:
        return None, False
    return element, is_extreme


def build_card_alias_map():
    mapping = {}
    for card_id in CARD_REGISTRY.keys():
        try:
            card = create_card(card_id)
        except Exception:
            continue
        _register_alias(mapping, card_id, (card_id, False))
        _register_alias(mapping, card.name, (card_id, False))
        _register_alias(mapping, format_card_display_name(card), (card_id, False))

        if has_upgrade(card):
            upgraded = upgrade_card(card)
            _register_alias(mapping, getattr(upgraded, "name", ""), (card_id, True))
            _register_alias(mapping, format_card_display_name(upgraded), (card_id, True))

    _register_alias(mapping, "粘液", ("card.status.slime_i", False))
    _register_alias(mapping, "黏液", ("card.status.slime_i", False))
    _register_alias(mapping, "灼伤", ("card.status.burn_i", False))
    return mapping


CARD_ALIAS_MAP = build_card_alias_map()


def resolve_card_spec(raw_name):
    raw_text = str(raw_name or "").strip()
    normalized = normalize_lookup_key(raw_text)
    resolved = CARD_ALIAS_MAP.get(normalized)
    if resolved is not None:
        return resolved

    if normalized.endswith("+"):
        base_name = raw_text[:-1]
        base = CARD_ALIAS_MAP.get(normalize_lookup_key(base_name))
        if base is not None:
            return base[0], True

    return None


def create_console_card(raw_name):
    spec = resolve_card_spec(raw_name)
    if spec is None:
        return None
    card_id, upgraded = spec
    card = create_card(card_id)
    if upgraded and has_upgrade(card):
        card = upgrade_card(card)
    return card


def build_relic_alias_map():
    mapping = {}
    for relic_id in RELIC_REGISTRY.keys():
        try:
            relic = create_relic(relic_id)
        except Exception:
            continue
        _register_alias(mapping, relic_id, relic_id)
        _register_alias(mapping, relic.name, relic_id)
        _register_alias(mapping, format_relic_display_name(relic), relic_id)
    return mapping


RELIC_ALIAS_MAP = build_relic_alias_map()


def resolve_relic_id(raw_name):
    raw_text = str(raw_name or "").strip()
    if raw_text in RELIC_REGISTRY:
        return raw_text
    return RELIC_ALIAS_MAP.get(normalize_lookup_key(raw_text))


def build_potion_alias_map():
    mapping = {}
    for potion_id in POTION_REGISTRY.keys():
        try:
            potion = create_potion(potion_id)
        except Exception:
            continue
        _register_alias(mapping, potion_id, potion_id)
        if potion_id.startswith("potion."):
            _register_alias(mapping, potion_id.split(".", 1)[1], potion_id)
        _register_alias(mapping, potion.name, potion_id)
        _register_alias(mapping, format_potion_display_name(potion), potion_id)
    return mapping


POTION_ALIAS_MAP = build_potion_alias_map()


def resolve_potion_id(raw_name):
    raw_text = str(raw_name or "").strip()
    if raw_text in POTION_REGISTRY:
        return raw_text
    return POTION_ALIAS_MAP.get(normalize_lookup_key(raw_text))


def create_console_potion(raw_name):
    potion_id = resolve_potion_id(raw_name)
    if potion_id is None:
        return None
    return create_potion(potion_id)


PILE_ALIASES = {
    "手牌": "hand",
    "hand": "hand",
    "h": "hand",
    "抽牌堆": "draw_pile",
    "抽牌": "draw_pile",
    "draw": "draw_pile",
    "drawpile": "draw_pile",
    "draw_pile": "draw_pile",
    "弃牌堆": "discard_pile",
    "弃牌": "discard_pile",
    "discard": "discard_pile",
    "discardpile": "discard_pile",
    "discard_pile": "discard_pile",
    "消耗牌堆": "exhaust_pile",
    "消耗堆": "exhaust_pile",
    "消耗": "exhaust_pile",
    "exhaust": "exhaust_pile",
    "exhaustpile": "exhaust_pile",
    "exhaust_pile": "exhaust_pile",
    "牌库": "master_deck",
    "卡组": "master_deck",
    "deck": "master_deck",
    "masterdeck": "master_deck",
    "master_deck": "master_deck",
}


def resolve_pile_name(raw_name):
    return PILE_ALIASES.get(normalize_lookup_key(raw_name))


def get_pile(run_state, pile_name):
    if pile_name == "master_deck":
        return getattr(run_state, "master_deck", None)

    game_state = getattr(run_state, "current_battle", None)
    if game_state is None:
        return None
    player = getattr(game_state, "player", None)
    if player is None:
        return None
    return getattr(player, pile_name, None)


def parse_positive_int(raw_value, default=1):
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def parse_amount(raw_value):
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return None


def parse_optional_count_and_pile(args):
    if not args:
        return 1, None

    first_as_count = parse_positive_int(args[0], default=None)
    if first_as_count is not None:
        pile_name = args[1] if len(args) >= 2 else None
        return first_as_count, pile_name

    if len(args) >= 2:
        last_as_count = parse_positive_int(args[-1], default=None)
        if last_as_count is not None:
            return last_as_count, args[0]

    return 1, args[0]


def card_matches(card, raw_name):
    spec = resolve_card_spec(raw_name)
    card_id = getattr(card, "card_id", "")
    card_name = getattr(card, "name", "")
    if spec is not None:
        expected_id, expected_upgraded = spec
        if card_id != expected_id:
            return False
        if expected_upgraded:
            return bool(getattr(card, "upgraded", False)) or normalize_lookup_key(card_name).endswith("+")
        return True

    target = normalize_lookup_key(raw_name)
    return target in (
        normalize_lookup_key(card_id),
        normalize_lookup_key(card_name),
        normalize_lookup_key(format_card_display_name(card)),
    )


def relic_matches(relic, raw_name):
    relic_id = resolve_relic_id(raw_name)
    if relic_id is not None:
        return getattr(relic, "relic_id", "") == relic_id
    target = normalize_lookup_key(raw_name)
    return target in (
        normalize_lookup_key(getattr(relic, "relic_id", "")),
        normalize_lookup_key(getattr(relic, "name", "")),
        normalize_lookup_key(format_relic_display_name(relic)),
    )


def potion_matches(potion, raw_name):
    potion_id = resolve_potion_id(raw_name)
    if potion_id is not None:
        return getattr(potion, "potion_id", "") == potion_id
    target = normalize_lookup_key(raw_name)
    return target in (
        normalize_lookup_key(getattr(potion, "potion_id", "")),
        normalize_lookup_key(getattr(potion, "name", "")),
        normalize_lookup_key(format_potion_display_name(potion)),
    )


def resolve_state_target(run_state, raw_target):
    target_text = normalize_lookup_key(raw_target or "self")
    game_state = getattr(run_state, "current_battle", None)
    if game_state is None:
        return None, "当前不在战斗中，不能修改战斗状态。"

    if target_text in ("self", "player", "玩家", "我", "自己"):
        return getattr(game_state, "player", None), ""

    match = re.match(r"^(enemy|敌人|e)\[?(\d+)\]?$", target_text)
    if match:
        index = int(match.group(2))
        enemies = getattr(game_state, "enemies", []) or []
        if index < 0 or index >= len(enemies):
            return None, "敌人编号无效：{}。".format(index)
        return enemies[index], ""

    return None, "未知目标：{}。可用 self 或 enemy[0]。".format(raw_target)


def sync_run_hp_from_battle(run_state):
    game_state = getattr(run_state, "current_battle", None)
    if game_state is None or getattr(game_state, "player", None) is None:
        return
    player = game_state.player
    run_state.hp = player.hp
    run_state.max_hp = player.max_hp


def handle_debug_console(run_state, parts):
    if len(parts) < 2:
        return debug_console_help()

    command = parts[1].lower()
    args = parts[2:]

    if command in ("help", "帮助"):
        return debug_console_help()
    if command == "addcard":
        return handle_add_card(run_state, args)
    if command == "removecard":
        return handle_remove_card(run_state, args)
    if command == "addrelic":
        return handle_add_relic(run_state, args)
    if command == "removerelic":
        return handle_remove_relic(run_state, args)
    if command in ("addpotion", "addpot", "添加药水", "加药水"):
        return handle_add_potion(run_state, args)
    if command in ("removepotion", "rmpotion", "delpotion", "删除药水", "移除药水"):
        return handle_remove_potion(run_state, args)
    if command in ("setpotionslots", "setpotion_slots", "setpotionslot", "设置药水栏", "设置药水栏位"):
        return handle_set_potion_slots(run_state, args)
    if command in ("addpotionslots", "addpotion_slots", "addpotionslot", "增加药水栏", "增加药水栏位"):
        return handle_add_potion_slots(run_state, args)
    if command == "addstate":
        return handle_add_state(run_state, args)
    if command == "removestate":
        return handle_remove_state(run_state, args)
    if command == "addzone":
        return handle_add_zone(run_state, args)
    if command == "addhp":
        return handle_add_hp(run_state, args)
    if command == "addmaxhp":
        return handle_add_max_hp(run_state, args)
    if command == "addcost":
        return handle_add_cost(run_state, args)
    if command == "addgold":
        return handle_add_gold(run_state, args)
    if command == "go":
        return handle_go_floor(run_state, args)
    if command == "testroom":
        return handle_test_room(run_state, args)
    if command in ("clearenemies", "clearenemy", "clearmonsters", "clear怪", "清怪", "清空怪物"):
        return handle_clear_enemies(run_state, args)

    return "未知 ctrl 指令：{}。".format(command)


def handle_go_floor(run_state, args):
    usage = "用法：/ctrl go x floor，其中 x 可为 1、2、3、4。"
    if len(args) != 2 or str(args[1]).strip().lower() != "floor":
        return usage

    try:
        act = int(args[0])
    except (TypeError, ValueError):
        return usage

    if act not in (1, 2, 3, 4):
        return "层数必须是 1、2、3、4 之一。"

    from data.route.route_templates import (
        generate_act1_grid_route,
        generate_act2_grid_route,
        generate_act3_grid_route,
        generate_act4_linear_route,
    )
    from game.constants import DEBUG_SEED
    from game.route import build_route
    from game.run_engine import enter_current_node, prepare_visible_boss_for_route

    route_generator_by_act = {
        1: generate_act1_grid_route,
        2: generate_act2_grid_route,
        3: generate_act3_grid_route,
        4: generate_act4_linear_route,
    }

    sync_run_hp_from_battle(run_state)
    run_state.current_battle = None
    run_state.current_battle_node_type = ""
    run_state.pending_reward = None
    run_state.pending_stolen_gold_rewards = []
    run_state.pending_post_battle_effects = []
    run_state.pending_bottle_selections = []
    run_state.pending_astrolabe_selections = []
    run_state.pending_empty_cage_selections = []
    run_state.pending_orrery_selection = False
    run_state.pending_orrery_groups = []
    run_state.pending_orrery_index = 0
    run_state.pending_dollys_mirror_selection = False
    run_state.pending_reward_injections = []
    run_state.clear_pending_nodes()
    run_state.node_entry_snapshot = None
    run_state.run_over = False
    run_state.victory = False

    run_seed_value = getattr(run_state, "run_seed", None)
    run_seed = DEBUG_SEED if run_seed_value is None else int(run_seed_value)
    route_seed = run_seed if act == 1 else run_seed + act * 100000
    route_template = route_generator_by_act[act](seed=route_seed)
    run_state.route_nodes = build_route(route_template)
    run_state.completed_node_ids = [
        node_id
        for node_id in (getattr(run_state, "completed_node_ids", []) or [])
        if not str(node_id).startswith("act{}.".format(act))
    ]
    run_state.current_node_id = "act{}.floor00".format(act)
    run_state.boss_encounter_id = ""
    run_state.boss_name = ""

    prepare_visible_boss_for_route(run_state, seed=run_seed, act=act)
    entry_text = enter_current_node(run_state, seed=run_seed)
    return "\n\n".join([
        "ctrl：已跳转到第 {} 层。".format(act),
        entry_text,
    ])


def handle_test_room(run_state, args):
    if not args:
        return get_test_room_usage()
    return enter_test_room(run_state, args[0])


def handle_add_card(run_state, args):
    if len(args) < 2:
        return "用法：/ctrl addcard 卡牌名 牌堆 [数量]。例如 /ctrl addcard 打击+ 手牌。"

    card_name = args[0]
    count, raw_pile = parse_optional_count_and_pile(args[1:])
    if count is None:
        return "数量必须是正整数。"

    pile_name = resolve_pile_name(raw_pile)
    if pile_name is None:
        return "未知牌堆：{}。".format(raw_pile)

    pile = get_pile(run_state, pile_name)
    if pile is None:
        return "当前没有可修改的{}。".format(raw_pile)

    sample = create_console_card(card_name)
    if sample is None:
        return "未知卡牌：{}。".format(card_name)

    for _ in range(count):
        card = copy.deepcopy(sample)
        if pile_name == "master_deck":
            assign_new_card_master_uid(run_state, card)
        pile.append(card)

    return "ctrl：已向{}加入 {} 张【{}】。".format(raw_pile, count, getattr(sample, "name", card_name))


def handle_remove_card(run_state, args):
    if len(args) < 2:
        return "用法：/ctrl removecard 卡牌名 牌堆 [数量]。例如 /ctrl removecard 粘液 弃牌堆。"

    card_name = args[0]
    count, raw_pile = parse_optional_count_and_pile(args[1:])
    if count is None:
        return "数量必须是正整数。"

    pile_name = resolve_pile_name(raw_pile)
    if pile_name is None:
        return "未知牌堆：{}。".format(raw_pile)

    pile = get_pile(run_state, pile_name)
    if pile is None:
        return "当前没有可修改的{}。".format(raw_pile)

    removed = []
    kept = []
    remaining = count
    for card in pile:
        if remaining > 0 and card_matches(card, card_name):
            removed.append(card)
            remaining -= 1
        else:
            kept.append(card)

    pile[:] = kept
    if not removed:
        return "ctrl：{}中没有找到【{}】。".format(raw_pile, card_name)

    return "ctrl：已从{}移除 {} 张【{}】。".format(
        raw_pile,
        len(removed),
        getattr(removed[0], "name", card_name)
    )


def handle_add_relic(run_state, args):
    if not args:
        return "用法：/ctrl addrelic 遗物名。例如 /ctrl addrelic 墨水瓶。"

    relic_name = args[0]
    count = parse_positive_int(args[1], default=1) if len(args) >= 2 else 1
    if count is None:
        return "数量必须是正整数。"

    relic_id = resolve_relic_id(relic_name)
    if relic_id is None:
        return "未知遗物：{}。".format(relic_name)

    logs = []
    first_relic = None
    for _ in range(count):
        relic = create_relic(relic_id)
        if first_relic is None:
            first_relic = relic
        run_state.relics.append(relic)
        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))

    sync_battle_relics(run_state)

    lines = ["ctrl：已获得 {} 个{}。".format(count, format_relic_display_name(first_relic))]
    lines.extend(logs)
    return "\n".join(lines)


def sync_battle_relics(run_state):
    game_state = getattr(run_state, "current_battle", None)
    if game_state is None or getattr(game_state, "player", None) is None:
        return
    if game_state.player.relics is not run_state.relics:
        game_state.player.relics = run_state.relics


def get_max_potion_slots(run_state):
    try:
        max_slots = int(getattr(run_state, "max_potion_slots", 3))
    except (TypeError, ValueError):
        max_slots = 3
    return max(0, max_slots)


def sync_battle_potions(run_state):
    game_state = getattr(run_state, "current_battle", None)
    if game_state is None or getattr(game_state, "player", None) is None:
        return
    game_state.player.max_potion_slots = get_max_potion_slots(run_state)
    if game_state.player.potions is not run_state.potions:
        game_state.player.potions = run_state.potions


def trim_potions_to_slots(run_state):
    potions = getattr(run_state, "potions", None)
    if potions is None:
        run_state.potions = []
        potions = run_state.potions
    max_slots = get_max_potion_slots(run_state)
    if len(potions) <= max_slots:
        return []
    removed = potions[max_slots:]
    del potions[max_slots:]
    return removed


def handle_remove_relic(run_state, args):
    if not args:
        return "用法：/ctrl removerelic 遗物名。例如 /ctrl removerelic 开心小花。"

    relic_name = args[0]
    count = parse_positive_int(args[1], default=1) if len(args) >= 2 else 1
    if count is None:
        return "数量必须是正整数。"

    removed = []
    kept = []
    remaining = count
    for relic in getattr(run_state, "relics", []) or []:
        if remaining > 0 and relic_matches(relic, relic_name):
            removed.append(relic)
            remaining -= 1
        else:
            kept.append(relic)

    run_state.relics[:] = kept
    sync_battle_relics(run_state)

    if not removed:
        return "ctrl：没有找到遗物【{}】。".format(relic_name)

    return "ctrl：已移除 {} 个{}。".format(len(removed), format_relic_display_name(removed[0]))


def handle_add_potion(run_state, args):
    if not args:
        return "用法：/ctrl addpotion 药水名 [数量]。例如 /ctrl addpotion 攻击药水。"

    potion_name = args[0]
    count = parse_positive_int(args[1], default=1) if len(args) >= 2 else 1
    if count is None:
        return "数量必须是正整数。"

    sample = create_console_potion(potion_name)
    if sample is None:
        return "未知药水：{}。".format(potion_name)

    potions = getattr(run_state, "potions", None)
    if potions is None:
        run_state.potions = []
        potions = run_state.potions

    max_slots = get_max_potion_slots(run_state)
    empty_slots = max_slots - len(potions)
    if count > empty_slots:
        return "药水栏位不足：当前 {}/{}，还需要 {} 个空位。可先使用 /ctrl addpotionslots 数量。".format(
            len(potions),
            max_slots,
            count - empty_slots
        )

    for _ in range(count):
        potions.append(create_potion(sample.potion_id))

    sync_battle_potions(run_state)
    return "ctrl：已获得 {} 瓶{}。药水栏：{}/{}。".format(
        count,
        format_potion_display_name(sample),
        len(potions),
        max_slots
    )


def handle_remove_potion(run_state, args):
    if not args:
        return "用法：/ctrl removepotion 药水名 [数量]，或 /ctrl removepotion 药水编号。"

    potions = getattr(run_state, "potions", None)
    if potions is None:
        run_state.potions = []
        potions = run_state.potions

    raw_target = args[0]
    index = parse_amount(raw_target)
    if index is not None:
        if index < 0 or index >= len(potions):
            return "药水编号无效：{}。".format(index)
        removed = potions.pop(index)
        sync_battle_potions(run_state)
        return "ctrl：已移除药水 [{}] {}。药水栏：{}/{}。".format(
            index,
            format_potion_display_name(removed),
            len(potions),
            get_max_potion_slots(run_state)
        )

    count = parse_positive_int(args[1], default=1) if len(args) >= 2 else 1
    if count is None:
        return "数量必须是正整数。"

    removed = []
    kept = []
    remaining = count
    for potion in potions:
        if remaining > 0 and potion_matches(potion, raw_target):
            removed.append(potion)
            remaining -= 1
        else:
            kept.append(potion)

    potions[:] = kept
    sync_battle_potions(run_state)

    if not removed:
        return "ctrl：没有找到药水【{}】。".format(raw_target)

    return "ctrl：已移除 {} 瓶{}。药水栏：{}/{}。".format(
        len(removed),
        format_potion_display_name(removed[0]),
        len(potions),
        get_max_potion_slots(run_state)
    )


def format_trimmed_potion_text(removed):
    if not removed:
        return ""
    names = [
        format_potion_display_name(potion)
        for potion in removed
    ]
    return "丢弃超出栏位的药水：{}。".format("、".join(names))


def handle_set_potion_slots(run_state, args):
    if not args:
        return "用法：/ctrl setpotionslots 数量。例如 /ctrl setpotionslots 4。"

    amount = parse_amount(args[0])
    if amount is None or amount < 0:
        return "药水栏位数量必须是非负整数。"

    old_slots = get_max_potion_slots(run_state)
    run_state.max_potion_slots = amount
    removed = trim_potions_to_slots(run_state)
    sync_battle_potions(run_state)

    lines = ["ctrl：药水栏位 {} -> {}。药水栏：{}/{}。".format(
        old_slots,
        amount,
        len(getattr(run_state, "potions", []) or []),
        get_max_potion_slots(run_state)
    )]
    trimmed_text = format_trimmed_potion_text(removed)
    if trimmed_text:
        lines.append(trimmed_text)
    return "\n".join(lines)


def handle_add_potion_slots(run_state, args):
    if not args:
        return "用法：/ctrl addpotionslots 数量。例如 /ctrl addpotionslots 1。可填负数减少栏位。"

    amount = parse_amount(args[0])
    if amount is None:
        return "药水栏位变化量必须是整数。"

    old_slots = get_max_potion_slots(run_state)
    run_state.max_potion_slots = max(0, old_slots + amount)
    removed = trim_potions_to_slots(run_state)
    sync_battle_potions(run_state)

    lines = ["ctrl：药水栏位 {} -> {}。药水栏：{}/{}。".format(
        old_slots,
        get_max_potion_slots(run_state),
        len(getattr(run_state, "potions", []) or []),
        get_max_potion_slots(run_state)
    )]
    trimmed_text = format_trimmed_potion_text(removed)
    if trimmed_text:
        lines.append(trimmed_text)
    return "\n".join(lines)


def handle_add_state(run_state, args):
    if len(args) < 1:
        return "用法：/ctrl addstate 状态 [数量] [self|enemy[0]]。例如 /ctrl addstate 易伤 1 enemy[0]。"

    status_key = resolve_status_key(args[0])
    if status_key is None:
        return "未知状态：{}。".format(args[0])

    amount = 1
    raw_target = "self"
    if len(args) >= 2:
        parsed_amount = parse_amount(args[1])
        if parsed_amount is None:
            raw_target = args[1]
        else:
            amount = parsed_amount
            if len(args) >= 3:
                raw_target = args[2]

    target, error = resolve_state_target(run_state, raw_target)
    if error:
        return error

    old_value = target.statuses.get(status_key)
    new_value = target.statuses.add(status_key, amount)
    return "ctrl：{} 的{} {} -> {}。".format(
        getattr(target, "name", raw_target),
        get_status_name(status_key),
        old_value,
        new_value
    )


def handle_remove_state(run_state, args):
    if len(args) < 1:
        return "用法：/ctrl removestate 状态 [数量] [self|enemy[0]]。不写数量会清空该状态。"

    status_key = resolve_status_key(args[0])
    if status_key is None:
        return "未知状态：{}。".format(args[0])

    amount = None
    raw_target = "self"
    if len(args) >= 2:
        parsed_amount = parse_amount(args[1])
        if parsed_amount is None:
            raw_target = args[1]
        else:
            amount = parsed_amount
            if len(args) >= 3:
                raw_target = args[2]

    target, error = resolve_state_target(run_state, raw_target)
    if error:
        return error

    old_value = target.statuses.get(status_key)
    if amount is None:
        target.statuses.remove(status_key)
        new_value = 0
    else:
        new_value = target.statuses.add(status_key, -abs(amount))

    return "ctrl：{} 的{} {} -> {}。".format(
        getattr(target, "name", raw_target),
        get_status_name(status_key),
        old_value,
        new_value
    )


def handle_add_zone(run_state, args):
    if not args:
        return "用法：/ctrl addzone 元素。例如 /ctrl addzone extreme_crystal。"

    game_state = getattr(run_state, "current_battle", None)
    if game_state is None:
        return "当前不在战斗中，不能设置 Zone。"

    element, is_extreme = resolve_zone_spec(args[0])
    if element is None:
        return "未知 Zone：{}。".format(args[0])

    duration = EXTREME_ZONE_DURATION if is_extreme else 0
    game_state.active_zone = ElementZone(element=element, is_extreme=is_extreme, duration=duration)
    return "ctrl：当前 Zone 已设置为{}{}Zone。".format(
        "极" if is_extreme else "",
        get_element_display_name(element)
    )


def handle_add_hp(run_state, args):
    if not args:
        return "用法：/ctrl addhp 数量。例如 /ctrl addhp 99。"

    amount = parse_amount(args[0])
    if amount is None:
        return "HP 数量必须是整数。"

    game_state = getattr(run_state, "current_battle", None)
    if game_state is not None and getattr(game_state, "player", None) is not None:
        owner = game_state.player
    else:
        owner = run_state

    old_hp = int(getattr(owner, "hp", 0))
    max_hp = int(getattr(owner, "max_hp", old_hp))
    owner.hp = max(0, min(max_hp, old_hp + amount))

    if owner is not run_state:
        sync_run_hp_from_battle(run_state)

    return "ctrl：HP {} -> {} / {}。".format(old_hp, owner.hp, max_hp)


def handle_add_max_hp(run_state, args):
    if not args:
        return "用法：/ctrl addmaxhp 数量。例如 /ctrl addmaxhp 99。"

    amount = parse_amount(args[0])
    if amount is None:
        return "最大 HP 数量必须是整数。"

    game_state = getattr(run_state, "current_battle", None)
    if game_state is not None and getattr(game_state, "player", None) is not None:
        owner = game_state.player
    else:
        owner = run_state

    old_max = int(getattr(owner, "max_hp", 0))
    old_hp = int(getattr(owner, "hp", 0))
    owner.max_hp = max(1, old_max + amount)
    owner.hp = max(0, min(owner.max_hp, old_hp + amount))

    if owner is not run_state:
        sync_run_hp_from_battle(run_state)

    return "ctrl：最大 HP {} -> {}，HP {} -> {}。".format(
        old_max,
        owner.max_hp,
        old_hp,
        owner.hp
    )


def handle_add_gold(run_state, args):
    if not args:
        return "用法：/ctrl addgold 数量。例如 /ctrl addgold 99。"

    amount = parse_amount(args[0])
    if amount is None:
        return "金币数量必须是整数。"

    old_gold = int(getattr(run_state, "gold", 0))
    run_state.gold = max(0, old_gold + amount)
    return "ctrl：金币 {} -> {}。".format(old_gold, run_state.gold)


def handle_add_cost(run_state, args):
    if not args:
        return "用法：/ctrl addcost 数量。例如 /ctrl addcost 3。"

    amount = parse_amount(args[0])
    if amount is None:
        return "费用数量必须是整数。"

    game_state = getattr(run_state, "current_battle", None)
    if game_state is None or getattr(game_state, "player", None) is None:
        return "当前不在战斗中，不能修改费用。"

    player = game_state.player
    old_cost = int(getattr(player, "cost", 0))
    max_cost = int(getattr(player, "max_cost", 0))
    player.cost = max(0, old_cost + amount)
    return "ctrl：费用 {} -> {} / {}。".format(old_cost, player.cost, max_cost)


def handle_clear_enemies(run_state, args):
    game_state = getattr(run_state, "current_battle", None)
    if game_state is None:
        return "当前不在战斗中，不能清空怪物。"

    enemies = getattr(game_state, "enemies", None)
    if enemies is None:
        return "当前战斗没有可清空的怪物列表。"

    count = len(enemies)
    if count <= 0:
        game_state.battle_over = True
        game_state.victory = True
        return "ctrl：当前房间没有怪物，已按战斗胜利处理。"

    clear_attack_target_lock(game_state)
    enemies[:] = []
    game_state.battle_over = True
    game_state.victory = True
    return "ctrl：已清空当前房间的 {} 个怪物。".format(count)


def debug_console_help():
    return "\n".join([
        "ctrl 控制台：",
        "/ctrl、.ctrl、。ctrl 等价；下面示例的开头都可以互换。",
        "/ctrl addcard 打击+ 手牌",
        "/ctrl removecard 粘液 弃牌堆",
        "/ctrl addrelic 墨水瓶",
        "/ctrl removerelic 开心小花",
        "/ctrl addpotion 攻击药水",
        "/ctrl removepotion 0",
        "/ctrl setpotionslots 4",
        "/ctrl addpotionslots 1",
        "/ctrl addstate 易伤 1 enemy[0]",
        "/ctrl removestate 易伤 enemy[0]",
        "/ctrl addzone extreme_crystal",
        "/ctrl addhp 99",
        "/ctrl addmaxhp 99",
        "/ctrl addcost 3",
        "/ctrl addgold 99",
        "/ctrl go 4 floor",
        "/ctrl testroom battle",
        "/ctrl testroom event",
        "/ctrl clearenemies",
    ])
