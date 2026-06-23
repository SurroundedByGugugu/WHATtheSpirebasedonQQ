# -*- coding: utf-8 -*-
# 商店节点：商品购买、定向删牌、随机删牌

import copy
import random
from dataclasses import dataclass, field
from typing import Any, List

from data.card.AAAregistry import create_card, CARD_REGISTRY
from data.potion.AAAregistry import create_potion
from data.relic.AAAregistry import create_relic
from game.command_help import command_tip
from game.deck_utils import remove_card_from_master_deck
from game.reward import (
    POTION_REWARD_POOL,
    SHOP_RELIC_POOL,
    FALLBACK_RELIC_ID,
    get_available_relic_ids,
    format_potion_slots,
    format_card_reward_choice,
)
from game.relic_logic.run_relic_utils import (
    add_card_to_master_deck_with_relics,
    has_run_relic,
    is_relic_available_by_floor,
    spend_gold_in_shop,
    apply_card_gain_preview_relics,
)

CARD_RARITY_WEIGHTS = [
    ("common", 8),
    ("uncommon", 7),
    ("rare", 5),
]

SHOP_CARD_QUANTITIES = {"common", "uncommon", "rare"}
SHOP_CARD_FALLBACK_QUANTITIES = {"starting", "common", "uncommon", "rare", "test"}

COLORED_CARD_PRICE_RANGE_BY_QUANTITY = {
    "common": (45, 55),
    "uncommon": (68, 82),
    "rare": (135, 165),

    # 小卡池兜底用。
    "starting": (45, 55),
    "test": (45, 55),
}

COLORLESS_CARD_PRICE_RANGE_BY_QUANTITY = {
    "uncommon": (81, 99),
    "rare": (162, 198),

    # 当前还没有真正的无色罕见 / 稀有牌时兜底用。
    "starting": (81, 99),
    "common": (81, 99),
    "test": (81, 99),
}

RELIC_PRICE_RANGE_BY_QUANTITY = {
    "common": (143, 157),
    "uncommon": (238, 262),
    "rare": (285, 315),
    "shop": (143, 157),

    # 现有占位遗物兜底用。
    "starting": (143, 157),
    "test": (143, 157),
    "ENDER": (143, 157),
}

POTION_PRICE_RANGE_BY_QUANTITY = {
    "common": (48, 52),
    "uncommon": (72, 78),
    "rare": (95, 105),
    "test": (48, 52),
}

SHOP_RANDOM_REMOVE_PRICE = 25
SHOP_REMOVE_PRICE_STEP = 25


def has_membership_card(run_state):
    return has_run_relic(run_state, "relic.membership_card")


def has_courier(run_state):
    return has_run_relic(run_state, "relic.the_courier")


def get_shop_price_multiplier(run_state):
    multiplier = 1.0
    if has_membership_card(run_state):
        multiplier *= 0.5
    if has_courier(run_state):
        multiplier *= 0.8
    return multiplier


def apply_shop_price_modifiers(run_state, items):
    multiplier = get_shop_price_multiplier(run_state)
    if multiplier >= 0.999:
        return
    for item in items:
        old_price = int(item.price)
        item.price = max(1, int(old_price * multiplier))
        tags = []
        if has_membership_card(run_state):
            tags.append("会员卡")
        if has_courier(run_state):
            tags.append("送货员")
        tag_text = "+".join(tags)
        if tag_text and tag_text not in item.title:
            item.title = item.title + "（{}折扣）".format(tag_text)


def get_effective_remove_price(run_state):
    base_price = int(getattr(run_state, "card_remove_price", 50))
    discounted_price = max(0, int(base_price * get_shop_price_multiplier(run_state)))
    if has_run_relic(run_state, "relic.smiling_mask"):
        return min(50, discounted_price)
    return discounted_price


def get_effective_random_remove_price(run_state):
    return max(0, int(SHOP_RANDOM_REMOVE_PRICE * get_shop_price_multiplier(run_state)))


