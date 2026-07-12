# -*- coding: utf-8 -*-

from data.status.base_status import StatusDef
from data.status.AAAregistry import register_status_def


register_status_def(StatusDef(
    key="strength",
    name="力量",
    description="攻击伤害增加。",
    category="buff",
    display_mode="value",
    order=10,
    can_be_negative=True,
))
register_status_def(StatusDef(
    key="flex",
    name="活动肌肉",
    description="回合结束时，失去等同于层数的力量，然后移除此状态。",
    category="debuff",
    display_mode="stack",
    order=15,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="dexterity",
    name="敏捷",
    description="获得格挡时数值增加。",
    category="buff",
    display_mode="value",
    order=20,
    can_be_negative=True,
))

register_status_def(StatusDef(
    key="next_turn_energy",
    name="下回合费用",
    description="下个玩家回合开始时，获得等同于层数的费用，然后移除此状态。",
    category="buff",
    display_mode="stack",
    order=74,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="next_turn_block",
    name="下回合格挡",
    description="下个玩家回合开始时，获得等同于层数的格挡，然后移除此状态。",
    category="buff",
    display_mode="stack",
    order=75,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="temporary_strength_loss",
    name="临时力量降低",
    description="回合结束时恢复等同于层数的力量。",
    category="debuff",
    display_mode="stack",
    order=76,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="anger",
    name="生气",
    description="每当受到攻击伤害时，获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
))
register_status_def(StatusDef(
    key="enrage",
    name="激怒",
    description="每当玩家打出一张技能牌时，获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
    order=12,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="shape_shift",
    name="形态转换",
    description="受到等同于层数的伤害后，切换为防御形态。",
    category="buff",
    display_mode="stack",
    order=13,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="sharp_hide",
    name="锋利外甲",
    description="每当玩家打出一张攻击牌时，玩家受到等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=14,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="vulnerable",
    name="易伤",
    description="受到攻击伤害增加。",
    category="debuff",
    display_mode="turns",
    order=30,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="weak",
    name="虚弱",
    description="造成攻击伤害降低。",
    category="debuff",
    display_mode="turns",
    order=40,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="entangled",
    name="缠身",
    description="本回合不能打出攻击牌。",
    category="debuff",
    display_mode="turns",
    order=43,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="poison",
    name="中毒",
    description="敌人行动前，失去等同于层数的生命，然后层数减少 1。",
    category="debuff",
    display_mode="stack",
    order=50,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="thorns",
    name="荆棘",
    description="受到攻击后，对攻击来源造成等同于荆棘层数的反伤。荆棘不随回合衰减。",
    category="buff",
    display_mode="stack",
    order=60,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="frail",
    name="脆弱",
    description="获得格挡降低。",
    category="debuff",
    display_mode="turns",
    order=45,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="poison_thorns",
    name="毒荆棘",
    description="受到攻击后，使攻击来源获得等同于层数的中毒。毒荆棘不随回合衰减。",
    category="buff",
    display_mode="stack",
    order=65,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="curl_up",
    name="蜷缩",
    description="受到攻击后，获得等同于层数的格挡，然后移除此状态。",
    category="buff",
    display_mode="stack",
    order=68,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="burn",
    name="烧伤",
    description="造成攻击伤害减半；回合结束时失去当前生命的 1/8，然后层数减少 1。",
    category="debuff",
    display_mode="turns",
    order=52,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="temporary_thorns",
    name="临时荆棘",
    description="受到攻击后，对攻击来源造成等同于层数的反伤；回合结束时消失。",
    category="buff",
    display_mode="stack",
    order=66,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="crystal_cocoon",
    name="晶茧",
    description="回合结束时，在敌人攻击完后，若你有格挡，每层使你获得 1 点力量，然后移除此状态。",
    category="buff",
    display_mode="stack",
    order=77,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="abyssal_form",
    name="深渊形态",
    description="攻击牌额外视为有极阴 Zone 效果；不会新开或覆盖 Zone。",
    category="buff",
    display_mode="stack",
    order=81,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="phantom_form",
    name="虚影形态",
    description="攻击牌无视格挡。",
    category="buff",
    display_mode="stack",
    order=82,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="regeneration",
    name="再生",
    description="回合结束时恢复等同于层数的生命，然后层数减少 1。",
    category="buff",
    display_mode="stack",
    order=67,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="no_draw",
    name="不能抽牌",
    description="本回合内不能再抽牌。",
    category="debuff",
    display_mode="stack",
    order=78,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="no_card_block",
    name="不能从卡牌获得格挡",
    description="无法从卡牌效果获得格挡。",
    category="debuff",
    display_mode="turns",
    order=79,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="rage",
    name="愤怒",
    description="本回合每打出一张攻击牌，获得等同于层数的格挡。该格挡不受敏捷等修正影响。",
    category="buff",
    display_mode="stack",
    order=79,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="combust",
    name="自燃",
    description="你的回合结束时，失去 1 点生命，并对所有敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=81,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="dark_embrace",
    name="黑暗之拥",
    description="每当有一张牌被消耗时，抽 1 张牌。",
    category="buff",
    display_mode="stack",
    order=82,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="evolve",
    name="进化",
    description="每当你抽到状态牌时，抽等同于层数的牌。",
    category="buff",
    display_mode="stack",
    order=83,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="feel_no_pain",
    name="无惧疼痛",
    description="每当有一张牌被消耗时，获得等同于层数的格挡。",
    category="buff",
    display_mode="stack",
    order=84,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="fire_breathing",
    name="火焰吐息",
    description="每当你抽到状态牌或诅咒牌时，对所有敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=85,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="fire_breathing_history",
    name="火焰吐息·旧",
    description="你的回合结束时，本回合每打出一张攻击牌，对所有敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=86,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="metallicize",
    name="金属化",
    description="你的回合结束时，获得等同于层数的格挡。",
    category="buff",
    display_mode="stack",
    order=87,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="rupture",
    name="撕裂",
    description="每当你因牌的效果失去生命时，获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
    order=88,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="demon_form",
    name="恶魔形态",
    description="每个回合开始时，获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
    order=70,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="ritual",
    name="仪式",
    description="每个回合开始时，获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
    order=72,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="spore_cloud",
    name="孢子云",
    description="死亡时，使玩家获得等同于层数的易伤。",
    category="buff",
    display_mode="stack",
    order=69,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="mirage_shadows",
    name="蜃楼复影",
    description="每个玩家回合开始时，获得由蜃楼复影记录的格挡。该格挡来自状态结算，不受敏捷影响。",
    category="buff",
    display_mode="stack",
    order=75,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="temporary_dexterity_loss",
    name="临时敏捷降低",
    description="回合结束时恢复等同于层数的敏捷。",
    category="debuff",
    display_mode="stack",
    order=76,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="temporary_dexterity_gain",
    name="临时敏捷提升",
    description="回合结束时失去等同于层数的敏捷。可被人工制品抵挡以保留敏捷。",
    category="debuff",
    display_mode="stack",
    order=76,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="god_in_hand",
    name="手中上帝",
    description="回合开始时结算生命与能量损失；持续结束后结算最终生命损失。",
    category="buff",
    display_mode="stack",
    order=77,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="artifact",
    name="人工制品",
    description="抵挡下一次将要获得的减益状态。每次抵挡消耗 1 层。",
    category="buff",
    display_mode="stack",
    order=80,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="stun",
    name="眩晕",
    description="下一次行动时无法行动；敌人被眩晕时不会推进意图。",
    category="debuff",
    display_mode="turns",
    order=90,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="flinch",
    name="畏缩",
    description="下一次行动时无法行动；敌人被畏缩时不会推进意图。",
    category="debuff",
    display_mode="stack",
    order=425,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="next_target_damage_taken",
    name="好，下一个",
    description="被锁定的攻击目标。来自玩家攻击牌的伤害按层数百分比提高。",
    category="debuff",
    display_mode="percent",
    order=95,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="barricade",
    name="壁垒",
    description="格挡不再在你的回合开始时消失。",
    category="buff",
    display_mode="stack",
    order=89,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="deva_form",
    name="天人形态",
    description="每个回合开始时，本场战斗费用上限增加等同于层数的数值。",
    category="buff",
    display_mode="stack",
    order=90,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="brutality",
    name="残暴",
    description="每个回合开始时，失去等同于层数的生命，并抽等同于层数的牌。",
    category="buff",
    display_mode="stack",
    order=91,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="corruption",
    name="腐化",
    description="所有技能牌耗能变为 0。所有技能牌被打出时消耗。",
    category="buff",
    display_mode="stack",
    order=92,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="juggernaut",
    name="势不可当",
    description="每当你获得格挡时，对随机一名敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=93,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="double_tap",
    name="双发",
    description="本回合接下来若干张攻击牌会额外结算 1 次。",
    category="buff",
    display_mode="stack",
    order=94,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="burst",
    name="爆发",
    description="本回合接下来若干张技能牌会额外结算 1 次。",
    category="buff",
    display_mode="stack",
    order=95,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="amplify",
    name="增幅",
    description="本回合接下来若干张能力牌会额外结算 1 次。",
    category="buff",
    display_mode="stack",
    order=96,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="duplication_potion_next_card",
    name="复制药水",
    description="本回合下一张牌会额外结算 1 次。",
    category="buff",
    display_mode="stack",
    order=97,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="intangible",
    name="无实体",
    description="受到未被格挡的伤害时，该伤害降低为 1。",
    category="buff",
    display_mode="turns",
    order=49,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="vigor",
    name="活力",
    description="下一张攻击牌造成的攻击伤害增加等同于层数的数值。多段攻击每段均受到加成。",
    category="buff",
    display_mode="stack",
    order=18,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="rock_layer",
    name="岩层",
    description="特殊资源状态。可被部分卡牌消耗。",
    category="special",
    display_mode="stack",
    order=19,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="hidden_gravel",
    name="隐蔽石砾",
    description="敌人执行不含攻击的意图前，对该敌人造成等同于层数的效果伤害。",
    category="buff",
    display_mode="stack",
    order=63,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="heavy_rock",
    name="重岩",
    description="每次获得岩层时，额外获得 2 层岩层。多层叠加。",
    category="buff",
    display_mode="stack",
    order=65,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="sedimentation",
    name="沉积作用",
    description="你的回合结束时，获得等同于层数的岩层。",
    category="buff",
    display_mode="stack",
    order=66,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="rock_polishing_9",
    name="岩石打磨",
    description="每个实例独立累计消耗岩层。每累计消耗 9 层岩层，获得 1 点敏捷。",
    category="buff",
    display_mode="stack",
    order=67,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="rock_polishing_6",
    name="岩石打磨+",
    description="每个实例独立累计消耗岩层。每累计消耗 6 层岩层，获得 1 点敏捷。",
    category="buff",
    display_mode="stack",
    order=68,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="magma_layer",
    name="岩浆层",
    description="受到攻击时，使攻击来源获得等同于层数的烧伤；回合结束时层数减少 1。",
    category="buff",
    display_mode="stack",
    order=64,
    decay_timing="turn_end",
    decay_amount=1,
))

