# -*- coding: utf-8 -*-
# 存敌人开场、行动、低血量、击杀玩家等专属台词。

import random


ENEMY_KILL_PLAYER_MESSAGES = {
    "enemy.test_dummy": [
        "测试假人击败了你。看来测试对象出现了一点问题。",
        "你倒在了测试假人面前。它沉默着，像一个没有感情的单元测试。",
        "测试假人完成了反向测试：证明玩家也可能被木桩打死。"
    ]
}


def get_enemy_kill_player_message(enemy):
    messages = ENEMY_KILL_PLAYER_MESSAGES.get(enemy.enemy_id)

    if not messages:
        return "{} 击败了你。".format(enemy.name)

    return random.choice(messages)