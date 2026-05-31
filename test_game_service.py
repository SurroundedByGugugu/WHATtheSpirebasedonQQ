# -*- coding: utf-8 -*-

from app.game_service import GameService


def main():
    service = GameService()

    session_id = "cli:test"
    user_id = "debug_user"

    print("输入 /card help 查看命令，输入 exit 退出。")
    print("*命令中的“/”与“。”和“.”等价")

    while True:
        raw_message = input("> ").strip()

        if raw_message == "exit":
            break

        reply = service.handle_message(session_id, user_id, raw_message)

        if reply is None:
            print("无响应。")
        else:
            print(reply)


if __name__ == "__main__":
    main()