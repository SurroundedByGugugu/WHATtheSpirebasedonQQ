# -*- coding: utf-8 -*-

import random

from game.multiplayer.engine import (
    choose_relic,
    create_player_slot,
    end_player_turn,
    format_room,
    play_card,
    start_test_battle,
)
from game.multiplayer.state import MultiRoomState, ROOM_STATUS_LOBBY


CHARACTER_CHOICES = [
    ("0", "character.test", "测试角色"),
    ("1", "character.armored_warrior", "铁甲战士"),
    ("2", "character.silent_huntress", "静默猎手"),
    ("3", "character.lumine", "昼·里辛塔法"),
    ("4", "character.yoirine", "Yoirine"),
    ("5", "character.suzuri", "Suzuri"),
]

MAX_PLAYERS = 6


class MultiRoomService(object):
    """Small command facade for the separate multiplayer test room."""

    def __init__(self):
        self.rooms = {}

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

    def character_choices_text(self):
        lines = ["多人测试房可选角色："]
        for index, character_id, name in CHARACTER_CHOICES:
            lines.append("[{}] {} ({})".format(index, name, character_id))
        return "\n".join(lines)

    def help_text(self):
        return "\n".join([
            "多人测试房命令：",
            "/card multi new [角色编号]    开一桌并加入",
            "/card multi join [角色编号]   加入/换角色（开战前）",
            "/card multi start            开始 starting encounter 测试战",
            "/card multi view             查看房间",
            "/card multi play 手牌编号 [敌人编号]",
            "/card multi end              结束当前行动者回合",
            "/card multi reward           查看奖励",
            "/card multi relic 编号|skip  选择遗物，冲突时 d100 小者获得",
            "/card multi close            关闭当前多人房间",
        ])

    def handle_message(self, session_id, user_id, parts):
        if len(parts) < 3:
            room = self.get_room(session_id)
            if room is None:
                return self.help_text()
            return format_room(room)

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
                return "当前会话还没有多人测试房。使用 /card multi new [角色编号] 开一桌。"
            return format_room(room)

        if action in ("start", "开始"):
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有多人测试房。使用 /card multi new [角色编号] 开一桌。"
            if str(room.host_user_id) != str(user_id):
                return "只有房主可以开始多人测试房。"
            return start_test_battle(room)

        if action == "play":
            return self.handle_play(session_id, user_id, parts)

        if action == "end":
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有多人测试房。"
            return end_player_turn(room, user_id)

        if action in ("reward", "奖励"):
            room = self.get_room(session_id)
            if room is None:
                return "当前会话还没有多人测试房。"
            return format_room(room)

        if action in ("relic", "遗物"):
            return self.handle_relic(session_id, user_id, parts)

        if action in ("close", "关闭", "clear"):
            return self.handle_close(session_id, user_id)

        return "未知多人测试房命令：{}。\n{}".format(action, self.help_text())

    def handle_new(self, session_id, user_id, parts):
        current = self.get_room(session_id)
        if current is not None:
            return "当前会话已有多人测试房。\n{}".format(format_room(current))

        character_id = self.resolve_character_id(parts)
        if character_id is None:
            return "角色编号无效。\n{}".format(self.character_choices_text())

        room = MultiRoomState(
            session_id=session_id,
            host_user_id=str(user_id),
            seed=random.randint(1, 999999999),
        )
        room.players.append(create_player_slot(user_id, character_id))
        self.rooms[session_id] = room
        return "\n".join([
            "多人测试房已创建，房主已加入。",
            "",
            format_room(room),
        ])

    def handle_join(self, session_id, user_id, parts):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话还没有多人测试房。使用 /card multi new [角色编号] 开一桌。"
        if room.status != ROOM_STATUS_LOBBY:
            return "当前多人测试房已经开战，暂不能加入或换角色。"

        character_id = self.resolve_character_id(parts)
        if character_id is None:
            return "角色编号无效。\n{}".format(self.character_choices_text())

        existing = room.get_player(user_id)
        if existing is not None:
            index = room.players.index(existing)
            room.players[index] = create_player_slot(user_id, character_id)
            return "\n".join(["已更新你的多人测试房角色。", "", format_room(room)])

        if len(room.players) >= MAX_PLAYERS:
            return "当前多人测试房人数已满（上限 {} 人）。".format(MAX_PLAYERS)

        room.players.append(create_player_slot(user_id, character_id))
        return "\n".join(["已加入多人测试房。", "", format_room(room)])

    def handle_play(self, session_id, user_id, parts):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话还没有多人测试房。"
        if len(parts) < 4:
            return "用法：/card multi play 手牌编号 [敌人编号]"
        try:
            hand_index = int(parts[3])
        except ValueError:
            return "手牌编号必须是数字。"
        target_index = None
        if len(parts) >= 5:
            try:
                target_index = int(parts[4])
            except ValueError:
                return "敌人编号必须是数字。"
        return play_card(room, user_id, hand_index, target_index)

    def handle_relic(self, session_id, user_id, parts):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话还没有多人测试房。"
        if len(parts) < 4:
            return "用法：/card multi relic 编号，或 /card multi relic skip"
        raw = parts[3].strip().lower()
        if raw in ("skip", "none", "no", "跳过", "不选"):
            return choose_relic(room, user_id, None)
        try:
            choice_index = int(raw)
        except ValueError:
            return "遗物编号必须是数字，或使用 skip。"
        return choose_relic(room, user_id, choice_index)

    def handle_close(self, session_id, user_id):
        room = self.get_room(session_id)
        if room is None:
            return "当前会话没有多人测试房。"
        if str(room.host_user_id) != str(user_id):
            return "只有房主可以关闭多人测试房。"
        self.clear_room(session_id)
        return "多人测试房已关闭。"