def should_mark_item_sold(run_state):
    return not has_courier(run_state)


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
    used_card_ids = set()

    # 1. 五张有色卡：2 攻击、2 技能、1 能力。
    colored_card_indices = []
    colored_slots = [
        ("attack", 2),
        ("skill", 2),
        ("power", 1),
    ]

    for card_type, count in colored_slots:
        for _ in range(count):
            item = create_colored_card_shop_item(
                rng=rng,
                owner_character_id=character_id,
                card_type=card_type,
                used_card_ids=used_card_ids,
                run_state=run_state
            )
            if item is not None:
                card = item.payload.get("card")
                if card is not None:
                    used_card_ids.add(getattr(card, "card_id", ""))

                colored_card_indices.append(len(items))
                items.append(item)

    # 有色卡中随机一张打五折。
    if colored_card_indices:
        discount_index = rng.choice(colored_card_indices)
        apply_shop_discount(items[discount_index])

    # 2. 两张无色卡：左边罕见，右边稀有。
    colorless_uncommon = create_colorless_card_shop_item(
        rng=rng,
        target_quantity="uncommon",
        used_card_ids=used_card_ids,
        run_state=run_state
    )
    if colorless_uncommon is not None:
        card = colorless_uncommon.payload.get("card")
        if card is not None:
            used_card_ids.add(getattr(card, "card_id", ""))
        items.append(colorless_uncommon)

    colorless_rare = create_colorless_card_shop_item(
        rng=rng,
        target_quantity="rare",
        used_card_ids=used_card_ids,
        run_state=run_state
    )
    if colorless_rare is not None:
        card = colorless_rare.payload.get("card")
        if card is not None:
            used_card_ids.add(getattr(card, "card_id", ""))
        items.append(colorless_rare)

    # 3. 三件遗物：前两件正常遗物，最右边固定商店遗物。
    relic_ids = get_normal_shop_relic_ids(
        run_state=run_state,
        rng=rng,
        count=2
    )
    relic_ids.append(get_shop_exclusive_relic_id(run_state, rng))

    for relic_id in relic_ids:
        relic = create_relic(relic_id)
        items.append(ShopItem(
            item_type="relic",
            title="遗物：【{}】".format(relic.name),
            price=get_relic_shop_price(relic, rng),
            payload={
                "relic": relic
            }
        ))

    # 4. 三瓶药水。
    for _ in range(3):
        potion_id = pick_potion_id_by_weighted_rarity(rng)
        if potion_id is None:
            continue

        potion = create_potion(potion_id)
        items.append(ShopItem(
            item_type="potion",
            title="药水：【{}】".format(potion.name),
            price=get_potion_shop_price(potion, rng),
            payload={
                "potion": potion
            }
        ))

    apply_shop_price_modifiers(run_state, items)

    return ShopState(
        items=items,
        source_node_type=source_node_type
    )


