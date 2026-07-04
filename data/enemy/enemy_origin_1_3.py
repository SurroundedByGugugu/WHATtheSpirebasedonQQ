# -*- coding: utf-8 -*-
# enemy_origin_1_3 表示来自原作1中三层怪物/事件怪物。

import random

from data.enemy.base_enemy import EnemyActionResult, EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy


def _weighted_choice(weighted_items):
    """weighted_items: [(key, weight), ...]"""
    items = [item[0] for item in weighted_items]
    weights = [item[1] for item in weighted_items]
    return random.choices(items, weights=weights, k=1)[0]
def _action_key_from_intent(intent):
    return getattr(intent, "_action_key", "") or getattr(intent, "kind", "")


# common
ORB_WALKER_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=10, attack_type="blunt"),
        EnemyIntent(kind="add_card_to_draw", card_id="card.status.burn_i", count=1),
        EnemyIntent(kind="add_card_to_discard", card_id="card.status.burn_i", count=1),
    ],
)
ORB_WALKER_B = EnemyIntent(
    kind="attack",
    value=15,
    attack_type="blunt",
)
class OrbWalkerEnemy(PatternEnemy):
    def __init__(self, max_hp=None):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.orb_walker",
            name="圆球行者",
            max_hp=max_hp if max_hp is not None else random.randint(90, 96),
            intent_cycle=[ORB_WALKER_A, ORB_WALKER_B],
        )
        self._orb_intent_history = []

        # 战斗开始时自带 3 层“每回合结束获得力量”的状态。
        # 当前工程里敌人 ritual 已按敌方回合结束触发。
        self.gain_status("ritual", 3)

    def _resolve_intent_slot(self, slot):
        choices = [ORB_WALKER_A, ORB_WALKER_B]
        history = list(getattr(self, "_orb_intent_history", []) or [])

        if len(history) >= 2 and history[-1] is history[-2]:
            chosen = ORB_WALKER_B if history[-1] is ORB_WALKER_A else ORB_WALKER_A
        else:
            chosen = random.choice(choices)

        history.append(chosen)
        if len(history) > 2:
            history = history[-2:]

        self._orb_intent_history = history
        return chosen

    def advance_intent(self):
        self._locked_intent = None
def create_orb_walker():
    return OrbWalkerEnemy()

MAW_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="status", target="player", status="frail", value=3),
        EnemyIntent(kind="status", target="player", status="weak", value=3),
    ],
)
MAW_A._action_key = "a"
MAW_B = EnemyIntent(kind="status", target="self", status="strength", value=3)
MAW_B._action_key = "b"
MAW_C = EnemyIntent(kind="attack", value=25, attack_type="blunt")
MAW_C._action_key = "c"
class TheMawEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.the_maw",
            name="巨口",
            max_hp=300,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self._last_action_key = ""

    def _build_maw_d(self):
        game_state = getattr(self, "_current_game_state", None)
        turn_count = int(getattr(game_state, "turn_count", 1) or 1)
        n = (turn_count + 1) // 2
        intent = EnemyIntent(kind="attack", value=5 * n, attack_type="blunt")
        intent._action_key = "d"
        return intent

    def _choose_next_intent(self):
        game_state = getattr(self, "_current_game_state", None)
        turn_count = int(getattr(game_state, "turn_count", 1) or 1)

        if turn_count <= 1 and not self._last_action_key:
            return MAW_A

        if turn_count == 2 and self._last_action_key == "a":
            return random.choice([MAW_C, self._build_maw_d()])

        if self._last_action_key == "c":
            return random.choice([MAW_B, self._build_maw_d()])

        if self._last_action_key == "b":
            return random.choice([MAW_C, self._build_maw_d()])

        if self._last_action_key == "d":
            return MAW_B

        return random.choice([MAW_C, self._build_maw_d()])

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_intent = self._choose_next_intent()
        return self._locked_intent

    def advance_intent(self):
        self._last_action_key = _action_key_from_intent(self.get_current_intent())
        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)
def create_the_maw():
    return TheMawEnemy()

