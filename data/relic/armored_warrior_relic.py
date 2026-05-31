# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.constants import EVENT_BATTLE_END


class BurningBloodRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.burning_blood",
            name="燃烧之血",
            story="……",
            description="每场战斗结束时，恢复 6 点 HP。",
            quantity="starting",
            owner_character_id="character.armored_warrior"
        )
    def on_event(self, event_name, context):
        logs = []
        player = context.player
        if player is None:
            return logs
        if event_name == EVENT_BATTLE_END:
            old_hp = player.hp
            player.hp += 6
            if player.hp > player.max_hp:
                player.hp = player.max_hp
            real_heal = player.hp - old_hp
            if real_heal > 0:
                logs.append("【{}】触发：战斗结束时，HP 恢复 {}。".format(
                    self.name,
                    real_heal
                ))
            else:
                logs.append("【{}】触发：HP 已满，没有恢复。".format(
                    self.name
                ))
            return logs
        return logs