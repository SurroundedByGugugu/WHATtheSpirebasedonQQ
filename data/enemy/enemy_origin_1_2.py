# -*- coding: utf-8 -*-
# enemy_origin_1_1表示来自原作1中1层怪物

from data.enemy.base_enemy import EnemyActionResult, EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy
import random
from game.constants import EVENT_DAMAGE_AFTER, EVENT_BATTLE_START

BYRD_A = EnemyIntent(
    kind="status",
    target="self",
    status="strength",
    value=1,
)
BYRD_B = EnemyIntent(
    kind="attack",
    value=1,
    repeat=5,
)
BYRD_C = EnemyIntent(
    kind="attack",
    value=12,
)
BYRD_STUN = EnemyIntent(
    kind="wait",
    message="坠落眩晕",
)
BYRD_FALL_ATTACK = EnemyIntent(
    kind="attack",
    value=3,
)
BYRD_RECOVER = EnemyIntent(
    kind="status",
    target="self",
    status="flying",
    value=3,
    message="重新起飞",
)
class ByrdEnemy(PatternEnemy):
    """
    异鸟 Byrd。

    飞行模式：
    - 初始 3 层飞行。
    - 飞行使受到的攻击伤害减半，层数在整张牌多段伤害结束后再扣。
    - 飞行被打破后，立即打断当前意图并进入坠落流程。

    坠落流程：
    1. 第一回合眩晕，不行动。
    2. 第二回合造成 3 点伤害。
    3. 第三回合获得 3 层飞行并返回飞行模式。
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.byrd",
            name="异鸟",
            max_hp=random.randint(25, 31),
            intent_cycle=[BYRD_B],
        )
        self._byrd_mode = "flying"
        self._byrd_ground_stage = 0
        self._byrd_history = []
        self._byrd_first_choice = True
        self._flying_max_hits = 3
        self.statuses.set("flying", 3)

    def _intent_key(self, intent):
        if intent is BYRD_A:
            return "a"
        if intent is BYRD_B:
            return "b"
        if intent is BYRD_C:
            return "c"
        return ""

    def _choose_flying_intent(self):
        if self._byrd_first_choice:
            weighted = [
                (32.5, "a", BYRD_A),
                (62.5, "b", BYRD_B),
            ]
        else:
            weighted = [
                (30, "a", BYRD_A),
                (50, "b", BYRD_B),
                (20, "c", BYRD_C),
            ]

        history = self._byrd_history
        candidates = []
        for weight, key, intent in weighted:
            if key == "a" and len(history) >= 1 and history[-1] == "a":
                continue
            if key == "b" and len(history) >= 2 and history[-2:] == ["b", "b"]:
                continue
            if key == "c" and len(history) >= 1 and history[-1] == "c":
                continue
            candidates.append((weight, key, intent))

        if not candidates:
            candidates = weighted

        choices = [item[2] for item in candidates]
        weights = [item[0] for item in candidates]
        return random.choices(choices, weights=weights, k=1)[0]

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent

        if self._byrd_mode == "grounded":
            if self._byrd_ground_stage == 0:
                self._locked_intent = BYRD_STUN
            elif self._byrd_ground_stage == 1:
                self._locked_intent = BYRD_FALL_ATTACK
            else:
                self._locked_intent = BYRD_RECOVER
            return self._locked_intent

        self._locked_intent = self._choose_flying_intent()
        return self._locked_intent

    def advance_intent(self):
        if self._byrd_mode == "grounded":
            if self._byrd_ground_stage == 0:
                self._byrd_ground_stage = 1
            elif self._byrd_ground_stage == 1:
                self._byrd_ground_stage = 2
            else:
                self._byrd_mode = "flying"
                self._byrd_ground_stage = 0
                self._byrd_history = []
            self._locked_intent = None
            return

        key = self._intent_key(self._locked_intent)
        if key:
            self._byrd_history.append(key)
            self._byrd_history = self._byrd_history[-3:]
        self._byrd_first_choice = False
        self._locked_intent = None

    def on_flying_broken(self, game_state, card=None):
        logs = []
        if not self.is_alive():
            return logs
        if self._byrd_mode != "flying":
            return logs
        self._byrd_mode = "grounded"
        self._byrd_ground_stage = 0
        self._byrd_history = []
        self._byrd_first_choice = False
        self._locked_intent = BYRD_STUN
        logs.append("{} 坠落，当前意图被打断。".format(self.name))
        return logs
def create_byrd():
    return ByrdEnemy()

SNECKO_A = EnemyIntent(
    kind="status",
    target="player",
    status="confusion",
    value=1,
)
SNECKO_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=8),
        EnemyIntent(
            kind="status",
            target="player",
            status="vulnerable",
            value=2,
        ),
    ]
)
SNECKO_C = EnemyIntent(
    kind="attack",
    value=15,
)
class SneckoEnemy(PatternEnemy):
    """
    异蛇 Snecko。

    a：施加 1 层混乱。首回合必定使用，每场战斗只使用一次。
    b：造成 8 点伤害，施加 2 层易伤。
    c：造成 15 点伤害，不能连续使用 3 次。

    b/c 概率：
    - 默认 b : c = 55 : 45。
    - 如果前两次都是 c，则强制 b。
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.snecko",
            name="异蛇",
            max_hp=random.randint(114, 120),
            intent_cycle=[SNECKO_A],
        )
        self._snecko_first_turn = True
        self._snecko_history = []
        self._locked_snecko_key = None

    def _choose_snecko_key(self):
        # 首回合必定混乱，并且 a 每场战斗只使用一次。
        if self._snecko_first_turn:
            return "a"

        # c 不能连续使用 3 次。
        if len(self._snecko_history) >= 2 and self._snecko_history[-2:] == ["c", "c"]:
            return "b"

        return random.choices(
            ["b", "c"],
            weights=[55, 45],
            k=1
        )[0]

    def _intent_by_key(self, key):
        if key == "a":
            return SNECKO_A
        if key == "b":
            return SNECKO_B
        return SNECKO_C

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_snecko_key = self._choose_snecko_key()
            self._locked_intent = self._intent_by_key(self._locked_snecko_key)
        return self._locked_intent

    def advance_intent(self):
        key = self._locked_snecko_key

        if key:
            self._snecko_history.append(key)
            self._snecko_history = self._snecko_history[-3:]

        if key == "a":
            self._snecko_first_turn = False

        self._locked_snecko_key = None
        self._locked_intent = None