register_status_def(StatusDef(
    key="buffer",
    name="缓冲",
    description="阻止下 X 次受到的生命值损伤。被格挡完全抵消的伤害不会消耗缓冲。",
    category="buff",
    display_mode="stack",
    order=48,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="plated_armor",
    name="多层护甲",
    description="每个玩家回合开始时获得等同于层数的格挡；受到来源敌人的未被格挡伤害后层数减少 1。",
    category="buff",
    display_mode="stack",
    order=47,
    decay_timing="none",
    decay_amount=0,
))


register_status_def(StatusDef(
    key="confusion",
    name="混乱",
    description="每当你抽到一张非 X 费用、非状态/诅咒牌时，将其本回合费用随机变为 0 到 3。",
    category="debuff",
    display_mode="stack",
    order=98,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="magnetism",
    name="磁力",
    description="每个回合开始时，增加一张随机无色牌到你的手牌。",
    category="buff",
    display_mode="stack",
    order=99,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="mayhem",
    name="乱战",
    description="每个回合开始时，打出抽牌堆顶部的牌。",
    category="buff",
    display_mode="stack",
    order=100,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="omega",
    name="欧米伽",
    description="玩家回合结束时，对所有敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=101,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="panache",
    name="神气制胜",
    description="每当同一回合内打出第 5、10、15... 张牌时，对所有敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=102,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="sadistic_nature",
    name="残虐天性",
    description="每当你对敌人造成负面状态，使其受到等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=103,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="the_bomb",
    name="炸弹",
    description="倒计时结束后，对所有敌人造成等同于层数的伤害。",
    category="buff",
    display_mode="stack",
    order=104,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="flying",
    name="飞行",
    description="受到攻击伤害降低 50%。如果在一个回合内被攻击伤害等同于层数的次数，该状态消失。",
    category="buff",
    display_mode="stack",
    order=69,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="hex",
    name="邪咒",
    description="每当你打出一张非攻击牌时，将等同于层数的【眩晕】随机放入你的抽牌堆。",
    category="debuff",
    display_mode="stack",
    order=44,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="malleable",
    name="柔韧",
    description="受到攻击时，获得等同于当前柔韧值的格挡。每触发一次，本场本回合内下一次获得的格挡增加 1。在玩家回合开始时重置为基础值。",
    category="buff",
    display_mode="stack",
    order=16,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="pain_stab",
    name="疼痛戳刺",
    description="每当这个敌人对你造成未被格挡的攻击伤害时，向你的弃牌堆加入等同于层数的【伤口】。",
    category="buff",
    display_mode="stack",
    order=17,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="reminiscence",
    name="追思",
    description="晶 Zone 下，每回合开始时每层额外抽 1 张牌。",
    category="buff",
    display_mode="stack",
    order=78,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="abyss_gaze",
    name="深渊凝视",
    description="每层使受到的阴属性攻击伤害增加 1%；被阴属性攻击后清空。拥有该状态的敌人造成的攻击伤害额外 ×0.9。",
    category="debuff",
    display_mode="stack",
    order=54,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="crystal_mist",
    name="结晶薄雾",
    description="没有真实场地 Zone 时，接下来每层使 1 张打出的牌视为在晶 Zone 下。无属性牌也会消耗层数。",
    category="buff",
    display_mode="stack",
    order=75,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="abyss_mist",
    name="深渊薄雾",
    description="没有真实场地 Zone 时，接下来 1 张打出的攻击牌视为在阴 Zone 下。",
    category="buff",
    display_mode="stack",
    order=76,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="abyss_mist_extreme",
    name="极·深渊薄雾",
    description="没有真实场地 Zone 时，接下来 1 张打出的攻击牌视为在极阴 Zone 下。",
    category="buff",
    display_mode="stack",
    order=77,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="tailwind",
    name="顺风",
    description="拥有飞行时，受到的攻击伤害变为 30%。",
    category="buff",
    display_mode="stack",
    order=78,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="insatiable_abyss",
    name="无厌之渊",
    description="对敌人造成阴属性攻击伤害并清除深渊凝视后，若敌人没有死亡，重新赋予一定比例的深渊凝视。层数表示百分比。",
    category="buff",
    display_mode="stack",
    order=79,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="quartz_ritual",
    name="石英祭仪",
    description="每回合开始时，本场战斗费用上限增加等同于层数的数值。地属性攻击牌伤害增加 0.5 倍，随层数叠加。",
    category="buff",
    display_mode="stack",
    order=69,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="living_soil_9",
    name="息壤",
    description="每个实例独立累计消耗岩层。每累计消耗 9 层岩层，获得 5 层岩层。",
    category="buff",
    display_mode="stack",
    order=70,
    decay_timing="none",
    decay_amount=0,
))
register_status_def(StatusDef(
    key="living_soil_6",
    name="息壤+",
    description="每个实例独立累计消耗岩层。每累计消耗 6 层岩层，获得 5 层岩层。",
    category="buff",
    display_mode="stack",
    order=71,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="life_link",
    name="生命链接",
    description="若场上还有其他小黑存活，则死亡后在倒计时结束时以 50% 生命复活。",
    category="buff",
    display_mode="turns",
    order=425,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="fading",
    name="消逝",
    description="倒计时结束时死亡。",
    category="special",
    display_mode="turns",
    order=426,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="shifting",
    name="变幻",
    description="每当受到伤害，将在回合结束前失去相应点数的力量。",
    category="buff",
    display_mode="flag",
    order=427,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="writhing",
    name="扭动",
    description="受到攻击伤害时，改变自己的行动意图。",
    category="buff",
    display_mode="flag",
    order=428,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="self_destruct",
    name="自爆",
    description="倒计时结束后爆炸，对玩家造成伤害，然后死亡。",
    category="buff",
    display_mode="turns",
    order=429,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="constricted",
    name="缠绕",
    description="在你的回合结束时，受到等同于层数的伤害。",
    category="debuff",
    display_mode="stack",
    order=46,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="slow",
    name="缓慢",
    description="本回合玩家每打出一张牌，该敌人受到的伤害增加 10%。",
    category="buff",
    display_mode="flag",
    order=430,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="curious",
    name="好奇",
    description="玩家每打出一张能力牌，该敌人获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
    order=431,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="time_warp",
    name="时间扭曲",
    description="每当玩家累计打出 12 张牌，强制结束玩家回合，并使时间吞噬者获得 2 点力量。",
    category="buff",
    display_mode="stack",
    order=432,
    decay_timing="none",
    decay_amount=0,
))

register_status_def(StatusDef(
    key="draw_reduction",
    name="抽牌减少",
    description="接下来若干回合少抽 1 张牌。",
    category="debuff",
    display_mode="turns",
    order=47,
    decay_timing="none",
    decay_amount=0,
))