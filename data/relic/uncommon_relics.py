# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.relic_logic.bottle_utils import start_pending_bottle_selection


class EtherMediumRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ether_medium",
            name="以太介质",
            description="每张牌在该场战斗中第一次打出时，无视自身属性 tag，获得当前 Zone 效果。",
            story="第五元素。（哦如果看到这里了现在的测试版本不建议买这个，除了某个角色暂时没有稳定开启zone的手段。拿了的话祝您战未来愉快？）",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

class BottledLightningRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.bottled_lightning",
            name="瓶装闪电",
            description="拾起时，选择一张技能牌。在每场战斗开始时，这张牌会出现在手牌中。",
            story="细看这团旋转的雷云，你仿佛能看见自己的一部分在回望着你。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        return start_pending_bottle_selection(run_state, self.relic_id, self.name, "skill")

class BottledFlameRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.bottled_flame",
            name="瓶装火焰",
            description="拾起时，选择一张攻击牌。在每场战斗开始时，这张牌会出现在手牌中。",
            story="在这个瓶子里，有着一团永远燃烧的火焰。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        return start_pending_bottle_selection(run_state, self.relic_id, self.name, "attack")

class BottledTornadoRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.bottled_tornado",
            name="瓶装旋风",
            description="拾起时，选择一张能力牌。在每场战斗开始时，这张牌会出现在手牌中。",
            story="这个瓶子中传来轻轻的嗡嗡声与嗖嗖声。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        return start_pending_bottle_selection(run_state, self.relic_id, self.name, "power")

