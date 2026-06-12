# -*- coding: utf-8 -*-
# enemy_origin_1_1表示来自原作1中1层怪物

from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy
import random
from game.constants import EVENT_DAMAGE_AFTER, EVENT_BATTLE_START

SPIKE_SLIME_ATTACK_AND_SLIME = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=16),
        EnemyIntent(
            kind="add_card_to_discard",
            card_id="card.status.slime_i",
            count=2,
        ),
    ]
)

SPIKE_SLIME_FRAIL = EnemyIntent(
    kind="status",
    target="player",
    status="frail",
    value=2,
)

SPIKE_SLIME_RANDOM_PATTERN = [
    (30, SPIKE_SLIME_ATTACK_AND_SLIME),
    (70, SPIKE_SLIME_FRAIL),
]

class SplittingSlimeEnemy(PatternEnemy):
    """
    尖刺史莱姆分裂基类。

    规则：
    1. 受到伤害后检测。
    2. HP > 0 且 HP <= max_hp / 2 时分裂。
    3. 分裂成 2 只下一尺寸史莱姆。
    4. 每只小史莱姆的当前 HP 和 max_hp 都设为分裂前当前 HP。
    5. small 尺寸不继承该类，因此不会分裂。
    """

    def __init__(self, enemy_id, name, max_hp, intent_cycle, split_to_enemy_id=""):
        PatternEnemy.__init__(
            self,
            enemy_id=enemy_id,
            name=name,
            max_hp=max_hp,
            intent_cycle=intent_cycle,
        )
        self.split_to_enemy_id = split_to_enemy_id
        self._has_split = False

    def should_split(self):
        if self._has_split:
            return False
        if not self.split_to_enemy_id:
            return False
        # 直接被打死时不分裂。
        if self.hp <= 0:
            return False
        return self.hp * 2 <= self.max_hp
    def make_split_child(self, hp):
        from data.enemy.AAAregistry import create_enemy
        child = create_enemy(self.split_to_enemy_id)
        # “每只都拥有当前生命值”：这里把 max_hp 也设成当前生命值，
        # 避免出现 16/12 这种当前 HP 大于最大 HP 的显示。
        child.max_hp = int(hp)
        child.hp = int(hp)
        child.block = 0

        return child
    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_DAMAGE_AFTER:
            return logs
        if context.target is not self:
            return logs
        if not self.should_split():
            return logs
        game_state = context.game_state
        split_hp = int(self.hp)
        child_a = self.make_split_child(split_hp)
        child_b = self.make_split_child(split_hp)
        try:
            index = game_state.enemies.index(self)
        except ValueError:
            return logs
        self._has_split = True
        self.hp = 0
        self.block = 0
        # 告诉 damage.py：这是分裂，不显示死亡台词。
        context.extra["suppress_death_message"] = True
        game_state.enemies[index:index + 1] = [child_a, child_b]
        logs.append("{} 的生命值降至一半以下，分裂成 2 只{}，每只 HP：{}/{}。".format(
            self.name,
            child_a.name,
            split_hp,
            split_hp,
        ))
        return logs
class SpikeSlimeSmallEnemy(PatternEnemy):
    def __init__(self, max_hp=12):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.spike_slime_small",
            name="小尖刺史莱姆",
            max_hp=max_hp,
            intent_cycle=[
                EnemyIntent(kind="attack", value=5),
            ],
        )
def create_spike_slime_large():
    return SplittingSlimeEnemy(
        enemy_id="enemy.spike_slime_large",
        name="大尖刺史莱姆",
        max_hp=random.randint(64, 70),
        intent_cycle=[
            SPIKE_SLIME_RANDOM_PATTERN,
        ],
        split_to_enemy_id="enemy.spike_slime_middle",
    )
def create_spike_slime_middle():
    return SplittingSlimeEnemy(
        enemy_id="enemy.spike_slime_middle",
        name="中尖刺史莱姆",
        max_hp=random.randint(28, 32),
        intent_cycle=[
            SPIKE_SLIME_RANDOM_PATTERN,
        ],
        split_to_enemy_id="enemy.spike_slime_small",
    )
def create_spike_slime_small():
    return SpikeSlimeSmallEnemy(max_hp=random.randint(10, 14))

def weighted_pick(weighted_items):
    choices = [item[1] for item in weighted_items]
    weights = [item[0] for item in weighted_items]
    return random.choices(choices, weights=weights, k=1)[0]
