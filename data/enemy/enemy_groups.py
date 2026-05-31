# -*- coding: utf-8 -*-
# 敌人组配置：一场战斗有哪些敌人

ENEMY_GROUPS = {
    "encounter.test_dummy": {
        "name": "测试假人",
        "enemy_ids": ["enemy.test_dummy"],
        "weight": 1
    }
}


def get_enemy_group(group_id):
    group = ENEMY_GROUPS.get(group_id)

    if group is None:
        raise ValueError("未知敌人组：{}".format(group_id))

    return group
