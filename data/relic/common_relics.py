# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class EtherMediumRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ether_medium",
            name="以太介质",
            description="每张牌在该场战斗中第一次打出时，无视自身属性 tag，获得当前 Zone 效果。该效果不影响敌人。",
            story="并非元素本身，只是让元素暂时有了落脚处。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
