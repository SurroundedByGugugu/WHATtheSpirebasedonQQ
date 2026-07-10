# -*- coding: utf-8 -*-

from app.game_service import GameService


CTRL_PREFIXES = ("/", ".", "。")

CTRL_COMMAND_CASES = [
    {
        "command": "addcard 打击 牌库",
        "expected": "ctrl：已向牌库加入",
    },
    {
        "command": "removecard 打击 牌库",
        "setup": ["/ctrl addcard 打击 牌库"],
        "expected": "ctrl：",
    },
    {
        "command": "addrelic 墨水瓶",
        "expected": "ctrl：已获得",
    },
    {
        "command": "removerelic 墨水瓶",
        "setup": ["/ctrl addrelic 墨水瓶"],
        "expected": "ctrl：已移除",
    },
    {
        "command": "addstate 力量 1 self",
        "setup": ["/ctrl testroom battle"],
        "expected": "ctrl：",
    },
    {
        "command": "removestate 力量 self",
        "setup": ["/ctrl testroom battle", "/ctrl addstate 力量 1 self"],
        "expected": "ctrl：",
    },
    {
        "command": "addzone fire",
        "setup": ["/ctrl testroom battle"],
        "expected": "ctrl：当前 Zone 已设置",
    },
    {
        "command": "addhp 1",
        "expected": "ctrl：HP",
    },
    {
        "command": "addmaxhp 1",
        "expected": "ctrl：最大 HP",
    },
    {
        "command": "addcost 1",
        "setup": ["/ctrl testroom battle"],
        "expected": "ctrl：费用",
    },
    {
        "command": "addgold 1",
        "expected": "ctrl：金币",
    },
    {
        "command": "testroom battle",
        "expected": "进入测试房间：本地测试战斗房间",
    },
    {
        "command": "clearenemies",
        "setup": ["/ctrl testroom battle"],
        "expected": "ctrl：已清空当前房间",
    },
]


def start_debug_run():
    service = GameService()
    session_id = "cli:test_room"
    user_id = "debug_user"
    reply = service.handle_message(session_id, user_id, "/card new 0")
    assert "新的路线开始" in reply
    run_state = service.get_run(session_id)
    assert run_state is not None
    return service, session_id, user_id, run_state


def test_ctrl_prefixes_are_equivalent_for_help_without_run():
    service = GameService()

    for prefix in CTRL_PREFIXES:
        reply = service.handle_message("cli:ctrl_help", "debug_user", "{}ctrl help".format(prefix))
        assert "ctrl 控制台：" in reply
        assert "/ctrl、.ctrl、。ctrl 等价" in reply


def test_ctrl_prefixes_are_equivalent_for_all_console_commands():
    for case in CTRL_COMMAND_CASES:
        for prefix in CTRL_PREFIXES:
            service, session_id, user_id, _run_state = start_debug_run()

            for setup_command in case.get("setup", []):
                service.handle_message(session_id, user_id, setup_command)

            reply = service.handle_message(
                session_id,
                user_id,
                "{}ctrl {}".format(prefix, case["command"]),
            )

            assert case["expected"] in reply


def test_ctrl_test_room_battle_assembles_local_room():
    service, session_id, user_id, run_state = start_debug_run()
    current_node_id = run_state.current_node_id

    reply = service.handle_message(session_id, user_id, "/ctrl testroom battle")

    run_state = service.get_run(session_id)
    assert "进入测试房间：本地测试战斗房间" in reply
    assert run_state.current_node_id == current_node_id
    assert run_state.pending_test_room["room_type"] == "battle"
    assert run_state.character_id == "character.test"
    assert run_state.gold == 99
    assert [relic.relic_id for relic in run_state.relics] == [
        "relic.placeholder_stone",
        "relic.happy_flower",
        "relic.ink_bottle",
    ]
    assert [potion.potion_id for potion in run_state.potions] == [
        "potion.test_strength",
        "potion.test_fire",
        "potion.test_dexterity",
    ]
    assert [card.card_id for card in run_state.master_deck[:7]] == [
        "card.global.strike",
        "card.global.defend",
        "card.gain_status_strength",
        "card.innate_thorns",
        "card.draw_discard_test",
        "card.test_heavy_strike",
        "card.test_x_drill",
    ]
    assert [card.name for card in run_state.master_deck[7:]] == ["烈火领域", "辉晶领域"]

    battle = run_state.current_battle
    assert battle is not None
    assert battle.player.statuses.get("strength") == 2
    assert battle.player.statuses.get("dexterity") == 1
    assert battle.player.statuses.get("artifact") == 1
    assert battle.active_zone.element == "fire"
    assert len(battle.active_fields) == 1
    assert battle.active_fields[0].field_id == "field.test"
    assert [enemy.enemy_id for enemy in battle.enemies] == [
        "enemy.test_dummy",
        "enemy.cultist",
    ]
    assert battle.enemies[0].statuses.get("vulnerable") == 2
    assert battle.enemies[1].statuses.get("weak") == 1


def test_ctrl_clear_enemies_finishes_test_room_without_route_progress():
    service, session_id, user_id, run_state = start_debug_run()
    current_node_id = run_state.current_node_id
    service.handle_message(session_id, user_id, "/ctrl testroom battle")

    reply = service.handle_message(session_id, user_id, "/ctrl clearenemies")

    run_state = service.get_run(session_id)
    assert "ctrl：已清空当前房间的 2 个怪物" in reply
    assert "测试战斗胜利：本地测试战斗房间 已完成" in reply
    assert run_state.current_battle is None
    assert run_state.pending_test_room is None
    assert run_state.pending_reward is None
    assert run_state.current_node_id == current_node_id
    assert current_node_id not in run_state.completed_node_ids
    assert not run_state.run_over


def test_card_test_room_event_finishes_without_route_progress():
    service, session_id, user_id, run_state = start_debug_run()
    current_node_id = run_state.current_node_id

    reply = service.handle_message(session_id, user_id, "/card testroom event")

    run_state = service.get_run(session_id)
    assert "进入测试房间：本地测试事件房间" in reply
    assert run_state.pending_event is not None
    assert run_state.pending_test_room["room_type"] == "event"
    assert run_state.current_node_id == current_node_id

    reply = service.handle_message(session_id, user_id, "/card event 0")

    run_state = service.get_run(session_id)
    assert "测试事件完成：本地测试事件房间 已结束" in reply
    assert run_state.pending_event is None
    assert run_state.pending_test_room is None
    assert run_state.current_node_id == current_node_id
    assert current_node_id not in run_state.completed_node_ids
    assert not run_state.run_over
