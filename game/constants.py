# -*- coding: utf-8 -*-
# 通用常量：事件名、牌堆名、关键词名、目标类型等
# DEBUG_SEED = 42
DEBUG_SEED = None
# 事件名
EVENT_BATTLE_START = "battle_start"
EVENT_BATTLE_END = "battle_end"

EVENT_TURN_START = "turn_start"
EVENT_TURN_END = "turn_end"

EVENT_CARD_PLAY_BEFORE = "card_play_before"
EVENT_CARD_PLAY_AFTER = "card_play_after"

EVENT_DAMAGE_BEFORE = "damage_before"
EVENT_DAMAGE_AFTER = "damage_after"

EVENT_GAIN_BLOCK_BEFORE = "gain_block_before"
EVENT_GAIN_BLOCK_AFTER = "gain_block_after"

EVENT_DRAW_CARD_BEFORE = "draw_card_before"
EVENT_DRAW_CARD_AFTER = "draw_card_after"

EVENT_ENEMY_DEATH = "enemy_death"
EVENT_PLAYER_DEATH = "player_death"

EVENT_TURN_START = "turn_start"
EVENT_CARD_PLAY_AFTER = "card_play_after"

# 药水
EVENT_POTION_USE_BEFORE = "potion_use_before"
EVENT_POTION_USE_AFTER = "potion_use_after"

# 牌堆名
PILE_DRAW = "draw_pile"
PILE_DISCARD = "discard_pile"
PILE_EXHAUST = "exhaust_pile"
PILE_HAND = "hand"

# 卡牌关键词
KEYWORD_EXHAUST = "exhaust"      # 消耗
KEYWORD_ETHEREAL = "ethereal"    # 虚无
KEYWORD_RETAIN = "retain"        # 保留
KEYWORD_INNATE = "innate"        # 固有
KEYWORD_CLEVER = "clever"        # 奇巧

# 目标类型
TARGET_SELF = "self"
TARGET_ENEMY = "enemy"
TARGET_ALL_ENEMIES = "all_enemies"
TARGET_RANDOM_ENEMY = "random_enemy"
TARGET_NONE = "none"

# 伤害来源
DAMAGE_SOURCE_PLAYED_CARD = "played_card"
DAMAGE_SOURCE_ENEMY_ACTION = "enemy_action"
DAMAGE_SOURCE_THORNS = "thorns"
DAMAGE_SOURCE_POISON = "poison"
DAMAGE_SOURCE_RELIC = "relic"
DAMAGE_SOURCE_POTION = "potion"
DAMAGE_SOURCE_STATUS = "status"
DAMAGE_SOURCE_EFFECT = "effect"

# 格挡来源
BLOCK_SOURCE_PLAYED_CARD = "played_card"
BLOCK_SOURCE_ENEMY_ACTION = "enemy_action"
BLOCK_SOURCE_REACTION = "reaction"
BLOCK_SOURCE_RELIC = "relic"
BLOCK_SOURCE_POTION = "potion"
BLOCK_SOURCE_STATUS = "status"
BLOCK_SOURCE_EFFECT = "effect"

# 基础状态倍率
VULNERABLE_PLAYER_CARD_DAMAGE_MULT = 1.5
VULNERABLE_ENEMY_ATTACK_DAMAGE_MULT = 1.5

FRAIL_PLAYER_CARD_BLOCK_MULT = 0.75
FRAIL_ENEMY_ACTION_BLOCK_MULT = 0.75

WEAK_PLAYER_CARD_DAMAGE_MULT = 0.75
WEAK_ENEMY_ATTACK_DAMAGE_MULT = 0.75