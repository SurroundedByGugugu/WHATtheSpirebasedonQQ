# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.constants import EVENT_BATTLE_END, EVENT_CARD_EXHAUST

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
            from game.relic_logic.combat_relic_utils import heal_player_in_combat
            logs.extend(heal_player_in_combat(context.game_state, 6, self.name))
            return logs
        return logs
    
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


class CharonAshesRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.charon_ashes",
            name="卡戎之灰",
            story="卡戎的……火车煤灰？谁让你把启光的运输长找过来了！谁让你从人家的彼岸号的炉子里掏一把煤灰说成是卡戎之灰了！",
            description="每当你 消耗 一张牌，对所有敌人造成 3 点伤害。",
            quantity="rare",
            owner_character_id="character.armored_warrior"
        )
    def on_event(self, event_name, context):
        logs = []
        if event_name != EVENT_CARD_EXHAUST:
            return logs
        game_state = context.game_state
        player = context.player
        card = context.card
        if game_state is None or player is None:
            return logs
        alive_enemies = [
            enemy for enemy in getattr(game_state, "enemies", [])
            if enemy.is_alive()
        ]
        if not alive_enemies:
            return logs
        card_name = getattr(card, "name", "一张牌")
        logs.append("【{}】触发：消耗【{}】，对所有敌人造成 3 点伤害。".format(
            self.name,
            card_name
        ))
        from game.damage import deal_damage
        for enemy in list(alive_enemies):
            if not enemy.is_alive():
                continue
            logs.extend(deal_damage(
                game_state=game_state,
                source=player,
                target=enemy,
                amount=3,
                damage_kind="effect",
                card=card,
                is_reaction_damage=True,
                ignore_block=False
            ))
        return logs
    