# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class CalipersRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.calipers",
            name="外卡钳",
            description="在你的回合开始时，不再失去所有格挡，而是失去 15 点格挡。",
            story="",
            quantity="rare",
            owner_character_id=""
        )

    def get_turn_start_block_loss(self, game_state, player, old_block):
        return 15
    
class KeystoneOfTheTombRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.keystone_of_the_tomb",
            name="墓塔楔石",
            description="每打出 6 张技能牌，将 1 张【灵魂】加入抽牌堆。",
            story="封印由邪恶的念想带来的邪崇之物的重要石头。有时能从石头里听到悲哭的声音。\n“……花岩怪从来没有否认过自己是六火亡魂。”",
            quantity="rare",
            owner_character_id="",
            allow_duplicate=False
        )

        # 跨整局累计，不在战斗开始时重置。
        self.skill_play_count = 0

    def on_event(self, event_name, context):
        logs = []

        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER:
            return logs

        game_state = getattr(context, "game_state", None)
        player = getattr(context, "player", None)
        card = getattr(context, "card", None)

        if game_state is None or player is None or card is None:
            return logs

        if getattr(card, "card_type", "") != "skill":
            return logs

        self.skill_play_count += 1

        # 非 6 的倍数不触发。
        if self.skill_play_count % 6 != 0:
            return logs

        # 彩蛋：第 108、216、324... 张技能牌时，替换当次普通触发。
        # 这一段不写进遗物 description。
        if self.skill_play_count % 108 == 0:
            logs.append("【{}】中传来了悲哭的声音。".format(self.name))
            logs.extend(self._add_soul_plus_to_hand_or_discard(game_state))
            return logs

        logs.extend(self._add_soul_to_draw_pile(game_state))
        return logs

    def _make_soul_card(self, upgraded=False):
        from data.card.AAAregistry import create_card

        card = create_card("card.soul")

        if upgraded:
            from data.card.upgrade_rules import upgrade_card
            card = upgrade_card(card)

        setattr(card, "temporary", True)
        setattr(card, "created_in_battle", True)
        return card

    def _add_soul_to_draw_pile(self, game_state):
        import random

        player = game_state.player
        soul = self._make_soul_card(upgraded=False)

        player.draw_pile.append(soul)
        random.shuffle(player.draw_pile)

        return ["【{}】触发：打出第 {} 张技能牌，将 1 张【{}】加入抽牌堆，并重洗抽牌堆。".format(
            self.name,
            self.skill_play_count,
            soul.name
        )]

    def _add_soul_plus_to_hand_or_discard(self, game_state):
        player = game_state.player
        soul = self._make_soul_card(upgraded=True)

        if player.is_hand_full():
            player.discard_pile.append(soul)
            return ["【{}】特殊触发：手牌已满，1 张【{}】进入弃牌堆。".format(
                self.name,
                soul.name
            )]

        player.hand.append(soul)
        return ["【{}】特殊触发：将 1 张【{}】加入手牌。".format(
            self.name,
            soul.name
        )]