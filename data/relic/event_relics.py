# -*- coding: utf-8 -*-

import random

from data.relic.base_relic import RelicTemplate


class GoldenIdolRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.golden_idol",
            name="金神像",
            description="敌人掉落的金币增加 25%。不会增加被抢劫的偷走又在战斗后拿回来的金币。",
            story="用纯金制成的鸟形小雕像，只是拿在手里就让你觉得自己有钱了。鸟的形象像是鸮形目的。",
            quantity="event",
            owner_character_id="",
            allow_duplicate=False
        )

    def modify_battle_gold_reward(self, amount, context=None):
        return int(amount * 1.25)


class OddMushroomRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.odd_mushroom",
            name="奇怪蘑菇",
            description="当你有 易伤 状态时，受到的额外伤害从 50% 下降为 25%。",
            story="吃了寄生毛菇之后，我觉得自己更高大了，也更……不容易受伤了。——兰伟德\n尽管建造这座塔的炼金师不建议参观者食用这种……呃，来自外地的，入侵物种，但说到底这玩意不是TA自己引进的？",
            quantity="event",
            owner_character_id="",
            allow_duplicate=False
        )


class SsserpentHeadRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ssserpent_head",
            name="蛇的头",
            description="每次进入？房间时获得 50 金币。",
            story="最幸福的人生当然就是什么东西都能买得起的土豪生活了！",
            quantity="event",
            owner_character_id="",
            allow_duplicate=False
        )


class WarpedTongsRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.warped_tongs",
            name="弯曲铁钳",
            description="在你的每个回合开始时，随机升级一张你的手牌（只影响本场战斗）。",
            story="这对被偷来的诅咒铁钳上散发着强烈的怨念，它似乎十分想要回到原本的地方。",
            quantity="event",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_turn_start_hand_ready(self, game_state, player):
        from data.card.upgrade_rules import has_upgrade, upgrade_card

        candidates = []
        for index, card in enumerate(getattr(player, "hand", []) or []):
            if has_upgrade(card):
                candidates.append((index, card))
        if not candidates:
            return []
        index, card = random.choice(candidates)
        upgraded_card = upgrade_card(card)
        player.hand[index] = upgraded_card
        return ["【弯曲铁钳】随机强化手牌：【{}】 -> 【{}】。".format(card.name, upgraded_card.name)]


class SpiritPoopRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.spirit_poop",
            name="精灵便便",
            description="没有任何效果。",
            story="不管怎么看都很不舒服……",
            quantity="event",
            owner_character_id="",
            allow_duplicate=False
        )


class RedMaskRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.red_mask",
            name="红面具",
            description="在每场战斗开始时，给予所有敌人 1 层虚弱。",
            story="这副看起来十分帅气的面具属于红面具强盗团的头子，这么说来，现在你应该是他们的老大了？",
            quantity="event",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        from game.status.status_gain import format_status_gain_log
        logs = ["【{}】触发。".format(self.name)]
        for enemy in getattr(context.game_state, "enemies", []) or []:
            if not enemy.is_alive():
                continue
            if hasattr(enemy, "gain_status_with_result"):
                result = enemy.gain_status_with_result("weak", 1)
                logs.append(format_status_gain_log(enemy, "weak", 1, result))
            else:
                current = enemy.gain_status("weak", 1)
                logs.append("{} 获得 1 点虚弱。当前虚弱：{}。".format(enemy.name, current))
        return logs
