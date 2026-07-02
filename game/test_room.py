# -*- coding: utf-8 -*-

import copy

from data.card.AAAregistry import create_deck
from data.character.AAAregistry import create_character
from data.fields.AAAregistry import create_field
import data.fields.test_fields  # noqa: F401 - 注册 field.test
from data.potion.AAAregistry import create_potions
from data.relic.AAAregistry import create_relics
from data.zones.element_zones import ElementZone
from game.constants import DEBUG_SEED
from game.engine import start_battle_with_player
from game.node.node_event_0 import EventChoice, EventState, format_event
from game.relic_logic.run_relic_utils import assign_new_card_master_uid
from game.run_engine import create_player_for_battle, make_node_entry_snapshot


TEST_ROOM_TYPE_ALIASES = {
    "battle": "battle",
    "fight": "battle",
    "combat": "battle",
    "战斗": "battle",
    "事件": "event",
    "event": "event",
}


TEST_ROOM_CONFIGS = {
    "battle": {
        "name": "本地测试战斗房间",
        "character_id": "character.test",
        "gold": 99,
        "deck_ids": [
            "card.strike",
            "card.defend",
            "card.gain_status_strength",
            "card.innate_thorns",
            "card.draw_discard_test",
            "card.test_heavy_strike",
            "card.test_x_drill",
            "card.fire_zone",
            "card.crystal_zone",
        ],
        "relic_ids": [
            "relic.placeholder_stone",
            "relic.happy_flower",
            "relic.ink_bottle",
        ],
        "potion_ids": [
            "potion.test_strength",
            "potion.test_fire",
            "potion.test_dexterity",
        ],
        "player_statuses": {
            "strength": 2,
            "dexterity": 1,
            "artifact": 1,
        },
        "zone": {
            "element": "fire",
            "is_extreme": False,
            "duration": 0,
        },
        "fields": [
            {
                "field_id": "field.test",
                "duration": 2,
            },
        ],
        "encounter": {
            "encounter_id": "encounter.test_room.local",
            "enemy_ids": [
                "enemy.test_dummy",
                "enemy.cultist",
            ],
            "enemy_statuses": [
                {
                    "vulnerable": 2,
                },
                {
                    "weak": 1,
                },
            ],
        },
    },
    "event": {
        "name": "本地测试事件房间",
        "character_id": "character.test",
        "gold": 99,
        "deck_ids": [
            "card.strike",
            "card.defend",
            "card.gain_status_strength",
            "card.draw_discard_test",
            "card.test_heavy_strike",
        ],
        "relic_ids": [
            "relic.placeholder_stone",
        ],
        "potion_ids": [
            "potion.test_strength",
            "potion.test_fire",
        ],
        "event": {
            "event_id": "event.test_room.local",
            "title": "本地测试事件",
            "description": "这是一间只会由测试入口创建的事件房间。它不出现在正常路线池里。",
            "choices": [
                {
                    "title": "离开。完成测试事件。",
                    "effect_type": "leave",
                },
            ],
        },
    },
}


def normalize_test_room_type(raw_room_type):
    text = str(raw_room_type or "battle").strip().lower()
    return TEST_ROOM_TYPE_ALIASES.get(text)


def get_test_room_usage():
    return "用法：/ctrl testroom battle 或 /ctrl testroom event。也可用 /card testroom battle。"


def reset_run_for_test_room(run_state, config):
    character = create_character(config.get("character_id", "character.test"))
    max_potion_slots = int(getattr(character, "max_potion_slots", 3) or 3)

    run_state.current_battle = None
    run_state.current_battle_node_type = ""
    run_state.pending_reward = None
    run_state.pending_stolen_gold_rewards = []
    run_state.pending_post_battle_effects = []
    run_state.pending_reward_injections = []
    run_state.clear_pending_nodes()

    run_state.character_id = character.character_id
    run_state.character_name = character.name
    run_state.max_hp = int(config.get("max_hp", character.max_hp))
    run_state.hp = int(config.get("hp", run_state.max_hp))
    run_state.max_cost = int(config.get("max_cost", character.max_cost))
    run_state.gold = int(config.get("gold", getattr(character, "starting_gold", 0)))
    run_state.max_potion_slots = max_potion_slots

    deck_ids = list(config.get("deck_ids", getattr(character, "starting_deck_ids", [])))
    run_state.master_deck = create_deck(deck_ids)
    for card in run_state.master_deck:
        assign_new_card_master_uid(run_state, card)

    relic_ids = list(config.get("relic_ids", getattr(character, "starting_relic_ids", [])))
    run_state.relics = create_relics(relic_ids)

    potion_ids = list(config.get("potion_ids", getattr(character, "starting_potion_ids", [])))
    run_state.potions = create_potions(potion_ids)[:max_potion_slots]

    run_state.pending_bottle_selections = []
    run_state.persistent_status_values = {}
    run_state.persistent_status_keys = []


def apply_statuses(target, statuses):
    if target is None or not statuses:
        return
    container = getattr(target, "statuses", None)
    if container is None:
        return
    for status_key, value in statuses.items():
        container.set(status_key, value)


