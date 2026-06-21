# -*- coding: utf-8 -*-
# 指令提示统一工具：让流程文本同步显示等效中文指令。

COMMAND_ALIASES = {
    "yes": ["y", "确认", "是"],
    "no": ["cancel", "取消", "否"],
    "exit": ["退出", "下一把"],
    "sl": ["读档", "回档", "回退"],

    "view": ["hand", "查看", "手牌", "查看战斗状态", "查看手牌"],
    "route": ["map", "路线", "地图"],
    "reward": ["rewards", "奖励", "查看奖励"],
    "next": ["go", "选择路线", "前进"],

    "event": ["事件"],
    "ancient": ["先古", "先古之民"],
    "rest": ["火堆", "休息"],
    "smith": ["upgrade", "锻造", "升级"],

    "take": ["claim", "领取", "拿取"],
    "pick": ["choose", "选择奖励", "选牌"],
    "skip": ["skip_reward", "跳过", "跳过奖励"],
    "replace_potion": ["replacepotion", "换药水", "替换药水"],

    "shop": ["商店"],
    "buy": ["购买"],
    "leave": ["离开"],
    "item": ["goods", "商品", "查看商品", "shop_item", "detail", "详情"],
    "remove": ["remove_card", "删牌", "删除牌"],
    "random_remove": ["randomremove", "随机删牌"],

    "drop": ["drop_hand", "丢弃手牌", "选择丢弃"],
    "top": ["headbutt", "置顶", "选择弃牌置顶"],
    "exhaust_hand": ["burn", "consume", "选择消耗", "消耗手牌"],
    "handtop": ["hand_top", "warcry", "置顶手牌", "手牌置顶"],
    "upgrade_hand": ["upgradehand", "armaments", "选择升级", "升级手牌"],
    "duplicate_hand": ["dual_wield", "复制手牌", "双持"],
    "exhume": ["发掘", "选择发掘"],

    # 目前没有中文等效，留空也能正常生成单行说明。
    "play": [],
    "end": [],
}


def command_alias_text(command):
    aliases = COMMAND_ALIASES.get(command, [])
    if not aliases:
        return ""
    return "【{}等效{}。】".format(command, "，".join(aliases))


def command_tip(command, usage):
    alias_text = command_alias_text(command)
    if alias_text:
        return usage + "\n" + alias_text
    return usage