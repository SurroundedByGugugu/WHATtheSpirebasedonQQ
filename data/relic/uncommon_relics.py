# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class EtherMediumRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ether_medium",
            name="以太介质",
            description="每张牌在该场战斗中第一次打出时，无视自身属性 tag，获得当前 Zone 效果。",
            story="第五元素。（哦如果看到这里了现在的测试版本不建议买这个，除了某个角色暂时没有任何正常开启zone的手段）",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
