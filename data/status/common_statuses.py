# data/status/common_statuses.py
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
    description="回合结束时失去等同于层数的生命，然后层数减少 1。",
    category="debuff",
    display_mode="stack",
    order=50,
    decay_timing="turn_end",
    decay_amount=1,
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
    key="demon_form",
    name="恶魔形态",
    description="每个玩家回合开始时，获得等同于层数的力量。",
    category="buff",
    display_mode="stack",
    order=70,
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