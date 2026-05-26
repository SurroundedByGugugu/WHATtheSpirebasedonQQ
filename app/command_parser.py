# -*- coding: utf-8 -*-
# QQ 指令解析：打牌、查看牌堆、选奖励、走路线等

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
    command = parts[0]
    args = parts[1:]

    return {
        "command": command,
        "args": args
    }