# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.constants import EVENT_TURN_START, EVENT_CARD_PLAY_AFTER


class PlaceholderStoneRelic(RelicTemplate):
    """
    占位符石头。

    测试用途：
    1. 回合开始触发器
    2. 打出技能牌触发器
    """

    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.placeholder_stone",
            name="龙舞石",
            story="最初world.test(target);时使用的一块石头，因为有太过强大的力量被封印了。",
            description="每回合开始时和每打出一张技能牌时，获得 1 点力量和 1 点敏捷。",
            quantity="test",
        )

    def on_event(self, event_name, context):
        logs = []
        player = context.player

        if player is None:
            return logs

        if event_name == EVENT_TURN_START:
            player.gain_status("strength", 1)
            player.gain_status("dexterity", 1)
            logs.append("【{}】触发：回合开始，获得 1 点力量和 1 点敏捷。".format(self.name))
            return logs

        if event_name == EVENT_CARD_PLAY_AFTER:
            card = context.card

            if card is None:
                return logs

            if getattr(card, "card_type", "") == "skill":
                player.gain_status("strength", 1)
                player.gain_status("dexterity", 1)
                logs.append("【{}】触发：打出技能牌【{}】，获得 1 点力量和 1 点敏捷。".format(
                    self.name,
                    card.name
                ))

        return logs