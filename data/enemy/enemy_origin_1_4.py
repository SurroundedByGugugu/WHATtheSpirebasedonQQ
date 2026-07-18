# -*- coding: utf-8 -*-
# enemy_origin_1_4 表示来自原作1中四层怪物/事件怪物。

import random

from data.enemy.base_enemy import EnemyActionResult, EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy


# ---------------------------------------------------------
# 高塔之盾
# ---------------------------------------------------------

SPIRE_SHIELD_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="attack",
            value=12
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="strength",
            value=-1
        ),
    ],
)
SPIRE_SHIELD_A._action_key = "a"

SPIRE_SHIELD_B = EnemyIntent(
    kind="block_all_allies",
    value=30
)
SPIRE_SHIELD_B._action_key = "b"

SPIRE_SHIELD_C = EnemyIntent(
    kind="attack_gain_block_equal_output",
    value=34
)
SPIRE_SHIELD_C._action_key = "c"


class SpireShieldEnemy(PatternEnemy):
    def __init__(self):
        if random.random() < 0.5:
            intent_cycle = [
                SPIRE_SHIELD_A,
                SPIRE_SHIELD_B,
                SPIRE_SHIELD_C,
            ]
        else:
            intent_cycle = [
                SPIRE_SHIELD_B,
                SPIRE_SHIELD_A,
                SPIRE_SHIELD_C,
            ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.spire_shield",
            name="高塔之盾",
            max_hp=110,
            intent_cycle=intent_cycle,
            loop_start_index=0,
        )

    def on_event(self, event_name, context):
        if event_name != "battle_start":
            return []

        from game.spire_orientation import (
            initialize_spire_elite_orientation
        )

        return initialize_spire_elite_orientation(
            context.game_state
        )


def create_spire_shield():
    return SpireShieldEnemy()


# ---------------------------------------------------------
# 高塔之矛
# ---------------------------------------------------------

SPIRE_SPEAR_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="attack",
            value=5,
            repeat=2
        ),
        EnemyIntent(
            kind="add_card_to_discard",
            card_id="card.status.burn_i",
            count=2
        ),
    ],
)
SPIRE_SPEAR_A._action_key = "a"

SPIRE_SPEAR_B = EnemyIntent(
    kind="status_all_allies",
    status="strength",
    value=2
)
SPIRE_SPEAR_B._action_key = "b"

SPIRE_SPEAR_C = EnemyIntent(
    kind="attack",
    value=10,
    repeat=3
)
SPIRE_SPEAR_C._action_key = "c"


class SpireSpearEnemy(PatternEnemy):
    def __init__(self):
        if random.random() < 0.5:
            repeating_cycle = [
                SPIRE_SPEAR_C,
                SPIRE_SPEAR_A,
                SPIRE_SPEAR_B,
            ]
        else:
            repeating_cycle = [
                SPIRE_SPEAR_C,
                SPIRE_SPEAR_B,
                SPIRE_SPEAR_A,
            ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.spire_spear",
            name="高塔之矛",
            max_hp=160,
            intent_cycle=[
                SPIRE_SPEAR_A,
            ] + repeating_cycle,
            loop_start_index=1,
        )

    def on_event(self, event_name, context):
        if event_name != "battle_start":
            return []

        from game.spire_orientation import (
            initialize_spire_elite_orientation
        )

        return initialize_spire_elite_orientation(
            context.game_state
        )


def create_spire_spear():
    return SpireSpearEnemy()


# ---------------------------------------------------------
# 腐化之心
# ---------------------------------------------------------

CORRUPT_HEART_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="status",
            target="player",
            status="vulnerable",
            value=2
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="weak",
            value=2
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="frail",
            value=2
        ),
        EnemyIntent(
            kind="add_card_to_draw",
            card_id="card.status.dazed",
            count=1
        ),
        EnemyIntent(
            kind="add_card_to_draw",
            card_id="card.status.slime_i",
            count=1
        ),
        EnemyIntent(
            kind="add_card_to_draw",
            card_id="card.status.wound",
            count=1
        ),
        EnemyIntent(
            kind="add_card_to_draw",
            card_id="card.status.burn_i",
            count=1
        ),
        EnemyIntent(
            kind="add_card_to_draw",
            card_id="card.status.void",
            count=1,
            shuffle_draw_pile=True,
            shuffle_batch_size=5
        ),
    ],
)
CORRUPT_HEART_A._action_key = "a"

