# -*- coding: utf-8 -*-
# 商店节点：商品购买、定向删牌、随机删牌

import copy
import random
from dataclasses import dataclass, field
from typing import Any, List

from data.card.AAAregistry import create_card, CARD_REGISTRY
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from game.reward import (
    POTION_REWARD_POOL,
    get_available_relic_ids,
    format_potion_slots,
    format_card_reward_choice,
)

CARD_PRICE_BY_QUANTITY = {
    "starting": 30,
    "common": 50,
    "uncommon": 75,
    "rare": 150,
    "myth": 250,
    "test": 30,
}

RELIC_PRICE_BY_QUANTITY = {
    "starting": 150,
    "common": 150,
    "uncommon": 200,
    "rare": 250,
    "myth": 350,
    "shop": 180,
    "event": 200,
    "test": 120,
    "ENDER": 150,
}

POTION_PRICE_BY_QUANTITY = {
    "common": 50,
    "uncommon": 75,
    "rare": 100,
    "test": 40,
}

SHOP_RANDOM_REMOVE_PRICE = 25
SHOP_REMOVE_PRICE_STEP = 25


@dataclass
class ShopItem:
    item_type: str
    title: str
    price: int
    payload: Any = None
    sold: bool = False


@dataclass
class ShopState:
    items: List[ShopItem] = field(default_factory=list)
    remove_used: bool = False
    source_node_type: str = "shop"


def create_shop_state(run_state, seed=None, source_node_type="shop"):
    rng = random.Random(seed)
    items = []

    character_id = getattr(run_state, "character_id", "")
    # 1. 本角色攻击牌 * 2
    add_card_shop_items(
        items=items,
        rng=rng,
        card_ids=get_card_shop_pool(
            owner_character_id=character_id,
            card_type="attack"
        ),
        count=2
    )
    # 2. 本角色技能牌 * 2
    add_card_shop_items(
        items=items,
        rng=rng,
        card_ids=get_card_shop_pool(
            owner_character_id=character_id,
            card_type="skill"
        ),
        count=2
    )
    # 3. 本角色能力牌 * 1
    add_card_shop_items(
        items=items,
        rng=rng,
        card_ids=get_card_shop_pool(
            owner_character_id=character_id,
            card_type="power"
        ),
        count=1
    )
    # 4. 无归属牌 * 2
    add_card_shop_items(
        items=items,
        rng=rng,
        card_ids=get_card_shop_pool(
            unowned_only=True
        ),
        count=2
    )
    # 5. 遗物 * 3，不够就用造物原型补足
    relic_ids = get_shop_relic_ids(
        run_state=run_state,
        rng=rng,
        count=3
    )
    for relic_id in relic_ids:
        relic = create_relic(relic_id)
        items.append(ShopItem(
            item_type="relic",
            title="遗物：【{}】".format(relic.name),
            price=get_relic_shop_price(relic),
            payload={
                "relic": relic
            }
        ))
    # 6. 药水 * 3
    potion_ids = _sample_or_choices(rng, POTION_REWARD_POOL, 3)
    for potion_id in potion_ids:
        potion = create_potion(potion_id)
        items.append(ShopItem(
            item_type="potion",
            title="药水：【{}】".format(potion.name),
            price=get_potion_shop_price(potion),
            payload={
                "potion": potion
            }
        ))
    return ShopState(
        items=items,
        source_node_type=source_node_type
    )

def get_card_shop_price(card):
    quantity = getattr(card, "quantity", "common")
    return CARD_PRICE_BY_QUANTITY.get(quantity, 50)


def get_relic_shop_price(relic):
    quantity = getattr(relic, "quantity", "common")
    return RELIC_PRICE_BY_QUANTITY.get(quantity, 150)


def get_potion_shop_price(potion):
    quantity = getattr(potion, "quantity", "common")
    return POTION_PRICE_BY_QUANTITY.get(quantity, 50)