DARKLING_BLOCK = EnemyIntent(kind="block", value=12)
DARKLING_BLOCK._action_key = "block"
DARKLING_DOUBLE = EnemyIntent(kind="attack", value=8, repeat=2, attack_type="blunt")
DARKLING_DOUBLE._action_key = "double"
class DarklingEnemy(PatternEnemy):
    def __init__(self, role="side", max_hp=None):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.darkling_{}".format(role),
            name="小黑",
            max_hp=max_hp if max_hp is not None else random.randint(48, 56),
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self.darkling_role = role
        self._single_damage = random.randint(7, 11)
        self._last_action_key = ""
        self._consecutive_single = 0
        self._darkling_revive_turns = 0
        self._darkling_down = False
        self.gain_status("life_link", 2)

    def _single_intent(self):
        intent = EnemyIntent(kind="attack", value=self._single_damage, attack_type="blunt")
        intent._action_key = "single"
        return intent

    def _choose_middle(self):
        if not self._last_action_key:
            return random.choice([DARKLING_BLOCK, self._single_intent()])

        if self._last_action_key == "block":
            return self._single_intent()

        if self._last_action_key == "single" and self._consecutive_single >= 2:
            return DARKLING_BLOCK

        if self._last_action_key == "single":
            return random.choice([DARKLING_BLOCK, self._single_intent()])

        return self._single_intent()

    def _choose_side(self):
        if not self._last_action_key:
            return random.choice([DARKLING_BLOCK, self._single_intent()])

        if self._last_action_key == "double":
            return random.choice([DARKLING_BLOCK, self._single_intent()])

        if self._last_action_key == "block":
            return _weighted_choice([
                (self._single_intent(), 3),
                (DARKLING_DOUBLE, 4),
            ])

        if self._last_action_key == "single" and self._consecutive_single >= 2:
            return _weighted_choice([
                (DARKLING_BLOCK, 3),
                (DARKLING_DOUBLE, 4),
            ])

        if self._last_action_key == "single":
            return _weighted_choice([
                (DARKLING_BLOCK, 3),
                (self._single_intent(), 3),
                (DARKLING_DOUBLE, 4),
            ])

        return random.choice([DARKLING_BLOCK, self._single_intent()])

    def get_current_intent(self):
        if self._darkling_down:
            return EnemyIntent(
                kind="wait",
                message="生命链接倒计时：{}".format(self._darkling_revive_turns)
            )

        if self._locked_intent is None:
            if self.darkling_role == "middle":
                self._locked_intent = self._choose_middle()
            else:
                self._locked_intent = self._choose_side()
        return self._locked_intent

    def advance_intent(self):
        key = _action_key_from_intent(self.get_current_intent())
        self._last_action_key = key

        if key == "single":
            self._consecutive_single += 1
        else:
            self._consecutive_single = 0

        self._locked_intent = None

    def act(self):
        if self._darkling_down:
            return EnemyActionResult(
                action={
                    "op": "enemy_wait",
                    "source_enemy_id": self.enemy_id,
                    "source_enemy_name": self.name,
                },
                logs=["{} 正在等待生命链接复活。".format(self.name)]
            )

        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def _has_other_living_darkling(self, game_state):
        for enemy in getattr(game_state, "enemies", []) or []:
            if enemy is self:
                continue
            if not enemy.is_alive():
                continue
            if str(getattr(enemy, "enemy_id", "")).startswith("enemy.darkling"):
                return True
        return False

    def on_event(self, event_name, context):
        logs = []

        if context is not None:
            setattr(self, "_current_game_state", context.game_state)

        if event_name == "damage_after" and context is not None:
            if context.target is not self:
                return logs
            if not context.extra.get("target_is_dead_after", False):
                return logs
            if self._darkling_down:
                return logs
            if not self._has_other_living_darkling(context.game_state):
                return logs

            self._darkling_down = True
            self._darkling_revive_turns = 2
            self._locked_intent = None
            self.block = 0

            # 用于阻止贪婪之手/狂宴等“非爪牙斩杀”收益。
            self._suppress_non_minion_kill_reward_once = True

            # 不显示普通死亡文本。
            context.extra["suppress_death_message"] = True

            logs.append("{} 的生命链接触发：只要还有其他小黑存活，它将在 2 回合后复活。".format(self.name))
            return logs

        if event_name == "turn_start" and self._darkling_down:
            game_state = context.game_state if context is not None else None

            if not self._has_other_living_darkling(game_state):
                self._darkling_down = False
                self._darkling_revive_turns = 0
                return logs

            self._darkling_revive_turns -= 1

            if self._darkling_revive_turns > 0:
                logs.append("{} 的生命链接倒计时：{}。".format(self.name, self._darkling_revive_turns))
                return logs

            self.hp = max(1, (int(self.max_hp) + 1) // 2)
            self.block = 0

            from game.status.status_container import StatusContainer
            self.statuses = StatusContainer()
            self.gain_status("life_link", 2)

            self._darkling_down = False
            self._darkling_revive_turns = 0
            self._suppress_non_minion_kill_reward_once = False
            self._locked_intent = None
            self._last_action_key = ""
            self._consecutive_single = 0

            logs.append("{} 通过生命链接复活，HP：{}/{}。".format(
                self.name,
                self.hp,
                self.max_hp
            ))
            return logs

        return logs

    def status_text(self, game_state=None):
        if self._darkling_down:
            return "{} HP：0/{}；格挡：0；意图：生命链接倒计时 {}；状态：生命链接".format(
                self.name,
                self.max_hp,
                self._darkling_revive_turns
            )
        return super(DarklingEnemy, self).status_text(game_state)
def create_darkling_left():
    return DarklingEnemy(role="left")
def create_darkling_middle():
    return DarklingEnemy(role="middle")
def create_darkling_right():
    return DarklingEnemy(role="right")

class TransientEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.transient",
            name="倏忽魔",
            max_hp=999,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self.gain_status("fading", 5)
        self.gain_status("shifting", 1)
        self._transient_strength_lost_this_turn = 0

    def get_current_intent(self):
        if self._locked_intent is None:
            game_state = getattr(self, "_current_game_state", None)
            turn_count = int(getattr(game_state, "turn_count", 1) or 1)
            self._locked_intent = EnemyIntent(
                kind="attack",
                value=20 + 10 * turn_count,
                attack_type="blunt"
            )
        return self._locked_intent

    def advance_intent(self):
        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def on_event(self, event_name, context):
        logs = []

        if context is not None:
            setattr(self, "_current_game_state", context.game_state)

        if event_name == "damage_after" and context is not None:
            if context.target is not self:
                return logs

            real_damage = int(context.extra.get("real_damage", 0) or 0)
            if real_damage <= 0:
                return logs

            if self.get_status_value("shifting") <= 0:
                return logs

            current = self.gain_status("strength", -real_damage)
            self._transient_strength_lost_this_turn += real_damage

            logs.append("{} 的变幻触发，暂时失去 {} 点力量。当前力量：{}。".format(
                self.name,
                real_damage,
                current
            ))
            return logs

        if event_name == "turn_end":
            restored = int(getattr(self, "_transient_strength_lost_this_turn", 0) or 0)

            if restored > 0 and self.is_alive():
                current = self.gain_status("strength", restored)
                logs.append("{} 的变幻结束，恢复 {} 点力量。当前力量：{}。".format(
                    self.name,
                    restored,
                    current
                ))

            self._transient_strength_lost_this_turn = 0

            if self.is_alive() and self.get_status_value("fading") > 0:
                left = self.gain_status("fading", -1)

                if left <= 0:
                    self.hp = 0
                    self.block = 0
                    logs.append("{} 的消逝结束，它消失了。".format(self.name))
                else:
                    logs.append("{} 的消逝倒计时：{}。".format(self.name, left))

            return logs

        return logs
def create_transient():
    return TransientEnemy()

WRITHING_PARASITE = EnemyIntent(
    kind="add_curse_to_master_deck",
    card_id="card.curse.parasite",
    count=1
)
WRITHING_PARASITE._action_key = "parasite"
WRITHING_HEAVY = EnemyIntent(kind="attack", value=32, attack_type="blunt")
WRITHING_HEAVY._action_key = "heavy"
WRITHING_WITHER = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=10, attack_type="blunt"),
        EnemyIntent(kind="status", target="player", status="vulnerable", value=2),
        EnemyIntent(kind="status", target="player", status="weak", value=2),
    ],
)
WRITHING_WITHER._action_key = "wither"
WRITHING_FLURRY = EnemyIntent(kind="attack", value=7, repeat=3, attack_type="blunt")
WRITHING_FLURRY._action_key = "flurry"
WRITHING_SHIELD = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=15, attack_type="blunt"),
        EnemyIntent(kind="block", value=16),
    ],
)
WRITHING_SHIELD._action_key = "shield"
class WrithingMassEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.writhing_mass",
            name="扭曲团块",
            max_hp=160,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self._last_action_key = ""
        self._parasite_used = False
        self.gain_status("writhing", 1)

    def _pool(self, first_turn=False):
        if first_turn:
            return [
                (WRITHING_WITHER, 1),
                (WRITHING_SHIELD, 1),
                (WRITHING_FLURRY, 1),
            ]

        return [
            (WRITHING_PARASITE, 1),
            (WRITHING_HEAVY, 1),
            (WRITHING_WITHER, 2),
            (WRITHING_SHIELD, 3),
            (WRITHING_FLURRY, 3),
        ]

    def _choose_from_pool(self, first_turn=False):
        pool = []

        for intent, weight in self._pool(first_turn=first_turn):
            key = _action_key_from_intent(intent)

            if key == self._last_action_key:
                continue

            if key == "parasite" and self._parasite_used:
                continue

            pool.append((intent, weight))

        if not pool:
            pool = [(WRITHING_HEAVY, 1)]

        return _weighted_choice(pool)

    def get_current_intent(self):
        if self._locked_intent is None:
            game_state = getattr(self, "_current_game_state", None)
            first_turn = int(getattr(game_state, "turn_count", 1) or 1) <= 1 and not self._last_action_key
            self._locked_intent = self._choose_from_pool(first_turn=first_turn)

        return self._locked_intent

    def _intent_to_action(self, intent):
        if getattr(intent, "kind", "") == "add_curse_to_master_deck":
            return {
                "op": "enemy_add_curse_to_master_deck",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "card_id": intent.card_id,
                "count": int(getattr(intent, "count", 1) or 1),
                "message": intent.message,
            }

        return super(WrithingMassEnemy, self)._intent_to_action(intent)

    def advance_intent(self):
        key = _action_key_from_intent(self.get_current_intent())
        self._last_action_key = key

        if key == "parasite":
            self._parasite_used = True

        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def on_event(self, event_name, context):
        logs = []

        if context is not None:
            setattr(self, "_current_game_state", context.game_state)

        if event_name != "damage_after" or context is None:
            return logs

        if context.target is not self:
            return logs

        if context.extra.get("damage_kind") != "attack":
            return logs

        if context.source is self:
            return logs

        real_damage = int(context.extra.get("real_damage", 0) or 0)
        if real_damage <= 0:
            return logs

        old_text = self.get_current_intent().to_text()
        old_key = _action_key_from_intent(self.get_current_intent())

        self._locked_intent = None

        saved_last = self._last_action_key
        self._last_action_key = old_key
        self._locked_intent = self._choose_from_pool(first_turn=False)
        self._last_action_key = saved_last

        new_text = self._locked_intent.to_text()

        logs.append("{} 的扭动触发：意图由【{}】变为【{}】。".format(
            self.name,
            old_text,
            new_text
        ))
        return logs
