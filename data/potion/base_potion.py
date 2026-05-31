# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class PotionTemplate:
    """
    药水 / 战斗道具模板。

    药水复用 effects 结构：
    - gain_status
    - deal_damage
    - gain_block
    - draw_cards
    - gain_energy
    """

    potion_id: str
    name: str
    description: str
    target: str = "self"

    effect_vars: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)

    consume_on_use: bool = True

    def summary_text(self):
        return "【{}】{}：{}".format(
            self.name,
            self.potion_id,
            self.description
        )