def create_snecko():
    return SneckoEnemy()

SHELLED_PARASITE_PLATED_ARMOR = 14
SHELLED_PARASITE_A = EnemyIntent(
    kind="attack",
    value=6,
    repeat=2,
)
SHELLED_PARASITE_B = EnemyIntent(
    kind="attack",
    value=10,
    heal_unblocked=True,
)
SHELLED_PARASITE_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=18),
        EnemyIntent(
            kind="status",
            target="player",
            status="frail",
            value=2,
        ),
    ],
)
SHELLED_PARASITE_STUN = EnemyIntent(
    kind="wait",
    message="护甲破裂，陷入眩晕",
)
class ShelledParasiteEnemy(PatternEnemy):
    """
    带壳寄生怪 Shelled Parasite。

    a：造成 6 点伤害 2 次。
       第一回合 50%，其他回合 40%，不能连续使用 3 次。

    b：造成 10 点伤害，回复与未被格挡伤害相等的生命。
       第一回合 50%，其他回合 40%，不能连续使用 3 次。

    c：造成 18 点伤害，给予 2 层脆弱。
       第一回合 0%，其他回合 20%，不能连续使用 2 次。

    初始拥有多层护甲。多层护甲被全部击破时，获得 1 层眩晕并打断当前意图。
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.shelled_parasite",
            name="带壳寄生怪",
            max_hp=random.randint(68, 72),
            intent_cycle=[SHELLED_PARASITE_A],
        )
        self.statuses.set("plated_armor", SHELLED_PARASITE_PLATED_ARMOR)
        self._parasite_first_turn = True
        self._parasite_history = []
        self._locked_parasite_key = None
        self._parasite_force_stun_intent = False

    def _choose_parasite_key(self):
        if self._parasite_first_turn:
            weighted = [
                (50, "a"),
                (50, "b"),
            ]
        else:
            weighted = [
                (40, "a"),
                (40, "b"),
                (20, "c"),
            ]

        history = self._parasite_history
        candidates = []

        for weight, key in weighted:
            # a 不能连续使用三次
            if key == "a" and len(history) >= 2 and history[-2:] == ["a", "a"]:
                continue
            # b 不能连续使用三次
            if key == "b" and len(history) >= 2 and history[-2:] == ["b", "b"]:
                continue
            # c 不能连续使用两次
            if key == "c" and len(history) >= 1 and history[-1] == "c":
                continue
            candidates.append((weight, key))

        if not candidates:
            candidates = weighted

        keys = [item[1] for item in candidates]
        weights = [item[0] for item in candidates]
        return random.choices(keys, weights=weights, k=1)[0]

    def _intent_by_key(self, key):
        if key == "a":
            return SHELLED_PARASITE_A
        if key == "b":
            return SHELLED_PARASITE_B
        if key == "c":
            return SHELLED_PARASITE_C
        return SHELLED_PARASITE_A

    def get_current_intent(self):
        # 只用于显示：被眩晕时显示眩晕，不提前选择下一次攻击意图。
        if self.get_status_value("stun") > 0 or self._parasite_force_stun_intent:
            return SHELLED_PARASITE_STUN
        if self._locked_intent is None:
            self._locked_parasite_key = self._choose_parasite_key()
            self._locked_intent = self._intent_by_key(self._locked_parasite_key)
        return self._locked_intent

    def advance_intent(self):
        key = self._locked_parasite_key
        if key:
            self._parasite_history.append(key)
            self._parasite_history = self._parasite_history[-3:]
        self._parasite_first_turn = False
        self._locked_parasite_key = None
        self._locked_intent = None

    def on_plated_armor_broken(self, game_state):
        logs = []
        if not self.is_alive():
            return logs
        # 多层护甲只在第一次归零时触发。由于状态归零后会被移除，通常不会重复进来。
        current_stun = max(1, self.get_status_value("stun"))
        self.statuses.set("stun", current_stun)
        # 打断当前意图：清掉已经锁定的意图。
        self._locked_parasite_key = None
        self._locked_intent = None
        self._parasite_force_stun_intent = True
        logs.append("{} 的壳被击碎，陷入眩晕，当前意图被打断。".format(self.name))
        return logs
    def act(self):
        # 如果 stun 被 engine.py 消耗了，act 正常不会被调用。
        # 这里保留兜底，避免特殊调用路径下卡住。
        if self.get_status_value("stun") > 0:
            self._parasite_force_stun_intent = True
            return super(ShelledParasiteEnemy, self).act()
        self._parasite_force_stun_intent = False
        return super(ShelledParasiteEnemy, self).act()
def create_shelled_parasite():
    return ShelledParasiteEnemy()

SPHERIC_GUARDIAN_A = EnemyIntent(
    kind="block",
    value=25,
)
SPHERIC_GUARDIAN_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=10),
        EnemyIntent(
            kind="status",
            target="player",
            status="frail",
            value=5,
        ),
    ],
)
SPHERIC_GUARDIAN_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=10),
        EnemyIntent(kind="block", value=15),
    ],
)
SPHERIC_GUARDIAN_D = EnemyIntent(
    kind="attack",
    value=10,
    repeat=2,
)
class SphericGuardianEnemy(PatternEnemy):
    """
    圆球守护者 Spheric Guardian。

    战斗开始时：
    - 40 点格挡
    - 3 层人工制品
    - 1 层壁垒
    行动固定：
    a：获得 25 点格挡
    b：造成 10 点伤害，施加 5 层脆弱
    c：造成 10 点伤害，获得 15 点格挡
    d：造成 10 点伤害 2 次

    意图循环：
    a -> b -> c -> d -> c -> d -> ...
    """
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.spheric_guardian",
            name="圆球守护者",
            max_hp=20,
            intent_cycle=[
                SPHERIC_GUARDIAN_A,
                SPHERIC_GUARDIAN_B,
                SPHERIC_GUARDIAN_C,
                SPHERIC_GUARDIAN_D,
            ],
            loop_start_index=2,
        )
        self.block = 40
        self.statuses.set("artifact", 3)
        self.statuses.set("barricade", 1)
def create_spheric_guardian():
    return SphericGuardianEnemy()

CHOSEN_A = EnemyIntent(
    kind="status",
    target="player",
    status="hex",
    value=1,
    message="挣扎吧…",
)
CHOSEN_B = EnemyIntent(
    kind="attack",
    value=5,
    repeat=2,
)
CHOSEN_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=10),
        EnemyIntent(
            kind="status",
            target="player",
            status="vulnerable",
            value=2,
        ),
    ],
)
CHOSEN_D = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="status",
            target="player",
            status="weak",
            value=3,
        ),
        EnemyIntent(
            kind="status",
            target="self",
            status="strength",
            value=3,
        ),
    ],
)
CHOSEN_E = EnemyIntent(
    kind="attack",
    value=18,
)
class ChosenEnemy(PatternEnemy):
    """
    被拣选者 Chosen。

    a：给予玩家 1 层邪咒。台词：“挣扎吧…”
    b：造成 5 点伤害 2 次
    c：造成 10 点伤害，给予玩家 2 层易伤
    d：给予玩家 3 层虚弱，自身获得 3 点力量
    e：造成 18 点伤害

    行动逻辑：
    - 第 1 回合：b
    - 第 2 回合：a
    - 后续：
      - a / b / e 后：c / d 对半
      - c / d 后：40% e，60% b
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.chosen",
            name="被拣选者",
            max_hp=random.randint(95, 99),
            intent_cycle=[CHOSEN_B],
        )
        self._chosen_action_count = 0
        self._chosen_last_key = None
        self._locked_chosen_key = None

    def _intent_by_key(self, key):
        if key == "a":
            return CHOSEN_A
        if key == "b":
            return CHOSEN_B
        if key == "c":
            return CHOSEN_C
        if key == "d":
            return CHOSEN_D
        if key == "e":
            return CHOSEN_E
        return CHOSEN_B

    def _choose_chosen_key(self):
        # 第一回合固定 b
        if self._chosen_action_count == 0:
            return "b"
        # 第二回合固定 a
        if self._chosen_action_count == 1:
            return "a"
        last = self._chosen_last_key
        # a / b / e 后：c / d 对半
        if last in ("a", "b", "e"):
            return random.choice(["c", "d"])
        # c / d 后：40% e，60% b
        if last in ("c", "d"):
            return random.choices(
                ["e", "b"],
                weights=[40, 60],
                k=1
            )[0]

        return "b"

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_chosen_key = self._choose_chosen_key()
            self._locked_intent = self._intent_by_key(self._locked_chosen_key)
        return self._locked_intent

    def advance_intent(self):
        key = self._locked_chosen_key
        if key:
            self._chosen_last_key = key
        self._chosen_action_count += 1
        self._locked_chosen_key = None
        self._locked_intent = None
