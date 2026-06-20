# -*- coding: utf-8 -*-
# enemy_origin_1_1表示来自原作1中1层怪物

from data.enemy.base_enemy import EnemyActionResult, EnemyIntent
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
SLIME_SPLIT_INTENT = EnemyIntent(kind="split")
class SplittingSlimeEnemy(PatternEnemy):
    """
    尖刺 / 酸液史莱姆分裂基类。

    规则调整：
    1. HP > 0 且 HP <= max_hp / 2 时，不立即分裂。
    2. 触发后将本回合意图改为“分裂”。
    3. 轮到敌人行动时执行分裂，分裂成 2 只下一尺寸史莱姆。
    4. 每只小史莱姆的当前 HP 和 max_hp 都设为分裂前当前 HP。
    5. small 尺寸不继承该类，因此不会继续分裂。
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
        self._pending_split = False

    def should_split(self):
        if self._has_split:
            return False
        if not self.split_to_enemy_id:
            return False
        # 直接被打死时不分裂。
        if self.hp <= 0:
            return False
        return self.hp * 2 <= self.max_hp

    def get_current_intent(self):
        if self._pending_split and self.should_split():
            return SLIME_SPLIT_INTENT
        return PatternEnemy.get_current_intent(self)

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
        self._pending_split = True
        self._locked_intent = SLIME_SPLIT_INTENT
        logs.append("{} 的生命值降至一半及以下，本回合意图变为分裂。".format(
            self.name
        ))
        return logs

    def resolve_split(self, game_state):
        logs = []
        if not self.should_split():
            self._pending_split = False
            self._locked_intent = None
            logs.append("{} 尝试分裂，但条件已经不满足。".format(self.name))
            return logs

        split_hp = int(self.hp)
        child_a = self.make_split_child(split_hp)
        child_b = self.make_split_child(split_hp)
        try:
            index = game_state.enemies.index(self)
        except ValueError:
            return logs

        self._has_split = True
        self._pending_split = False
        self._locked_intent = None
        self.hp = 0
        self.block = 0
        game_state.enemies[index:index + 1] = [child_a, child_b]
        logs.append("{} 分裂成 2 只{}，每只 HP：{}/{}。".format(
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


RED_SLAVER_A = EnemyIntent(
    kind="attack",
    value=13,
    attack_type="slash",
)
RED_SLAVER_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="attack",
            value=8,
            attack_type="slash",
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="vulnerable",
            value=1,
        ),
    ]
)
RED_SLAVER_C = EnemyIntent(
    kind="status",
    target="player",
    status="entangled",
    value=1,
)
class RedSlaverEnemy(PatternEnemy):
    """
    红色奴隶主。

    a. 造成 13 点伤害
    b. 造成 8 点伤害，给予 1 层易伤
    c. 给予玩家 1 层缠身

    行动逻辑：
    - 第一回合固定 a
    - 之后每回合有 1/4 概率 c
    - 若不为 c，则按 b a b a 循环
    - c 之后：45% a，55% b
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.red_slaver",
            name="红色奴隶主",
            max_hp=random.randint(46, 50),
            intent_cycle=[RED_SLAVER_A],
        )

        self._red_slaver_intents = {
            "a": RED_SLAVER_A,
            "b": RED_SLAVER_B,
            "c": RED_SLAVER_C,
        }

        self._red_slaver_history = []
        self._locked_red_slaver_key = None

        # 第一回合 a 后，后续非 c 行动从 b 开始，形成 b a b a。
        self._next_baba_key = "b"

    def choose_red_slaver_key(self):
        if not self._red_slaver_history:
            return "a"

        last = self._red_slaver_history[-1]

        if last == "c":
            return weighted_pick([
                (45, "a"),
                (55, "b"),
            ])

        # 之后每回合有 1/4 概率 c。
        if random.randint(1, 4) == 1:
            return "c"

        return self._next_baba_key

    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_red_slaver_key = self.choose_red_slaver_key()
            self._locked_intent = self._red_slaver_intents[self._locked_red_slaver_key]

        return self._locked_intent

    def advance_intent(self):
        if self._locked_red_slaver_key is not None:
            key = self._locked_red_slaver_key
            self._red_slaver_history.append(key)

            if len(self._red_slaver_history) > 2:
                self._red_slaver_history = self._red_slaver_history[-2:]

            if key == "a":
                self._next_baba_key = "b"
            elif key == "b":
                self._next_baba_key = "a"

        self._locked_red_slaver_key = None
        self._locked_intent = None
