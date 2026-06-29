# -*- coding: utf-8 -*-
"""
统一内容开关。

这里暂时只提供框架和空白名单表；具体私货 ID 后续直接填到对应集合即可。
private 内容默认开启，关闭后会从随机池、奖励池、商店池、事件池等入口过滤。
"""

PRIVATE_CONTENT_ENABLED = True

PRIVATE_CARD_IDS = [
    "card.fire_strike",
    "card.fire_zone",

    "card.crystal_piercing",
    "card.spreading_wing",
    "card.crystal_zone",
    "card.crystal_cocoon",
    "card.crystal_thorns",
    "card.reminiscence",
    "card.abyssal_form",
    "card.phantom_form",
    "card.rockbound_wish",
    "card.abyssal_erosion",
    "card.brave_bird",
    "card.roost",
    "card.fleeting_shadow",
    "card.call_of_the_abyss",
    "card.to_your_tranquility",
    "card.trace_pursuit",
    "card.abyss_gaze",

    "card.mirage_shadows",
    "card.god_in_hand",
    "card.transfer",
    "card.inducing",
    "card.cheap_intuition",
    "card.energetic",
    "card.factor_separate",
    "card.fast_transfer",
    "card.brain_shockwave",
    "card.ok_next",
]

PRIVATE_RELIC_IDS = [
    "relic.cabbage",
    "relic.keystone_of_the_tomb",
    "relic.saturated_fissure",
    "relic.cross_earring",
    "relic.placeholder_stone",
    "relic.ether_medium",
    "relic.unsealed_abyss",

]
PRIVATE_EVENT_IDS = []

PRIVATE_ENCOUNTER_IDS = [
    "encounter.test_dummy",
    "encounter.corsoal_single",
    "encounter.mareanie_single",
    "encounter.elite.chaos_fragment",
    "encounter.elite.plastic_bag",
    "encounter.corsoal_mareanie_pack"
]


def is_private_content_enabled():
    return bool(PRIVATE_CONTENT_ENABLED)


def set_private_content_enabled(enabled):
    global PRIVATE_CONTENT_ENABLED
    PRIVATE_CONTENT_ENABLED = bool(enabled)


def get_private_content_status_text():
    return "开启" if is_private_content_enabled() else "关闭"


def is_private_content(kind, content_id):
    content_id = str(content_id or "")
    if kind == "card":
        return content_id in PRIVATE_CARD_IDS
    if kind == "relic":
        return content_id in PRIVATE_RELIC_IDS
    if kind == "event":
        return content_id in PRIVATE_EVENT_IDS
    if kind == "encounter":
        return content_id in PRIVATE_ENCOUNTER_IDS
    return False


def is_content_enabled(kind, content_id):
    return is_private_content_enabled() or not is_private_content(kind, content_id)


def filter_content_ids(kind, content_ids):
    return [
        content_id
        for content_id in content_ids
        if is_content_enabled(kind, content_id)
    ]


def filter_card_ids(card_ids):
    return filter_content_ids("card", card_ids)


def filter_relic_ids(relic_ids):
    return filter_content_ids("relic", relic_ids)


def filter_event_ids(event_ids):
    return filter_content_ids("event", event_ids)


def filter_encounter_ids(encounter_ids):
    return filter_content_ids("encounter", encounter_ids)
