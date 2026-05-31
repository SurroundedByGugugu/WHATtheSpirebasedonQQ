# -*- coding: utf-8 -*-

import random

ENEMY_DEATH_MESSAGES = {
    "enemy.test_dummy": [
        "测试假人倒下了。它的测试使命到此为止。",
        "测试假人失去了测试价值，并安详地变成了一段日志。",
        "测试假人被击败了。它甚至没有来得及申请工伤。"
    ]
}


def get_enemy_death_message(enemy):
    messages = ENEMY_DEATH_MESSAGES.get(enemy.enemy_id)

    if not messages:
        return "{} 被击败了。".format(enemy.name)

    return random.choice(messages)

