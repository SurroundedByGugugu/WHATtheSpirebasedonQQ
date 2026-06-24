# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.constants import EVENT_TURN_START, EVENT_CARD_PLAY_AFTER


class BlackBloodRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.black_blood", name="黑暗之血",
            description="替换燃烧之血。在战斗结束时，回复 12 点生命。",
            story="你的愤怒变得更加黑暗。", quantity="myth", owner_character_id="character.armored_warrior", allow_duplicate=False)

    def on_obtained(self, run_state):
        logs = []
        for index, relic in enumerate(list(getattr(run_state, "relics", []) or [])):
            if getattr(relic, "relic_id", "") == "relic.burning_blood":
                run_state.relics.pop(index)
                logs.append("【{}】替换了【燃烧之血】。".format(self.name))
                break
        return logs

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_END
        if event_name != EVENT_BATTLE_END:
            return []
        from game.relic_logic.combat_relic_utils import heal_player_in_combat
        return heal_player_in_combat(context.game_state, 12, self.name)