def create_writhing_mass():
    return WrithingMassEnemy()


SPIRE_GROWTH_A = EnemyIntent(kind="attack", value=16, attack_type="blunt")
SPIRE_GROWTH_A._action_key = "a"
SPIRE_GROWTH_B = EnemyIntent(kind="attack", value=22, attack_type="blunt")
SPIRE_GROWTH_B._action_key = "b"
SPIRE_GROWTH_C = EnemyIntent(kind="status", target="player", status="constricted", value=10)
SPIRE_GROWTH_C._action_key = "c"
class SpireGrowthEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.spire_growth",
            name="塔内增生组织",
            max_hp=170,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self._history = []

    def _player_has_constricted(self):
        game_state = getattr(self, "_current_game_state", None)
        player = getattr(game_state, "player", None)

        if player is None:
            return False

        return int(player.get_status_value("constricted")) > 0

    def _would_make_three_attacks(self, key):
        if key not in ("a", "b"):
            return False

        return (
            len(self._history) >= 2
            and self._history[-1] in ("a", "b")
            and self._history[-2] in ("a", "b")
        )

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent

        # 按当前描述：未缠绕时 a/c 各半；已缠绕时 a/c = 60/40。
        # b 动作已定义，但暂不进入随机池。
        if not self._player_has_constricted():
            pool = [(SPIRE_GROWTH_A, 1), (SPIRE_GROWTH_C, 1)]
        else:
            pool = [(SPIRE_GROWTH_A, 6), (SPIRE_GROWTH_B, 4)]

        filtered = [
            (intent, weight)
            for intent, weight in pool
            if not self._would_make_three_attacks(_action_key_from_intent(intent))
        ]

        self._locked_intent = _weighted_choice(filtered or pool)
        return self._locked_intent

    def advance_intent(self):
        self._history.append(_action_key_from_intent(self.get_current_intent()))

        if len(self._history) > 3:
            self._history = self._history[-3:]

        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def on_event(self, event_name, context):
        if context is not None:
            setattr(self, "_current_game_state", context.game_state)
        return []
