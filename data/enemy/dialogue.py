# -*- coding: utf-8 -*-
# 存敌人开场、行动、低血量、击杀玩家等专属台词。

import random


ENEMY_KILL_PLAYER_MESSAGES = {
    "enemy.test_dummy": [
        "测试假人击败了你。看来测试对象出现了一点问题。",
        "你倒在了测试假人面前。它沉默着，像一个没有感情的单元测试。",
        "测试假人完成了反向测试：证明玩家也可能被木桩打死。"
    ],
    "enemy.chaos_fragment":[
        "你在混沌碎片的注视中归于虚无。"
    ],
    "enemy.corsoal":[
        "太阳珊瑚也有可能扎死它们的天敌……之外的什么？"
    ],
    "enemy.mareanie":[
        "棘冠海星把你当成珊瑚准备开饭了。"
    ],
    "enemy.cultist":[
        "咔咔！！",
        "我的力量无人能及！"
    ]
}


def get_enemy_kill_player_message(enemy):
    messages = ENEMY_KILL_PLAYER_MESSAGES.get(enemy.enemy_id)

    if not messages:
        return "{} 击败了你。".format(enemy.name)

    return random.choice(messages)