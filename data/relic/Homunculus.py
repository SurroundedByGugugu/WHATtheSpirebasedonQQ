# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class HomunculusPrototypeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.homunculus_prototype",
            name="造物原型",
            story="炼金师已停用的荷姆克鲁斯……收集多个可能会有其他事发生？……\n掷骰子的鲸的原型。给予解答的树的原型。于此显现。",
            description="你已经拿到所有可能出现的遗物了！",
            quantity="ENDER",
            allow_duplicate=True
        )

# 好吧哥们值得单开一桌