BLUE_SLAVER_A = EnemyIntent(
    kind="attack",
    value=12,
    attack_type="slash",
)
BLUE_SLAVER_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="attack",
            value=7,
            attack_type="slash",
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="weak",
            value=1,
        ),
    ]
)
BLUE_SLAVER_RANDOM_PATTERN = [
    (3, BLUE_SLAVER_A),
    (2, BLUE_SLAVER_B),
]
def create_red_slaver():
    return RedSlaverEnemy()
def create_blue_slaver():
    return PatternEnemy(
        enemy_id="enemy.blue_slaver",
        name="蓝色奴隶主",
        max_hp=random.randint(46, 50),
        intent_cycle=[
            BLUE_SLAVER_RANDOM_PATTERN,
        ],
    )


class ThiefEnemy(PatternEnemy):
    """
    抢劫的 / 打劫的 通用逻辑。

    行动逻辑：
    - 第一、第二回合固定 a
    - 第三回合 b / c 概率对半
    - b 后必然 c
    - c 后必然 d

    a. 攻击，同时偷 15 金币
    b. 高伤攻击
    c. 获得格挡
    d. 带着所有盗窃的金币逃离战斗
    """

    def __init__(
        self,
        enemy_id,
        name,
        max_hp,
        steal_attack_damage,
        heavy_attack_damage,
        smoke_block
    ):
        self._thief_a = EnemyIntent(
            kind="multi",
            actions=[
                EnemyIntent(
                    kind="attack",
                    value=steal_attack_damage,
                    attack_type="slash",
                ),
                EnemyIntent(
                    kind="steal_gold",
                    value=15,
                    message="把钱交出来！",
                ),
            ]
        )
        self._thief_b = EnemyIntent(
            kind="attack",
            value=heavy_attack_damage,
            attack_type="slash",
        )
        self._thief_c = EnemyIntent(
            kind="block",
            value=smoke_block,
            message="我的烟雾弹在哪里呢？",
        )
        self._thief_d = EnemyIntent(
            kind="escape",
            message=random.choice([
                "我可溜啦！",
                "谢谢你的钱了！",
            ]),
        )
        PatternEnemy.__init__(
            self,
            enemy_id=enemy_id,
            name=name,
            max_hp=max_hp,
            intent_cycle=[self._thief_a],
        )
        self._thief_intents = {
            "a": self._thief_a,
            "b": self._thief_b,
            "c": self._thief_c,
            "d": self._thief_d,
        }
        self._thief_history = []
        self._locked_thief_key = None
        self._stolen_gold = 0
        self._escaped = False
        self._stolen_gold_reward_added = False

    def choose_thief_key(self):
        turn_index = len(self._thief_history)
        if turn_index < 2:
            return "a"
        if turn_index == 2:
            return random.choice(["b", "c"])
        last = self._thief_history[-1]
        if last == "b":
            return "c"
        if last == "c":
            return "d"
        # 理论兜底：如果 d 后仍然活着，再次逃跑。
        return "d"
    def get_current_intent(self):
        if self._locked_intent is None:
            self._locked_thief_key = self.choose_thief_key()
            self._locked_intent = self._thief_intents[self._locked_thief_key]
        return self._locked_intent

    def advance_intent(self):
        if self._locked_thief_key is not None:
            self._thief_history.append(self._locked_thief_key)
            if len(self._thief_history) > 5:
                self._thief_history = self._thief_history[-5:]
        self._locked_thief_key = None
        self._locked_intent = None

    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_DAMAGE_AFTER:
            return logs
        if context.target is not self:
            return logs
        if self.is_alive():
            return logs
        if getattr(self, "_escaped", False):
            return logs
        if self._stolen_gold_reward_added:
            return logs
        stolen = int(getattr(self, "_stolen_gold", 0))
        if stolen <= 0:
            return logs
        self._stolen_gold_reward_added = True
        context.game_state.stolen_gold_rewards.append({
            "source": self.name,
            "amount": stolen,
        })
        logs.append("{} 掉落了被偷走的 {} 金币。".format(
            self.name,
            stolen
        ))
        return logs
