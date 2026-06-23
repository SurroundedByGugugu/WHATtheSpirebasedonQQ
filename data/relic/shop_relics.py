# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class XPotionRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.x_potion",
            name="X药",
            story="看起来像炼成失败的东西。装着黑色液体的瓶子上画了大大的“×”号。",
            description="你打出 X 费用牌时，X + 2。",
            quantity="shop"
        )

    def modify_x_value(self, x, context):
        new_x = x + 2

        card = context.card
        card_name = "X费用牌"

        if card is not None:
            card_name = card.name

        return new_x, [
            "【{}】触发：【{}】的 X + 2。".format(
                self.name,
                card_name
            )
        ]

class TwistedFunnelRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.twisted_funnel",
            name="扭曲漏斗",
            description="在每场战斗开始时，给予所有敌人 4 层中毒。",
            story="“个人建议不要用这个来喝东西。”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
        logs = ["【{}】触发。".format(self.name)]
        for enemy in getattr(context.game_state, "enemies", []) or []:
            if enemy.is_alive():
                logs.extend(apply_status_with_player_relics(
                    game_state=context.game_state,
                    source=context.player,
                    target=enemy,
                    status_key="poison",
                    amount=4
                ))
        return logs


class MembershipCardRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.membership_card",
            name="会员卡",
            description="所有商品打折 50%！",
            story="“会员资格！只有本店最尊贵的客人，才有机会获得哦！”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )


class DragonFruitRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.dragon_fruit",
            name="火龙果",
            description="每当你获得金币时，提升 1 点你的最大生命值。",
            story="一种生在在干旱地区，但是储水很多的果实。",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )


class MedicalKitRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.medical_kit",
            name="医药箱",
            description="可以打出原本不能被打出的状态牌。打出状态牌会将其消耗。",
            story="“什么都有！治痒痒、治烧伤、治中毒，应有尽有！”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def can_play_card(self, game_state, card, play_reason):
        if getattr(card, "card_type", "") == "status" and card.has_keyword("unplayable"):
            return True, "【医药箱】允许打出状态牌。"
        return None

