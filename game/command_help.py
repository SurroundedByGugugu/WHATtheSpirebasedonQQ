# -*- coding: utf-8 -*-
# 指令提示统一工具：让流程文本同步显示等效中文指令。

COMMAND_ALIASES = {
    "characters": ["character", "chars", "角色", "角色选择", "查看角色"],
    "info": ["说明", "查看说明", "buffinfo", "状态说明"],
    "private": ["私货"],
    "multi": ["mp", "多人", "联机"],
    "pvp": ["对战", "演绎"],

    "yes": ["y", "确认", "是"],
    "no": ["cancel", "取消", "否"],
    "exit": ["退出", "下一把"],
    "sl": ["读档", "回档", "回退"],

    "view": [
        "hand", "查看", "手牌", "查看战斗状态", "查看手牌",
        "run", "info", "角色", "角色状态", "当前状态",
    ],
    "status": ["状态", "查看状态", "查看buff", "buff", "debuff"],
    "state": ["zone", "field", "场地", "查看场地", "查看zone", "查看field"],
    "route": ["map", "路线", "地图"],
    "reward": ["rewards", "奖励", "查看奖励"],
    "chest": ["treasure", "宝箱", "查看宝箱"],
    "open": ["open_chest", "打开", "开宝箱", "打开宝箱"],
    "relics": ["relic", "遗物", "查看已有遗物", "查看遗物"],
    "relic_story": ["relicstory", "lore", "遗物故事", "查看遗物故事"],
    "potions": ["potion_list", "药水", "查看药水"],
    "deck": ["master_deck", "牌库", "查看牌库", "卡组", "查看卡组"],
    "next": ["go", "选择路线", "前进"],

    "event": ["事件"],
    "ancient": ["先古", "先古之民"],
    "rest": ["火堆", "休息"],
    "smith": ["upgrade", "锻造", "升级"],
    "rest_remove": ["pipe", "peace_pipe", "烟斗", "宁静烟斗"],
    "testroom": ["test_room", "测试房间"],

    "take": ["claim", "领取", "拿取"],
    "pick": ["choose", "选择奖励", "选牌"],
    "skip": ["skip_reward", "跳过", "跳过奖励"],
    "replace_potion": ["replacepotion", "换药水", "替换药水"],
    "bowl": ["singing_bowl", "颂钵", "唱歌碗"],
    "bottle": ["bottled", "瓶装", "选择瓶装"],
    "astrolabe": ["星盘"],
    "cage": ["empty_cage", "鸟笼", "空鸟笼"],
    "orrery": ["星系仪"],
    "mirror": ["dolly", "dollys_mirror", "镜子", "多利之镜"],

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
    "retain": ["retain_hand", "选择保留", "保留"],
    "nightmare": ["night_terror", "night", "夜魇"],
    "fossil": ["化石"],
    "reflect": ["reflection", "映照", "辉晶映照"],
    "sync": ["synchronize", "同调"],
    "abyss_index": ["abyssindex", "index_shade", "深渊索引", "索引"],
    "potion_pick": ["potion_card", "药水选牌", "选择药水牌"],
    "elixir": ["万灵", "万灵药水"],
    "codex": ["nilry", "nilrys", "宝典", "尼利"],

    "potion": ["use_potion", "useitem", "使用药水", "使用道具"],
    "plate": ["plating", "镀层", "选择镀层"],
    "toolbox": ["工具箱"],
    "draw": ["drawpile", "draw_pile", "抽牌堆", "查看抽牌堆"],
    "discard": ["discardpile", "discard_pile", "弃牌堆", "查看弃牌堆"],
    "exhaust": [
        "exhaustpile", "exhaust_pile", "消耗牌堆", "消耗堆",
        "查看消耗牌堆", "查看消耗堆",
    ],

    # 目前没有中文等效，留空也能正常生成单行说明。
    "new": [],
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
