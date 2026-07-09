# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class RingOfTheSnakeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ring_of_the_snake",
            name="蛇之戒指",
            description="在每场战斗开始时，额外抽 2 张牌。",
            story="用蛇的化石制成的戒指，优秀女猎手的象征。",
            quantity="starting",
            owner_character_id="character.silent_huntress",
            allow_duplicate=False,
        )

    def get_opening_draw_bonus(self, game_state=None, player=None):
        return 2


class RingOfTheSerpentRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ring_of_the_serpent",
            name="长蛇戒指",
            description="替换蛇之戒指。在你的每个回合开始时，额外抽 1 张牌。",
            story="你的戒指改变了形态，焕然一新。",
            quantity="myth",
            owner_character_id="character.silent_huntress",
            allow_duplicate=False,
        )

    def get_turn_draw_bonus(self, game_state=None, player=None):
        return 1

    def get_opening_draw_bonus(self, game_state=None, player=None):
        return 1

    def on_obtained(self, run_state):
        logs = []
        for index, relic in enumerate(list(getattr(run_state, "relics", []) or [])):
            if getattr(relic, "relic_id", "") == "relic.ring_of_the_snake":
                run_state.relics.pop(index)
                logs.append("【{}】替换了【蛇之戒指】。".format(self.name))
                break
        return logs