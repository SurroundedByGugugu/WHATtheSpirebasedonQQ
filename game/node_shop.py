# -*- coding: utf-8 -*-
# 商店节点：商品购买、定向删牌、随机删牌

import copy
import random
from dataclasses import dataclass, field
from typing import Any, List

from data.card.AAAregistry import create_card
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from game.reward import (
    CARD_REWARD_POOL,
    POTION_REWARD_POOL,
    get_available_relic_ids,
    format_potion_slots,
)


SHOP_CARD_PRICE = 30
SHOP_RELIC_PRICE = 150
SHOP_POTION_PRICE = 50

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

    card_ids = _sample_or_choices(rng, CARD_REWARD_POOL, 3)
    for card_id in card_ids:
        card = create_card(card_id)
        items.append(ShopItem(
            item_type="card",
            title="卡牌：【{}】".format(card.name),
            price=SHOP_CARD_PRICE,
            payload={
                "card": card
            }
        ))

    relic_ids = get_available_relic_ids(run_state)
    if relic_ids:
        relic = create_relic(rng.choice(relic_ids))
        items.append(ShopItem(
            item_type="relic",
            title="遗物：【{}】".format(relic.name),
            price=SHOP_RELIC_PRICE,
            payload={
                "relic": relic
            }
        ))

    potion_ids = _sample_or_choices(rng, POTION_REWARD_POOL, 2)
    for potion_id in potion_ids:
        potion = create_potion(potion_id)
        items.append(ShopItem(
            item_type="potion",
            title="药水：【{}】".format(potion.name),
            price=SHOP_POTION_PRICE,
            payload={
                "potion": potion
            }
        ))

    return ShopState(
        items=items,
        source_node_type=source_node_type
    )


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
    lines.append("使用 /card leave 离开商店。")

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