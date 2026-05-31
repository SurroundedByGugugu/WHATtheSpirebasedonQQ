import asyncio
import json
import os
import re
import configparser

import websockets

from app.game_service import GameService


HOST = "127.0.0.1"
PORT = 15804

CONFIG_PATH = "bot_config.ini"

# 总开关：True 表示正常处理插件；False 表示只接收，不传给后续模块
BOT_ENABLED = True

# 卡牌测试服务：当前以 session_id 管理战斗状态
game_service = GameService()

# 全局配置对象
BOT_CONFIG = {
    "admin_user_ids": set(),
    "enabled_group_ids": set(),
    "blacklist_user_ids": set(),
    "blacklist_group_ids": set()
}


def split_id_list(text):
    """
    把 ini 中的 ID 字符串拆成 set。
    支持英文逗号、分号、空格、换行。
    """
    if not text:
        return set()

    parts = re.split(r"[,;\s]+", text.strip())
    result = set()

    for item in parts:
        item = item.strip()
        if item:
            result.add(item)

    return result


def ensure_default_config():
    """
    如果配置文件不存在，自动创建一个默认配置。
    默认不启用任何群，避免误触发。
    """
    if os.path.exists(CONFIG_PATH):
        return

    content = """[admin]
; 管理员 QQ 号，用英文逗号分隔
; 如果这里不填，测试阶段默认所有人都能使用 /pybot 控制命令
user_ids =

[groups]
; 群号 = 1 表示启用
; 群号不存在，或值不是 1，都视为关闭
; 例如：
; 1030875571 = 1

[blacklist]
; 用户黑名单：命中后私聊和群聊都拦截
user_ids =

; 群黑名单：命中后该群所有消息都拦截
group_ids =
"""

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def load_bot_config():
    """
    读取 bot_config.ini。
    群聊默认关闭，只有 [groups] 中配置为 1 的群才启用。
    """
    global BOT_CONFIG

    ensure_default_config()

    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(CONFIG_PATH, encoding="utf-8")

    admin_user_ids = set()
    enabled_group_ids = set()
    blacklist_user_ids = set()
    blacklist_group_ids = set()

    if parser.has_section("admin"):
        admin_user_ids = split_id_list(parser.get("admin", "user_ids", fallback=""))

    if parser.has_section("groups"):
        for group_id, value in parser.items("groups"):
            group_id = str(group_id).strip()
            value = str(value).strip()

            if value == "1":
                enabled_group_ids.add(group_id)

    if parser.has_section("blacklist"):
        blacklist_user_ids = split_id_list(parser.get("blacklist", "user_ids", fallback=""))
        blacklist_group_ids = split_id_list(parser.get("blacklist", "group_ids", fallback=""))

    BOT_CONFIG = {
        "admin_user_ids": admin_user_ids,
        "enabled_group_ids": enabled_group_ids,
        "blacklist_user_ids": blacklist_user_ids,
        "blacklist_group_ids": blacklist_group_ids
    }

    print("配置读取完成：")
    print("  管理员用户：{}".format(BOT_CONFIG["admin_user_ids"]))
    print("  启用群聊：{}".format(BOT_CONFIG["enabled_group_ids"]))
    print("  用户黑名单：{}".format(BOT_CONFIG["blacklist_user_ids"]))
    print("  群黑名单：{}".format(BOT_CONFIG["blacklist_group_ids"]))


def is_admin(user_id):
    """
    判断是否为管理员。
    如果 admin_user_ids 为空，则测试阶段允许所有人使用控制命令。
    正式使用建议在 bot_config.ini 中填写管理员 QQ 号。
    """
    user_id = str(user_id)

    admin_user_ids = BOT_CONFIG.get("admin_user_ids", set())

    if not admin_user_ids:
        return True

    return user_id in admin_user_ids


def is_blacklisted(event):
    """
    黑名单优先级最高。
    命中后直接拦截，不回复、不进入控制命令、不进入插件模块。
    """
    user_id = str(event.get("user_id", ""))
    group_id = str(event.get("group_id", ""))

    blacklist_user_ids = BOT_CONFIG.get("blacklist_user_ids", set())
    blacklist_group_ids = BOT_CONFIG.get("blacklist_group_ids", set())

    if user_id and user_id in blacklist_user_ids:
        print("黑名单拦截：user_id={}".format(user_id))
        return True

    if group_id and group_id in blacklist_group_ids:
        print("黑名单拦截：group_id={}".format(group_id))
        return True

    return False


def is_session_enabled(event):
    """
    会话启用判断：
    - 私聊：默认启用
    - 群聊：只有群号在 ini 的 [groups] 中配置为 1 才启用
    """
    message_type = event.get("message_type")

    if message_type == "private":
        return True

    if message_type == "group":
        group_id = str(event.get("group_id", ""))
        enabled_group_ids = BOT_CONFIG.get("enabled_group_ids", set())

        if group_id in enabled_group_ids:
            return True

        print("群聊未启用，已忽略：group_id={}".format(group_id))
        return False

    return False


