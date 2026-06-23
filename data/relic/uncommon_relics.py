# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate
from game.relic_logic.bottle_utils import start_pending_bottle_selection


class EtherMediumRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ether_medium",
            name="以太介质",
            description="每张牌在该场战斗中第一次打出时，无视自身属性 tag，获得当前 Zone 效果。",
            story="第五元素。（哦如果看到这里了现在的测试版本不建议买这个，除了某个角色暂时没有稳定开启zone的手段。拿了的话祝您战未来愉快？）",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

class BottledLightningRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.bottled_lightning",
            name="瓶装闪电",
            description="拾起时，选择一张技能牌。在每场战斗开始时，这张牌会出现在手牌中。",
            story="细看这团旋转的雷云，你仿佛能看见自己的一部分在回望着你。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        return start_pending_bottle_selection(run_state, self.relic_id, self.name, "skill")

class BottledFlameRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.bottled_flame",
            name="瓶装火焰",
            description="拾起时，选择一张攻击牌。在每场战斗开始时，这张牌会出现在手牌中。",
            story="在这个瓶子里，有着一团永远燃烧的火焰。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        return start_pending_bottle_selection(run_state, self.relic_id, self.name, "attack")

class BottledTornadoRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.bottled_tornado",
            name="瓶装旋风",
            description="拾起时，选择一张能力牌。在每场战斗开始时，这张牌会出现在手牌中。",
            story="这个瓶子中传来轻轻的嗡嗡声与嗖嗖声。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        return start_pending_bottle_selection(run_state, self.relic_id, self.name, "power")



class PearRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.pear",
            name="梨子",
            description="拾起时，将你的最大生命值提升 10。",
            story="在高塔荒疫发生之前十分常见的水果。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import increase_max_hp
        return increase_max_hp(run_state, 10, self.name)


class WarPaintRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.war_paint",
            name="战纹涂料",
            description="拾起时，随机升级 2 张技能牌。",
            story="在过去，铁甲军团的士兵们会在战斗前使用带有魔力的涂料来绘制保护性的战纹。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from data.relic.common_relics import _upgrade_random_cards_by_type
        return _upgrade_random_cards_by_type(run_state, "skill", 2, self.name)


class TheCourierRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.the_courier",
            name="送货员",
            description="商人的卡牌、遗物和药水不再会卖光，并且所有商品打折 20%。",
            story="这是商人的宠物！",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class HornCleatRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.horn_cleat",
            name="船夹板",
            description="在你的第二回合开始时，获得 14 点格挡。",
            story="拿在手里有一种莫名的愉悦感，这是什么东西呢？",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name != EVENT_TURN_START or int(getattr(context.game_state, "turn_count", 1)) != 2:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(
            game_state=context.game_state,
            source=context.player,
            target=context.player,
            amount=14,
            block_source="horn_cleat",
            card=None,
            message="【{}】触发：第二回合开始，获得 14 点格挡。当前格挡：{}。".format(self.name, context.player.block + 14)
        )


class BlueCandleRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.blue_candle",
            name="蓝蜡烛",
            description="可以打出原本不能被打出的诅咒牌。打出诅咒牌会让你失去 1 点生命并将其消耗。",
            story="当处于黑暗中时，这支蜡烛会自动点燃。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def can_play_card(self, game_state, card, play_reason):
        if getattr(card, "card_type", "") == "curse" and card.has_keyword("unplayable"):
            return True, "【蓝蜡烛】允许打出诅咒牌。"
        return None


class EternalFeatherRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.eternal_feather",
            name="永恒羽毛",
            description="你牌组中每有 5 张牌，当你进入休息处时就会回复 3 点生命。",
            story="这片羽毛似乎完全无法摧毁，会是从什么鸟身上来的呢？",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class FrozenEggRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.frozen_egg",
            name="冻结之蛋",
            description="每当你获得能力牌时，将其升级。奖励、商店与事件中见到的能力牌会直接以已升级状态呈现。",
            story="这个蛋冻结着，没有丝毫生气，永远也不会孵化。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.max_reward_floor = 48


class ToxicEggRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.toxic_egg",
            name="毒素之蛋",
            description="每当你获得技能牌时，将其升级。奖励、商店与事件中见到的技能牌会直接以已升级状态呈现。",
            story="“真是了不起的发现！这似乎是某种魔法生物已经不起作用了的蛋，究竟是谁或什么制造了这东西呢？”——兰伟德",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.max_reward_floor = 48


class MoltenEggRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.molten_egg",
            name="熔火之蛋",
            description="每当你获得攻击牌时，将其升级。奖励、商店与事件中见到的攻击牌会直接以已升级状态呈现。",
            story="凤凰的蛋，可以看到有岩浆在滋滋发热，红得发烫。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.max_reward_floor = 48


class DarkstonePeriaptRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.darkstone_periapt",
            name="黑石护符",
            description="每当你获得一张诅咒，将你的最大生命值提高 6。",
            story="这块黑石能吸取黑暗的能量，将其转化为佩戴者的生命力。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.max_reward_floor = 48


class GremlinHornRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.gremlin_horn",
            name="地精之角",
            description="每当有一名敌人死亡，获得 1 点能量并抽 1 张牌。",
            story="“地精大块头到死都能一直长得更大，真是厉害。”——兰伟德",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_DAMAGE_AFTER
        if event_name != EVENT_DAMAGE_AFTER:
            return []
        target = getattr(context, "target", None)
        if target is None or not hasattr(target, "enemy_id"):
            return []
        if not bool(context.extra.get("target_was_alive", False)):
            return []
        if not bool(context.extra.get("target_is_dead_after", False)):
            return []
        if getattr(target, "_gremlin_horn_triggered", False):
            return []
        setattr(target, "_gremlin_horn_triggered", True)
        player = context.player
        player.cost += 1
        logs = ["【{}】触发：敌人【{}】死亡，获得 1 点能量并抽 1 张牌。当前费用：{}/{}。".format(
            self.name, getattr(target, "name", "敌人"), player.cost, player.max_cost
        )]
        logs.extend(player.draw_cards(1, game_state=context.game_state, draw_source="gremlin_horn"))
        return logs


class KunaiRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.kunai",
            name="苦无",
            description="你每在同一回合内打出 3 张攻击牌，获得 1 点敏捷。",
            story="受到刺客喜爱的远距离利刃。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER or getattr(context.card, "card_type", "") != "attack":
            return []
        counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
        if int(counts.get("attack", 0)) % 3 != 0:
            return []
        current = context.player.gain_status("dexterity", 1)
        return ["【{}】触发：本回合打出第 {} 张攻击牌，获得 1 点敏捷。当前敏捷：{}。".format(
            self.name, int(counts.get("attack", 0)), current
        )]


class ShurikenRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.shuriken",
            name="手里剑",
            description="你每在同一回合内打出 3 张攻击牌，获得 1 点力量。",
            story="轻型的投掷武器，尤其推荐对着眼睛扔。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER or getattr(context.card, "card_type", "") != "attack":
            return []
        counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
        if int(counts.get("attack", 0)) % 3 != 0:
            return []
        current = context.player.gain_status("strength", 1)
        return ["【{}】触发：本回合打出第 {} 张攻击牌，获得 1 点力量。当前力量：{}。".format(
            self.name, int(counts.get("attack", 0)), current
        )]


class OrnamentalFanRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ornamental_fan",
            name="精致折扇",
            description="你每在同一回合内打出 3 张攻击牌，就获得 4 点格挡。",
            story="这把折扇似乎会在洒到血时自动伸展并且变硬。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER or getattr(context.card, "card_type", "") != "attack":
            return []
        counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
        if int(counts.get("attack", 0)) % 3 != 0:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(
            game_state=context.game_state,
            source=context.player,
            target=context.player,
            amount=4,
            block_source="ornamental_fan",
            card=None,
            message="【{}】触发：本回合打出第 {} 张攻击牌，获得 4 点格挡。当前格挡：{}。".format(
                self.name, int(counts.get("attack", 0)), context.player.block + 4
            )
        )


class LetterOpenerRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.letter_opener",
            name="开信刀",
            description="你每在同一回合内打出 3 张技能牌，对所有敌人造成 5 点伤害。",
            story="锋利到不自然。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER or getattr(context.card, "card_type", "") != "skill":
            return []
        counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
        if int(counts.get("skill", 0)) % 3 != 0:
            return []
        from game.damage import deal_damage
        logs = ["【{}】触发：本回合打出第 {} 张技能牌，对所有敌人造成 5 点伤害。".format(
            self.name, int(counts.get("skill", 0))
        )]
        for enemy in list(getattr(context.game_state, "enemies", []) or []):
            if enemy.is_alive():
                logs.extend(deal_damage(
                    game_state=context.game_state,
                    source=context.player,
                    target=enemy,
                    amount=5,
                    damage_kind="relic",
                    card=None,
                    is_reaction_damage=False,
                    ignore_block=False
                ))
        return logs


class MatryoshkaRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.matryoshka",
            name="套娃",
            description="你接下来打开的 2 个宝箱内会有 2 件遗物。Boss 宝箱除外。",
            story="一套环环相套的娃娃，上面的图案是一只白眼蓝羽毛的鸟，你不知道这是只什么鸟。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.charges = 2

    def summary_text(self):
        return "{}：{}（剩余 {} 次）".format(self.name, self.description, int(getattr(self, "charges", 0)))


class MeatOnTheBoneRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.meat_on_the_bone",
            name="带骨肉",
            description="如果你在战斗结束时生命值等于或低于 50%，回复 12 点生命。",
            story="这块肉会不断恢复，似乎永远也不会彻底吃光。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_END
        if event_name != EVENT_BATTLE_END:
            return []
        player = context.player
        if player.hp * 2 > player.max_hp:
            return []
        from game.relic_logic.combat_relic_utils import heal_player_in_combat
        return heal_player_in_combat(context.game_state, 12, self.name)


class MercuryHourglassRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.mercury_hourglass",
            name="水银沙漏",
            description="在你的回合开始时，对所有敌人造成 3 点伤害。",
            story="一个附加魔力的沙漏，一直都在不断滴下水银。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name != EVENT_TURN_START:
            return []
        from game.damage import deal_damage
        logs = ["【{}】触发：对所有敌人造成 3 点伤害。".format(self.name)]
        for enemy in list(getattr(context.game_state, "enemies", []) or []):
            if enemy.is_alive():
                logs.extend(deal_damage(
                    game_state=context.game_state,
                    source=context.player,
                    target=enemy,
                    amount=3,
                    damage_kind="relic",
                    card=None,
                    is_reaction_damage=False,
                    ignore_block=False
                ))
        return logs


class MummifiedHandRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.mummified_hand",
            name="干瘪之手",
            description="你每打出一张能力牌，手牌中就有一张随机牌在这个回合耗能变为 0。",
            story="这只手经常都在抽动，尤其是在你心跳很快的时候。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER or getattr(context.card, "card_type", "") != "power":
            return []
        import random
        from game.card_cost import get_card_current_cost
        candidates = []
        for hand_card in getattr(context.player, "hand", []) or []:
            if getattr(hand_card, "card_type", "") in ("status", "curse"):
                continue
            try:
                current_cost = int(get_card_current_cost(context.game_state, hand_card))
            except (TypeError, ValueError):
                continue
            if current_cost > 0:
                candidates.append(hand_card)
        if not candidates:
            return ["【{}】触发，但手牌中没有可降费的牌。".format(self.name)]
        chosen = random.choice(candidates)
        setattr(chosen, "temporary_cost_override", 0)
        return ["【{}】触发：【{}】本回合费用变为 0。".format(self.name, chosen.name)]


class NinjaScrollRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ninja_scroll",
            name="忍术卷轴",
            description="每场战斗开始时，手牌中增加 3 张小刀。",
            story="暗杀秘术尽在其中。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        from data.card.AAAregistry import create_card
        logs = ["【{}】触发：加入 3 张【小刀】。".format(self.name)]
        for _ in range(3):
            card = create_card("card.shiv")
            setattr(card, "temporary", True)
            setattr(card, "created_in_battle", True)
            if context.player.is_hand_full():
                context.player.discard_pile.append(card)
                logs.append("手牌已满，【{}】进入弃牌堆。".format(card.name))
            else:
                context.player.hand.append(card)
                logs.append("【{}】加入手牌。".format(card.name))
        return logs


class PantographRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.pantograph",
            name="缩放仪",
            description="在 Boss 战开始时，回复 25 点生命值。",
            story="“坚实的地基从不是出自偶然，规划工具是重中之重。”——建筑师",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        run_state = getattr(context.game_state, "run_state", None) or getattr(context.player, "run_state", None)
        node_type = getattr(run_state, "current_battle_node_type", "") if run_state is not None else ""
        if node_type != "boss":
            return []
        from game.relic_logic.combat_relic_utils import heal_player_in_combat
        return heal_player_in_combat(context.game_state, 25, self.name)


class PaperCraneRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.paper_crane",
            name="纸鹤",
            description="有虚弱状态的敌人造成的伤害降低 40% 而非 25%。",
            story="某种过去时代生物的折纸。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class PaperFrogRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.paper_frog",
            name="纸蛙",
            description="有易伤状态的敌人受到的伤害增加 75% 而非 50%。",
            story="这张纸似乎会不断自己翻折，变成某种小动物的形状。",
            quantity="uncommon",
            owner_character_id="character.armored_warrior",
            allow_duplicate=False
        )


class QuestionCardRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.question_card",
            name="问号牌",
            description="在选奖励牌时，可供选择的牌数增加 1 张。",
            story="“选择多，则不受其乱。”——忽必烈大帝",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class SelfFormingClayRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.self_forming_clay",
            name="自成型黏土",
            description="每当你在战斗中失去生命，就在下回合获得 3 点格挡。",
            story="“真是有意思！这东西看起来可以按照我的想法自己成型！读心的黏土吗？”——兰伟德",
            quantity="uncommon",
            owner_character_id="character.armored_warrior",
            allow_duplicate=False
        )
        self.pending_block = 0

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START, EVENT_DAMAGE_AFTER, EVENT_TURN_START
        if event_name == EVENT_BATTLE_START:
            self.pending_block = 0
            return []
        if event_name == EVENT_DAMAGE_AFTER:
            if context.target is context.player and int(context.extra.get("real_damage", 0)) > 0:
                self.pending_block += 3
                return ["【{}】触发：下回合将获得 3 点格挡（待获得：{}）。".format(self.name, self.pending_block)]
            return []
        if event_name == EVENT_TURN_START and self.pending_block > 0:
            amount = self.pending_block
            self.pending_block = 0
            from game.block import gain_block_without_modifiers
            return gain_block_without_modifiers(
                game_state=context.game_state,
                source=context.player,
                target=context.player,
                amount=amount,
                block_source="self_forming_clay",
                card=None,
                message="【{}】触发：获得 {} 点格挡。当前格挡：{}。".format(self.name, amount, context.player.block + amount)
            )
        return []


class SingingBowlRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.singing_bowl",
            name="颂钵",
            description="可以将卡牌奖励转变为 +2 最大生命值。",
            story="这件被使用过无数次的法器在被敲打时会发出不绝于耳的悠扬旋律，也被称为“唱歌碗”。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class WhiteBeastStatueRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.white_beast_statue",
            name="白兽雕像",
            description="战斗结束后必定掉落药水。",
            story="一个小小的白色雕像，这种动物你从来没有见过。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class InkBottleRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ink_bottle",
            name="墨水瓶",
            description="你每打出 10 张牌，抽 1 张牌。",
            story="每次用光，都会自动装满一种颜色不同的墨水。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.card_count = 0

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER:
            return []
        self.card_count += 1
        if self.card_count % 10 != 0:
            return []
        logs = ["【{}】触发：打出第 {} 张牌，抽 1 张牌。".format(self.name, self.card_count)]
        logs.extend(context.player.draw_cards(1, game_state=context.game_state, draw_source="ink_bottle"))
        return logs


class StrikeDummyRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.strike_dummy",
            name="打击木偶",
            description="名字中有“打击”的卡牌造成 3 点额外伤害。",
            story="被打得破破烂烂的。",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )


class SundialRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.sundial",
            name="日晷",
            description="你每洗牌 3 次，获得 2 点能量。",
            story="“古代人类愚昧地执着于时间，他们抬头望向天空，希望能得到永恒的引导。”——佐罗斯",
            quantity="uncommon",
            owner_character_id="",
            allow_duplicate=False
        )
        self.shuffle_count = 0

    def on_shuffle(self, game_state, player):
        self.shuffle_count += 1
        if self.shuffle_count % 3 != 0:
            return []
        player.cost += 2
        return ["【{}】触发：第 {} 次洗牌，获得 2 点能量。当前费用：{}/{}。".format(
            self.name, self.shuffle_count, player.cost, player.max_cost
        )]

