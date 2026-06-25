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


class BloodyIdolRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.bloody_idol", name="鲜血神像",
            description="每当你获得金币时，回复 5 点生命。",
            story="这个形似鸮形目鸟类的神像现在一直在流着血泪。", quantity="event", owner_character_id="", allow_duplicate=False)


class EnchiridionRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.enchiridion", name="英雄宝典",
            description="每场战斗开始时增加一张随机能力牌到你的手牌，这张牌在第一回合的耗能变为 0。",
            story="一名古老巫妖的传奇日志。", quantity="event", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        import random, copy
        from data.card.AAAregistry import create_card
        from data.content_gate import filter_card_ids
        from game.reward import get_card_reward_pool, CARD_REWARD_POOL
        run_state = getattr(context.game_state, "run_state", None)
        pool = get_card_reward_pool(run_state, ignore_prismatic=True) if run_state is not None else filter_card_ids(CARD_REWARD_POOL)
        power_ids = []
        for card_id in pool:
            try:
                card = create_card(card_id)
            except Exception:
                continue
            if getattr(card, "card_type", "") == "power" and getattr(card, "quantity", "") not in ("starting", "status", "curse", "test"):
                power_ids.append(card_id)
        if not power_ids:
            return ["【{}】触发，但没有可生成的能力牌。".format(self.name)]
        rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + int(getattr(context.game_state, "turn_count", 1)) + 7177) if run_state is not None else random
        card = create_card(rng.choice(power_ids))
        setattr(card, "temporary", True)
        setattr(card, "created_in_battle", True)
        setattr(card, "temporary_cost_override", 0)
        player = context.player
        if player.is_hand_full():
            player.discard_pile.append(card)
            return ["【{}】触发：手牌已满，随机能力牌【{}】进入弃牌堆。本回合费用变为 0。".format(self.name, card.name)]
        player.hand.append(card)
        return ["【{}】触发：随机能力牌【{}】加入手牌，本回合费用变为 0。".format(self.name, card.name)]


class NecronomiconRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.necronomicon", name="死灵之书",
            description="你每回合打出的第一张耗能大于等于 2 的攻击牌将被打出两次。拾起时被诅咒。",
            story="只有傻瓜才会想要去掌控这种邪恶的力量。你每晚的梦境中都充斥着这本书将你的心智逐渐吞噬的噩梦。\n“密大图书馆里有，记载了大量能够乱人神智的禁忌知识……嗯，老实说，我喜欢这个。”——炼金师", quantity="event", owner_character_id="", allow_duplicate=False)

    def on_obtained(self, run_state):
        from data.card.AAAregistry import create_card
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics
        return add_card_to_master_deck_with_relics(run_state, create_card("card.curse.necronomicurse"), source=self.name)


class NilrysCodexRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.nilrys_codex", name="尼利的宝典",
            description="在每回合结束时，你可以从 3 张随机牌中选择 1 张，随机洗入你的抽牌堆。",
            story="由臭名昭著的游戏大师本人编制，据说能拓宽人的心智。", quantity="event", owner_character_id="", allow_duplicate=True)

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_END
        if event_name != EVENT_TURN_END:
            return []
        from game.engine import queue_nilrys_codex_selection
        return queue_nilrys_codex_selection(context.game_state, self.name)


class NlothsGiftRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.nloths_gift", name="恩洛斯的礼物",
            description="使你在怪物奖励中遇见稀有牌的几率变为 3 倍。",
            story="恩洛斯给你的奇怪礼物，每次你试着拆开包装时，都会从里面找到另一个相同大小且包装完好的盒子。", quantity="event", owner_character_id="", allow_duplicate=False)


class MarkOfTheBloomRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.mark_of_the_bloom", name="绽放印记",
            description="你无法再回复生命。",
            story="在高塔的深处，思维与现实成为了一体。", quantity="event", owner_character_id="", allow_duplicate=False)


class NlothsMaskRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.nloths_mask", name="恩洛斯的饥饿的脸",
            description="你打开的下一个非 Boss 宝箱将是空的。",
            story="你觉得好饿。", quantity="event", owner_character_id="", allow_duplicate=False)
        self.charges = 1


class FaceOfClericRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.face_of_cleric", name="牧师的脸",
            description="每场战斗后你的最大生命值增加 1。",
            story="人人都爱牧师。", quantity="event", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_END
        if event_name != EVENT_BATTLE_END:
            return []
        player = context.player
        old_max = int(getattr(player, "max_hp", 0))
        old_hp = int(getattr(player, "hp", 0))
        player.max_hp = old_max + 1
        # 最大生命提升保留现有生命，不视为回复。
        return ["【{}】触发：最大生命值 {} -> {}，HP：{} -> {}。".format(self.name, old_max, player.max_hp, old_hp, player.hp)]


class CultistMaskRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.cultist_mask", name="邪教徒头套",
            description="你觉得自己有开腔的欲望。除此之外，没有任何作用。",
            story="自己人！自己人！", quantity="event", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        import random
        line = random.choice(["我的力量无人能及！", "咔！咔咔！（CAW! CAAAW！）", "谷咕固！！谷咕固！"])
        return ["【{}】触发：{}".format(self.name, line)]


class GremlinMaskRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.gremlin_mask", name="地精容貌",
            description="在每场战斗开始时，你拥有 1 层虚弱。",
            story="呜哇，好想逃跑。", quantity="event", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        current = context.player.gain_status("weak", 1)
        return ["【{}】触发：获得 1 层虚弱。当前虚弱：{}。".format(self.name, current)]


class MutagenicStrengthRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.mutagenic_strength", name="突变之力",
            description="在每场战斗开始时获得 3 点力量，在你的第一个回合结束时失去 3 点力量。",
            story="“效果似乎稍纵即逝，只在危险时才会触发。”——佚名", quantity="event", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        player = context.player
        s = player.gain_status("strength", 3)
        f = player.gain_status("flex", 3)
        return ["【{}】触发：获得 3 点力量与 3 层活动肌肉。当前力量：{}，活动肌肉：{}。".format(self.name, s, f)]
