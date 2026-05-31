# -*- coding: utf-8 -*-
# 更复杂敌人 AI 父类，占位


from data.enemy.base_enemy import Enemy


class AIEnemy(Enemy):
    """
    复杂 AI 敌人父类。

    PatternEnemy 适合固定循环。
    AIEnemy 预留给根据玩家状态、回合数、血量阶段改变行动的敌人。
    """

    def choose_intent(self, game_state):
        raise NotImplementedError