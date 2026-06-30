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
    # 药水稀有度。当前用于商店价格。
    quantity: str = "common"
    owner_character_id: str = ""
    effect_vars: Dict[str, Any] = field(default_factory=dict)
    effects: List[Dict[str, Any]] = field(default_factory=list)

    consume_on_use: bool = True

    def summary_text(self):
        from game.display_names import format_potion_display_name

        return "{}{}：{}".format(
            format_potion_display_name(self),
            self.potion_id,
            self.description
        )