ACID_SLIME_LARGE_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=11),
        EnemyIntent(
            kind="add_card_to_discard",
            card_id="card.status.slime_i",
            count=2,
        ),
    ]
)
ACID_SLIME_LARGE_B = EnemyIntent(
    kind="attack",
    value=16,
)
ACID_SLIME_LARGE_C = EnemyIntent(
    kind="status",
    target="player",
    status="weak",
    value=2,
)
ACID_SLIME_MIDDLE_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=7),
        EnemyIntent(
            kind="add_card_to_discard",
            card_id="card.status.slime_i",
            count=1,
        ),
    ]
)
ACID_SLIME_MIDDLE_B = EnemyIntent(
    kind="attack",
    value=10,
)
ACID_SLIME_MIDDLE_C = EnemyIntent(
    kind="status",
    target="player",
    status="weak",
    value=1,
)
class AcidSlimeEnemy(SplittingSlimeEnemy):
    """
    酸液史莱姆 large / middle 共用行动逻辑。

    行动：
    a. 攻击并向弃牌堆加入黏液I
    b. 高伤攻击
    c. 施加虚弱

    选择规则：
    1. b 后，a / c 等概率。
    2. 连续 aa 后，b : c = 4 : 3。
    3. 连续 cc 后，b : a = 4 : 3。
    4. 其他情况下，a : b : c = 3 : 4 : 3。
    """
    def __init__(
        self,
        enemy_id,
        name,
        max_hp,
        intent_a,
        intent_b,
        intent_c,
        split_to_enemy_id=""
    ):
        SplittingSlimeEnemy.__init__(
            self,
            enemy_id=enemy_id,
            name=name,
            max_hp=max_hp,
            intent_cycle=[intent_a],
            split_to_enemy_id=split_to_enemy_id,
        )
        self._acid_intents = {
            "a": intent_a,
            "b": intent_b,
            "c": intent_c,
        }
        self._acid_history = []
        self._locked_acid_key = None
    def choose_acid_key(self):
        if len(self._acid_history) >= 1:
            last = self._acid_history[-1]
            # b 后，a / c 等概率。
            if last == "b":
                return random.choice(["a", "c"])
        if len(self._acid_history) >= 2:
            last_two = self._acid_history[-2:]
            # 连续 aa 后，b : c = 4 : 3。
            if last_two == ["a", "a"]:
                return weighted_pick([
                    (4, "b"),
                    (3, "c"),
                ])
            # 连续 cc 后，b : a = 4 : 3。
            if last_two == ["c", "c"]:
                return weighted_pick([
                    (4, "b"),
                    (3, "a"),
                ])
        # 其他情况下，a : b : c = 3 : 4 : 3。
        return weighted_pick([
            (3, "a"),
            (4, "b"),
            (3, "c"),
        ])
    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_acid_key = self.choose_acid_key()
            self._locked_intent = self._acid_intents[self._locked_acid_key]
        return self._locked_intent
    def advance_intent(self):
        if self._locked_acid_key is not None:
            self._acid_history.append(self._locked_acid_key)
            # 只需要判断最近两次，保留 2 个即可。
            if len(self._acid_history) > 2:
                self._acid_history = self._acid_history[-2:]
        self._locked_acid_key = None
        self._locked_intent = None
ACID_SLIME_SMALL_A = EnemyIntent(
    kind="attack",
    value=3,
)
ACID_SLIME_SMALL_B = EnemyIntent(
    kind="status",
    target="player",
    status="weak",
    value=1,
)
class AcidSlimeSmallEnemy(PatternEnemy):
    """
    小酸液史莱姆：
    a. 造成 3 点伤害
    b. 施加 1 层虚弱

    轮流行动，第一个意图随机。
    """

    def __init__(self, max_hp=12):
        first = random.choice(["a", "b"])
        if first == "a":
            intent_cycle = [
                ACID_SLIME_SMALL_A,
                ACID_SLIME_SMALL_B,
            ]
        else:
            intent_cycle = [
                ACID_SLIME_SMALL_B,
                ACID_SLIME_SMALL_A,
            ]
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.acid_slime_small",
            name="小酸液史莱姆",
            max_hp=max_hp,
            intent_cycle=intent_cycle,
            loop_start_index=0,
        )
def create_acid_slime_large():
    return AcidSlimeEnemy(
        enemy_id="enemy.acid_slime_large",
        name="大酸液史莱姆",
        max_hp=random.randint(65, 69),
        intent_a=ACID_SLIME_LARGE_A,
        intent_b=ACID_SLIME_LARGE_B,
        intent_c=ACID_SLIME_LARGE_C,
        split_to_enemy_id="enemy.acid_slime_middle",
    )