def apply_battle_room_environment(game_state, config):
    apply_statuses(game_state.player, config.get("player_statuses", {}))

    encounter = config.get("encounter", {})
    enemy_statuses = list(encounter.get("enemy_statuses", []) or [])
    for index, statuses in enumerate(enemy_statuses):
        enemies = getattr(game_state, "enemies", []) or []
        if index >= len(enemies):
            break
        apply_statuses(enemies[index], statuses)

    zone_spec = config.get("zone")
    if zone_spec:
        game_state.active_zone = ElementZone(
            element=zone_spec.get("element", "fire"),
            is_extreme=bool(zone_spec.get("is_extreme", False)),
            duration=int(zone_spec.get("duration", 0) or 0),
        )

    active_fields = []
    for field_spec in config.get("fields", []) or []:
        active_fields.append(create_field(
            field_spec.get("field_id", "field.test"),
            duration=int(field_spec.get("duration", 1) or 1),
        ))
    game_state.active_fields = active_fields


def build_test_event_state(config):
    event_config = config.get("event", {})
    choices = []
    for choice_config in event_config.get("choices", []) or []:
        choices.append(EventChoice(
            choice_config.get("title", "离开。"),
            choice_config.get("effect_type", "leave"),
            amount=int(choice_config.get("amount", 0) or 0),
            payload=copy.deepcopy(choice_config.get("payload")),
        ))

    if not choices:
        choices.append(EventChoice("离开。", "leave"))

    return EventState(
        title=event_config.get("title", config.get("name", "本地测试事件")),
        description=event_config.get("description", ""),
        choices=choices,
        event_id=event_config.get("event_id", "event.test_room.local"),
        data=copy.deepcopy(event_config.get("data", {})),
    )


def enter_test_battle_room(run_state, config, seed=DEBUG_SEED):
    encounter = config.get("encounter", {})
    enemy_ids = list(encounter.get("enemy_ids", ["enemy.test_dummy"]))
    player = create_player_for_battle(run_state)
    game_state, battle_reply = start_battle_with_player(
        session_id=run_state.session_id,
        character_id=run_state.character_id,
        player=player,
        enemy_ids=enemy_ids,
        seed=seed,
        run_state=run_state,
    )
    game_state.run_state = run_state
    apply_battle_room_environment(game_state, config)

    run_state.current_battle = game_state
    run_state.current_battle_node_type = "test_room"
    run_state.pending_test_room = {
        "room_type": "battle",
        "name": config.get("name", "本地测试战斗房间"),
    }
    run_state.node_entry_snapshot = make_node_entry_snapshot(run_state)

    return "\n".join([
        "进入测试房间：{}。".format(config.get("name", "本地测试战斗房间")),
        "遭遇：{}".format(encounter.get("encounter_id", "encounter.test_room.local")),
        "",
        battle_reply,
        "",
        "测试房间已组装：character / relic / potion / deck / status / zone / field / encounter.enemy。",
    ])


def enter_test_event_room(run_state, config):
    run_state.pending_event = build_test_event_state(config)
    run_state.pending_test_room = {
        "room_type": "event",
        "name": config.get("name", "本地测试事件房间"),
    }
    run_state.node_entry_snapshot = make_node_entry_snapshot(run_state)

    return "\n".join([
        "进入测试房间：{}。".format(config.get("name", "本地测试事件房间")),
        "",
        format_event(run_state),
        "",
        "测试房间已组装：character / relic / potion / deck / event。",
    ])


def enter_test_room(run_state, raw_room_type="battle", seed=DEBUG_SEED):
    room_type = normalize_test_room_type(raw_room_type)
    if room_type is None:
        return get_test_room_usage()

    config = TEST_ROOM_CONFIGS[room_type]
    reset_run_for_test_room(run_state, config)

    if room_type == "battle":
        return enter_test_battle_room(run_state, config, seed=seed)
    return enter_test_event_room(run_state, config)


def is_pending_test_room(run_state, room_type=None):
    pending = getattr(run_state, "pending_test_room", None)
    if not pending:
        return False
    if room_type is None:
        return True
    return pending.get("room_type") == room_type


def finish_test_battle_room(run_state, victory, battle_end_logs=None):
    name = "测试房间"
    pending = getattr(run_state, "pending_test_room", None)
    if pending:
        name = pending.get("name", name)

    run_state.current_battle = None
    run_state.current_battle_node_type = ""
    run_state.pending_stolen_gold_rewards = []
    run_state.pending_post_battle_effects = []
    run_state.pending_reward_injections = []
    run_state.pending_test_room = None

    lines = []
    if victory:
        lines.append("测试战斗胜利：{} 已完成。".format(name))
    else:
        lines.append("测试战斗失败：{} 已结束。".format(name))

    if battle_end_logs:
        lines.append("")
        lines.extend(battle_end_logs)

    lines.append("")
    lines.append("测试房间不会推进路线，也不会生成普通战斗奖励。")
    return "\n".join(lines)


def finish_test_event_room(run_state, text):
    name = "测试房间"
    pending = getattr(run_state, "pending_test_room", None)
    if pending:
        name = pending.get("name", name)

    run_state.pending_event = None
    run_state.pending_test_room = None

    return "\n".join([
        text,
        "",
        "测试事件完成：{} 已结束。".format(name),
        "测试房间不会推进路线。",
    ])