def create_looter():
    return ThiefEnemy(
        enemy_id="enemy.looter",
        name="抢劫的",
        max_hp=random.randint(44, 48),
        steal_attack_damage=10,
        heavy_attack_damage=12,
        smoke_block=6,
    )
def create_mugger():
    return ThiefEnemy(
        enemy_id="enemy.mugger",
        name="打劫的",
        max_hp=random.randint(48, 52),
        steal_attack_damage=10,
        heavy_attack_damage=16,
        smoke_block=11,
    )

FAT_GREMLIN_ATTACK = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(
            kind="attack",
            value=4,
        ),
        EnemyIntent(
            kind="status",
            target="player",
            status="weak",
            value=1,
        ),
    ]
)
def create_fat_gremlin():
    return PatternEnemy(
        enemy_id="enemy.fat_gremlin",
        name="胖地精",
        max_hp=random.randint(13,17),
        intent_cycle=[
            FAT_GREMLIN_ATTACK,
        ]
    )
MAD_GREMLIN_ATTACK = EnemyIntent(
    kind="attack",
    value=4,
)
def create_mad_gremlin():
    enemy = PatternEnemy(
        enemy_id="enemy.mad_gremlin",
        name="火大地精",
        max_hp=random.randint(20,24),
        intent_cycle=[
            MAD_GREMLIN_ATTACK,
        ]
    )
    enemy.statuses.set("anger",1)
    return enemy
SNEAKY_GREMLIN_ATTACK = EnemyIntent(
    kind="attack",
    value=9,
)
def create_sneaky_gremlin():
    return PatternEnemy(
        enemy_id="enemy.sneaky_gremlin",
        name="卑鄙地精",
        max_hp=random.randint(10,14),
        intent_cycle=[
            SNEAKY_GREMLIN_ATTACK,
        ]
    )
SHIELD_GREMLIN_SMART = EnemyIntent(
    kind="smart_ally_block_or_attack",
    value=7,
    count=6,
)
class ShieldGremlinEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.shield_gremlin",
            name="持盾地精",
            max_hp=random.randint(12, 15),
            intent_cycle=[SHIELD_GREMLIN_SMART],
        )
GREMLIN_WIZARD_CHARGE0 = EnemyIntent(
    kind="wait",
    message="开始准备了！"
)
GREMLIN_WIZARD_CHARGE1 = EnemyIntent(
    kind="wait",
    message="在蓄能咯！"
)
GREMLIN_WIZARD_CHARGE2 = EnemyIntent(
    kind="wait",
    message="要来咯！"
)
GREMLIN_WIZARD_ATTACK = EnemyIntent(
    kind="attack",
    value=25,
)
class GremlinWizardEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.gremlin_wizard",
            name="地精法师",
            max_hp=random.randint(21, 25),
            intent_cycle=[GREMLIN_WIZARD_CHARGE0],
        )
        self.stage = 0

    def get_current_intent(self):
        if self.stage == 0:
            return GREMLIN_WIZARD_CHARGE0
        if self.stage == 1:
            return GREMLIN_WIZARD_CHARGE1
        if self.stage == 2:
            return GREMLIN_WIZARD_CHARGE2
        return GREMLIN_WIZARD_ATTACK

    def advance_intent(self):
        if self.stage == 0:
            self.stage = 1
        elif self.stage == 1:
            self.stage = 2
        elif self.stage == 2:
            self.stage = 3
        else:
            self.stage = 0
        self._locked_intent = None
def create_shield_gremlin():
    return ShieldGremlinEnemy()
def create_gremlin_wizard():
    return GremlinWizardEnemy()


# 一层精英：Gremlin Nob / Lagavulin / Sentry
GREMLIN_NOB_A = EnemyIntent(
    kind="status",
    target="self",
    status="enrage",
    value=2,
)
GREMLIN_NOB_B = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=6),
        EnemyIntent(kind="status", target="player", status="vulnerable", value=2),
    ]
)
GREMLIN_NOB_C = EnemyIntent(
    kind="attack",
    value=14,
)
GREMLIN_NOB_BC_RANDOM = [
    (1, GREMLIN_NOB_B),
    (2, GREMLIN_NOB_C),
]
def create_gremlin_nob():
    return PatternEnemy(
        enemy_id="enemy.gremlin_nob",
        name="地精大块头",
        max_hp=random.randint(82, 86),
        intent_cycle=[
            GREMLIN_NOB_A,
            GREMLIN_NOB_BC_RANDOM,
        ],
        loop_start_index=1,
    )