def create_spire_growth():
    return SpireGrowthEnemy()


SPIKER_A = EnemyIntent(kind="attack", value=7, attack_type="piercing")
SPIKER_A._action_key = "a"
SPIKER_B = EnemyIntent(kind="status", target="self", status="thorns", value=2)
SPIKER_B._action_key = "b"
class SpikerEnemy(PatternEnemy):
    def __init__(self, max_hp=None):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.spiker",
            name="钉刺机",
            max_hp=max_hp if max_hp is not None else random.randint(42, 56),
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self.gain_status("thorns", 3)
        self._last_action_key = ""
        self._buff_count = 0

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent

        can_b = self._buff_count < 6

        if not can_b:
            self._locked_intent = SPIKER_A
        elif self._last_action_key == "a":
            self._locked_intent = SPIKER_B
        else:
            self._locked_intent = random.choice([SPIKER_A, SPIKER_B])

        return self._locked_intent

    def advance_intent(self):
        key = _action_key_from_intent(self.get_current_intent())
        self._last_action_key = key

        if key == "b":
            self._buff_count += 1

        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)
def create_spiker():
    return SpikerEnemy()
class ExploderEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.exploder",
            name="爆炸机",
            max_hp=30,
            intent_cycle=[
                EnemyIntent(kind="attack", value=9, attack_type="blunt"),
                EnemyIntent(kind="attack", value=9, attack_type="blunt"),
                EnemyIntent(kind="attack", value=30, attack_type="blunt"),
            ],
        )
        self.gain_status("self_destruct", 3)
        self._explode_this_action = False

    def advance_intent(self):
        self._intent_index += 1
        self._locked_intent = None

        left = max(0, 3 - self._intent_index)
        self.statuses.set("self_destruct", left)

        if self._intent_index >= 3:
            self._intent_index = 2

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]

        self._explode_this_action = (self._intent_index >= 2)

        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def after_enemy_action(self, game_state):
        if not self._explode_this_action:
            return []

        self._explode_this_action = False
        self.hp = 0
        self.block = 0

        return ["{} 自爆后死亡。".format(self.name)]
