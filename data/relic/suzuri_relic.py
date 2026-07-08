# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.constants import EVENT_BATTLE_START, EVENT_DAMAGE_AFTER


class PiercingLanceRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.piercing_lance",
            name="“贯岩”",
            story="坚硬的重型骑枪。锐利的尖端仿佛能贯穿一切阻碍。",
            description="每场战斗第一次，攻击被完全格挡时，直接破除全部格挡。",
            quantity="starting",
            owner_character_id="character.suzuri",
            allow_duplicate=False,
        )
        self.used_this_battle = False

    def on_event(self, event_name, context):
        if event_name == EVENT_BATTLE_START:
            self.used_this_battle = False
            return []

        if event_name != EVENT_DAMAGE_AFTER:
            return []

        if self.used_this_battle:
            return []

        game_state = getattr(context, "game_state", None)
        player = getattr(context, "player", None)
        source = getattr(context, "source", None)
        target = getattr(context, "target", None)
        card = getattr(context, "card", None)
        extra = getattr(context, "extra", {}) or {}

        if game_state is None or player is None:
            return []
        if source is not player:
            return []
        if target is None or not hasattr(target, "enemy_id"):
            return []
        if getattr(card, "card_type", "") != "attack":
            return []
        if extra.get("damage_kind") != "attack":
            return []
        if bool(extra.get("ignore_block", False)):
            return []
        if int(extra.get("amount", 0) or 0) <= 0:
            return []
        if int(extra.get("real_damage", 0) or 0) != 0:
            return []

        current_block = int(getattr(target, "block", 0) or 0)
        if current_block <= 0:
            return []

        self.used_this_battle = True
        target.block = 0

        return [
            "【{}】触发：【{}】的攻击被完全格挡，破除【{}】全部 {} 点格挡。".format(
                self.name,
                getattr(card, "name", "攻击牌"),
                getattr(target, "name", "敌人"),
                current_block
            )
        ]
    
class NostalgicCrystalRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.nostalgic_crystal",
            name="令人怀念的结晶",
            description="拾起时，在牌组中添加 1 张【辉晶映照】。",
            story="带着温度的灰色结晶。边缘仿佛被深渊浸染，但没有表现出深渊的攻击性。",
            quantity="common",
            owner_character_id="character.suzuri",
            allow_duplicate=False,
        )

    def on_obtained(self, run_state):
        from data.card.AAAregistry import create_card
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics

        card = create_card("card.radiant_crystal_reflection")
        return add_card_to_master_deck_with_relics(run_state, card, source=self.name)

class StalactiteRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.stalactite",
            name="钟乳石",
            description="战斗开始时，获得等于当前阶段数的岩层。若被饱和碳酸钙溶液强化，则额外增加对应层数。",
            story="“一种锥形的岩溶生成物……”",
            quantity="common",
            owner_character_id="",
            allow_duplicate=False,
        )
        self.extra_rock_layer = 0

    def increase_start_rock_layer(self, amount=1):
        self.extra_rock_layer = int(getattr(self, "extra_rock_layer", 0) or 0) + int(amount)

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []

        run_state = getattr(context.game_state, "run_state", None)

        try:
            from game.route import get_current_route_act
            act = get_current_route_act(run_state)
        except Exception:
            act = 1

        act = max(1, min(3, int(act)))
        extra = int(getattr(self, "extra_rock_layer", 0) or 0)
        amount = act + extra

        from game.suzuri_rock import gain_rock_layer

        logs = ["【{}】触发：当前阶段为 {}，获得 {} 层岩层。".format(
            self.name,
            act,
            amount
        )]

        logs.extend(gain_rock_layer(
            game_state=context.game_state,
            target=context.player,
            amount=amount,
            source_name=self.name
        ))

        return logs
