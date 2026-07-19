# -*- coding: utf-8 -*-
"""
统一内容开关。

这里暂时只提供框架和空白名单表；具体私货 ID 后续直接填到对应集合即可。
private 内容默认开启，关闭后会从随机池、奖励池、商店池、事件池等入口过滤。
"""

import contextlib
import contextvars


PRIVATE_CONTENT_DEFAULT_ENABLED = True
PRIVATE_CONTENT_SESSION_SETTINGS = {}
_CURRENT_SESSION_ID = contextvars.ContextVar("private_content_session_id", default=None)

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
    "card.abyss_plating",
    "card.crystal_plating",
    "card.crystal_mist",
    "card.abyss_mist",
    "card.tailwind",
    "card.crystal_dust_explosion",
    "card.lightless_prayer",    
    "card.abyss_mire",
    "card.divine_bird",
    "card.abyss_index",
    "card.insatiable_abyss",
    "card.abyss_manifestation",
    "card.prayer_echo",
    "card.abyss_hunt",
    "card.swallow_return",
    "card.abyss_symbiosis",
    "card.abyss_wail",
    "card.sink_into_abyss",
    "card.abyss_chaos",

    "card.mirage_shadows",
    "card.deva_form",
    "card.god_in_hand",
    "card.transfer",
    "card.inducing",
    "card.cheap_intuition",
    "card.energetic",
    "card.everyone_gets_hit",
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
    "relic.whirlwall_sparrow_down",
    "relic.abyssal_whisper",
    "relic.homeward_deep_longing",
    "relic.matte_false_eye",
    "relic.flower_in_abyss",
    
    "relic.piercing_lance",
    "relic.nostalgic_crystal",
    "relic.stalactite",
    "relic.hometown_clear_stone",
    "relic.resonant_azure_sky_stone",

    "relic.cross_earring",

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


def normalize_session_id(session_id):
    if session_id is None:
        return None
    session_id = str(session_id).strip()
    if not session_id:
        return None
    return session_id


def set_private_content_settings(default_enabled=None, session_settings=None):
    """
    从外部配置整体刷新 private 开关。
    session_settings 的 key 使用 group:{group_id} 或 private:{user_id}。
    """
    global PRIVATE_CONTENT_DEFAULT_ENABLED
    global PRIVATE_CONTENT_SESSION_SETTINGS

    if default_enabled is not None:
        PRIVATE_CONTENT_DEFAULT_ENABLED = bool(default_enabled)

    if session_settings is not None:
        cleaned = {}
        for session_id, enabled in session_settings.items():
            session_id = normalize_session_id(session_id)
            if session_id is not None:
                cleaned[session_id] = bool(enabled)
        PRIVATE_CONTENT_SESSION_SETTINGS = cleaned


def is_private_content_enabled(session_id=None):
    session_id = normalize_session_id(session_id)
    if session_id is None:
        session_id = normalize_session_id(_CURRENT_SESSION_ID.get())

    if session_id is not None and session_id in PRIVATE_CONTENT_SESSION_SETTINGS:
        return bool(PRIVATE_CONTENT_SESSION_SETTINGS[session_id])

    return bool(PRIVATE_CONTENT_DEFAULT_ENABLED)


def set_private_content_enabled(enabled, session_id=None):
    global PRIVATE_CONTENT_DEFAULT_ENABLED

    session_id = normalize_session_id(session_id)
    if session_id is None:
        session_id = normalize_session_id(_CURRENT_SESSION_ID.get())

    if session_id is None:
        PRIVATE_CONTENT_DEFAULT_ENABLED = bool(enabled)
        return

    PRIVATE_CONTENT_SESSION_SETTINGS[session_id] = bool(enabled)


def get_private_content_status_text(session_id=None):
    return "开启" if is_private_content_enabled(session_id=session_id) else "关闭"


@contextlib.contextmanager
def private_content_session(session_id):
    token = _CURRENT_SESSION_ID.set(normalize_session_id(session_id))
    try:
        yield
    finally:
        _CURRENT_SESSION_ID.reset(token)


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
