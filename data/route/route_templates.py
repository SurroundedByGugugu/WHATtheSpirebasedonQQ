# -*- coding: utf-8 -*-
# 路线模板

ACT1_TEST_ROUTE = [
    {
        "node_id": "act1.ancient.start",
        "node_type": "ancient",
        "name": "先古之民",
        "next_node_ids": ["act1.node.01"]
    },

    {
        "node_id": "act1.node.01",
        "node_type": "normal_enemy",
        "name": "入口战斗",
        "encounter_id": "encounter.test_dummy",
        "next_node_ids": ["act1.node.02a", "act1.node.02b"]
    },

    {
        "node_id": "act1.node.02a",
        "node_type": "normal_enemy",
        "name": "左路战斗",
        "encounter_id": "encounter.test_dummy",
        "next_node_ids": ["act1.node.03a", "act1.node.03b"]
    },
    {
        "node_id": "act1.node.02b",
        "node_type": "mystery",
        "name": "右路？",
        "next_node_ids": ["act1.node.03b"]
    },

    {
        "node_id": "act1.node.03a",
        "node_type": "shop",
        "name": "临时商店",
        "next_node_ids": ["act1.node.04a"]
    },
    {
        "node_id": "act1.node.03b",
        "node_type": "mystery",
        "name": "岔路？",
        "next_node_ids": ["act1.node.04a", "act1.node.04b"]
    },

    {
        "node_id": "act1.node.04a",
        "node_type": "elite",
        "name": "精英战斗",
        "encounter_id": "encounter.elite.chaos_fragment",
        "next_node_ids": ["act1.node.05"]
    },
    {
        "node_id": "act1.node.04b",
        "node_type": "normal_enemy",
        "name": "普通战斗",
        "encounter_id": "encounter.test_dummy",
        "next_node_ids": ["act1.node.05"]
    },

    {
        "node_id": "act1.node.05",
        "node_type": "event",
        "name": "异常房间",
        "next_node_ids": ["act1.node.06a", "act1.node.06b"]
    },

    {
        "node_id": "act1.node.06a",
        "node_type": "rest",
        "name": "小火堆",
        "next_node_ids": ["act1.node.07"]
    },
    {
        "node_id": "act1.node.06b",
        "node_type": "shop",
        "name": "路边商店",
        "next_node_ids": ["act1.node.07"]
    },

    {
        "node_id": "act1.node.07",
        "node_type": "normal_enemy",
        "name": "中段战斗",
        "encounter_id": "encounter.test_dummy",
        "next_node_ids": ["act1.node.08a", "act1.node.08b"]
    },

    {
        "node_id": "act1.node.08a",
        "node_type": "mystery",
        "name": "深处？",
        "next_node_ids": ["act1.node.09"]
    },
    {
        "node_id": "act1.node.08b",
        "node_type": "treasure",
        "name": "旧宝箱",
        "next_node_ids": ["act1.node.09"]
    },

    {
        "node_id": "act1.node.09",
        "node_type": "elite",
        "name": "门前精英",
        "encounter_id": "encounter.elite_dummy",
        "next_node_ids": ["act1.node.10a", "act1.node.10b"]
    },

    {
        "node_id": "act1.node.10a",
        "node_type": "normal_enemy",
        "name": "最后战斗",
        "encounter_id": "encounter.test_dummy",
        "next_node_ids": ["act1.rest.before_boss"]
    },
    {
        "node_id": "act1.node.10b",
        "node_type": "shop",
        "name": "Boss 前商店",
        "next_node_ids": ["act1.rest.before_boss"]
    },

    {
        "node_id": "act1.rest.before_boss",
        "node_type": "rest",
        "name": "Boss 前火堆",
        "next_node_ids": ["act1.boss"]
    },

    {
        "node_id": "act1.boss",
        "node_type": "boss",
        "name": "一层 Boss",
        "encounter_id": "encounter.boss_dummy",
        "next_node_ids": ["act2.ancient.start"]
    },

    {
        "node_id": "act2.ancient.start",
        "node_type": "ancient",
        "name": "下一层的先古之民",
        "next_node_ids": []
    },
]

ACT2_TEST_ROUTE=[
    {
        "node_id": "act1.ancient.start",
        "node_type": "ancient",
        "name": "先古之民",
        "next_node_ids": ["act1.node.01"]
    },
    {
        "node_id": "act1.node.01",
        "node_type": "normal_enemy",
        "name": "入口战斗",
        "encounter_id": "encounter.test_dummy",
        "next_node_ids": ["act1.node.02"]
    },
    {
        "node_id": "act1.node.02",
        "node_type": "event",
        "name": "异常房间",
        "next_node_ids": ["act1.node.04"]
    },
    {
        "node_id": "act1.node.04",
        "node_type": "shop",
        "name": "Boss 前商店",
        "next_node_ids": ["act1.rest.before_boss"]
    },

    {
        "node_id": "act1.rest.before_boss",
        "node_type": "rest",
        "name": "Boss 前火堆",
        "next_node_ids": ["act1.boss"]
    },
    {
        "node_id": "act1.boss",
        "node_type": "elite",
        "name": "伪装成boss的精英",
        "encounter_id": "encounter.elite_dummy",
        "next_node_ids": ["act1.node.10a", "act1.node.10b"]
    },
]


TEST_ROUTE = ACT2_TEST_ROUTE