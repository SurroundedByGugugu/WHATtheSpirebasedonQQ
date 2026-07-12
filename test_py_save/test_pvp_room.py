# -*- coding: utf-8 -*-

from app.game_service import GameService
from data.card.AAAregistry import create_card
from game.pvp.engine import _ensure_card_uid


def _started_pvp_room():
    service = GameService()
    session_id = "cli:pvp_test"
    assert "PVP 演绎房已创建" in service.handle_message(session_id, "u1", "/card pvp new 1")
    assert "已加入 PVP 房" in service.handle_message(session_id, "u2", "/card pvp join 1")
    assert "PVP 演绎房开战" in service.handle_message(session_id, "u1", "/card pvp start")
    return service, session_id, service.pvp_service.get_room(session_id)


def test_pvp_dedicated_ctrl_configures_resources_and_plain_ctrl_is_not_intercepted():
    service = GameService()
    session_id = "cli:pvp_ctrl"

    reply = service.handle_message(session_id, "u1", "/card pvp new 1")
    assert "PVP 演绎房已创建" in reply

    room = service.pvp_service.get_room(session_id)
    before_deck_count = len(room.players[0].master_deck)

    reply = service.handle_message(session_id, "u1", "/card pvp ctrl addcard 打击 牌库")
    assert "PVP ctrl：已向" in reply
    assert len(room.players[0].master_deck) == before_deck_count + 1

    reply = service.handle_message(session_id, "u1", "/card pvp ctrl addrelic 墨水瓶")
    assert "PVP ctrl：" in reply and "获得" in reply

    reply = service.handle_message(session_id, "u1", "/ctrl addcard 打击 牌库")
    assert "当前会话还没有路线" in reply

    reply = service.handle_message(session_id, "u2", "/card pvp join 1")
    assert "已加入 PVP 房" in reply

    reply = service.handle_message(session_id, "u2", "/card pvp start")
    assert "只有房主可以开始 PVP" in reply

    reply = service.handle_message(session_id, "u1", "/card pvp start")
    assert "PVP 演绎房开战" in reply

    reply = service.handle_message(session_id, "u1", "/card pvp ctrl addcard u1 打击 手牌")
    assert "PVP ctrl：已向" in reply
    assert any(getattr(card, "name", "") == "打击" for card in room.players[0].player_state.hand)


def test_pvp_ctrl_rule_changes_affect_battle_flow():
    service = GameService()
    session_id = "cli:pvp_rules"

    assert "PVP 演绎房已创建" in service.handle_message(session_id, "u1", "/card pvp new 1")
    assert "PVP 规则 base_cost" in service.handle_message(session_id, "u1", "/card pvp ctrl rule base_cost 5")
    assert "PVP 规则 max_cards_per_turn" in service.handle_message(session_id, "u1", "/card pvp ctrl rule max_cards 2")
    assert "PVP 规则 forced_turn_bonus" in service.handle_message(session_id, "u1", "/card pvp ctrl rule forced_bonus 3")
    assert "已加入 PVP 房" in service.handle_message(session_id, "u2", "/card pvp join 1")
    assert "PVP 演绎房开战" in service.handle_message(session_id, "u1", "/card pvp start")

    room = service.pvp_service.get_room(session_id)
    active = room.players[0]
    opponent = room.players[1]
    assert active.player_state.max_cost == 5
    assert active.player_state.cost == 5

    strike = create_card("card.strike")
    active.player_state.hand[:] = [strike]
    active.player_state.cost = 5
    room.battle.cards_played_this_turn = 1

    reply = service.handle_message(session_id, "u1", "/card pvp play 0")

    assert "强制进入对方回合" in reply
    assert room.battle.active_user_id == "u2"
    assert opponent.player_state.cost == 8


def test_pvp_twelfth_card_forces_turn_and_grants_bonus_energy():
    service, session_id, room = _started_pvp_room()
    active = room.players[0]
    opponent = room.players[1]

    strike = create_card("card.strike")
    active.player_state.hand[:] = [strike]
    active.player_state.cost = 4
    room.battle.cards_played_this_turn = 11

    old_opponent_hp = opponent.player_state.hp
    reply = service.handle_message(session_id, "u1", "/card pvp play 0")

    assert "强制进入对方回合" in reply
    assert room.battle.active_user_id == "u2"
    assert room.battle.cards_played_this_turn == 0
    assert opponent.player_state.cost == 5
    assert opponent.player_state.hp < old_opponent_hp


def test_pvp_card_instance_overheats_after_four_plays_this_turn():
    service, session_id, room = _started_pvp_room()
    active = room.players[0]

    strike = create_card("card.strike")
    uid = _ensure_card_uid(strike)
    active.player_state.hand[:] = [strike]
    active.player_state.cost = 4
    room.battle.card_play_counts_this_turn[uid] = 4

    reply = service.handle_message(session_id, "u1", "/card pvp play 0")

    assert "过热" in reply
    assert strike in active.overheated_cards
    assert strike in active.player_state.exhaust_pile
