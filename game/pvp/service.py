# -*- coding: utf-8 -*-

import random

from game.pvp.ctrl import PvpCtrlConsole
from game.pvp.engine import (
    create_player_slot,
    end_turn,
    finish_battle,
    format_room,
    play_card,
    start_pvp_battle,
)
from game.pvp.state import PVP_STATUS_LOBBY, PvpRoomState


CHARACTER_CHOICES = [
    ("0", "character.test", "测试角色"),
    ("1", "character.armored_warrior", "铁甲战士"),
    ("2", "character.silent_huntress", "静默猎手"),
    ("3", "character.lumine", "昼·里辛塔法"),
    ("4", "character.yoirine", "Yoirine"),
    ("5", "character.suzuri", "Suzuri"),
]

MAX_PVP_PLAYERS = 2


class PvpRoomService(object):
    """Command facade for the standalone PVP room."""

    def __init__(self):
        self.rooms = {}
        self.ctrl_console = PvpCtrlConsole()

    def get_room(self, session_id):
        return self.rooms.get(session_id)

    def clear_room(self, session_id):
        if session_id in self.rooms:
            del self.rooms[session_id]

    def resolve_character_id(self, parts, default="character.test"):
        if len(parts) < 4:
            return default
        raw = str(parts[3]).strip().lower()
        for index, character_id, _name in CHARACTER_CHOICES:
            if raw == index or raw == character_id.lower():
                return character_id
        return None

    def _next_side(self, room):
        used = {slot.side for slot in room.players}
        for side in ("A", "B"):
            if side not in used:
                return side
        return "B"

    def character_choices_text(self):
        lines = ["PVP 可选角色："]
        for index, character_id, name in CHARACTER_CHOICES:
            lines.append("[{}] {} ({})".format(index, name, character_id))
        return "\n".join(lines)

    def help_text(self):
        return "\n".join([
            "PVP 演绎房命令：",
            "/card pvp new [角色编号]      创建 PVP 房并加入 A 侧",
            "/card pvp join [角色编号]     加入/换角色（开战前）",
            "/card pvp start              房主开始 1v1 PVP",
            "/card pvp view               查看房间",
            "/card pvp play 手牌编号 [目标玩家编号]",
            "/card pvp end                结束当前行动者回合",
            "/card pvp finish             任意参战者结束战斗，胜负自定",
            "/card pvp ctrl ...           PVP 专用控制台，开战前后都可用",
            "/card pvp close              房主关闭房间",
            "普通 /ctrl 不再接入 PVP；PVP 调度请使用 /card pvp ctrl。",
        ])

    def handle_message(self, session_id, user_id, parts):
        if len(parts) < 3:
            room = self.get_room(session_id)
            if room is None:
                return self.help_text()
            return format_room(room, viewer_user_id=user_id)

        action = parts[2].lower()

        if action in ("help", "帮助"):
            return self.help_text()
        if action in ("chars", "characters", "character", "角色", "角色选择"):
            return self.character_choices_text()
        if action == "new":
            return self.handle_new(session_id, user_id, parts)
        if action in ("join", "加入"):
            return self.handle_join(session_id, user_id, parts)
        if action in ("view", "status", "查看", "房间"):
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有 PVP 房。使用 /card pvp new [角色编号] 创建。"
            return format_room(room, viewer_user_id=user_id)
        if action in ("start", "开始"):
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有 PVP 房。使用 /card pvp new [角色编号] 创建。"
            if str(room.host_user_id) != str(user_id):
                return "只有房主可以开始 PVP。"
            return start_pvp_battle(room)
        if action == "play":
            return self.handle_play(session_id, user_id, parts)
        if action == "end":
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有 PVP 房。"
            return end_turn(room, user_id)
        if action in ("finish", "stop", "结束战斗", "终止"):
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有 PVP 房。"
            return finish_battle(room, user_id)
        if action in ("ctrl", "console", "控制台"):
            room = self.get_room(session_id)
            return self.ctrl_console.handle(room, user_id, parts)
        if action in ("close", "关闭", "clear"):
            return self.handle_close(session_id, user_id)

        return "未知 PVP 命令：{}。\n{}".format(action, self.help_text())

    def handle_new(self, session_id, user_id, parts):
        current = self.get_room(session_id)
        if current is not None:
            return "当前会话已有 PVP 房。\n{}".format(format_room(current, viewer_user_id=user_id))

        character_id = self.resolve_character_id(parts)
        if character_id is None:
            return "角色编号无效。\n{}".format(self.character_choices_text())

        room = PvpRoomState(
            session_id=session_id,
            host_user_id=str(user_id),
            seed=random.randint(1, 999999999),
        )
        room.players.append(create_player_slot(user_id, character_id, "A"))
        self.rooms[session_id] = room
        return "\n".join([
            "PVP 演绎房已创建，房主加入 A 侧。",
            "",
            format_room(room, viewer_user_id=user_id),
        ])

    def handle_join(self, session_id, user_id, parts):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话还没有 PVP 房。使用 /card pvp new [角色编号] 创建。"
        if room.status != PVP_STATUS_LOBBY:
            return "当前 PVP 已开始，不能加入或换角色。"

        character_id = self.resolve_character_id(parts)
        if character_id is None:
            return "角色编号无效。\n{}".format(self.character_choices_text())

        existing = room.get_player(user_id)
        if existing is not None:
            index = room.players.index(existing)
            room.players[index] = create_player_slot(user_id, character_id, existing.side)
            return "\n".join(["已更新你的 PVP 角色。", "", format_room(room, viewer_user_id=user_id)])

        if len(room.players) >= MAX_PVP_PLAYERS:
            return "当前 PVP 房人数已满（第一版上限 {} 人）。".format(MAX_PVP_PLAYERS)

        room.players.append(create_player_slot(user_id, character_id, self._next_side(room)))
        return "\n".join(["已加入 PVP 房。", "", format_room(room, viewer_user_id=user_id)])

    def handle_play(self, session_id, user_id, parts):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话还没有 PVP 房。"
        if len(parts) < 4:
            return "用法：/card pvp play 手牌编号 [目标玩家编号]"
        try:
            hand_index = int(parts[3])
        except ValueError:
            return "手牌编号必须是数字。"
        target_index = None
        if len(parts) >= 5:
            try:
                target_index = int(parts[4])
            except ValueError:
                return "目标玩家编号必须是数字。"
        return play_card(room, user_id, hand_index, target_index)

    def handle_close(self, session_id, user_id):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话没有 PVP 房。"
        if str(room.host_user_id) != str(user_id):
            return "只有房主可以关闭 PVP 房。"
        self.clear_room(session_id)
        return "PVP 房已关闭。"
