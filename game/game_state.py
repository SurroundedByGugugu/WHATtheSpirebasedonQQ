# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Any


@dataclass
class GameState:
    """
    一场战斗的完整状态。

    注意：
    GameState 不认识 QQ，不认识 LLOB。
    它只保存战斗状态。
    """

    session_id: str
    character_id: str
    player: Any
    enemies: List[Any]

    turn_count: int = 1
    battle_over: bool = False
    victory: bool = False
    # 需要玩家继续选择的临时流程。
    pending_discard_selection: bool = False
    pending_discard_source: str = ""
    pending_discard_to_draw_selection: bool = False
    pending_discard_to_draw_source: str = ""
    pending_discard_to_draw_options: List[Any] = field(default_factory=list)
    
    pending_exhaust_hand_selection: bool = False
    pending_exhaust_hand_source: str = ""
    pending_exhaust_hand_options: List[Any] = field(default_factory=list)
    pending_exhaust_hand_source_card: Any = None
    pending_exhaust_hand_target_index: int = 0
    pending_exhaust_hand_required_card_types: List[str] = field(default_factory=list)
    pending_exhaust_hand_after_effects: List[Any] = field(default_factory=list)

    pending_hand_to_draw_top_selection: bool = False
    pending_hand_to_draw_top_source: str = ""
    pending_hand_to_draw_top_options: List[Any] = field(default_factory=list)

    pending_upgrade_hand_selection: bool = False
    pending_upgrade_hand_source: str = ""
    pending_upgrade_hand_options: List[Any] = field(default_factory=list)

    pending_duplicate_hand_selection: bool = False
    pending_duplicate_hand_source: str = ""
    pending_duplicate_hand_options: List[Any] = field(default_factory=list)
    pending_duplicate_hand_count: int = 0
    
    pending_exhume_selection: bool = False
    pending_exhume_source: str = ""
    pending_exhume_options: List[Any] = field(default_factory=list)

    # 药水带来的选择流程：攻击/技能/能力药水、液态记忆、万灵药水。
    pending_potion_card_selection: bool = False
    pending_potion_card_source: str = ""
    pending_potion_card_options: List[Any] = field(default_factory=list)
    pending_potion_card_copy_count: int = 1
    pending_potion_card_mode: str = ""

    pending_elixir_selection: bool = False
    pending_elixir_source: str = ""
    pending_elixir_options: List[Any] = field(default_factory=list)

    # 先占位，后续 zone / field 系统接这里
    active_zone: Any = None
    active_fields: List[Any] = field(default_factory=list)

    # 本场战斗已经打出过的牌对象，用于“第一次打出”类效果。
    played_card_keys_this_battle: set = field(default_factory=set)

    # 本场战斗中，玩家 HP 实际减少的次数。
    # 每次 real_damage > 0 记 1 次，不按损失点数累计。
    player_life_loss_count_this_battle: int = 0

    # 本回合玩家已经打出的攻击牌数量。
    # 用于火焰吐息·旧：即使能力牌在中途打出，也要统计此前的攻击牌。
    player_card_type_played_counts_this_turn: dict = field(default_factory=lambda: {
        "attack": 0,
        "skill": 0,
        "power": 0,
        "status": 0,
        "curse": 0,
    })
    
    # 本场战斗中，击败盗贼后可以返还的被偷金币。
    # 每个元素形如：{"source": "抢劫的", "amount": 15}
    stolen_gold_rewards: List[Any] = field(default_factory=list)

    def get_alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy.is_alive()]

    def is_all_enemies_dead(self):
        return len(self.get_alive_enemies()) == 0

    def status_text(self):
        lines = []
        lines.append("=== 战斗状态 ===")
        lines.append("回合：{}".format(self.turn_count))
        lines.append(self.player.status_text())

        lines.append("")
        lines.append("敌人：")

        for index, enemy in enumerate(self.enemies):
            lines.append("[{}] {}".format(index, enemy.status_text(self)))

        if self.active_zone is not None:
            lines.append("")
            lines.append("当前 Zone：{}".format(self.active_zone))

        if self.active_fields:
            lines.append("")
            lines.append("当前 Field：{}".format(", ".join([str(x) for x in self.active_fields])))

        if self.battle_over:
            lines.append("")
            if self.victory:
                lines.append("战斗结束：胜利。")
            else:
                lines.append("战斗结束：失败。")

        return "\n".join(lines)