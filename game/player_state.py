# -*- coding: utf-8 -*-

import random
from dataclasses import dataclass, field
from typing import List, Any
from game.status.status_container import StatusContainer
from game.status.status_display import get_status_display_text

@dataclass
class PlayerState:
    """
    战斗中的玩家状态。

    CharacterTemplate 是角色模板；
    PlayerState 是进入战斗后的实际状态。
    """

    character_id: str
    name: str
    max_hp: int
    hp: int
    max_cost: int
    cost: int
    max_hand_size: int = 10
    block: int = 0

    statuses: StatusContainer = field(default_factory=StatusContainer)

    relics: List[Any] = field(default_factory=list)

    max_potion_slots: int = 3
    potions: List[Any] = field(default_factory=list)

    draw_pile: List[Any] = field(default_factory=list)
    discard_pile: List[Any] = field(default_factory=list)
    exhaust_pile: List[Any] = field(default_factory=list)
    hand: List[Any] = field(default_factory=list)

    def is_alive(self):
        return self.hp > 0

    def start_turn(self):
        """
        玩家回合开始。
        暂时规则：
        1. 格挡清零
        2. 费用恢复到 max_cost
        """
        self.block = 0
        self.cost = self.max_cost

    def is_hand_full(self):
        return len(self.hand) >= self.max_hand_size

    def draw_cards(self, count):
        """
        抽牌。
        抽牌堆空时，把弃牌堆洗回抽牌堆。
        手牌达到上限时停止抽牌。
        """
        logs = []

        for _ in range(count):
            if self.is_hand_full():
                logs.append("手牌已满，停止抽牌。")
                break

            if not self.draw_pile:
                if self.discard_pile:
                    self.draw_pile = self.discard_pile
                    self.discard_pile = []
                    random.shuffle(self.draw_pile)
                    logs.append("弃牌堆洗回抽牌堆。")
                else:
                    logs.append("无牌可抽。")
                    break

            card = self.draw_pile.pop()
            self.hand.append(card)
            logs.append("抽到【{}】。".format(card.name))

        return logs

    def draw_to_full(self):
        count = self.max_hand_size - len(self.hand)

        if count <= 0:
            return ["手牌已经达到上限 {}。".format(self.max_hand_size)]

        logs = []
        logs.append("尝试抽牌直到手牌达到上限 {}。".format(self.max_hand_size))
        logs.extend(self.draw_cards(count))
        return logs

    def discard_hand(self):
        """
        回合结束时丢弃所有手牌。
        """
        count = len(self.hand)
        self.discard_pile.extend(self.hand)
        self.hand = []
        return "丢弃了 {} 张手牌。".format(count)

    def take_damage(self, damage):
        """
        玩家受到伤害，先用格挡抵消。
        """
        if damage <= 0:
            return "{} 没有受到伤害。".format(self.name)

        blocked = min(self.block, damage)
        self.block -= blocked

        real_damage = damage - blocked
        self.hp -= real_damage

        if self.hp < 0:
            self.hp = 0

        return "{} 受到 {} 点伤害，剩余 HP：{}/{}，格挡：{}。".format(
            self.name,
            real_damage,
            self.hp,
            self.max_hp,
            self.block
        )

    def status_text(self):
        return "{} HP：{}/{}，费用：{}/{}，格挡：{}，状态：{}".format(
            self.name,
            self.hp,
            self.max_hp,
            self.cost,
            self.max_cost,
            self.block,
            get_status_display_text(self.statuses)
        )
    
    def relics_text(self):
        lines = []
        lines.append("=== 已有遗物 ===")

        if not self.relics:
            lines.append("当前没有遗物。")
            return "\n".join(lines)

        for index, relic in enumerate(self.relics):
            lines.append("[{}] {}".format(index, relic.summary_text()))

        return "\n".join(lines)

    def pile_text(self, pile_name, title):
        pile = getattr(self, pile_name)

        lines = []
        lines.append("=== {} ===".format(title))
        lines.append("数量：{}".format(len(pile)))

        if not pile:
            lines.append("空。")
            return "\n".join(lines)

        for index, card in enumerate(pile):
            lines.append("[{}] {}".format(index, card.summary_text()))

        return "\n".join(lines)

    def draw_pile_text(self):
        return self.pile_text("draw_pile", "抽牌堆")

    def discard_pile_text(self):
        return self.pile_text("discard_pile", "弃牌堆")

    def exhaust_pile_text(self):
        return self.pile_text("exhaust_pile", "消耗牌堆")

    def hand_text(self, game_state=None):
        if not self.hand:
            return "当前没有手牌。"

        lines = []
        lines.append("当前手牌：")

        for index, card in enumerate(self.hand):
            line = "[{}] {}".format(index, card.summary_text())
            if game_state is not None:
                from game.card_preview import format_card_actual_preview
                preview_text = format_card_actual_preview(game_state, card)
                if preview_text:
                    line += " | {}".format(preview_text)
            lines.append(line)
        return "\n".join(lines)
    
    def get_status_value(self, key):
        return self.statuses.get(key)

    def gain_status(self, key, amount):
        from game.status.status_gain import add_status_with_artifact
        result = add_status_with_artifact(self, key, amount)
        return result["current"]

    def gain_status_with_result(self, key, amount):
        from game.status.status_gain import add_status_with_artifact
        return add_status_with_artifact(self, key, amount)

    @property
    def dexterity(self):
        return self.get_status_value("dexterity")

    @dexterity.setter
    def dexterity(self, value):
        self.statuses.set("dexterity", value)

    def potions_text(self):
        lines = []
        lines.append("=== 药水 ===")
        lines.append("数量：{}/{}".format(
            len(self.potions),
            self.max_potion_slots
        ))

        if not self.potions:
            lines.append("当前没有药水。")
            return "\n".join(lines)

        for index, potion in enumerate(self.potions):
            lines.append("[{}] {}".format(index, potion.summary_text()))

        return "\n".join(lines)