def create_chosen():
    return ChosenEnemy()

SNAKE_PLANT_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="status",
            target="player",
            status="weak",
            value=2,
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="frail",
            value=2,
        ),
    ],
)
SNAKE_PLANT_B = EnemyIntent(
    kind="attack",
    value=7,
    repeat=3,
)
class SnakePlantEnemy(PatternEnemy):
    """
    蛇花 Snake Plant。

    开局自带柔韧 3：
    - 受到攻击时获得 X 点格挡。
    - 每触发一次，下一次获得的格挡值 +1。
    - 玩家回合开始时重置回 X。

    a：给予玩家 2 层虚弱和 2 层脆弱
    b：造成 7 点伤害 3 次

    行动逻辑：
    - a 后：必定 b
    - 连续 b b 后：必定 a
    - 其他：35% a，65% b
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.snake_plant",
            name="蛇花",
            max_hp=random.randint(75, 79),
            intent_cycle=[SNAKE_PLANT_B],
        )
        self.statuses.set("malleable", 3)
        self._malleable_current_block = 3

        self._snake_plant_history = []
        self._locked_snake_plant_key = None

    def _intent_by_key(self, key):
        if key == "a":
            return SNAKE_PLANT_A
        if key == "b":
            return SNAKE_PLANT_B
        return SNAKE_PLANT_B

    def _choose_snake_plant_key(self):
        history = self._snake_plant_history

        # a 后必定 b
        if len(history) >= 1 and history[-1] == "a":
            return "b"

        # 连续 b b 后必定 a
        if len(history) >= 2 and history[-2:] == ["b", "b"]:
            return "a"

        # 其他情况：35% a，65% b
        return random.choices(
            ["a", "b"],
            weights=[35, 65],
            k=1
        )[0]

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_snake_plant_key = self._choose_snake_plant_key()
            self._locked_intent = self._intent_by_key(self._locked_snake_plant_key)
        return self._locked_intent

    def advance_intent(self):
        key = self._locked_snake_plant_key

        if key:
            self._snake_plant_history.append(key)
            self._snake_plant_history = self._snake_plant_history[-3:]
        self._locked_snake_plant_key = None
        self._locked_intent = None
def create_snake_plant():
    return SnakePlantEnemy()

MYSTIC_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=8),
        EnemyIntent(
            kind="status",
            target="player",
            status="frail",
            value=2,
        ),
    ],
)
MYSTIC_B = EnemyIntent(
    kind="heal_all_allies",
    value=16,
)
MYSTIC_C = EnemyIntent(
    kind="status_all_allies",
    status="strength",
    value=2,
)
class MysticEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.mystic",
            name="神秘术士",
            max_hp=random.randint(48, 56),
            intent_cycle=[MYSTIC_A],
        )
        self._mystic_history = []
        self._locked_mystic_key = None

    def _has_badly_wounded_ally(self, game_state):
        if game_state is None:
            return False

        for target in getattr(game_state, "enemies", []) or []:
            if not target.is_alive():
                continue

            if int(getattr(target, "max_hp", 0)) - int(getattr(target, "hp", 0)) >= 16:
                return True

        return False

    def _last_two_are_not_a(self):
        if len(self._mystic_history) < 2:
            return False
        return "a" not in self._mystic_history[-2:]

    def _choose_mystic_key(self, game_state=None):
        history = self._mystic_history

        if self._last_two_are_not_a() and self._has_badly_wounded_ally(game_state):
            return "b"

        if len(history) >= 2 and history[-2:] == ["c", "c"]:
            return "a"

        if len(history) >= 2 and history[-2:] == ["a", "a"]:
            return "c"

        return random.choices(["a", "c"], weights=[40, 60], k=1)[0]

    def _intent_by_key(self, key):
        if key == "a":
            return MYSTIC_A
        if key == "b":
            return MYSTIC_B
        if key == "c":
            return MYSTIC_C
        return MYSTIC_A

    def _lock_intent_if_needed(self, game_state=None):
        if self._locked_intent is None:
            self._locked_mystic_key = self._choose_mystic_key(game_state)
            self._locked_intent = self._intent_by_key(self._locked_mystic_key)

    def get_current_intent(self):
        self._lock_intent_if_needed(getattr(self, "_current_game_state", None))
        return self._locked_intent

    def get_intent_text(self, game_state=None):
        if not self.is_alive():
            return "已经走了有一会了"

        self._lock_intent_if_needed(game_state)

        if game_state is not None:
            from game.intent_preview import format_enemy_intent_text
            return format_enemy_intent_text(game_state, self)

        return self._locked_intent.to_text()

    def act(self):
        self._lock_intent_if_needed(getattr(self, "_current_game_state", None))
        return super(MysticEnemy, self).act()

    def advance_intent(self):
        key = self._locked_mystic_key

        if key:
            self._mystic_history.append(key)
            self._mystic_history = self._mystic_history[-3:]

        self._locked_mystic_key = None
        self._locked_intent = None
def create_mystic():
    return MysticEnemy()

CENTURION_A = EnemyIntent(
    kind="attack",
    value=12,
)
CENTURION_B = EnemyIntent(
    kind="block_mystic_or_self",
    value=15,
)
CENTURION_C = EnemyIntent(
    kind="attack",
    value=6,
    repeat=3,
)
class CenturionEnemy(PatternEnemy):
    """
    百夫长 Centurion。

    a：造成 12 点伤害
    b：如果神秘术士存在，则令该神秘术士获得 15 格挡；若不存在，则自身获得 15 格挡。
    c：造成 6 点伤害 3 次

    队友存在：
    - 连续 b b 后：a
    - 连续 a a 后：b
    - 其他：35% a，65% b

    队友死亡后：
    - b 替换为 c。
    - 若本回合已经锁定为 b，但神秘术士在行动前死亡，则 b 的行动效果改为自身获得 15 格挡。
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.centurion",
            name="百夫长",
            max_hp=random.randint(76, 80),
            intent_cycle=[CENTURION_A],
        )
        self._centurion_history = []
        self._locked_centurion_key = None

    def _mystic_is_alive(self, game_state):
        if game_state is None:
            return True

        for target in getattr(game_state, "enemies", []) or []:
            if target is self:
                continue
            if not target.is_alive():
                continue
            if getattr(target, "enemy_id", "") == "enemy.mystic":
                return True

        return False

    def _choose_centurion_base_key(self):
        history = self._centurion_history

        if len(history) >= 2 and history[-2:] == ["b", "b"]:
            return "a"

        if len(history) >= 2 and history[-2:] == ["a", "a"]:
            return "b"

        return random.choices(
            ["a", "b"],
            weights=[35, 65],
            k=1
        )[0]

    def _choose_centurion_key(self, game_state=None):
        key = self._choose_centurion_base_key()

        # 新意图选择时，如果神秘术士已经死亡，则 b 替换为 c。
        if key == "b" and not self._mystic_is_alive(game_state):
            return "c"

        return key

    def _intent_by_key(self, key):
        if key == "a":
            return CENTURION_A
        if key == "b":
            return CENTURION_B
        if key == "c":
            return CENTURION_C
        return CENTURION_A

    def _lock_intent_if_needed(self, game_state=None):
        if self._locked_intent is None:
            self._locked_centurion_key = self._choose_centurion_key(game_state)
            self._locked_intent = self._intent_by_key(self._locked_centurion_key)

    def get_current_intent(self):
        self._lock_intent_if_needed(getattr(self, "_current_game_state", None))
        return self._locked_intent

    def get_intent_text(self, game_state=None):
        if not self.is_alive():
            return "已经走了有一会了"

        self._lock_intent_if_needed(game_state)

        if game_state is not None:
            from game.intent_preview import format_enemy_intent_text
            return format_enemy_intent_text(game_state, self)

        return self._locked_intent.to_text()

    def act(self):
        self._lock_intent_if_needed(getattr(self, "_current_game_state", None))
        return super(CenturionEnemy, self).act()

    def advance_intent(self):
        key = self._locked_centurion_key

        # 历史记录保留“基础行为”关系：
        # c 是神秘术士死后的 b 替换版，因此按 b 记录，方便连续 bb 后接 a。
        if key == "c":
            record_key = "b"
        else:
            record_key = key

        if record_key:
            self._centurion_history.append(record_key)
            self._centurion_history = self._centurion_history[-3:]

        self._locked_centurion_key = None
        self._locked_intent = None
def create_centurion():
    return CenturionEnemy()
