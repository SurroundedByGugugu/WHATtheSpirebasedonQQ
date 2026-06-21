# -*- coding: utf-8 -*-
# 一局游戏的总状态：路线、当前节点、牌组、遗物、金币等

from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class RunState:
    """
    一局游戏的总状态。

    GameState 只管当前战斗。
    RunState 管整局流程：
    - 路线
    - 当前节点
    - 长期 HP
    - 长期牌组
    - 遗物
    - 药水
    - 金币
    - 当前战斗
    - 待选择奖励
    """
    
    session_id: str
    character_id: str
    run_seed: int = None
    character_name: str = ""
    max_hp: int = 0
    hp: int = 0
    max_cost: int = 3
    master_deck: List[Any] = field(default_factory=list)
    relics: List[Any] = field(default_factory=list)
    potions: List[Any] = field(default_factory=list)
    max_potion_slots: int = 3
    gold: int = 0
    ascension_level: int = 0

    route_nodes: List[Any] = field(default_factory=list)
    current_node_id: str = ""
    completed_node_ids: List[str] = field(default_factory=list)

    # 开局即确定并公开的本层 Boss。
    # 同时会写入 boss RouteNode.encounter_id，保证显示结果和实际战斗一致。
    boss_encounter_id: str = ""
    boss_name: str = ""

    current_battle: Any = None

    # 实际战斗节点类型。
    # 主要用于 mystery 随机出普通战斗 / 精英战斗后的奖励结算。
    current_battle_node_type: str = ""

    pending_reward: Any = None

    # 上一场战斗中，击败盗贼后返还的金币奖励。
    pending_stolen_gold_rewards: List[Any] = field(default_factory=list)

    # 事件战斗胜利后的额外结算。
    # 例如：蘑菇事件胜利后获得奇怪蘑菇；冒险者尸体战斗后补发未搜索到的奖励。
    pending_post_battle_effects: List[Any] = field(default_factory=list)

    # 进入当前节点前的快照，用于 /card sl 回退到本节点入口。
    # 保存的是“进入节点前”的 RunState 深拷贝，不包含自身，避免递归膨胀。
    node_entry_snapshot: Any = None

    pending_shop: Any = None
    pending_event: Any = None
    # 待处理的瓶装遗物选择队列。
    # 每项格式：
    # {
    #   "relic_id": "relic.bottled_lightning",
    #   "relic_name": "瓶装闪电",
    #   "required_card_type": "skill",
    #   "required_card_type_name": "技能牌",
    # }
    pending_bottle_selections: List[Any] = field(default_factory=list)
    # 已经遇到过的事件 id，用于事件随机优先选择未遇到事件。
    seen_event_ids: List[str] = field(default_factory=list)
    pending_rest: Any = None
    pending_ancient: Any = None

    # 商店定向删牌价格。
    # 初始 50，每次定向删除成功后 +25。
    # 随机删除不影响该价格。
    card_remove_price: int = 50

    # 跨战斗保留状态预留。
    # 当前默认不保留力量、敏捷、荆棘等普通战斗状态。
    persistent_status_values: dict = field(default_factory=dict)
    persistent_status_keys: List[str] = field(default_factory=list)

    reward_count: int = 0

    run_over: bool = False
    victory: bool = False

    # ？房间概率。
    # 当前实现按一层/阶段初始化一次：怪物 10%、宝箱 2%、商店 3%。
    # elite 10% 只给“冒险者尸体”这类事件使用，普通 ? 房间不会直接掷出精英。
    mystery_base_chances: dict = field(default_factory=lambda: {
        "normal_enemy": 10,
        "treasure": 2,
        "shop": 3,
        "elite": 10,
    })
    mystery_current_chances: dict = field(default_factory=dict)

    # 已进入的 ? 房间数量。用于小宝箱。
    mystery_rooms_entered: int = 0

    # 奖励统计：用于未来成就、隐藏事件、路线结算等。
    reward_stats: dict = field(default_factory=dict)
    # 已获得成就占位。
    achievements: list = field(default_factory=list)
    
    def init_reward_stats_if_needed(self):
        if self.reward_stats:
            return

        self.reward_stats = {
            "gold_offered": 0,
            "gold_taken": 0,
            "gold_skipped": 0,

            "relic_offered": 0,
            "relic_taken": 0,
            "relic_skipped": 0,

            "potion_offered": 0,
            "potion_taken": 0,
            "potion_skipped": 0,

            "card_reward_offered": 0,
            "card_reward_taken": 0,
            "card_reward_skipped": 0,
        }
    
    def get_current_node(self):
        for node in self.route_nodes:
            if node.node_id == self.current_node_id:
                return node
        return None

    def mark_current_node_completed(self):
        if self.current_node_id and self.current_node_id not in self.completed_node_ids:
            self.completed_node_ids.append(self.current_node_id)

    def is_node_completed(self, node_id):
        return node_id in self.completed_node_ids
    
    def clear_pending_nodes(self):
        self.pending_shop = None
        self.pending_event = None
        self.pending_rest = None
        self.pending_ancient = None

    def has_pending_node(self):
        return any([
            self.pending_shop is not None,
            self.pending_event is not None,
            self.pending_rest is not None,
            self.pending_ancient is not None,
        ])