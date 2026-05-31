# -*- coding: utf-8 -*-
# 读写存档，占位
import json
import os


SAVE_DIR = "saves"


def ensure_save_dir():
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)


def get_save_path(session_id):
    ensure_save_dir()
    return os.path.join(SAVE_DIR, "{}.json".format(session_id))


def save_json(session_id, data):
    path = get_save_path(session_id)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(session_id):
    path = get_save_path(session_id)

    if not os.path.exists(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)