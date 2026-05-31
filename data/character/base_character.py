# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List


@dataclass
class CharacterTemplate:
    """
    角色模板。

    注意：
    这里描述的是角色初始配置，不是战斗中的玩家状态。
    战斗中的 hp、力量、格挡、手牌等，后面应该由 PlayerState / GameState 管理。
    """

    character_id: str
    name: str
    max_hp: int
    max_cost: int
    starting_relic_ids: List[str] = field(default_factory=list)
    starting_deck_ids: List[str] = field(default_factory=list)
    starting_potion_ids: List[str] = field(default_factory=list)
    max_potion_slots: int = 3
    starting_gold : int = 99

    def summary_text(self):
        lines = []
        lines.append("角色：{}".format(self.name))
        lines.append("ID：{}".format(self.character_id))
        lines.append("初始 HP：{}".format(self.max_hp))
        lines.append("初始费用：{}".format(self.max_cost))
        lines.append("初始金币：{}".format(self.starting_gold))
        lines.append("初始遗物：{}".format(", ".join(self.starting_relic_ids)))
        lines.append("初始牌组：{}".format(", ".join(self.starting_deck_ids)))
        lines.append("初始药水：{}".format(", ".join(self.starting_potion_ids)))
        return "\n".join(lines)