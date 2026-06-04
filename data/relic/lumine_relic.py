# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.constants import EVENT_BATTLE_START, EVENT_CARD_PLAY_AFTER


class CrossEarringRelic(RelicTemplate):
    """
    十字架耳坠：
    每打出 4 张技能牌，获得 1 点敏捷。

    计数按战斗内计算：
    - 每场战斗开始时重置为 0
    - 每打出 1 张 skill 牌，计数 +1
    - 到 4 后获得 1 点敏捷并清零
    """

    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.cross_earring",
            name="十字架耳坠",
            story="……",
            description="每打出 4 张技能牌，获得 1 点敏捷。",
            quantity="starting",
            owner_character_id="character.lumine"
        )

        self.skill_play_count = 0

    def on_event(self, event_name, context):
        logs = []
        player = context.player
        if player is None:
            return logs
        if event_name == EVENT_BATTLE_START:
            self.skill_play_count = 0
            return logs
        if event_name != EVENT_CARD_PLAY_AFTER:
            return logs
        card = context.card
        if card is None:
            return logs
        if getattr(card, "card_type", "") != "skill":
            return logs
        self.skill_play_count += 1
        if self.skill_play_count < 4:
            logs.append("【{}】计数：技能牌 {}/4。".format(
                self.name,
                self.skill_play_count
            ))
            return logs

        self.skill_play_count = 0
        current = player.gain_status("dexterity", 1)

        logs.append("【{}】触发：打出第 4 张技能牌，获得 1 点敏捷。当前敏捷：{}。".format(
            self.name,
            current
        ))

        return logs