def create_exploder():
    return ExploderEnemy()
REPULSOR_A = EnemyIntent(kind="attack", value=11, attack_type="blunt")
REPULSOR_A._action_key = "a"
REPULSOR_B = EnemyIntent(kind="add_card_to_draw", card_id="card.status.dazed", count=2)
REPULSOR_B._action_key = "b"
class RepulsorEnemy(PatternEnemy):
    def __init__(self, max_hp=None):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.repulsor",
            name="反冲机",
            max_hp=max_hp if max_hp is not None else random.randint(29, 35),
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self._last_action_key = ""

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent

        if self._last_action_key == "a":
            self._locked_intent = REPULSOR_B
        else:
            self._locked_intent = _weighted_choice([
                (REPULSOR_A, 20),
                (REPULSOR_B, 80),
            ])

        return self._locked_intent

    def advance_intent(self):
        self._last_action_key = _action_key_from_intent(self.get_current_intent())
        self._locked_intent = None

    def act(self):
        intent = self.get_current_intent()
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)
def create_repulsor():
    return RepulsorEnemy()


GIANT_HEAD_A = EnemyIntent(kind="attack", value=13, attack_type="blunt")
GIANT_HEAD_A._action_key = "a"
GIANT_HEAD_B = EnemyIntent(kind="status", target="player", status="weak", value=1)
GIANT_HEAD_B._action_key = "b"
class GiantHeadEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.giant_head",
            name="大脑袋",
            max_hp=500,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self.gain_status("slow", 1)
        self._giant_head_countdown = 5
        self._time_for_it_count = 0
        self._last_action_key = ""

    def _build_c(self):
        intent = EnemyIntent(kind="attack", value=30 + 5 * self._time_for_it_count, attack_type="blunt")
        intent._action_key = "c"
        return intent

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent

        game_state = getattr(self, "_current_game_state", None)
        turn_count = int(getattr(game_state, "turn_count", 1) or 1)

        if turn_count <= 4:
            self._locked_intent = random.choice([GIANT_HEAD_A, GIANT_HEAD_B])
        else:
            self._locked_intent = self._build_c()
        return self._locked_intent

    def act(self):
        intent = self.get_current_intent()
        logs = []
        if self._giant_head_countdown > 0:
            logs.append("{}：「{}……」".format(self.name, self._giant_head_countdown))
            self._giant_head_countdown -= 1
        if _action_key_from_intent(intent) == "c":
            logs.append("{}：「是时候了。」".format(self.name))
            self._time_for_it_count += 1
        logs.append("{} 准备执行：{}。".format(self.name, intent.to_text()))
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def advance_intent(self):
        self._last_action_key = _action_key_from_intent(self.get_current_intent())
        self._locked_intent = None
def create_giant_head():
    return GiantHeadEnemy()

REPTOMANCER_A = EnemyIntent(kind="summon_fixed_enemies", actions=["enemy.dagger"], count=1, message="召唤 1 把匕首")
REPTOMANCER_A._action_key = "a"
REPTOMANCER_B = EnemyIntent(kind="attack", value=30, attack_type="blunt")
REPTOMANCER_B._action_key = "b"
REPTOMANCER_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=13, repeat=2, attack_type="blunt"),
        EnemyIntent(kind="status", target="player", status="weak", value=1),
    ],
)
REPTOMANCER_C._action_key = "c"
class ReptomancerEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.reptomancer",
            name="拜蛇术士",
            max_hp=random.randint(180, 190),
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self._history = []

    def _dagger_count(self):
        game_state = getattr(self, "_current_game_state", None)
        return sum(
            1 for enemy in getattr(game_state, "enemies", []) or []
            if enemy.is_alive() and getattr(enemy, "enemy_id", "") == "enemy.dagger"
        )

    def _choose_key(self):
        if not self._history:
            return "a"

        weights = {"a": 1, "b": 1, "c": 1}
        if self._dagger_count() >= 4:
            weights["c"] += weights["a"]
            weights["a"] = 0

        candidates = []
        for key, weight in weights.items():
            if weight <= 0:
                continue
            if key in ("b", "c") and self._history and self._history[-1] == key:
                continue
            if key == "a" and len(self._history) >= 2 and self._history[-2:] == ["a", "a"]:
                continue
            candidates.append((key, weight))

        if not candidates:
            candidates = [("a", 1), ("b", 1), ("c", 1)]

        return _weighted_choice(candidates)

    def _intent_by_key(self, key):
        if key == "a":
            return REPTOMANCER_A
        if key == "b":
            return REPTOMANCER_B
        return REPTOMANCER_C

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_reptomancer_key = self._choose_key()
            self._locked_intent = self._intent_by_key(self._locked_reptomancer_key)
        return self._locked_intent

    def advance_intent(self):
        key = getattr(self, "_locked_reptomancer_key", "")
        if key:
            self._history.append(key)
            self._history = self._history[-3:]
        self._locked_reptomancer_key = ""
        self._locked_intent = None