def get_card_shop_pool(owner_character_id="", card_type=None, unowned_only=False):
    """
    获取商店用卡牌池。

    owner_character_id:
    - 指定角色 ID 时，抽该角色归属卡。
    - unowned_only=True 时，只抽 owner_character_id 为空的通用牌。
    """
    result = []

    for card_id in CARD_REGISTRY.keys():
        card = create_card(card_id)
        card_owner = getattr(card, "owner_character_id", "")
        current_card_type = getattr(card, "card_type", "")

        if unowned_only:
            if card_owner != "":
                continue
        else:
            if card_owner != owner_character_id:
                continue

        if card_type is not None and current_card_type != card_type:
            continue

        result.append(card_id)

    return result


def add_card_shop_items(items, rng, card_ids, count):
    selected_card_ids = _sample_or_choices(rng, card_ids, count)

    for card_id in selected_card_ids:
        card = create_card(card_id)
        items.append(ShopItem(
            item_type="card",
            title="卡牌：【{}】".format(card.name),
            price=get_card_shop_price(card),
            payload={
                "card": card
            }
        ))


def get_shop_relic_ids(run_state, rng, count):
    """
    商店遗物：
    - 优先从当前可获得遗物中抽。
    - 不够 count 个时，用造物原型补足。
    """
    fallback_relic_id = "relic.homunculus_prototype"

    available_relic_ids = list(get_available_relic_ids(run_state))

    normal_relic_ids = []
    for relic_id in available_relic_ids:
        if relic_id == fallback_relic_id:
            continue
        normal_relic_ids.append(relic_id)

    result = []

    if normal_relic_ids:
        if len(normal_relic_ids) >= count:
            result.extend(rng.sample(normal_relic_ids, count))
        else:
            result.extend(rng.sample(normal_relic_ids, len(normal_relic_ids)))

    while len(result) < count:
        result.append(fallback_relic_id)

    return result


def format_owner_id(owner_character_id):
    if not owner_character_id:
        return "无归属"

    owner_names = {
        "character.armored_warrior": "铁甲战士",
        "character.yoirine": "Yoirine",
        "character.test": "测试角色",
    }

    return owner_names.get(owner_character_id, owner_character_id)


def format_quantity(quantity):
    names = {
        "starting": "初始",
        "common": "普通",
        "uncommon": "罕见",
        "rare": "稀有",
        "myth": "神话",
        "shop": "商店",
        "event": "事件",
        "test": "测试",
        "ENDER": "终局占位",
    }
    return names.get(quantity, quantity)

def _sample_or_choices(rng, pool, count):
    if not pool:
        return []

    if count <= len(pool):
        return rng.sample(pool, count)

    return [
        rng.choice(pool)
        for _ in range(count)
    ]


def format_shop(run_state):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    lines = []
    lines.append("=== 商店 ===")
    lines.append("金币：{}".format(run_state.gold))
    lines.append("")
    lines.append("商品：")

    if not shop_state.items:
        lines.append("无商品。")
    else:
        for index, item in enumerate(shop_state.items):
            status = ""

            if item.sold:
                status = "（已售罄）"

            lines.append("[{}] {} 价格：{} 金币{}".format(
                index,
                item.title,
                item.price,
                status
            ))

    lines.append("")
    lines.append("服务：")

    if shop_state.remove_used:
        lines.append("[已使用] 本商店已经使用过删牌服务。")
    else:
        lines.append("定向删除一张牌：{} 金币。使用 /card remove 查看牌组。".format(
            getattr(run_state, "card_remove_price", 50)
        ))
        lines.append("随机删除一张牌：{} 金币。使用 /card random_remove。".format(
            SHOP_RANDOM_REMOVE_PRICE
        ))

    lines.append("")
    lines.append("使用 /card buy 0 购买商品。")
    lines.append("使用 /card buy 0,1,2 批量购买商品。")
    lines.append("使用 /card leave 离开商店。")
    lines.append("使用 /card item 0 查看商品详情。")

    return "\n".join(lines)


