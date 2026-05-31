# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class XPotionRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.x_potion",
            name="X药",
            story="看起来像炼成失败的东西。装着黑色液体的瓶子上画了大大的“×”号。",
            description="你打出 X 费用牌时，X + 2。",
            quantity="shop"
        )

    def modify_x_value(self, x, context):
        new_x = x + 2

        card = context.card
        card_name = "X费用牌"

        if card is not None:
            card_name = card.name

        return new_x, [
            "【{}】触发：【{}】的 X + 2。".format(
                self.name,
                card_name
            )
        ]