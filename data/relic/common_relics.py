# -*- coding: utf-8 -*-

import random

from data.relic.base_relic import RelicTemplate
from game.constants import (
    EVENT_BATTLE_START,
    EVENT_TURN_START,
    EVENT_PLAYER_TURN_END,
    EVENT_CARD_PLAY_AFTER,
    EVENT_DAMAGE_AFTER,
    EVENT_POTION_USE_AFTER,
)


def _heal_entity(entity, amount, source_name):
    amount = int(amount)
    try:
        from game.relic_logic.combat_relic_utils import apply_magic_flower_heal_amount
        heal_amount = apply_magic_flower_heal_amount(entity, amount)
    except Exception:
        heal_amount = amount
    old_hp = int(getattr(entity, "hp", 0))
    max_hp = int(getattr(entity, "max_hp", old_hp))
    entity.hp = min(max_hp, old_hp + heal_amount)
    real = entity.hp - old_hp
    flower_text = ""
    if heal_amount != amount:
        flower_text = "【魔法花】使回复量 {} -> {}。".format(amount, heal_amount)
    if real > 0:
        return ["【{}】触发：{}回复 {} 点生命。HP：{} -> {}。".format(source_name, flower_text, real, old_hp, entity.hp)]
    return ["【{}】触发：{}HP 已满，没有恢复。".format(source_name, flower_text)]


def _gain_status_log(target, status_key, amount):
    from game.status.status_gain import format_status_gain_log
    if hasattr(target, "gain_status_with_result"):
        result = target.gain_status_with_result(status_key, amount)
        return format_status_gain_log(target, status_key, amount, result)
    current = target.gain_status(status_key, amount)
    from game.status.status_defs import get_status_name
    status_name = get_status_name(status_key)
    return "{} 获得 {} 点{}。当前{}：{}。".format(target.name, amount, status_name, status_name, current)


class JuzuBraceletRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.juzu_bracelet",
            name="佛珠手链",
            description="你在 ? 房间中不会再遭遇常规战斗。",
            story="抵御未知危险的护身道具。",
            quantity="common",
            owner_character_id="",
            allow_duplicate=False
        )


class TinyChestRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.tiny_chest",
            name="小宝箱",
            description="每 4 个 ? 房间的最后一个必是宝箱房。",
            story="“作为原型而言相当不错。”——建筑师",
            quantity="common",
            owner_character_id="",
            allow_duplicate=False
        )


class BagOfMarblesRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.bag_of_marbles",
            name="弹珠袋",
            description="在每场战斗开始时，给予所有敌人 1 层易伤。",
            story="曾经这在城市区是流行的玩具，现在你可以用它让敌人们失去平衡。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        logs = []
        for enemy in getattr(context.game_state, "enemies", []) or []:
            if enemy.is_alive():
                logs.append(_gain_status_log(enemy, "vulnerable", 1))
        if logs:
            return ["【{}】触发。".format(self.name)] + logs
        return logs


class BloodVialRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.blood_vial",
            name="小血瓶",
            description="在每场战斗开始时，回复 2 点生命。",
            story="装着纯种年长吸血鬼血液的一个小瓶。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        return _heal_entity(context.player, 2, self.name)


class BronzeScalesRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.bronze_scales",
            name="铜制鳞片",
            description="在每场战斗开始时，获得 3 点荆棘。",
            story="守护者身上的锐利鳞片，会自动变形来保护使用者。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        return ["【{}】触发。".format(self.name), _gain_status_log(context.player, "thorns", 3)]


class CentennialPuzzleRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.centennial_puzzle",
            name="百年积木",
            description="你在每场战斗中第一次损伤生命时，抽 3 张牌。",
            story="解开积木的谜题时，你感到心中有一股强大的暖意。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_DAMAGE_AFTER:
            return []
        player = context.player
        if context.target is not player:
            return []
        if int(context.extra.get("real_damage", 0)) <= 0:
            return []
        if getattr(context.game_state, "_centennial_puzzle_triggered", False):
            return []
        context.game_state._centennial_puzzle_triggered = True
        logs = ["【{}】触发：本场战斗第一次损伤生命，抽 3 张牌。".format(self.name)]
        logs.extend(player.draw_cards(3, game_state=context.game_state, draw_source="centennial_puzzle"))
        return logs


class TheBootRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.the_boot",
            name="发条靴",
            description="每当你造成小于等于 5 点未被格挡的攻击伤害时，将伤害提升为 5。只影响攻击伤害。",
            story="拧动发条会让这只靴子变得更大。",
            quantity="common",
        )


class DreamCatcherRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.dream_catcher",
            name="捕梦网",
            description="每当你休息时，可以增加一张牌到你的牌组。",
            story="北方部落会在入睡时挂上这种网，相信这样做能够实现自我提升。",
            quantity="common",
        )
        self.max_reward_floor = 47


class HappyFlowerRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.happy_flower",
            name="开心小花",
            description="每 3 个回合，获得一点能量。",
            story="这朵一直面带笑容的花是贵族间流行的小礼物。",
            quantity="common",
        )
        self.turn_counter = 0

    def on_event(self, event_name, context):
        if event_name != EVENT_TURN_START:
            return []
        self.turn_counter += 1
        if self.turn_counter % 3 != 0:
            return []
        context.player.cost += 1
        return ["【{}】触发：第 {} 个回合，获得 1 点能量。当前费用：{}/{}。".format(
            self.name, self.turn_counter, context.player.cost, context.player.max_cost
        )]


class LanternRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.lantern",
            name="灯笼",
            description="在每场战斗的第一回合获得一点能量。",
            story="一盏诡异的灯笼，只为提灯者照明。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_TURN_START or int(getattr(context.game_state, "turn_count", 1)) != 1:
            return []
        context.player.cost += 1
        return ["【{}】触发：第一回合获得 1 点能量。当前费用：{}/{}。".format(
            self.name, context.player.cost, context.player.max_cost
        )]


class OddlySmoothStoneRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.oddly_smooth_stone",
            name="意外光滑的石头",
            description="在每场战斗开始时，获得 1 点敏捷。",
            story="你从没有见过这么光滑完好的东西，这一定是出自先古之民的手艺。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        return ["【{}】触发。".format(self.name), _gain_status_log(context.player, "dexterity", 1)]


class VajraRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.vajra",
            name="金刚杵",
            description="在每场战斗开始时，获得 1 点力量。",
            story="一件交给在战斗中展示了荣耀的战士们的装饰性遗物。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        return ["【{}】触发。".format(self.name), _gain_status_log(context.player, "strength", 1)]


class OmamoriRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.omamori",
            name="御守",
            description="抵消你下 2 次获得的诅咒。",
            story="常见的用来抵御邪灵的护身符，这个护符里似乎有一股神圣的能量。",
            quantity="common",
        )
        self.charges = 2
        self.max_reward_floor = 47

    def summary_text(self):
        return "{}：{}（剩余 {} 次）".format(self.name, self.description, int(getattr(self, "charges", 0)))


class OrichalcumRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.orichalcum",
            name="奥利哈钢",
            description="如果你在回合结束时没有任何格挡，获得 6 点格挡。",
            story="一块出处不明、带着些绿色的金属。似乎完全不会毁坏。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_PLAYER_TURN_END:
            return []
        player = context.player
        if int(getattr(player, "block", 0)) > 0:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(
            game_state=context.game_state,
            source=player,
            target=player,
            amount=6,
            block_source="orichalcum",
            card=None,
            message="【{}】触发：回合结束时没有格挡，获得 6 点格挡。当前格挡：{}。".format(self.name, player.block + 6)
        )


class RedSkullRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.red_skull",
            name="红头骨",
            description="当你的生命值等于或低于 50% 时，你获得额外 3 点力量。",
            story="一个用装饰性颜料涂红的小小头骨。",
            quantity="common",
            owner_character_id="character.armored_warrior",
        )
        self.active = False

    def on_event(self, event_name, context):
        if event_name == EVENT_BATTLE_START:
            self.active = False
        if event_name not in (EVENT_BATTLE_START, EVENT_TURN_START, EVENT_DAMAGE_AFTER):
            return []
        player = context.player
        if getattr(player, "character_id", "") != "character.armored_warrior":
            return []
        if not player.is_alive():
            return []
        low = player.hp * 2 <= player.max_hp
        if low and not self.active:
            self.active = True
            current = player.gain_status("strength", 3)
            return ["【{}】触发：生命值低于一半，获得 3 点力量。当前力量：{}。".format(self.name, current)]
        if (not low) and self.active:
            self.active = False
            current = player.gain_status("strength", -3)
            return ["【{}】停止生效：生命值高于一半，失去 3 点力量。当前力量：{}。".format(self.name, current)]
        return []


class RegalPillowRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.regal_pillow",
            name="皇家枕头",
            description="在休息时额外回复 15 点生命。",
            story="这下能好好睡一觉了。",
            quantity="common",
        )


class SmilingMaskRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.smiling_mask",
            name="微笑面具",
            description="商人的卡牌移除服务现在价格永远是 50 金币。",
            story="商人戴着的面具，看来他有很多备用的……",
            quantity="common",
        )
        self.max_reward_floor = 48
        self.can_appear_in_shop = False


class SnakeSkullRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.snake_skull",
            name="异蛇头骨",
            description="每当你给予敌人中毒状态时，额外给予 1 层中毒。",
            story="保存完好的异蛇头骨，十分离奇地非常干净和光滑，任何灰尘和污垢都无法沾上它，这是为什么呢。",
            quantity="common",
        )


class StrawberryRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.strawberry",
            name="莓",
            description="拾起时，将你的最大生命值提升 7。",
            story="太好吃了！荒疫之后就没见过这东西了啊。”——兰伟德\n嗯嗯对，进行育种和定向优化……说不定以后能种出更好的？——炼金师",
            quantity="common",
        )

    def on_obtained(self, run_state):
        from game.relic_logic.run_relic_utils import increase_max_hp
        return increase_max_hp(run_state, 7, self.name)


class PotionBeltRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.potion_belt",
            name="药水腰带",
            description="拾起时，获得 2 个药水栏位。",
            story="穿上这条腰带，我就能携带更多药水！",
            quantity="common",
        )

    def on_obtained(self, run_state):
        old = int(getattr(run_state, "max_potion_slots", 3))
        run_state.max_potion_slots = old + 2
        return ["【{}】生效：药水栏位 {} -> {}。".format(self.name, old, run_state.max_potion_slots)]


class MealTicketRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.meal_ticket",
            name="餐券",
            description="每当你进入商店房间时，回复 15 点生命。",
            story="“这里的肉丸子可是有名的！以后每次来都可以尝尝哦！”",
            quantity="common",
        )
        self.max_reward_floor = 48

    def on_enter_shop(self, run_state):
        old = int(getattr(run_state, "hp", 0))
        run_state.hp = min(int(getattr(run_state, "max_hp", old)), old + 15)
        return ["【{}】触发：进入商店，HP：{} -> {}。".format(self.name, old, run_state.hp)]


class WhetstoneRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.whetstone",
            name="磨刀石",
            description="拾起时，随机升级 2 张攻击牌。",
            story="“肉体永远无法打败钢铁。”——忽必烈大帝",
            quantity="common",
        )

    def on_obtained(self, run_state):
        return _upgrade_random_cards_by_type(run_state, "attack", 2, self.name)


class MawBankRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.maw_bank",
            name="巨口储蓄罐",
            description="每攀爬一层楼层获得 12 金币。一旦在商店中花费金币就会失效。",
            story="尽管巨口袭击频繁发生，这个造型的储蓄罐却意外相当流行。",
            quantity="common",
        )
        self.max_reward_floor = 47
        self.can_appear_in_shop = False


class NunchakuRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.nunchaku",
            name="双节棍",
            description="你每打出 10 张攻击牌，获得一点能量。",
            story="优良的练武器具，能改善使用者的姿势、提升灵活度。",
            quantity="common",
        )
        self.attack_count = 0

    def on_event(self, event_name, context):
        if event_name != EVENT_CARD_PLAY_AFTER:
            return []
        card = context.card
        if getattr(card, "card_type", "") != "attack":
            return []
        self.attack_count += 1
        if self.attack_count % 10 != 0:
            return []
        context.player.cost += 1
        return ["【{}】触发：打出第 {} 张攻击牌，获得 1 点能量。当前费用：{}/{}。".format(
            self.name, self.attack_count, context.player.cost, context.player.max_cost
        )]


class PreservedInsectRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.preserved_insect",
            name="昆虫标本",
            description="精英战中的敌人生命减少 25%。",
            story="这只昆虫似乎会对尤其巨大的敌人们散发出虚弱的光环。",
            quantity="common",
        )
        self.max_reward_floor = 52

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        run_state = getattr(context.game_state, "run_state", None) or getattr(context.player, "run_state", None)
        node_type = getattr(run_state, "current_battle_node_type", "") if run_state is not None else ""
        if node_type not in ("elite", "event_elite"):
            return []
        logs = ["【{}】触发：精英战敌人生命减少 25%。".format(self.name)]
        for enemy in getattr(context.game_state, "enemies", []) or []:
            old_max = enemy.max_hp
            old_hp = enemy.hp
            enemy.max_hp = max(1, int(enemy.max_hp * 0.75))
            enemy.hp = min(enemy.max_hp, int(enemy.hp * 0.75))
            logs.append("{} HP：{}/{} -> {}/{}。".format(enemy.name, old_hp, old_max, enemy.hp, enemy.max_hp))
        return logs


class CeramicFishRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.ceramic_fish",
            name="陶瓷小鱼",
            description="每次你往自己的牌组中加入一张卡牌时，获得 9 金币。",
            story="这些被精心上色的鱼儿被认为可以带来滚滚财源。",
            quantity="common",
        )


class AkabekoRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.akabeko",
            name="赤牛",
            description="你在每场战斗中的第一次攻击造成 8 点额外伤害。",
            story="哞～",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        return ["【{}】触发。".format(self.name), _gain_status_log(context.player, "vigor", 8)]


class PenNibRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.pen_nib",
            name="钢笔尖",
            description="你每打出的第 10 张攻击牌将会造成双倍伤害。",
            story="拿着这支笔尖时，你可以看见所有被笔尖前主人杀死过的人。真是血腥的历史。",
            quantity="common",
        )
        self.attack_count = 0

    def on_card_play_start(self, game_state, player, card):
        if getattr(card, "card_type", "") != "attack":
            return []
        self.attack_count += 1
        if self.attack_count % 10 != 0:
            return []
        setattr(player, "_pen_nib_active_card", card)
        return ["【{}】触发：第 {} 张攻击牌【{}】伤害翻倍。".format(self.name, self.attack_count, card.name)]

    def on_event(self, event_name, context):
        if event_name == EVENT_CARD_PLAY_AFTER and getattr(context.player, "_pen_nib_active_card", None) is context.card:
            setattr(context.player, "_pen_nib_active_card", None)
        return []


class ToyOrnithopterRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.toy_ornithopter",
            name="玩具扑翼飞机",
            description="你每使用一瓶药水，回复 5 点生命。",
            story="这个小玩具最适合陪伴孤独一人的冒险者啦！",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_POTION_USE_AFTER:
            return []
        return _heal_entity(context.player, 5, self.name)


class BagOfPreparationRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.bag_of_preparation",
            name="准备背包",
            description="在每场战斗开始时，额外抽 2 张牌。",
            story="冒险者专用的超大号背包，有很多口袋和皮带。",
            quantity="common",
        )

    def get_opening_draw_bonus(self, game_state, player):
        return 2


class AncientTeaSetRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.ancient_tea_set",
            name="古茶具套装",
            description="到达休息处后的下一场战斗开始时获得 2 点能量。",
            story="能让你神清气爽睡得香。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_TURN_START or int(getattr(context.game_state, "turn_count", 1)) != 1:
            return []
        run_state = getattr(context.game_state, "run_state", None) or getattr(context.player, "run_state", None)
        if run_state is None or not getattr(run_state, "ancient_tea_set_ready", False):
            return []
        run_state.ancient_tea_set_ready = False
        context.player.cost += 2
        return ["【{}】触发：休息处后的下一场战斗第一回合获得 2 点能量。当前费用：{}/{}。".format(
            self.name, context.player.cost, context.player.max_cost
        )]


class ArtOfWarRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.art_of_war",
            name="孙子兵法",
            description="如果你在回合中不打出任何攻击牌，在下一回合得到一点额外能量。",
            story="这本古兵书记载着远古时代的智慧。",
            quantity="common",
        )
        self.next_turn_bonus = False

    def on_event(self, event_name, context):
        if event_name == EVENT_TURN_START:
            if self.next_turn_bonus:
                self.next_turn_bonus = False
                context.player.cost += 1
                return ["【{}】触发：本回合获得 1 点额外能量。当前费用：{}/{}。".format(
                    self.name, context.player.cost, context.player.max_cost
                )]
            return []
        if event_name == EVENT_PLAYER_TURN_END:
            counts = getattr(context.game_state, "player_card_type_played_counts_this_turn", {}) or {}
            self.next_turn_bonus = int(counts.get("attack", 0)) <= 0
            return []
        if event_name == EVENT_BATTLE_START:
            self.next_turn_bonus = False
        return []


class AnchorRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.anchor",
            name="锚",
            description="每场战斗开始时获得 10 点格挡。",
            story="拿着这个小小的装饰，你觉得自己更稳也更重了。",
            quantity="common",
        )

    def on_event(self, event_name, context):
        if event_name != EVENT_BATTLE_START:
            return []
        from game.block import gain_block_without_modifiers
        return gain_block_without_modifiers(
            game_state=context.game_state,
            source=context.player,
            target=context.player,
            amount=10,
            block_source="anchor",
            card=None,
            message="【{}】触发：获得 10 点格挡。当前格挡：{}。".format(self.name, context.player.block + 10)
        )


def _upgrade_random_cards_by_type(run_state, card_type, count, relic_name):
    from data.card.upgrade_rules import has_upgrade, upgrade_card
    from game.relic_logic.bottle_utils import copy_bottled_flags

    candidates = []
    for index, card in enumerate(getattr(run_state, "master_deck", []) or []):
        if getattr(card, "card_type", "") != card_type:
            continue
        if getattr(card, "upgraded", False) and not getattr(card, "multi_upgrade", False):
            continue
        if has_upgrade(card):
            candidates.append((index, card))
    if not candidates:
        return ["【{}】没有找到可升级的{}牌。".format(relic_name, "攻击" if card_type == "attack" else "技能")]
    chosen = random.sample(candidates, min(count, len(candidates)))
    logs = ["【{}】生效：随机升级 {} 张{}牌。".format(relic_name, len(chosen), "攻击" if card_type == "attack" else "技能")]
    for index, card in chosen:
        upgraded = copy_bottled_flags(card, upgrade_card(card))
        run_state.master_deck[index] = upgraded
        logs.append("【{}】 -> 【{}】。".format(card.name, upgraded.name))
    return logs