def create_reptomancer():
    return ReptomancerEnemy()

DAGGER_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=9, attack_type="piercing"),
        EnemyIntent(kind="add_card_to_discard", card_id="card.status.wound", count=1),
    ],
)
DAGGER_B = EnemyIntent(kind="attack", value=25, attack_type="piercing")
class DaggerEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.dagger",
            name="匕首",
            max_hp=random.randint(20, 25),
            intent_cycle=[DAGGER_A, DAGGER_B],
        )
        self.is_minion = True
        self._die_after_action = False

    def act(self):
        intent = self.get_current_intent()
        self._die_after_action = (self._intent_index == 1)
        logs = ["{} 准备执行：{}。".format(self.name, intent.to_text())]
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def after_enemy_action(self, game_state):
        if not self._die_after_action:
            return []
        self._die_after_action = False
        if self.is_alive():
            self.hp = 0
            self.block = 0
            return ["{} 使用致命攻击后死亡。".format(self.name)]
        return []
def create_dagger():
    return DaggerEnemy()

NEMESIS_A = EnemyIntent(kind="add_card_to_discard", card_id="card.status.burn_i", count=3)
NEMESIS_A._action_key = "a"
NEMESIS_B = EnemyIntent(kind="attack", value=6, repeat=3, attack_type="blunt")
NEMESIS_B._action_key = "b"
NEMESIS_C = EnemyIntent(kind="attack", value=45, attack_type="blunt")
NEMESIS_C._action_key = "c"
class NemesisEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.nemesis",
            name="天罚",
            max_hp=185,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self._history = []

    def _choose_key(self):
        if not self._history:
            weighted = [("a", 1), ("b", 1)]
        else:
            weighted = [("a", 35), ("b", 35), ("c", 30)]

        candidates = []
        for key, weight in weighted:
            if key == "b" and len(self._history) >= 2 and self._history[-2:] == ["b", "b"]:
                continue
            if key == "c" and self._history and self._history[-1] == "c":
                continue
            candidates.append((key, weight))

        return _weighted_choice(candidates or weighted)

    def _intent_by_key(self, key):
        if key == "a":
            return NEMESIS_A
        if key == "b":
            return NEMESIS_B
        return NEMESIS_C

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_nemesis_key = self._choose_key()
            self._locked_intent = self._intent_by_key(self._locked_nemesis_key)
        return self._locked_intent

    def advance_intent(self):
        key = getattr(self, "_locked_nemesis_key", "")
        if key:
            self._history.append(key)
            self._history = self._history[-3:]
        self._locked_nemesis_key = ""
        self._locked_intent = None

    def on_event(self, event_name, context):
        if context is not None:
            setattr(self, "_current_game_state", context.game_state)
        if event_name == "turn_start" and context is not None:
            turn_count = int(getattr(context.game_state, "turn_count", 1) or 1)
            if turn_count % 2 == 0 and self.is_alive():
                current = self.gain_status("intangible", 1)
                return ["{} 在偶数回合获得 1 层无实体。当前无实体：{}。".format(self.name, current)]
        return []
def create_nemesis():
    return NemesisEnemy()

DECA_A = EnemyIntent(kind="wait", message="所有敌人获得 16 点格挡")
DECA_A._action_key = "a"
DECA_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=10, repeat=2, attack_type="blunt"),
        EnemyIntent(kind="add_card_to_discard", card_id="card.status.dazed", count=2),
    ],
)
DECA_B._action_key = "b"
class DecaEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.deca",
            name="八体",
            max_hp=250,
            intent_cycle=[DECA_A, DECA_B],
        )
        self.gain_status("artifact", 2)

    def _intent_to_action(self, intent):
        if intent is DECA_A:
            return {
                "op": "enemy_all_gain_block",
                "source_enemy_id": self.enemy_id,
                "source_enemy_name": self.name,
                "block": 16,
                "message": intent.message,
            }
        return super(DecaEnemy, self)._intent_to_action(intent)
