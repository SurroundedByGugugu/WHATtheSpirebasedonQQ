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

    owner_character_id: str = ""
    # 卡牌变量，例如 damage、block、base_damage、strength_multiplier
    card_vars: Dict[str, Any] = field(default_factory=dict)

    # X 费用规则。
    # 例如：
    # [{"op": "if_ge_mul", "threshold": 3, "multiplier": 2}]
    x_rules: List[Dict[str, Any]] = field(default_factory=list)

    # 效果列表，例如 deal_damage / gain_block / gain_status
    effects: List[Dict[str, Any]] = field(default_factory=list)

    # 关键词，后面可以放 exhaust / retain / ethereal 等
    keywords: List[str] = field(default_factory=list)
    
    upgraded: bool = False
    upgrade_patch: Dict[str, Any] = field(default_factory=dict)

    def summary_text(self):
        """
        手牌显示用文本。
        """
        from data.card.keyword_rules import get_card_keyword_display_text

        keyword_text = get_card_keyword_display_text(self)

        if keyword_text:
            return "【{}】{}费 {} [{}]：{}".format(
                self.name,
                self.cost,
                self.card_type,
                keyword_text,
                self.description
            )

        return "【{}】{}费 {}：{}".format(
            self.name,
            self.cost,
            self.card_type,
            self.description
        )

    def has_keyword(self, keyword):
        return keyword in self.keywords