def get_card_shop_price(card, rng, colorless=False, forced_quantity=None, discount=False):
    quantity = forced_quantity or getattr(card, "quantity", "common")

    if colorless:
        ranges = COLORLESS_CARD_PRICE_RANGE_BY_QUANTITY
    else:
        ranges = COLORED_CARD_PRICE_RANGE_BY_QUANTITY

    low, high = ranges.get(quantity, ranges["common"])
    price = rng.randint(low, high)

    if discount:
        price = max(1, price // 2)

    return price


def get_relic_shop_price(relic, rng):
    quantity = getattr(relic, "quantity", "common")
    low, high = RELIC_PRICE_RANGE_BY_QUANTITY.get(
        quantity,
        RELIC_PRICE_RANGE_BY_QUANTITY["common"]
    )
    return rng.randint(low, high)


def get_potion_shop_price(potion, rng):
    quantity = getattr(potion, "quantity", "common")
    low, high = POTION_PRICE_RANGE_BY_QUANTITY.get(
        quantity,
        POTION_PRICE_RANGE_BY_QUANTITY["common"]
    )
    return rng.randint(low, high)


def apply_shop_discount(item):
    item.price = max(1, item.price // 2)

    if "打折" not in item.title:
        item.title = item.title + "（打折）"

    item.payload["discounted"] = True


def weighted_choice(rng, weighted_items):
    total = 0
    for _, weight in weighted_items:
        total += weight

    if total <= 0:
        return None

    roll = rng.uniform(0, total)
    current = 0

    for value, weight in weighted_items:
        current += weight
        if roll <= current:
            return value

    return weighted_items[-1][0]


def remove_used_ids(card_ids, used_card_ids):
    if not used_card_ids:
        return card_ids

    unused = []
    for card_id in card_ids:
        if card_id not in used_card_ids:
            unused.append(card_id)

    # 如果小卡池不够，允许重复兜底，避免商店栏位缺失过多。
    if unused:
        return unused

    return card_ids


def create_colored_card_shop_item(rng, owner_character_id, card_type, used_card_ids=None, run_state=None):
    target_quantity = weighted_choice(rng, CARD_RARITY_WEIGHTS)

    card_ids = get_card_shop_pool(
        owner_character_id=owner_character_id,
        card_type=card_type,
        quantity=target_quantity,
        unowned_only=False,
        strict_quantity=True
    )
    card_ids = remove_used_ids(card_ids, used_card_ids)

    forced_price_quantity = None

    # 小卡池兜底：
    # 如果该类型没有抽中的稀有度，则放宽稀有度；
    # 仍然保持角色归属和卡牌类型。
    if not card_ids:
        card_ids = get_card_shop_pool(
            owner_character_id=owner_character_id,
            card_type=card_type,
            unowned_only=False,
            strict_quantity=False
        )
        card_ids = remove_used_ids(card_ids, used_card_ids)
        forced_price_quantity = target_quantity

    if not card_ids:
        return None

    card_id = rng.choice(card_ids)
    card = create_card(card_id)
    if run_state is not None:
        card = apply_card_gain_preview_relics(run_state, card)

    return ShopItem(
        item_type="card",
        title="卡牌：【{}】".format(card.name),
        price=get_card_shop_price(
            card=card,
            rng=rng,
            colorless=False,
            forced_quantity=forced_price_quantity
        ),
        payload={
            "card": card,
            "shop_slot": "colored",
            "target_quantity": target_quantity,
        }
    )


def create_colorless_card_shop_item(rng, target_quantity, used_card_ids=None, run_state=None):
    card_ids = get_card_shop_pool(
        unowned_only=True,
        quantity=target_quantity,
        strict_quantity=True
    )
    card_ids = remove_used_ids(card_ids, used_card_ids)

    forced_price_quantity = None

    # 当前项目还没有真正的无色罕见 / 稀有牌。
    # 为了商店栏位稳定，临时回退到无归属非状态牌。
    # 后续添加 quantity="uncommon"/"rare" 且 owner_character_id="" 的无色卡后，会自动优先使用真无色卡。
    if not card_ids:
        card_ids = get_card_shop_pool(
            unowned_only=True,
            strict_quantity=False
        )
        card_ids = remove_used_ids(card_ids, used_card_ids)
        forced_price_quantity = target_quantity

    if not card_ids:
        return None

    card_id = rng.choice(card_ids)
    card = create_card(card_id)
    if run_state is not None:
        card = apply_card_gain_preview_relics(run_state, card)

    return ShopItem(
        item_type="card",
        title="无色卡牌：【{}】".format(card.name),
        price=get_card_shop_price(
            card=card,
            rng=rng,
            colorless=True,
            forced_quantity=forced_price_quantity
        ),
        payload={
            "card": card,
            "shop_slot": "colorless",
            "target_quantity": target_quantity,
        }
    )


def get_card_shop_pool(owner_character_id="", card_type=None, quantity=None, unowned_only=False, strict_quantity=True):
    """
    获取商店用卡牌池。

    owner_character_id:
    - 指定角色 ID 时，抽该角色归属卡。
    - unowned_only=True 时，只抽 owner_character_id 为空的无色 / 通用牌。

    quantity:
    - strict_quantity=True 时，只抽指定稀有度。
    - strict_quantity=False 时，允许在 SHOP_CARD_FALLBACK_QUANTITIES 内兜底。
    """
    result = []

    for card_id in CARD_REGISTRY.keys():
        card = create_card(card_id)
        card_owner = getattr(card, "owner_character_id", "")
        current_card_type = getattr(card, "card_type", "")
        current_quantity = getattr(card, "quantity", "")

        # 状态牌永远不进商店。
        if current_card_type == "status" or current_quantity == "status":
            continue

        if unowned_only:
            if card_owner != "":
                continue
        else:
            if card_owner != owner_character_id:
                continue

        if card_type is not None and current_card_type != card_type:
            continue

        if quantity is not None and strict_quantity:
            if current_quantity != quantity:
                continue
        else:
            if current_quantity not in SHOP_CARD_FALLBACK_QUANTITIES:
                continue

        result.append(card_id)

    return result


def get_normal_shop_relic_ids(run_state, rng, count):
    """
    商店前两件遗物：
    - 来自正常遗物池。
    - 排除 shop 稀有度遗物，保证商店遗物是唯一来源。
    - 不够时用造物原型兜底，保证栏位稳定。
    """
    available_relic_ids = list(get_available_relic_ids(run_state))

    normal_relic_ids = []
    for relic_id in available_relic_ids:
        if relic_id == FALLBACK_RELIC_ID:
            continue

        relic = create_relic(relic_id)
        if getattr(relic, "quantity", "") == "shop":
            continue
        if getattr(relic, "can_appear_in_shop", True) is False:
            continue
        if not is_relic_available_by_floor(run_state, relic):
            continue

        normal_relic_ids.append(relic_id)

    result = []

    while len(result) < count:
        if normal_relic_ids:
            relic_id = pick_relic_id_by_weighted_rarity(rng, normal_relic_ids)
            if relic_id is None:
                relic_id = rng.choice(normal_relic_ids)

            result.append(relic_id)
            normal_relic_ids.remove(relic_id)
        else:
            result.append(FALLBACK_RELIC_ID)

    return result


def pick_relic_id_by_weighted_rarity(rng, relic_ids):
    if not relic_ids:
        return None

    target_quantity = weighted_choice(rng, CARD_RARITY_WEIGHTS)

    matching = []
    for relic_id in relic_ids:
        relic = create_relic(relic_id)
        if getattr(relic, "quantity", "") == target_quantity:
            matching.append(relic_id)

    if matching:
        return rng.choice(matching)

    return rng.choice(relic_ids)


def get_shop_exclusive_relic_id(run_state, rng):
    """
    商店最右侧遗物：只从 SHOP_RELIC_POOL 里出。
    如果商店遗物都已拥有且不允许重复，使用造物原型兜底。
    """
    owned_relic_ids = set()
    for relic in getattr(run_state, "relics", []):
        owned_relic_ids.add(getattr(relic, "relic_id", ""))

    current_character_id = getattr(run_state, "character_id", "")
    candidates = []

    for relic_id in SHOP_RELIC_POOL:
        relic = create_relic(relic_id)

        relic_owner = getattr(relic, "owner_character_id", "")
        if relic_owner and relic_owner != current_character_id:
            continue

        if not is_relic_available_by_floor(run_state, relic):
            continue

        allow_duplicate = getattr(relic, "allow_duplicate", False)
        if not allow_duplicate and relic_id in owned_relic_ids:
            continue

        candidates.append(relic_id)

    if candidates:
        return rng.choice(candidates)

    return FALLBACK_RELIC_ID


def pick_potion_id_by_weighted_rarity(rng):
    if not POTION_REWARD_POOL:
        return None

    target_quantity = weighted_choice(rng, CARD_RARITY_WEIGHTS)

    matching = []
    for potion_id in POTION_REWARD_POOL:
        potion = create_potion(potion_id)
        if getattr(potion, "quantity", "common") == target_quantity:
            matching.append(potion_id)

    if matching:
        return rng.choice(matching)

    return rng.choice(POTION_REWARD_POOL)


def _sample_or_choices(rng, pool, count):
    if not pool:
        return []

    if count <= len(pool):
        return rng.sample(pool, count)

    return [
        rng.choice(pool)
        for _ in range(count)
    ]

def format_owner_id(owner_character_id):
    if not owner_character_id:
        return "无归属"

    owner_names = {
        "character.armored_warrior": "铁甲战士",
        "character.yoirine": "Yoirine",
        "character.lumine": "Lumine",
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
            get_effective_remove_price(run_state)
        ))
        lines.append("随机删除一张牌：{} 金币。使用 /card random_remove。".format(
            get_effective_random_remove_price(run_state)
        ))

    lines.append("")
    lines.append(command_tip("buy", "使用 /card buy 0 购买商品。"))
    lines.append(command_tip("buy", "使用 /card buy 0,1,2 批量购买商品。"))
    lines.append(command_tip("leave", "使用 /card leave 离开商店。"))
    lines.append(command_tip("item", "使用 /card item 0 查看商品详情。"))

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
        actual_quantity = getattr(card, "quantity", "")
        target_quantity = item.payload.get("target_quantity", "")
        lines.append("稀有度：{}".format(format_quantity(actual_quantity)))
        if target_quantity and target_quantity != actual_quantity:
            lines.append("商店栏位稀有度：{}".format(format_quantity(target_quantity)))
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
        item.sold = should_mark_item_sold(run_state)
        logs = []
        logs.append("购买卡牌：【{}】。当前金币：{}。".format(card.name, run_state.gold))
        logs.extend(spend_gold_in_shop(run_state, item.price))
        logs.extend(add_card_to_master_deck_with_relics(run_state, card, source="购买卡牌"))
        if has_courier(run_state):
            logs.append("【送货员】使该商品没有售罄。")
        return "\n".join(logs)

    if item.item_type == "relic":
        relic = item.payload.get("relic")
        run_state.gold -= item.price
        run_state.relics.append(relic)
        item.sold = should_mark_item_sold(run_state)

        logs = []
        logs.append("购买遗物：【{}】。当前金币：{}。".format(
            relic.name,
            run_state.gold
        ))
        logs.extend(spend_gold_in_shop(run_state, item.price))

        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))
        if has_courier(run_state):
            logs.append("【送货员】使该商品没有售罄。")

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
        item.sold = should_mark_item_sold(run_state)
        logs = []
        logs.append("购买药水：【{}】。当前金币：{}。".format(potion.name, run_state.gold))
        logs.extend(spend_gold_in_shop(run_state, item.price))
        if has_courier(run_state):
            logs.append("【送货员】使该商品没有售罄。")
        return "\n".join(logs)

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

        before_gold = int(run_state.gold)
        before_sold = item.sold
        reply = buy_shop_item(run_state, item_index)
        logs.append("批量购买第 {} 项：[{}]".format(seen_step, item_index))
        logs.append(reply)

        # 药水栏满等情况会返回提示且不扣金币。送货员存在时商品不会售罄，
        # 因而用金币变化辅助判断是否购买成功。
        if int(run_state.gold) == before_gold and not before_sold and not item.sold:
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

    price = get_effective_remove_price(run_state)

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
    lines.append(command_tip("remove", "使用 /card remove 0 删除对应牌。"))

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

    price = get_effective_remove_price(run_state)

    if run_state.gold < price:
        return "金币不足。当前金币：{}，需要：{}。".format(
            run_state.gold,
            price
        )

    removed_card, remove_logs = remove_card_from_master_deck(run_state, card_index, reason="shop_remove")
    if removed_card is None:
        return "\n".join(remove_logs)

    old_base_price = int(getattr(run_state, "card_remove_price", 50))
    run_state.gold -= price
    run_state.card_remove_price = old_base_price + SHOP_REMOVE_PRICE_STEP
    shop_state.remove_used = True

    logs = []
    logs.append("定向删除【{}】。花费 {} 金币，当前金币：{}。下次定向删除基础价格：{}。".format(
        removed_card.name,
        price,
        run_state.gold,
        run_state.card_remove_price
    ))
    logs.extend(spend_gold_in_shop(run_state, price))
    logs.extend(remove_logs[1:])
    return "\n".join(logs)

def random_remove_card(run_state, seed=None):
    shop_state = run_state.pending_shop

    if shop_state is None:
        return "当前不在商店。"

    if shop_state.remove_used:
        return "本商店已经使用过删牌服务。"

    deck = getattr(run_state, "master_deck", [])

    if not deck:
        return "当前牌组为空，无法删除。"

    price = get_effective_random_remove_price(run_state)

    if run_state.gold < price:
        return "金币不足。当前金币：{}，需要：{}。".format(
            run_state.gold,
            price
        )

    rng = random.Random(seed)
    card_index = rng.randrange(len(deck))
    removed_card, remove_logs = remove_card_from_master_deck(run_state, card_index, reason="shop_random_remove")
    if removed_card is None:
        return "\n".join(remove_logs)

    run_state.gold -= price
    shop_state.remove_used = True

    logs = []
    logs.append("你支付了 {} 金币。商人随手抽走了一张【{}】。当前金币：{}。定向删除价格仍为 {}。".format(
        price,
        removed_card.name,
        run_state.gold,
        get_effective_remove_price(run_state)
    ))
    logs.extend(spend_gold_in_shop(run_state, price))
    logs.extend(remove_logs[1:])
    return "\n".join(logs)