async def send_private_msg(ws, user_id, text):
    payload = {
        "action": "send_private_msg",
        "params": {
            "user_id": user_id,
            "message": [
                {
                    "type": "text",
                    "data": {
                        "text": text
                    }
                }
            ]
        },
        "echo": "send_private_msg"
    }

    await ws.send(json.dumps(payload, ensure_ascii=False))


async def send_group_msg(ws, group_id, text):
    payload = {
        "action": "send_group_msg",
        "params": {
            "group_id": group_id,
            "message": [
                {
                    "type": "text",
                    "data": {
                        "text": text
                    }
                }
            ]
        },
        "echo": "send_group_msg"
    }

    await ws.send(json.dumps(payload, ensure_ascii=False))


async def send_reply(ws, event, text):
    message_type = event.get("message_type")

    if message_type == "private":
        user_id = event.get("user_id")
        if user_id is not None:
            await send_private_msg(ws, user_id, text)

    elif message_type == "group":
        group_id = event.get("group_id")
        if group_id is not None:
            await send_group_msg(ws, group_id, text)


async def handle_main_control(ws, event):
    """
    main.py 层面的控制命令。
    支持：
    /pybot on
    /pybot off
    /pybot status
    /pybot reload
    """
    global BOT_ENABLED

    raw_message = event.get("raw_message", "").strip()
    user_id = event.get("user_id")

    if not raw_message.startswith("/pybot"):
        return False

    if not is_admin(user_id):
        await send_reply(ws, event, "你没有权限控制 Python 插件。")
        return True

    parts = raw_message.split()

    if len(parts) != 2:
        await send_reply(ws, event, "用法：/pybot on、/pybot off、/pybot status、/pybot reload")
        return True

    action = parts[1].lower()

    if action == "on":
        BOT_ENABLED = True
        await send_reply(ws, event, "Python 插件总开关：已开启。")
        return True

    if action == "off":
        BOT_ENABLED = False
        await send_reply(ws, event, "Python 插件总开关：已关闭。现在只接收消息，不传入后续模块。")
        return True

    if action == "status":
        message_type = event.get("message_type")
        group_id = event.get("group_id")

        if BOT_ENABLED:
            bot_status = "开启"
        else:
            bot_status = "关闭"

        if message_type == "group":
            group_id_text = str(group_id)
            if group_id_text in BOT_CONFIG.get("enabled_group_ids", set()):
                group_status = "当前群已启用"
            else:
                group_status = "当前群未启用"

            reply = "Python 插件总开关：{}。\n{}。".format(bot_status, group_status)
        else:
            reply = "Python 插件总开关：{}。\n私聊默认启用。".format(bot_status)

        await send_reply(ws, event, reply)
        return True

    if action == "reload":
        load_bot_config()
        await send_reply(ws, event, "配置已重新读取。")
        return True

    await send_reply(ws, event, "未知控制命令。用法：/pybot on、/pybot off、/pybot status、/pybot reload")
    return True


async def dispatch_to_plugins(ws, event):
    """
    后续插件分发层。
    只有通过以下检查后才会进入这里：
    1. 未命中黑名单
    2. 私聊默认启用，或群聊在 ini 中配置为 1
    3. BOT_ENABLED=True

    当前接入：
    - /card 命令交给 GameService
    - 群聊 session_id 使用 group:{group_id}
    - 私聊 session_id 使用 private:{user_id}
    """
    raw_message = event.get("raw_message", "")
    message_type = event.get("message_type")
    user_id = str(event.get("user_id", ""))

    if message_type == "group":
        session_id = "group:{}".format(event.get("group_id"))
    elif message_type == "private":
        session_id = "private:{}".format(user_id)
    else:
        return

    reply = game_service.handle_message(session_id, user_id, raw_message)

    if reply is not None:
        await send_reply(ws, event, reply)


async def handle_connection(ws):
    print("LLOB 已连接到 Python 插件")

    async for raw_data in ws:
        try:
            event = json.loads(raw_data)
        except json.JSONDecodeError:
            print("收到非 JSON 数据：{}".format(raw_data))
            continue

        # 只处理消息事件
        if event.get("post_type") != "message":
            continue

        raw_message = event.get("raw_message", "")
        user_id = event.get("user_id")
        group_id = event.get("group_id")
        message_type = event.get("message_type")

        print("收到消息：type={}, user_id={}, group_id={}, raw_message={}".format(
            message_type,
            user_id,
            group_id,
            raw_message
        ))

        # 第一优先级：黑名单
        if is_blacklisted(event):
            continue

        # 第二优先级：私聊默认启用；群聊按 ini 配置启用
        if not is_session_enabled(event):
            continue

        # 第三优先级：main.py 自己处理控制命令
        handled_by_main = await handle_main_control(ws, event)
        if handled_by_main:
            continue

        # 第四优先级：总开关
        if not BOT_ENABLED:
            print("总开关关闭，消息已接收但未传入插件模块。")
            continue

        # 第五优先级：进入后续插件模块
        await dispatch_to_plugins(ws, event)


async def main():
    load_bot_config()

    print("Python 插件启动，监听 ws://{}:{}".format(HOST, PORT))

    async with websockets.serve(handle_connection, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())