LAGAVULIN_SLEEP = EnemyIntent(
    kind="wait",
    message="沉睡",
)
LAGAVULIN_WAKE_STUN = EnemyIntent(
    kind="wait",
    message="惊醒后眩晕",
)
LAGAVULIN_B = EnemyIntent(
    kind="attack",
    value=18,
)
LAGAVULIN_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="status", target="player", status="strength", value=-1),
        EnemyIntent(kind="status", target="player", status="dexterity", value=-1),
    ]
)
class LagavulinEnemy(PatternEnemy):
    """
    乐加维林。

    默认版本：
    - 开局沉睡，8 金属化，8 格挡。
    - 沉睡期间行动为 wait。
    - 生命流失时苏醒，并在本回合眩晕，不采取行动。
    - 未被打醒时，第 4 个敌人行动回合自然苏醒，并立即攻击 18。
    - 苏醒后移除金属化，行动按 b b c 循环。

    event_awake=True：
    - 事件限定版本，开局已苏醒。
    - 第一回合 c，之后 b b c 循环。
    """

    def __init__(self, event_awake=False):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.lagavulin_awake" if event_awake else "enemy.lagavulin",
            name="乐加维林",
            max_hp=random.randint(109, 111),
            intent_cycle=[LAGAVULIN_SLEEP],
        )
        self._lag_asleep = not bool(event_awake)
        self._lag_sleep_turns_done = 0
        self._lag_wake_stun_pending = False
        self._lag_awake_cycle = [
            LAGAVULIN_B,
            LAGAVULIN_B,
            LAGAVULIN_C,
        ]
        # 普通苏醒后从 b 开始。
        # 事件苏醒版第一回合为 c，之后回到 b b c。
        self._lag_awake_index = 2 if event_awake else 0
        if self._lag_asleep:
            self.statuses.set("metallicize", 8)
            self.block = 8

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent
        if self._lag_wake_stun_pending:
            self._locked_intent = LAGAVULIN_WAKE_STUN
            return self._locked_intent
        if self._lag_asleep:
            if self._lag_sleep_turns_done >= 3:
                self._locked_intent = LAGAVULIN_B
            else:
                self._locked_intent = LAGAVULIN_SLEEP
            return self._locked_intent
        self._locked_intent = self._lag_awake_cycle[self._lag_awake_index]
        return self._locked_intent

    def act(self):
        intent = self.get_current_intent()
        logs = []
        if self._lag_asleep and self._lag_sleep_turns_done >= 3:
            self._lag_asleep = False
            self.statuses.remove("metallicize")
            logs.append("{} 自然苏醒，金属化消失。".format(self.name))

        logs.append("{} 准备执行：{}。".format(
            self.name,
            intent.to_text()
        ))
        action = self._intent_to_action(intent)
        self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def advance_intent(self):
        if self._lag_wake_stun_pending:
            self._lag_wake_stun_pending = False
            self._lag_awake_index = 0
            self._locked_intent = None
            return
        if self._lag_asleep:
            self._lag_sleep_turns_done += 1
            self._locked_intent = None
            return
        if self._locked_intent is LAGAVULIN_B and self._lag_awake_index == 0:
            self._lag_awake_index = 1
        else:
            self._lag_awake_index = (self._lag_awake_index + 1) % len(self._lag_awake_cycle)
        self._locked_intent = None

    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_DAMAGE_AFTER:
            return logs
        if context.target is not self:
            return logs
        if not self._lag_asleep:
            return logs
        if not self.is_alive():
            return logs
        real_damage = int(context.extra.get("real_damage", 0))
        if real_damage <= 0:
            return logs
        self._lag_asleep = False
        self._lag_wake_stun_pending = True
        self._lag_awake_index = 0
        self.statuses.remove("metallicize")
        self._locked_intent = LAGAVULIN_WAKE_STUN
        logs.append("{} 因生命流失而苏醒，金属化消失；本回合将眩晕，无法行动。".format(
            self.name
        ))
        return logs