def format_shop_item_detail(run_state, item_index):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if item_index < 0 or item_index >= len(shop_state.items):
        return "商品编号无效。"

    item = shop_state.items[item_index]

    lines = []
    lines.append("=== 商品详情 ===")
    lines.append("[{}] {}".format(item_index, item.title))
    lines.append("价格：{} 金币".format(item.price))
    lines.append("状态：{}".format("已售罄" if item.sold else "可购买"))
    lines.append("")

    if item.item_type == "card":
        card = item.payload.get("card")

        if card is None:
            lines.append("卡牌数据异常。")
            return "\n".join(lines)

        lines.append("类型：卡牌")
        lines.append("归属：{}".format(format_owner_id(getattr(card, "owner_character_id", ""))))
        lines.append("稀有度：{}".format(format_quantity(getattr(card, "quantity", ""))))
        lines.append("卡牌类型：{}".format(getattr(card, "card_type", "")))
        lines.append("")
        lines.append(format_card_reward_choice(card))
        return "\n".join(lines)

    if item.item_type == "relic":
        relic = item.payload.get("relic")

        if relic is None:
            lines.append("遗物数据异常。")
            return "\n".join(lines)

        lines.append("类型：遗物")
        lines.append("归属：{}".format(format_owner_id(getattr(relic, "owner_character_id", ""))))
        lines.append("稀有度：{}".format(format_quantity(getattr(relic, "quantity", ""))))
        lines.append("")
        lines.append(relic.summary_text())

        story = getattr(relic, "story", "")
        if story:
            lines.append("")
            lines.append("故事：{}".format(story))

        return "\n".join(lines)

    if item.item_type == "potion":
        potion = item.payload.get("potion")

        if potion is None:
            lines.append("药水数据异常。")
            return "\n".join(lines)

        lines.append("类型：药水")
        lines.append("稀有度：{}".format(format_quantity(getattr(potion, "quantity", "common"))))
        lines.append("")
        lines.append(potion.summary_text())
        return "\n".join(lines)

    lines.append("未知商品类型：{}。".format(item.item_type))
    return "\n".join(lines)

def buy_shop_item(run_state, item_index):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if item_index < 0 or item_index >= len(shop_state.items):
        return "商品编号无效。"

    item = shop_state.items[item_index]

    if item.sold:
        return "该商品已经售罄。"

    if run_state.gold < item.price:
        return "金币不足。当前金币：{}，需要：{}。".format(
            run_state.gold,
            item.price
        )

    if item.item_type == "card":
        card = copy.deepcopy(item.payload.get("card"))
        run_state.gold -= item.price
        run_state.master_deck.append(card)
        item.sold = True
        return "购买卡牌：【{}】。当前金币：{}。".format(
            card.name,
            run_state.gold
        )

    if item.item_type == "relic":
        relic = item.payload.get("relic")
        run_state.gold -= item.price
        run_state.relics.append(relic)
        item.sold = True

        logs = []
        logs.append("购买遗物：【{}】。当前金币：{}。".format(
            relic.name,
            run_state.gold
        ))

        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))

        return "\n".join(logs)

    if item.item_type == "potion":
        potion = item.payload.get("potion")
        max_slots = getattr(run_state, "max_potion_slots", 3)

        if len(run_state.potions) >= max_slots:
            return "\n".join([
                "药水栏已满，无法购买【{}】。".format(potion.name),
                "",
                format_potion_slots(run_state)
            ])

        run_state.gold -= item.price
        run_state.potions.append(potion)
        item.sold = True
        return "购买药水：【{}】。当前金币：{}。".format(
            potion.name,
            run_state.gold
        )

    return "未知商品类型：{}。".format(item.item_type)