def create_deca():
    return DecaEnemy()

DONU_A = EnemyIntent(kind="status_all_allies", target="self", status="strength", value=3)
DONU_A._action_key = "a"
DONU_B = EnemyIntent(kind="attack", value=10, repeat=2, attack_type="blunt")
DONU_B._action_key = "b"
class DonuEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.donu",
            name="甜圈",
            max_hp=250,
            intent_cycle=[DONU_A, DONU_B],
        )
        self.gain_status("artifact", 2)
def create_donu():
    return DonuEnemy()

AWAKENED_ONE_UNAWAKENED_A = EnemyIntent(kind="attack", value=20, attack_type="slash")
AWAKENED_ONE_UNAWAKENED_A._action_key = "ua"
AWAKENED_ONE_UNAWAKENED_B = EnemyIntent(kind="attack", value=6, repeat=4, attack_type="slash")
AWAKENED_ONE_UNAWAKENED_B._action_key = "ub"
AWAKENED_ONE_AWAKENED_A = EnemyIntent(kind="attack", value=40, attack_type="slash")
AWAKENED_ONE_AWAKENED_A._action_key = "aa"
AWAKENED_ONE_AWAKENED_B = EnemyIntent(kind="attack", value=10, repeat=3, attack_type="slash")
AWAKENED_ONE_AWAKENED_B._action_key = "ab"
AWAKENED_ONE_AWAKENED_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=18, attack_type="slash"),
        EnemyIntent(kind="add_card_to_draw", card_id="card.status.void", count=1),
    ],
)
AWAKENED_ONE_AWAKENED_C._action_key = "ac"
AWAKENED_ONE_WAIT = EnemyIntent(kind="wait", message="正在觉醒，无法被攻击")
class AwakenedOneEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.awakened_one",
            name="觉醒者",
            max_hp=300,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self.gain_status("regeneration", 10)
        self.gain_status("curious", 1)
        self._awakened_phase = False
        self._rebirthing = False
        self._first_death_used = False
        self._history = []
        self._force_opening_awakened_attack = False

    def _choose_unawakened_key(self):
        if not self._history:
            return "ua"
        return _weighted_choice([("ua", 75), ("ub", 25)])

    def _choose_awakened_key(self):
        if self._force_opening_awakened_attack:
            return "aa"
        candidates = []
        if not (len(self._history) >= 2 and self._history[-2:] == ["ab", "ab"]):
            candidates.append(("ab", 50))
        candidates.append(("ac", 50))
        return _weighted_choice(candidates)

    def _intent_by_key(self, key):
        if key == "ua":
            return AWAKENED_ONE_UNAWAKENED_A
        if key == "ub":
            return AWAKENED_ONE_UNAWAKENED_B
        if key == "aa":
            return AWAKENED_ONE_AWAKENED_A
        if key == "ab":
            return AWAKENED_ONE_AWAKENED_B
        if key == "ac":
            return AWAKENED_ONE_AWAKENED_C
        return AWAKENED_ONE_WAIT

    def get_current_intent(self):
        if self._rebirthing:
            return AWAKENED_ONE_WAIT
        if self._locked_intent is None:
            if self._awakened_phase:
                self._locked_awakened_key = self._choose_awakened_key()
            else:
                self._locked_awakened_key = self._choose_unawakened_key()
            self._locked_intent = self._intent_by_key(self._locked_awakened_key)
        return self._locked_intent

    def advance_intent(self):
        key = getattr(self, "_locked_awakened_key", "")
        if key:
            self._history.append(key)
            self._history = self._history[-3:]
        if key == "aa":
            self._force_opening_awakened_attack = False
        self._locked_awakened_key = ""
        self._locked_intent = None

    def act(self):
        if self._rebirthing:
            return EnemyActionResult(
                action={"op": "enemy_wait", "source_enemy_id": self.enemy_id, "source_enemy_name": self.name},
                logs=["{} 正在觉醒。".format(self.name)]
            )
        return super(AwakenedOneEnemy, self).act()

    def _clear_awakened_negative_statuses(self):
        removed = []
        from game.status.status_defs import get_status_def, get_status_name
        active = list(getattr(self.statuses, "values", {}).items())
        for status_key, value in active:
            status_def = get_status_def(status_key)
            category = getattr(status_def, "category", "") if status_def is not None else ""
            should_remove = category == "debuff"
            if status_key in ("strength", "dexterity") and int(value) < 0:
                should_remove = True
            if status_key == "curious":
                should_remove = True
            if should_remove:
                self.statuses.remove(status_key)
                removed.append(get_status_name(status_key))
        return removed

    def on_event(self, event_name, context):
        logs = []
        if context is not None:
            setattr(self, "_current_game_state", context.game_state)

        if event_name == "damage_after" and context is not None:
            if context.target is not self:
                return logs
            if not context.extra.get("target_is_dead_after", False):
                return logs
            if self._first_death_used:
                return logs

            self._first_death_used = True
            self._rebirthing = True
            self.hp = 1
            self.block = 0
            self._locked_intent = None
            setattr(self, "_unselectable", True)
            context.extra["suppress_death_message"] = True

            removed = self._clear_awakened_negative_statuses()
            if removed:
                logs.append("{} 移除了负面状态：{}。".format(self.name, "、".join(removed)))
            logs.append("{} 第一次死亡，开始觉醒；它暂时无法被攻击。".format(self.name))
            return logs

        if event_name == "turn_start" and self._rebirthing:
            self._rebirthing = False
            self._awakened_phase = True
            self._force_opening_awakened_attack = True
            self.hp = self.max_hp
            self.block = 0
            setattr(self, "_unselectable", False)
            self._history = []
            self._locked_intent = None
            logs.append("{} 完成觉醒，HP 恢复至 {}/{}。".format(self.name, self.hp, self.max_hp))
            return logs

        if event_name == "damage_after" and context is not None:
            pass
        return logs

    def status_text(self, game_state=None):
        if self._rebirthing:
            return "{} HP：{}/{}；格挡：{}；意图：正在觉醒，无法被攻击；状态：{}".format(
                self.name, self.hp, self.max_hp, self.block, self.statuses.to_text() if hasattr(self.statuses, "to_text") else "觉醒中"
            )
        return super(AwakenedOneEnemy, self).status_text(game_state)