def create_acid_slime_middle():
    return AcidSlimeEnemy(
        enemy_id="enemy.acid_slime_middle",
        name="中酸液史莱姆",
        max_hp=random.randint(28, 32),
        intent_a=ACID_SLIME_MIDDLE_A,
        intent_b=ACID_SLIME_MIDDLE_B,
        intent_c=ACID_SLIME_MIDDLE_C,
        split_to_enemy_id="enemy.acid_slime_small",
    )
def create_acid_slime_small():
    return AcidSlimeSmallEnemy(max_hp=random.randint(8, 12))

def create_cultist():
    return PatternEnemy(
        enemy_id="enemy.cultist",
        name="邪教徒",
        max_hp=random.randint(48, 54),
        intent_cycle=[
            EnemyIntent(kind="status",target="self",status="ritual",value=3),
            EnemyIntent(kind="attack",value=6,attack_type="slash"),
        ],
        loop_start_index=1
    )

JAW_WORM_A = EnemyIntent(kind="attack",value=11,)
JAW_WORM_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="status",target="self",status="strength",value=3,),
        EnemyIntent(kind="block",value=6,),
    ]
)
JAW_WORM_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack",value=7,),
        EnemyIntent(kind="block",value=5,),
    ]
)
class JawWormEnemy(PatternEnemy):
    """
    大颚虫。
    a. 造成 11 点伤害
    b. 获得 3 点力量，获得 6 点格挡
    c. 造成 7 点伤害，获得 5 点格挡

    行动逻辑：
    - a 后：60b，40c
    - b 后：45a，55c
    - 连续 cc 后：36a，64b
    - 其他情况下：25a，45b，30c
    prebuff=True 时：
    - 战斗开始时额外执行 b 的增益部分
    - 不写入行动历史
    - 第一回合仍然按 25a，45b，30c 选择
    """

    def __init__(self, enemy_id, max_hp=42, prebuff=False):
        PatternEnemy.__init__(
            self,
            enemy_id=enemy_id,
            name="大颚虫",
            max_hp=max_hp,
            intent_cycle=[JAW_WORM_A],
        )
        self._jaw_intents = {
            "a": JAW_WORM_A,
            "b": JAW_WORM_B,
            "c": JAW_WORM_C,
        }
        self._jaw_history = []
        self._locked_jaw_key = None
        self._prebuff = bool(prebuff)
        self._prebuff_done = False

    def choose_jaw_key(self):
        if len(self._jaw_history) >= 2:
            last_two = self._jaw_history[-2:]
            if last_two == ["c", "c"]:
                return weighted_pick([
                    (36, "a"),
                    (64, "b"),
                ])
        if len(self._jaw_history) >= 1:
            last = self._jaw_history[-1]
            if last == "a":
                return weighted_pick([
                    (60, "b"),
                    (40, "c"),
                ])
            if last == "b":
                return weighted_pick([
                    (45, "a"),
                    (55, "c"),
                ])
        return weighted_pick([
            (25, "a"),
            (45, "b"),
            (30, "c"),
        ])

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_jaw_key = self.choose_jaw_key()
            self._locked_intent = self._jaw_intents[self._locked_jaw_key]
        return self._locked_intent

    def advance_intent(self):
        if self._locked_jaw_key is not None:
            self._jaw_history.append(self._locked_jaw_key)
            if len(self._jaw_history) > 2:
                self._jaw_history = self._jaw_history[-2:]
        self._locked_jaw_key = None
        self._locked_intent = None

    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_BATTLE_START:
            return logs
        if not self._prebuff:
            return logs
        if self._prebuff_done:
            return logs
        if not self.is_alive():
            return logs
        self._prebuff_done = True
        current_strength = self.gain_status("strength", 3)
        self.block += 6
        logs.append("{} 战斗开始时咆哮，获得 3 点力量和 6 点格挡。当前力量：{}。".format(
            self.name,
            current_strength
        ))
        return logs
def create_jaw_worm_g1():
    return JawWormEnemy(
        enemy_id="enemy.jaw_worm_g1",
        max_hp=random.randint(40, 44),
        prebuff=False,
    )
def create_jaw_worm_g2():
    return JawWormEnemy(
        enemy_id="enemy.jaw_worm_g2",
        max_hp=random.randint(40, 44),
        prebuff=True,
    )