def create_lagavulin():
    return LagavulinEnemy(event_awake=False)
def create_lagavulin_awake():
    return LagavulinEnemy(event_awake=True)

SENTRY_A = EnemyIntent(
    kind="attack",
    value=9,
)
SENTRY_B = EnemyIntent(
    kind="add_card_to_discard",
    card_id="card.status.dazed",
    count=2,
)
def create_sentry_a():
    return PatternEnemy(
        enemy_id="enemy.sentry_a",
        name="哨卫",
        max_hp=random.randint(38, 42),
        intent_cycle=[
            SENTRY_A,
            SENTRY_B,
        ],
        loop_start_index=0,
    )
def create_sentry_b():
    return PatternEnemy(
        enemy_id="enemy.sentry_b",
        name="哨卫",
        max_hp=random.randint(38, 42),
        intent_cycle=[
            SENTRY_B,
            SENTRY_A,
        ],
        loop_start_index=0,
    )


# 一层 Boss：Hexaghost / Guardian / Slime Boss
HEXAGHOST_IGNITE = EnemyIntent(
    kind="wait",
    message="六火亡魂正在点燃狱火",
)
HEXAGHOST_A = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=6),
        EnemyIntent(kind="add_card_to_discard", card_id="card.status.burn_i", count=1),
    ]
)
HEXAGHOST_B = EnemyIntent(kind="attack", value=5, repeat=2)
HEXAGHOST_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="status", target="self", status="strength", value=2),
        EnemyIntent(kind="block", value=12),
    ]
)
HEXAGHOST_D_BURN_CARD = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=2, repeat=6),
        EnemyIntent(kind="add_card_to_discard", card_id="card.status.burn_ii", count=3),
    ]
)
HEXAGHOST_D_BURN_STATUS = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="attack", value=2, repeat=6),
        EnemyIntent(kind="status", target="player", status="burn", value=1),
    ]
)
class HexaghostEnemy(PatternEnemy):
    """
    六火亡魂。

    行动：
    - 第 1 次行动：不行动，只显示点燃狱火。
    - 第 2 次行动：造成 X 点伤害 6 次，X = 玩家当前生命 // 12 + 1。
    - 之后循环：a b a c b a d。
    - d 槽位在“3 张升级灼伤”和“1 层烧伤”之间 1:1 随机。
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.hexaghost",
            name="六火亡魂",
            max_hp=250,
            intent_cycle=[HEXAGHOST_IGNITE],
        )
        self._hex_action_count = 0
        self._hex_loop = [
            HEXAGHOST_A,
            HEXAGHOST_B,
            HEXAGHOST_A,
            HEXAGHOST_C,
            HEXAGHOST_B,
            HEXAGHOST_A,
            [(1, HEXAGHOST_D_BURN_CARD), (1, HEXAGHOST_D_BURN_STATUS)],
        ]
        self._hex_loop_index = 0
        self._hex_game_state = None
    def on_event(self, event_name, context):
        if event_name == EVENT_BATTLE_START:
            self._hex_game_state = context.game_state
        return []

    def _make_divider_intent(self):
        hp = 0
        if self._hex_game_state is not None and self._hex_game_state.player is not None:
            hp = int(self._hex_game_state.player.hp)
        value = int(hp / 12) + 1
        if value < 1:
            value = 1
        return EnemyIntent(kind="attack", value=value, repeat=6)

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent
        if self._hex_action_count == 0:
            self._locked_intent = HEXAGHOST_IGNITE
            return self._locked_intent
        if self._hex_action_count == 1:
            self._locked_intent = self._make_divider_intent()
            return self._locked_intent
        slot = self._hex_loop[self._hex_loop_index]
        self._locked_intent = self._resolve_intent_slot(slot)
        return self._locked_intent
    
    def advance_intent(self):
        self._hex_action_count += 1
        if self._hex_action_count >= 2:
            self._hex_loop_index = (self._hex_loop_index + 1) % len(self._hex_loop)
        self._locked_intent = None
def create_hexaghost():
    return HexaghostEnemy()


GUARDIAN_A = EnemyIntent(kind="block", value=9)
GUARDIAN_B = EnemyIntent(kind="attack", value=32)
GUARDIAN_C = EnemyIntent(
    kind="multi",
    actions=[
        EnemyIntent(kind="status", target="player", status="weak", value=2),
        EnemyIntent(kind="status", target="player", status="vulnerable", value=2),
    ]
)
GUARDIAN_D = EnemyIntent(kind="attack", value=5, repeat=4)
GUARDIAN_E = EnemyIntent(kind="status", target="self", status="sharp_hide", value=3)
GUARDIAN_F = EnemyIntent(kind="attack", value=9)
GUARDIAN_G = EnemyIntent(kind="attack", value=8, repeat=2)
class GuardianEnemy(PatternEnemy):
    """
    守护者。

    攻击形态：a b c d 循环，初始第一回合 a。
    防御形态：e f g 执行一轮，g 后回到攻击形态，并使形态转换阈值永久 +10。
    """

    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.guardian",
            name="守护者",
            max_hp=240,
            intent_cycle=[GUARDIAN_A],
        )
        self._guardian_mode = "attack"
        self._guardian_attack_cycle = [
            GUARDIAN_A,
            GUARDIAN_B,
            GUARDIAN_C,
            GUARDIAN_D,
        ]
        self._guardian_attack_index = 0
        self._guardian_defense_cycle = [
            GUARDIAN_E,
            GUARDIAN_F,
            GUARDIAN_G,
        ]
        self._guardian_defense_index = 0
        self._guardian_shape_threshold = 30
        self._guardian_is_acting = False
        self._guardian_pending_transform = False
        self._guardian_return_to_attack_pending = False
        self.statuses.set("shape_shift", self._guardian_shape_threshold)

    def get_current_intent(self):
        if self._locked_intent is not None:
            return self._locked_intent
        if self._guardian_mode == "defense":
            self._locked_intent = self._guardian_defense_cycle[self._guardian_defense_index]
            return self._locked_intent
        self._locked_intent = self._guardian_attack_cycle[self._guardian_attack_index]
        return self._locked_intent

    def advance_intent(self):
        if self._guardian_mode == "defense":
            if self._guardian_defense_index == 2:
                self._guardian_switch_to_attack_after_defense()
            else:
                self._guardian_defense_index += 1
            self._locked_intent = None
            return
        self._guardian_attack_index = (
            self._guardian_attack_index + 1
        ) % len(self._guardian_attack_cycle)
        self._locked_intent = None

    def before_enemy_action(self, game_state):
        self._guardian_is_acting = True
        return []

    def after_enemy_action(self, game_state):
        self._guardian_is_acting = False
        logs = []
        if self._guardian_return_to_attack_pending:
            self._guardian_return_to_attack_pending = False
            self._guardian_switch_to_attack_after_defense()
            logs.append("{} 切换回攻击形态，形态转换永久提高至 {}。".format(
                self.name,
                self._guardian_shape_threshold
            ))
        if self._guardian_pending_transform and self.is_alive():
            self._guardian_pending_transform = False
            logs.extend(self._guardian_enter_defense(game_state))
        self._guardian_pending_transform = False
        return logs

    def _guardian_enter_defense(self, game_state):
        logs = []
        if self._guardian_mode == "defense":
            return logs
        if not self.is_alive():
            return logs
        self._guardian_mode = "defense"
        self._guardian_defense_index = 0
        self._locked_intent = GUARDIAN_E
        self.statuses.remove("shape_shift")
        logs.append("{} 进入防御形态，形态转换暂时消失。".format(self.name))
        from game.block import gain_block_without_modifiers
        logs.extend(gain_block_without_modifiers(
            game_state=game_state,
            source=self,
            target=self,
            amount=20,
            block_source="guardian_shape_shift",
            card=None,
            message="{} 进入防御形态，立即获得 20 点格挡。当前格挡：{}。".format(
                self.name,
                self.block + 20
            )
        ))
        return logs

    def _guardian_switch_to_attack_after_defense(self):
        self._guardian_mode = "attack"
        self._guardian_shape_threshold += 10
        self.statuses.set("shape_shift", self._guardian_shape_threshold)
        self.statuses.remove("sharp_hide")
        # 形态转换后攻击形态第一回合为 d。
        self._guardian_attack_index = 3

    def act(self):
        intent = self.get_current_intent()
        logs = []

        logs.append("{} 准备执行：{}。".format(
            self.name,
            intent.to_text()
        ))
        action = self._intent_to_action(intent)
        if intent is GUARDIAN_G:
            self._guardian_return_to_attack_pending = True
            self._guardian_defense_index = 2
            self._locked_intent = None
            logs.append("{} 将在本次攻击后切换回攻击形态。".format(self.name))
        else:
            self.advance_intent()
        return EnemyActionResult(action=action, logs=logs)

    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_DAMAGE_AFTER:
            return logs
        if context.target is not self:
            return logs
        if not self.is_alive():
            return logs
        if self._guardian_mode != "attack":
            return logs
        if self._guardian_pending_transform:
            return logs
        real_damage = int(context.extra.get("real_damage", 0))
        if real_damage <= 0:
            return logs
        current = self.statuses.add("shape_shift", -real_damage)
        if current > 0:
            logs.append("{} 的形态转换减少 {}，当前为 {}。".format(
                self.name,
                real_damage,
                current
            ))
            return logs
        self.statuses.set("shape_shift", 0)
        logs.append("{} 的形态转换减少 {}，已满足转换条件。".format(
            self.name,
            real_damage
        ))
        if self._guardian_is_acting:
            self._guardian_pending_transform = True
            logs.append("{} 正在完成当前攻击，防御形态将在全部攻击结算后生效。".format(
                self.name
            ))
            return logs
        logs.extend(self._guardian_enter_defense(context.game_state))
        return logs
def create_guardian():
    return GuardianEnemy()


SLIME_BOSS_A = EnemyIntent(
    kind="add_card_to_discard",
    card_id="card.status.slime_i",
    count=3,
)
SLIME_BOSS_B = EnemyIntent(
    kind="wait",
    message="预备……",
)
SLIME_BOSS_C = EnemyIntent(
    kind="attack",
    value=35,
    message="史莱姆撞击！",
)
class SlimeBossEnemy(PatternEnemy):
    def __init__(self):
        PatternEnemy.__init__(
            self,
            enemy_id="enemy.slime_boss",
            name="史莱姆老大",
            max_hp=140,
            intent_cycle=[
                SLIME_BOSS_A,
                SLIME_BOSS_B,
                SLIME_BOSS_C,
            ],
            loop_start_index=0,
        )
        self._has_split = False
        self._pending_split = False

    def should_split(self):
        if self._has_split:
            return False
        if self.hp <= 0:
            return False
        return self.hp * 2 <= self.max_hp

    def get_current_intent(self):
        if self._pending_split and self.should_split():
            return SLIME_SPLIT_INTENT
        return PatternEnemy.get_current_intent(self)

    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_DAMAGE_AFTER:
            return logs
        if context.target is not self:
            return logs
        if not self.should_split():
            return logs
        self._pending_split = True
        self._locked_intent = SLIME_SPLIT_INTENT
        logs.append("{} 的生命值降至一半及以下，本回合意图变为分裂。".format(
            self.name
        ))
        return logs

    def make_split_child(self, enemy_id, hp):
        from data.enemy.AAAregistry import create_enemy
        child = create_enemy(enemy_id)
        child.max_hp = int(hp)
        child.hp = int(hp)
        child.block = 0
        return child

    def resolve_split(self, game_state):
        logs = []
        if not self.should_split():
            self._pending_split = False
            self._locked_intent = None
            logs.append("{} 尝试分裂，但条件已经不满足。".format(self.name))
            return logs
        split_hp = int(self.hp)
        spike = self.make_split_child("enemy.spike_slime_large", split_hp)
        acid = self.make_split_child("enemy.acid_slime_large", split_hp)
        try:
            index = game_state.enemies.index(self)
        except ValueError:
            return logs
        self._has_split = True
        self._pending_split = False
        self._locked_intent = None
        self.hp = 0
        self.block = 0
        game_state.enemies[index:index + 1] = [spike, acid]
        logs.append("{} 分裂成大尖刺史莱姆与大酸液史莱姆，每只 HP：{}/{}。".format(
            self.name,
            split_hp,
            split_hp
        ))
        return logs
def create_slime_boss():
    return SlimeBossEnemy()
