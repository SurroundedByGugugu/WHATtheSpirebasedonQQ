# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class SaturatedFissureRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.saturated_fissure",
            name="饱和裂隙",
            story="上溢的深渊。无法再容纳的容器。",
            description="展开 Zone 时自动升为极 Zone。",
            quantity="starting",
            owner_character_id="character.yoirine"
        )

    def modify_zone_deploy(self, context):
        return {
            "force_extreme": True,
            "logs": [
                "【{}】触发：展开 Zone 时自动再次展开，升级为极 Zone。".format(self.name)
            ]
        }