def buy_shop_items(run_state, item_indices):
    """
    批量购买商店商品。

    规则：
    1. 按输入顺序依次购买。
    2. 每次购买都按当前金币、当前商品状态重新判断。
    3. 某一项购买失败时中止，后续商品不再计算。
    4. 已经成功购买的商品不会回滚。
    """
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if not item_indices:
        return "没有指定要购买的商品编号。"

    logs = []
    seen_step = 0

    for item_index in item_indices:
        seen_step += 1

        if item_index < 0 or item_index >= len(shop_state.items):
            logs.append("批量购买第 {} 项中止：商品编号无效：{}。".format(
                seen_step,
                item_index
            ))
            break

        item = shop_state.items[item_index]

        if item.sold:
            logs.append("批量购买第 {} 项中止：[{}] 已售罄。".format(
                seen_step,
                item_index
            ))
            break

        if run_state.gold < item.price:
            logs.append("批量购买第 {} 项中止：金币不足。当前金币：{}，需要：{}。".format(
                seen_step,
                run_state.gold,
                item.price
            ))
            break

        before_sold = item.sold
        reply = buy_shop_item(run_state, item_index)
        logs.append("批量购买第 {} 项：[{}]".format(seen_step, item_index))
        logs.append(reply)

        # 药水栏满等情况会返回提示，但不会把 item.sold 改成 True。
        # 这种视为购买失败，中止后续购买。
        if not before_sold and not item.sold:
            logs.append("该商品未成功购买，批量购买中止。")
            break

    return "\n".join(logs)

def format_remove_card_choices(run_state):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if shop_state.remove_used:
        return "本商店已经使用过删牌服务。"

    deck = getattr(run_state, "master_deck", [])

    if not deck:
        return "当前牌组为空，无法删除。"

    price = getattr(run_state, "card_remove_price", 50)

    lines = []
    lines.append("=== 定向删除牌 ===")
    lines.append("当前费用：{} 金币。".format(price))
    lines.append("")

    for index, card in enumerate(deck):
        lines.append("[{}] {}".format(
            index,
            card.summary_text()
        ))

    lines.append("")
    lines.append("使用 /card remove 0 删除对应牌。")

    return "\n".join(lines)


def remove_card_by_index(run_state, card_index):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if shop_state.remove_used:
        return "本商店已经使用过删牌服务。"

    deck = getattr(run_state, "master_deck", [])

    if not deck:
        return "当前牌组为空，无法删除。"

    if card_index < 0 or card_index >= len(deck):
        return "卡牌编号无效。"

    price = getattr(run_state, "card_remove_price", 50)

    if run_state.gold < price:
        return "金币不足。当前金币：{}，需要：{}。".format(
            run_state.gold,
            price
        )

    removed_card = deck.pop(card_index)

    run_state.gold -= price
    run_state.card_remove_price = price + SHOP_REMOVE_PRICE_STEP
    shop_state.remove_used = True

    return "定向删除【{}】。花费 {} 金币，当前金币：{}。下次定向删除价格：{}。".format(
        removed_card.name,
        price,
        run_state.gold,
        run_state.card_remove_price
    )


def random_remove_card(run_state, seed=None):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if shop_state.remove_used:
        return "本商店已经使用过删牌服务。"

    deck = getattr(run_state, "master_deck", [])

    if not deck:
        return "当前牌组为空，无法删除。"

    if run_state.gold < SHOP_RANDOM_REMOVE_PRICE:
        return "金币不足。当前金币：{}，需要：{}。".format(
            run_state.gold,
            SHOP_RANDOM_REMOVE_PRICE
        )

    rng = random.Random(seed)
    card_index = rng.randrange(len(deck))
    removed_card = deck.pop(card_index)

    run_state.gold -= SHOP_RANDOM_REMOVE_PRICE
    shop_state.remove_used = True

    return "你支付了 {} 金币。商人随手抽走了一张【{}】。当前金币：{}。定向删除价格仍为 {}。".format(
        SHOP_RANDOM_REMOVE_PRICE,
        removed_card.name,
        run_state.gold,
        getattr(run_state, "card_remove_price", 50)
    )