def create_awakened_one():
    return AwakenedOneEnemy()

TIME_EATER_A = EnemyIntent(kind="attack", value=7, repeat=3, attack_type="blunt")
TIME_EATER_A._action_key = "a"
TIME_EATER_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=26, attack_type="blunt"),
        EnemyIntent(kind="status", target="player", status="draw_reduction", value=2),
    ],
)
TIME_EATER_B._action_key = "b"
TIME_EATER_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="block", value=20),
        EnemyIntent(kind="status", target="player", status="vulnerable", value=1),
        EnemyIntent(kind="status", target="player", status="weak", value=1),
    ],
)
TIME_EATER_C._action_key = "c"
TIME_EATER_D = EnemyIntent(kind="wait", message="恢复至 50% 生命值，移除所有减益")
TIME_EATER_D._action_key = "d"
class TimeEaterEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.time_eater",
            name="时间吞噬者",
            max_hp=456,
            intent_cycle=[EnemyIntent(kind="wait")],
        )
        self.gain_status("time_warp", 12)
        self._history = []
        self._healed_once = False
        self._force_heal = False

    def on_event(self, event_name, context):
        if context is not None:
            setattr(self, "_current_game_state", context.game_state)
        if event_name == "battle_start":
            return ["{}：「啊，居然有人来了。」".format(self.name)]
        if event_name == "damage_after" and context is not None:
            if context.target is self and self.is_alive() and not self._healed_once:
                if self.hp < (self.max_hp + 1) // 2:
                    self._force_heal = True
                    self._locked_intent = None
        return []

    def _choose_key(self):
        if self._force_heal and not self._healed_once:
            return "d"
        weighted = [("c", 20), ("a", 45), ("b", 35)]
        candidates = []
        for key, weight in weighted:
            if key == "a" and len(self._history) >= 2 and self._history[-2:] == ["a", "a"]:
                continue
            if key in ("b", "c") and self._history and self._history[-1] == key:
                continue
            candidates.append((key, weight))
        return _weighted_choice(candidates or weighted)

    def _intent_by_key(self, key):
        if key == "a":
            return TIME_EATER_A
        if key == "b":
            return TIME_EATER_B
        if key == "c":
            return TIME_EATER_C
        return TIME_EATER_D

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_time_eater_key = self._choose_key()
            self._locked_intent = self._intent_by_key(self._locked_time_eater_key)
        return self._locked_intent

    def _intent_to_action(self, intent):
        if intent is TIME_EATER_D:
            return {"op": "enemy_time_eater_heal", "source_enemy_id": self.enemy_id, "source_enemy_name": self.name, "message": intent.message}
        return super(TimeEaterEnemy, self)._intent_to_action(intent)

    def advance_intent(self):
        key = getattr(self, "_locked_time_eater_key", "")
        if key:
            self._history.append(key)
            self._history = self._history[-3:]
        if key == "d":
            self._healed_once = True
            self._force_heal = False
        self._locked_time_eater_key = ""
        self._locked_intent = None
def create_time_eater():
    return TimeEaterEnemy()
