# -*- coding: utf-8 -*-

from app.game_service import GameService
from game.multiplayer.engine import _check_battle_result


def test_multiplayer_room_start_and_relic_conflict_resolution():
    service = GameService()
    session_id = "cli:multi_test"

    reply = service.handle_message(session_id, "u1", "/card multi new 1")
    assert "多人测试房已创建" in reply

    reply = service.handle_message(session_id, "u2", "/card multi join 1")
    assert "已加入多人测试房" in reply

    reply = service.handle_message(session_id, "u1", "/card multi start")
    assert "多人测试房间开战" in reply

    room = service.multiplayer_service.get_room(session_id)
    assert room is not None
    assert room.battle is not None
    assert len(room.players) == 2
    assert room.battle.enemies

    for enemy in room.battle.enemies:
        # The first multiplayer room is about state flow, not damage math.
        enemy.hp = 0

    reward_text = _check_battle_result(room)
    assert "进入多人奖励选择" in reward_text
    assert room.reward is not None
    assert len(room.reward.relic_options) == len(room.players)

    reply = service.handle_message(session_id, "u1", "/card multi relic 0")
    assert "等待其他玩家决定" in reply

    reply = service.handle_message(session_id, "u2", "/card multi relic 0")
    assert "多人遗物选择结算" in reply
    assert room.reward.resolved
    winners = [
        slot
        for slot in room.players
        if any(relic is room.reward.relic_options[0] for relic in slot.relics)
    ]
    assert len(winners) == 1


def test_multiplayer_room_host_start_and_player_limit():
    service = GameService()
    session_id = "cli:multi_limit"

    reply = service.handle_message(session_id, "u1", "/card multi new 0")
    assert "多人测试房已创建" in reply

    reply = service.handle_message(session_id, "u1", "/card multi join 1")
    assert "已更新你的多人测试房角色" in reply
    room = service.multiplayer_service.get_room(session_id)
    assert len(room.players) == 1
    assert room.players[0].character_id == "character.armored_warrior"

    for index in range(2, 7):
        reply = service.handle_message(session_id, "u{}".format(index), "/card multi join 0")
        assert "已加入多人测试房" in reply

    reply = service.handle_message(session_id, "u7", "/card multi join 0")
    assert "人数已满" in reply
    assert len(room.players) == 6

    reply = service.handle_message(session_id, "u2", "/card multi start")
    assert "只有房主可以开始" in reply

    reply = service.handle_message(session_id, "u1", "/card multi start")
    assert "多人测试房间开战" in reply

    reply = service.handle_message(session_id, "u7", "/card multi join 0")
    assert "已经开战" in reply
