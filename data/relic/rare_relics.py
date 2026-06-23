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

class MangoRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.mango",
            name="芒果",
            description="拾起时，将你的最大生命值提升 14。",
            story="在众多被遗忘的水果中最令人垂涎的一种。被完美地保存了下来，没有任何受到高塔荒疫影响的迹象。",
            quantity="rare",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import increase_max_hp
        return increase_max_hp(run_state, 14, self.name)


class CaptainsWheelRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.captains_wheel",
            name="舵盘",
            description="在你的第三回合开始时，获得 18 点格挡。",
            story="精雕细琢的木质物件，上面用陌生的语言刻着一个名字。",
            quantity="rare",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name != EVENT_TURN_START or int(getattr(context.game_state, "turn_count", 1)) != 3:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(
            game_state=context.game_state,
            source=context.player,
            target=context.player,
            amount=18,
            block_source="captains_wheel",
            card=None,
            message="【{}】触发：第三回合开始，获得 18 点格挡。当前格挡：{}。".format(self.name, context.player.block + 18)
        )


class IceCreamRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.ice_cream",
            name="冰淇淋",
            description="多余的能量可以留到下一回合。",
            story="震撼 美味！",
            quantity="rare",
            owner_character_id="",
            allow_duplicate=False
        )




class IncenseBurnerRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.incense_burner", name="香炉",
            description="每 6 回合，获得 1 层无实体。", 
            story="香炉中的烟让拥有者获得被焚烧者的灵力。",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.turn_counter = 0

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name != EVENT_TURN_START:
            return []
        self.turn_counter += 1
        if self.turn_counter < 6:
            return ["【{}】计数：{}/6。".format(self.name, self.turn_counter)]
        self.turn_counter = 0
        current = context.player.gain_status("intangible", 1)
        return ["【{}】触发：计数达到 6，获得 1 层无实体。当前无实体：{}。".format(self.name, current)]

    def summary_text(self):
        return "{}：{}（计数 {}/6）".format(self.name, self.description, int(getattr(self, 'turn_counter', 0)))


class StoneCalendarRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.stone_calendar", name="历石",
            description="在第 7 回合结束时，对所有敌人造成 52 点伤害。", 
            story="在高塔中几乎感觉不到时间的流逝。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_END
        if event_name != EVENT_TURN_END or int(getattr(context.game_state, "turn_count", 0)) != 7:
            return []
        from game.damage import deal_damage
        logs = ["【{}】触发：第 7 回合结束，对所有敌人造成 52 点伤害。".format(self.name)]
        for enemy in list(getattr(context.game_state, "enemies", []) or []):
            if enemy.is_alive():
                logs.extend(deal_damage(context.game_state, context.player, enemy, 52, damage_kind="relic", card=None))
        return logs


class PocketwatchRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.pocketwatch", name="怀表",
            description="若你在某个回合打出的牌少于等于 3 张，则在你的下个回合开始时额外抽 3 张牌。", 
            story="指针似乎永远卡在3点的位置。",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.pending_draw = False

    def on_event(self, event_name, context):
        from game.constants import EVENT_PLAYER_TURN_END, EVENT_TURN_START, EVENT_BATTLE_START
        if event_name == EVENT_BATTLE_START:
            self.pending_draw = False
            return []
        if event_name == EVENT_PLAYER_TURN_END:
            counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
            total = sum(int(v) for v in counts.values())
            if total <= 3:
                self.pending_draw = True
                return ["【{}】记录：本回合只打出 {} 张牌，下回合额外抽 3 张牌。".format(self.name, total)]
            self.pending_draw = False
            return []
        if event_name == EVENT_TURN_START and self.pending_draw:
            self.pending_draw = False
            logs = ["【{}】触发：额外抽 3 张牌。".format(self.name)]
            logs.extend(context.player.draw_cards(3, game_state=context.game_state, draw_source="pocketwatch"))
            return logs
        return []


class FossilizedHelixRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.fossilized_helix", name="螺类化石",
            description="阻止你在每场战斗中第一次受到的生命值损伤。", 
            story="似乎坚不可摧，你很好奇究竟是何种生物曾拥有这样的部分。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        current = context.player.gain_status("buffer", 1)
        return ["【{}】触发：获得 1 层缓冲。当前缓冲：{}。".format(self.name, current)]


class CloakClaspRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.cloak_clasp", name="斗篷扣",
            description="在你的回合结束时，每有一张手牌获得 1 点格挡。", 
            story="设计简约但牢固。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_PLAYER_TURN_END
        if event_name != EVENT_PLAYER_TURN_END:
            return []
        amount = len(getattr(context.player, "hand", []) or [])
        if amount <= 0:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(context.game_state, context.player, context.player, amount,
            block_source="cloak_clasp", card=None,
            message="【{}】触发：回合结束时手牌 {} 张，获得 {} 点格挡。当前格挡：{}。".format(self.name, amount, amount, context.player.block + amount))


class TungstenRodRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.tungsten_rod", name="钨合金棍",
            description="你每次失去生命时，减少失去的生命值 1 点。", 
            story="非常非常重。",
            quantity="rare", owner_character_id="", allow_duplicate=False)


class GamblingChipRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.gambling_chip", name="赌博筹码",
            description="在每场战斗开始时，丢弃任意张牌，然后抽相同数量张牌。", 
            story="你能看见筹码的一面上刻着一行小字：“熊的幸运筹码！",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_turn_start_hand_ready(self, game_state, player):
        if int(getattr(game_state, "turn_count", 1)) != 1:
            return []
        if getattr(game_state, "_gambling_chip_offered", False):
            return []
        game_state._gambling_chip_offered = True
        game_state.pending_discard_selection = True
        game_state.pending_discard_source = "gambling_chip"
        return ["【{}】触发：可以丢弃任意张手牌，然后抽相同数量的牌。用法：/card drop 0 2 3；不丢弃则 /card drop none。".format(self.name)]


class BirdFacedUrnRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.bird_faced_urn", name="鸟面瓮",
            description="每当你打出一张能力牌，回复 2 点生命。", 
            story="这个瓮上雕着乌鸦之神Mazaleth嘲弄的样貌。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER or getattr(context.card, "card_type", "") != "power":
            return []
        from game.relic_logic.combat_relic_utils import heal_player_in_combat
        return heal_player_in_combat(context.game_state, 2, self.name)


class ChampionBeltRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.champion_belt", name="冠军腰带",
            description="每当你给予易伤时，同时给予 1 层虚弱。", 
            story="只有最强者才配佩戴这条腰带。",
            quantity="rare", owner_character_id="character.armored_warrior", allow_duplicate=False)


class DuVuDollRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.du_vu_doll", name="毒巫娃娃",
            description="你的牌组中每有一张诅咒牌，你在战斗开始时就额外获得 1 点力量。", 
            story="一个设计为能从邪恶能量中获得力量的娃娃。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        cards = []
        player = context.player
        for pile_name in ("draw_pile", "hand", "discard_pile", "exhaust_pile"):
            cards.extend(getattr(player, pile_name, []) or [])
        count = sum(1 for c in cards if getattr(c, "card_type", "") == "curse")
        if count <= 0:
            return []
        current = player.gain_status("strength", count)
        return ["【{}】触发：牌组中有 {} 张诅咒，获得 {} 点力量。当前力量：{}。".format(self.name, count, count, current)]


class DeadBranchRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.dead_branch", name="枯木树枝",
            description="每当你消耗一张牌，增加一张随机卡牌到你的手牌。", 
            story="一个早已被遗忘的时代所遗留下来的树木枝条。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_EXHAUST
        if event_name != EVENT_CARD_EXHAUST:
            return []
        import random
        from game.reward import CARD_REWARD_POOL
        from data.card.AAAregistry import create_card
        card = create_card(random.choice(CARD_REWARD_POOL))
        setattr(card, "temporary", True)
        setattr(card, "created_in_battle", True)
        if context.player.is_hand_full():
            context.player.discard_pile.append(card)
            return ["【{}】触发：手牌已满，随机生成的【{}】进入弃牌堆。".format(self.name, card.name)]
        context.player.hand.append(card)
        return ["【{}】触发：消耗【{}】，随机生成【{}】加入手牌。".format(self.name, getattr(context.card, "name", "一张牌"), card.name)]


class GingerRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.ginger", name="生姜",
            description="你不会再被虚弱。", 
            story="在许多补品中都能用上的好东西。",
            quantity="rare", owner_character_id="", allow_duplicate=False)


class TurnipRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.turnip", name="萝卜",
            description="你不会再被脆弱。", 
            story="与生姜搭配尤为适合",
            quantity="rare", owner_character_id="", allow_duplicate=False)


class CabbageRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.cabbage", name="白菜",
            description="你被添加易伤时，持续时间 -1。", 
            story="萝卜白菜，各有所爱。",
            quantity="rare", owner_character_id="", allow_duplicate=False)


class GiryaRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.girya", name="壶铃",
            description="你现在能在休息处获得力量。（最多 3 次）", 
            story="这个壶铃重到难以想象，用这个锻炼一定能变得更强！",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.lifts = 0
        self.max_reward_floor = 48

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        lifts = int(getattr(self, "lifts", 0))
        if lifts <= 0:
            return []
        current = context.player.gain_status("strength", lifts)
        return ["【{}】触发：根据锻炼次数获得 {} 点力量。当前力量：{}。".format(self.name, lifts, current)]

    def summary_text(self):
        return "{}：{}（已锻炼 {}/3 次）".format(self.name, self.description, int(getattr(self, 'lifts', 0)))


class PeacePipeRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.peace_pipe", name="宁静烟斗",
            description="现在你可以在休息处移除你牌组中的牌。", 
            story="放空心智，洁净灵魂。",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.max_reward_floor = 48


class ShovelRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.shovel", name="铲子",
            description="现在你可以在休息处挖掘遗物。", 
            story="高塔中有着无数过去文明遗留下的遗物和强大的冒险者们遗失的宝物，现在你可以把它们挖出来了！",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.max_reward_floor = 48


class MiniatureTentRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.miniature_tent", name="微型帐篷",
            description="你可以在休息处选择任意数量的选项。", 
            story="出来郊游吗。玩得愉快！",
            quantity="shop", owner_character_id="", allow_duplicate=False)
        self.max_reward_floor = 48


class LizardTailRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.lizard_tail", name="蜥蜴尾巴",
            description="当你要被杀死时，免死并回复到最大生命值的 50%。（仅能起效一次）", 
            story="在战斗中可以用来骗过敌人的假尾巴。",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.used = False

    def summary_text(self):
        suffix = "已使用" if getattr(self, "used", False) else "未使用"
        return "{}：{}（{}）".format(self.name, self.description, suffix)


class MagicFlowerRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.magic_flower", name="魔法花",
            description="战斗中的回复效果提升 50%。", 
            story="被认为是早已绝种的一朵花，竟被完美地保存了下来。",
            quantity="rare", owner_character_id="character.armored_warrior", allow_duplicate=False)


class OldCoinRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.old_coin", name="古钱币",
            description="拾起时，获得 300 金币。", 
            story="因为其历史价值和稀有金属成分而被商人出以高价的独特钱币。",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.max_reward_floor = 48

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import gain_gold_with_relics
        return gain_gold_with_relics(run_state, 300, source="古钱币")


class PrayerWheelRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.prayer_wheel", name="转经轮",
            description="普通敌人多掉落一次卡牌奖励。", 
            story="经轮一直转动，永远不停。",
            quantity="rare", owner_character_id="", allow_duplicate=False)
        self.max_reward_floor = 48


class TheSpecimenRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.the_specimen", name="生物样本",
            description="每当有敌人死去时，将其身上的中毒层数移到一名随机敌人身上。", 
            story="“有意思！我发现了一个有着惊人毒性的变异生物，先采集份样本以后再仔细研究吧。”——兰伟德",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_DAMAGE_AFTER
        if event_name != EVENT_DAMAGE_AFTER:
            return []
        dead = getattr(context, "target", None)
        if dead is None or not hasattr(dead, "enemy_id"):
            return []
        if not context.extra.get("target_was_alive", False) or not context.extra.get("target_is_dead_after", False):
            return []
        if getattr(dead, "_specimen_triggered", False):
            return []
        poison = 0
        if hasattr(dead, "get_status_value"):
            poison = int(dead.get_status_value("poison"))
        if poison <= 0:
            return []
        alive = [e for e in getattr(context.game_state, "enemies", []) or [] if e is not dead and e.is_alive()]
        if not alive:
            return []
        import random
        target = random.choice(alive)
        setattr(dead, "_specimen_triggered", True)
        if hasattr(dead, "statuses"):
            dead.statuses.remove("poison")
        current = target.gain_status("poison", poison)
        return ["【{}】触发：将【{}】身上的 {} 层中毒转移给【{}】。当前中毒：{}。".format(self.name, dead.name, poison, target.name, current)]


class ThreadAndNeedleRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.thread_and_needle", name="针线",
            description="在每场战斗开始时，获得 4 层多层护甲。", 
            story="将这些魔法线缠绕在你的周围时，你觉得自己变得更坚硬了。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        current = context.player.gain_status("plated_armor", 4)
        return ["【{}】触发：获得 4 层多层护甲。当前多层护甲：{}。".format(self.name, current)]


class TingshaRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.tingsha", name="铜钹",
            description="你每在你的回合丢弃一张牌，就对一名随机敌人造成 3 点伤害。", 
            story="这件乐器发出的响声似乎能回荡到让人耳朵发痛。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_card_discard(self, game_state, player, card, reason):
        alive = [e for e in getattr(game_state, "enemies", []) or [] if e.is_alive()]
        if not alive:
            return []
        import random
        from game.damage import deal_damage
        target = random.choice(alive)
        logs = ["【{}】触发：丢弃【{}】，对随机敌人【{}】造成 3 点伤害。".format(self.name, getattr(card, "name", "一张牌"), target.name)]
        logs.extend(deal_damage(game_state, player, target, 3, damage_kind="relic", card=None))
        return logs


class ToriiRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.torii", name="鸟居",
            description="每当你受到小于等于 5 点的未被格挡攻击伤害时，将伤害降低为 1。", 
            story="你拿着这个小小的鸟居，感觉心中有一股宁静与安全的感觉。",
            quantity="rare", owner_character_id="", allow_duplicate=False)


class ToughBandagesRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.tough_bandages", name="结实绷带",
            description="你每在你的回合丢弃一张牌，就获得 3 点格挡。", 
            story="失去给人带来力量",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_card_discard(self, game_state, player, card, reason):
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(game_state, player, player, 3,
            block_source="tough_bandages", card=None,
            message="【{}】触发：丢弃【{}】，获得 3 点格挡。当前格挡：{}。".format(self.name, getattr(card, "name", "一张牌"), player.block + 3))


class UnceasingTopRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(self, relic_id="relic.unceasing_top", name="不休陀螺",
            description="在你的回合，当你没有手牌时，抽一张牌。", 
            story="这个陀螺始终轻松地旋转着，让你觉得自己仿佛是在梦中。",
            quantity="rare", owner_character_id="", allow_duplicate=False)

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER
        if event_name != EVENT_CARD_PLAY_AFTER:
            return []
        if getattr(context.player, "hand", None):
            return []
        from game.modifiers import get_status_value
        if get_status_value(context.player, "no_draw") > 0:
            return ["【{}】触发，但受到不能抽牌影响，没有抽牌。".format(self.name)]
        logs = ["【{}】触发：手牌为空，抽 1 张牌。".format(self.name)]
        logs.extend(context.player.draw_cards(1, game_state=context.game_state, draw_source="unceasing_top"))
        return logs
