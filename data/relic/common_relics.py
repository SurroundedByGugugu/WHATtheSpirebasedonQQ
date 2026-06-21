# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate



class JuzuBraceletRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.juzu_bracelet",
            name="佛珠手链",
            description="你在 ? 房间中不会再遭遇常规战斗。",
            story="抵御未知危险的护身道具。",
            quantity="common",
            owner_character_id="",
            allow_duplicate=False
        )


class TinyChestRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.tiny_chest",
            name="小宝箱",
            description="每 4 个 ? 房间的最后一个必是宝箱房。",
            story="“作为原型而言相当不错。”——建筑师",
            quantity="common",
            owner_character_id="",
            allow_duplicate=False
        )
