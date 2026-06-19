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
    key="berserk",
    name="狂暴",
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