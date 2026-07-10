# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Dict, List, Any




@dataclass
class CardTemplate:
    """
    卡牌模板。

    这里只描述卡牌本身的数据，不负责真正结算。
    真正结算由 game/effects.py 和 game/engine.py 处理。
    """

    card_id: str
    name: str
    card_type: str
    cost: Any
    target: str
    description: str

    quantity:str  # starting, common, uncommon, rare, myth,

    attack_type: str = ""       #slash/piercing/blunt/magic
    attack_element: str = ""    #fire/earth/wind/water/thunder/shade/crystal
    skip_auto_zone_hp_loss: bool = False
    ignore_zone_replay: bool = False
    owner_character_id: str = ""
    # 卡牌变量，例如 damage、block、base_damage、strength_multiplier
    card_vars: Dict[str, Any] = field(default_factory=dict)

    # X 费用规则。
    # 例如：
    # [{"op": "if_ge_mul", "threshold": 3, "multiplier": 2}]
    x_rules: List[Dict[str, Any]] = field(default_factory=list)

    # 动态费用规则，例如以血还血：本场战斗每失去生命一次，费用 -1
    cost_rules: List[Dict[str, Any]] = field(default_factory=list)
    # 是否允许重复升级，例如灼热攻击
    multi_upgrade: bool = False
    # 已升级次数，主要给灼热攻击这类多次升级牌使用
    upgrade_count: int = 0
    
    # 出牌条件，例如交锋：手牌必须全是攻击牌
    play_conditions: List[Dict[str, Any]] = field(default_factory=list)

    # 被消耗时触发的效果，例如哨卫：被消耗时获得能量
    exhaust_effects: List[Dict[str, Any]] = field(default_factory=list)
    
    # 效果列表，例如 deal_damage / gain_block / gain_status
    effects: List[Dict[str, Any]] = field(default_factory=list)

    # 关键词，后面可以放 exhaust / retain / ethereal 等
    keywords: List[str] = field(default_factory=list)

    # 附魔，与 keywords 平行。
    # 允许多个附魔，也允许同名附魔重复叠加。
    enchanted: List[str] = field(default_factory=list)

    upgraded: bool = False
    upgrade_patch: Dict[str, Any] = field(default_factory=dict)

    def summary_text(self):
        """
        手牌、牌组和各种卡牌选择界面使用的简略文本。
        """
        from data.card.keyword_rules import (
            get_card_keyword_display_text
        )
        from data.card.enchantment_rules import (
            get_card_enchantment_display_text
        )
        from game.display_names import format_card_display_name

        keyword_text = get_card_keyword_display_text(self)
        enchantment_text = get_card_enchantment_display_text(self)
        display_name = format_card_display_name(self)

        extra_parts = []

        if keyword_text:
            extra_parts.append("[{}]".format(keyword_text))

        if enchantment_text:
            extra_parts.append("[{}]".format(enchantment_text))

        if extra_parts:
            return "{}{}费 {} {}：{}".format(
                display_name,
                self.cost,
                self.card_type,
                " ".join(extra_parts),
                self.description
            )

        return "{}{}费 {}：{}".format(
            display_name,
            self.cost,
            self.card_type,
            self.description
        )

    def has_keyword(self, keyword):
        return keyword in self.keywords
    
    def is_enchanted(self):
        return bool(getattr(self, "enchanted", []))


    def has_enchantment(self, enchantment_id):
        from data.card.enchantment_rules import (
            has_card_enchantment
        )

        return has_card_enchantment(
            self,
            enchantment_id
        )


    def get_enchantment_stacks(self, enchantment_id):
        from data.card.enchantment_rules import (
            get_card_enchantment_stacks
        )

        return get_card_enchantment_stacks(
            self,
            enchantment_id
        )