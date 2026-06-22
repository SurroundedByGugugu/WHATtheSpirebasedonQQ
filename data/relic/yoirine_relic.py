# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class SaturatedFissureRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.saturated_fissure",
            name="饱和裂隙",
            story="上溢的深渊。无法再容纳的容器。",
            description="展开 Zone 时自动升为极 Zone；同属性极 Zone 期间再次展开时，额外延长 2 回合。",
            quantity="starting",
            owner_character_id="character.yoirine"
        )

    def modify_zone_deploy(self, context):
        game_state = context.game_state
        element = str(context.extra.get("element", "")).strip().lower()
        current_zone = getattr(game_state, "active_zone", None)

        same_extreme_zone = (
            current_zone is not None
            and getattr(current_zone, "is_extreme", False)
            and not current_zone.is_expired()
            and str(getattr(current_zone, "element", "")).strip().lower() == element
        )

        if same_extreme_zone:
            return {
                "extreme_extend_bonus": 2,
                "logs": [
                    "【{}】触发：同属性极 Zone 再展开时，额外延长 2 回合。".format(self.name)
                ]
            }

        return {
            "force_extreme": True,
            "logs": [
                "【{}】触发：展开 Zone 时自动再次展开，升级为极 Zone。".format(self.name)
            ]
        }