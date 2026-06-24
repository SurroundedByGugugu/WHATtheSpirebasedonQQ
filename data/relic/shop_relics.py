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




class CauldronRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.cauldron",
            name="大锅",
            description="拾起时，制作 5 瓶随机药水。",
            story="商人其实是位技术相当不错的药剂师。买四送一。\n“无证经营！”——炼金师",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        import random
        from data.potion.AAAregistry import create_potion
        from game.reward import roll_potion_id_by_rarity
        from game.relic_logic.run_relic_utils import try_gain_potion_with_relics
        rng = random.Random(int(getattr(run_state, "run_seed", 0) or 0) + 6401 + len(getattr(run_state, "potions", []) or []))
        logs = ["【{}】触发：制作 5 瓶随机药水。".format(self.name)]
        for i in range(5):
            potion_id = roll_potion_id_by_rarity(rng, run_state=run_state, include_event=False)
            if potion_id is None:
                logs.append("第 {} 瓶药水制作失败：没有可用药水。".format(i + 1))
                continue
            logs.extend(try_gain_potion_with_relics(run_state, create_potion(potion_id), source="大锅"))
        return logs


class LeesWaffleRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.lees_waffle",
            name="李家华夫饼",
            description="拾起时，将你的最大生命值提升 7 点，并回复所有生命。",
            story="“全高塔你能找到的最好吃的东西！今天特地为你烤的。”\n“无食品销售许可证经营！”——炼金师",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import increase_max_hp, heal_run_hp_with_relics
        logs = []
        logs.extend(increase_max_hp(run_state, 7, self.name))
        missing = max(0, int(getattr(run_state, "max_hp", 0)) - int(getattr(run_state, "hp", 0)))
        logs.extend(heal_run_hp_with_relics(run_state, missing, source=self.name))
        return logs


class OrreryRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.orrery",
            name="星系仪",
            description="拾起时，从五组三选一的卡牌中选择 5 张牌加入你的牌组。",
            story="“一旦你理解了宇宙……”——佐罗斯",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import start_pending_orrery_selection, format_pending_orrery
        logs = ["【{}】触发：从五组三选一的卡牌中选择 5 张牌加入牌组。".format(self.name)]
        start_pending_orrery_selection(run_state)
        logs.append(format_pending_orrery(run_state))
        return logs


class StrangeSpoonRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.strange_spoon",
            name="奇怪的勺子",
            description="应该消耗的牌在被打出时会有 50% 几率只被丢弃。",
            story="如果你盯着这把勺子看，它似乎就会在你眼前弯曲变形。\n“谁家胡地掉在这儿的……”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )


class ToolboxRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.toolbox",
            name="工具箱",
            description="在每场战斗开始时，你可以从 3 张随机无色牌中选择 1 张增加到你的手牌。",
            story="不管面对什么工作，都能找到相应的工具。",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_turn_start_hand_ready(self, game_state, player):
        if int(getattr(game_state, "turn_count", 1)) != 1:
            return []
        if getattr(game_state, "_toolbox_offered", False):
            return []
        from game.engine import queue_toolbox_selection
        game_state._toolbox_offered = True
        return queue_toolbox_selection(game_state, self.name)


class TheAbacusRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.the_abacus",
            name="算盘",
            description="你每次将抽牌堆洗牌时，获得 6 点格挡。",
            story="“EIN，DOS，TROIS，NE，FEM，LIU……EXECUTION……”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_shuffle(self, game_state, player):
        if game_state is None:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(
            game_state, player, player, 6,
            block_source="relic", card=None,
            message="【{}】触发：洗牌时获得 6 点格挡。当前格挡：{}。".format(self.name, int(getattr(player, "block", 0)) + 6)
        )


class DollysMirrorRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.dollys_mirror",
            name="多利之镜",
            description="拾起时，从你的牌组中选择一张牌进行复制。",
            story="“照出来我的样子怪怪的。”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import start_pending_dollys_mirror_selection, format_pending_dollys_mirror
        if not getattr(run_state, "master_deck", []):
            return ["【{}】触发，但当前牌组为空，无法复制。".format(self.name)]
        start_pending_dollys_mirror_selection(run_state)
        return ["【{}】触发：选择一张牌进行复制。".format(self.name), format_pending_dollys_mirror(run_state)]


class ClockworkSouvenirRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.clockwork_souvenir",
            name="齿轮工艺品",
            description="每场战斗开始时，获得 1 层人工制品。",
            story="“你看里面齿轮这么多，是不是很精巧。”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        current = context.player.gain_status("artifact", 1)
        return ["【{}】触发：获得 1 层人工制品。当前人工制品：{}。".format(self.name, current)]


class HandDrillRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.hand_drill",
            name="手钻",
            description="每当你突破敌人的格挡时，给予其 2 层易伤。",
            story="“螺旋超危险的啊。”\n超银河红莲螺岩！",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )


class SlingOfCourageRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.sling_of_courage",
            name="勇气投石索",
            description="在与精英敌人战斗时，获得 2 点力量。",
            story="“对格外强大的对手非常好用的工具。”",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START
        if event_name != EVENT_BATTLE_START:
            return []
        run_state = getattr(context.game_state, "run_state", None)
        node_type = getattr(run_state, "current_battle_node_type", "") if run_state is not None else ""
        if node_type not in ("elite", "event_elite"):
            return []
        current = context.player.gain_status("strength", 2)
        return ["【{}】触发：精英战开始，获得 2 点力量。当前力量：{}。".format(self.name, current)]


class OrangePelletsRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.orange_pellets",
            name="橙色药丸",
            description="你每在同一回合内打出能力牌、攻击牌和技能牌各一张，移除你身上的所有负面效果。",
            story="“用塔里各处真菌做出来的药，包治百病！”\n“需要药品售卖资格证！而且我家没那么多菌子！”——炼金师",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_BATTLE_START, EVENT_TURN_START, EVENT_CARD_PLAY_AFTER
        if event_name in (EVENT_BATTLE_START, EVENT_TURN_START):
            context.game_state._orange_pellets_types = set()
            return []
        if event_name != EVENT_CARD_PLAY_AFTER:
            return []
        card_type = getattr(context.card, "card_type", "")
        if card_type not in ("attack", "skill", "power"):
            return []
        played = set(getattr(context.game_state, "_orange_pellets_types", set()) or set())
        played.add(card_type)
        context.game_state._orange_pellets_types = played
        if not {"attack", "skill", "power"}.issubset(played):
            return []
        context.game_state._orange_pellets_types = set()
        removed = []
        statuses = getattr(context.player, "statuses", None)
        if statuses is None:
            return []
        from data.status.AAAregistry import get_status_def, get_status_name
        active = list(statuses.all_active().items())
        for key, value in active:
            status_def = get_status_def(key)
            is_negative = False
            if status_def is not None and getattr(status_def, "category", "") == "debuff":
                is_negative = True
            if int(value) < 0:
                is_negative = True
            if is_negative:
                statuses.remove(key)
                removed.append(get_status_name(key))
        if not removed:
            return ["【{}】触发：没有可移除的负面效果。".format(self.name)]
        return ["【{}】触发：移除负面效果：{}。".format(self.name, "，".join(removed))]


class BrimstoneRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.brimstone",
            name="硫磺",
            description="在你的每个回合开始时，你获得 2 点力量，所有敌人也获得 1 点力量。",
            story="散发出地狱般的高热。",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START
        if event_name != EVENT_TURN_START:
            return []
        logs = []
        current = context.player.gain_status("strength", 2)
        logs.append("【{}】触发：你获得 2 点力量。当前力量：{}。".format(self.name, current))
        for enemy in getattr(context.game_state, "enemies", []) or []:
            if not enemy.is_alive():
                continue
            value = enemy.gain_status("strength", 1)
            logs.append("{} 获得 1 点力量。当前力量：{}。".format(enemy.name, value))
        return logs


class PrismaticShardRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.prismatic_shard",
            name="棱镜碎片",
            description="战斗奖励掉落的卡牌现在会包括无所属牌和其他角色的牌。",
            story="通过碎片，你能以全新的视角观察这个世界。",
            quantity="shop",
            owner_character_id="",
            allow_duplicate=False
        )