CORRUPT_HEART_B = EnemyIntent(
    kind="attack",
    value=40
)
CORRUPT_HEART_B._action_key = "b"

CORRUPT_HEART_C = EnemyIntent(
    kind="attack",
    value=2,
    repeat=12
)
CORRUPT_HEART_C._action_key = "c"

CORRUPT_HEART_D_PLACEHOLDER = EnemyIntent(
    kind="heart_buff",
    count=1
)
CORRUPT_HEART_D_PLACEHOLDER._action_key = "d"


class CorruptHeartEnemy(PatternEnemy):
    INVINCIBLE_BASE = 300

    def __init__(self):
        if random.random() < 0.5:
            repeating_cycle = [
                CORRUPT_HEART_B,
                CORRUPT_HEART_C,
                CORRUPT_HEART_D_PLACEHOLDER,
            ]
        else:
            repeating_cycle = [
                CORRUPT_HEART_C,
                CORRUPT_HEART_B,
                CORRUPT_HEART_D_PLACEHOLDER,
            ]

        PatternEnemy.__init__(
            self,
            enemy_id="enemy.corrupt_heart",
            name="腐化之心",
            max_hp=750,
            intent_cycle=[
                CORRUPT_HEART_A,
            ] + repeating_cycle,
            loop_start_index=1,
        )

        self._heart_buff_count = 0

        self._invincible_remaining = (
            self.INVINCIBLE_BASE
        )

        # 战斗以第 1 回合开始。
        # 避免初始 turn_start 再输出一次刷新日志。
        self._invincible_last_refresh_turn = 1

        self.statuses.set(
            "beat_of_death",
            1
        )

        self.statuses.set(
            "invincible",
            self._invincible_remaining
        )

    def get_current_intent(self):
        intent = PatternEnemy.get_current_intent(self)

        # 节点快照和 SL 会 deepcopy 敌人及其意图循环。
        # deepcopy 后意图对象不再与模块级占位对象保持对象同一性，
        # 因此这里根据意图类型判断，不能使用 is 判断。
        if getattr(intent, "kind", "") != "heart_buff":
            return intent

        buff_index = max(
            1,
            int(getattr(self, "_heart_buff_count", 0) or 0) + 1
        )

        dynamic_intent = EnemyIntent(
            kind="heart_buff",
            count=buff_index
        )
        dynamic_intent._action_key = "d"

        self._locked_intent = dynamic_intent
        return self._locked_intent


    def advance_intent(self):
        if (
            getattr(self._locked_intent, "kind", "")
            == "heart_buff"
        ):
            executed_buff_index = int(
                getattr(self._locked_intent, "count", 0) or 0
            )

            if executed_buff_index <= 0:
                executed_buff_index = (
                    int(getattr(self, "_heart_buff_count", 0) or 0)
                    + 1
                )

            # 记录实际执行的强化档位，避免计数与动态意图再次脱节。
            self._heart_buff_count = max(
                int(getattr(self, "_heart_buff_count", 0) or 0),
                executed_buff_index
            )

        PatternEnemy.advance_intent(self)

    def on_event(self, event_name, context):
        if event_name != "turn_start":
            return []

        game_state = context.game_state

        current_turn = int(
            getattr(game_state, "turn_count", 0) or 0
        )

        if (
            self._invincible_last_refresh_turn
            == current_turn
        ):
            return []

        old_remaining = int(
            getattr(
                self,
                "_invincible_remaining",
                self.INVINCIBLE_BASE
            )
        )

        self._invincible_remaining = (
            self.INVINCIBLE_BASE
        )

        self._invincible_last_refresh_turn = (
            current_turn
        )

        self.statuses.set(
            "invincible",
            self._invincible_remaining
        )

        if old_remaining >= self.INVINCIBLE_BASE:
            return []

        return [
            "{}的坚不可摧刷新至 {}。".format(
                self.name,
                self.INVINCIBLE_BASE
            )
        ]


def create_corrupt_heart():
    return CorruptHeartEnemy()
