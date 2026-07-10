# -*- coding: utf-8 -*-
# QQ 指令解析：打牌、查看牌堆、选奖励、走路线等

COMMAND_PREFIXES = ("/", ".", "。")
CANONICAL_COMMAND_PREFIX = "/"


def normalize_command_prefix(command):
    """
    把 .card、。card、/card 这类根命令统一成 /card。
    子命令和参数不在这里改动。
    """
    text = str(command or "").strip()
    if not text:
        return text

    if text[0] in COMMAND_PREFIXES:
        return CANONICAL_COMMAND_PREFIX + text[1:]

    return text


def matches_root_command(text, command_name):
    """
    判断消息首个 token 是否是指定根命令。
    /、.、。 三种前缀等价，且只匹配完整根命令。
    """
    message = str(text or "").strip()
    if not message:
        return False

    first_token = message.split(maxsplit=1)[0]
    expected = CANONICAL_COMMAND_PREFIX + str(command_name or "").strip().lower()
    return normalize_command_prefix(first_token).lower() == expected


def parse_command(text):
    """
    把 QQ 消息文本解析成命令。

    返回：
    {
        "command": "play_card",
        "args": [...]
    }
    """
    text = text.strip()

    if not text:
        return {
            "command": "",
            "args": []
        }

    parts = text.split()
    command = normalize_command_prefix(parts[0])
    args = parts[1:]

    return {
        "command": command,
        "args": args
    }