class LouseEnemy(PatternEnemy):
    """
    虱虫通用逻辑。
    红色虱虫：
    - 25% 自身获得 3 点力量
    - 75% 攻击 X 点，X 在生成敌人时随机为 5~7，之后固定
    绿色虱虫：
    - 25% 给予玩家 2 点脆弱
    - 75% 攻击 X 点，X 在生成敌人时随机为 5~7，之后固定
    限制：
    - 状态行动不会连续两次
    - 攻击不会连续三次
    """
    def __init__(self, enemy_id, name, max_hp, status_intent):
        self._attack_value = random.randint(5, 7)

        self._louse_attack_intent = EnemyIntent(
            kind="attack",
            value=self._attack_value,
            attack_type="slash",
        )
        self._louse_status_intent = status_intent
        PatternEnemy.__init__(
            self,
            enemy_id=enemy_id,
            name=name,
            max_hp=max_hp,
            intent_cycle=[
                self._louse_attack_intent,
            ],
        )
        self._louse_intents = {
            "attack": self._louse_attack_intent,
            "status": self._louse_status_intent,
        }
        self._louse_history = []
        self._locked_louse_key = None
    def choose_louse_key(self):
        if len(self._louse_history) >= 1:
            last = self._louse_history[-1]

            # 力量 / 脆弱不会连续两次。
            if last == "status":
                return "attack"
        if len(self._louse_history) >= 2:
            last_two = self._louse_history[-2:]

            # 攻击不会连续三次。
            if last_two == ["attack", "attack"]:
                return "status"
        # 正常概率：25 状态，75 攻击。
        roll = random.randint(1, 100)
        if roll <= 25:
            return "status"
        return "attack"
    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_louse_key = self.choose_louse_key()
            self._locked_intent = self._louse_intents[self._locked_louse_key]
        return self._locked_intent

    def advance_intent(self):
        if self._locked_louse_key is not None:
            self._louse_history.append(self._locked_louse_key)
            if len(self._louse_history) > 2:
                self._louse_history = self._louse_history[-2:]
        self._locked_louse_key = None
        self._locked_intent = None
def create_red_louse():
    enemy = LouseEnemy(
        enemy_id="enemy.red_louse",
        name="红色虱虫",
        max_hp=random.randint(10, 15),
        status_intent=EnemyIntent(
            kind="status",
            target="self",
            status="strength",
            value=3,
        ),
    )
    enemy.statuses.set("curl_up", random.randint(3, 7))
    return enemy
def create_green_louse():
    enemy = LouseEnemy(
        enemy_id="enemy.green_louse",
        name="绿色虱虫",
        max_hp=random.randint(11, 17),
        status_intent=EnemyIntent(
            kind="status",
            target="player",
            status="frail",
            value=2,
        ),
    )
    enemy.statuses.set("curl_up", random.randint(3, 7))
    return enemy
def create_random_louse():
    if random.choice([True, False]):
        return create_red_louse()
    return create_green_louse()

FUNGI_BEAST_A = EnemyIntent(
    kind="attack",
    value=6,
    attack_type="slash",
)
FUNGI_BEAST_B = EnemyIntent(
    kind="status",
    target="self",
    status="strength",
    value=3,
)
class FungiBeastEnemy(PatternEnemy):
    """
    真菌兽。
    a. 造成 6 点伤害
    b. 获得 3 点力量

    行动逻辑：
    - 连续 aa 后：b
    - b 后：a
    - 其他情况：60a，40b
    """

    def __init__(self, max_hp):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.fungi_beast",
            name="真菌兽",
            max_hp=max_hp,
            intent_cycle=[
                FUNGI_BEAST_A,
            ],
        )

        self._fungi_intents = {
            "a": FUNGI_BEAST_A,
            "b": FUNGI_BEAST_B,
        }
        self._fungi_history = []
        self._locked_fungi_key = None

    def choose_fungi_key(self):
        if len(self._fungi_history) >= 2:
            last_two = self._fungi_history[-2:]
            if last_two == ["a", "a"]:
                return "b"

        if len(self._fungi_history) >= 1:
            last = self._fungi_history[-1]
            if last == "b":
                return "a"

        roll = random.randint(1, 100)
        if roll <= 60:
            return "a"
        return "b"

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_fungi_key = self.choose_fungi_key()
            self._locked_intent = self._fungi_intents[self._locked_fungi_key]
        return self._locked_intent

    def advance_intent(self):
        if self._locked_fungi_key is not None:
            self._fungi_history.append(self._locked_fungi_key)
            if len(self._fungi_history) > 2:
                self._fungi_history = self._fungi_history[-2:]
        self._locked_fungi_key = None
        self._locked_intent = None
def create_fungi_beast():
    enemy = FungiBeastEnemy(
        max_hp=random.randint(22, 28),
    )
    enemy.statuses.set("spore_cloud", 2)
    return enemy