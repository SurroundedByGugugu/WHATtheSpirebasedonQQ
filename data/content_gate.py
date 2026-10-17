# -*- coding: utf-8 -*-
"""
统一内容开关。

private 内容默认开启，关闭后会从随机池、奖励池、商店池、事件池等入口过滤。
专属内容按角色归属自动分类；原作角色的自定义内容、通用内容维护显式名单。
STS2 内容仍算原作，不按稀有度、属性或球类型推断来源。
"""

import contextlib
import contextvars


PRIVATE_CONTENT_DEFAULT_ENABLED = True
PRIVATE_CONTENT_SESSION_SETTINGS = {}
_CURRENT_SESSION_ID = contextvars.ContextVar("private_content_session_id", default=None)

PRIVATE_CHARACTER_IDS = {
    'character.lumine', 'character.yoirine', 'character.suzuri', 'character.lizhou',
}

PRIVATE_CARD_IDS = [
    "card.recrystallization", "card.full_crystal",
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
    "card.crystal_dust",
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
    "card.flash",
    "card.crystal_curtain_strike",
    "card.crystal_reflection",
    "card.phase_plating",
    "card.mirror_reflection",

    "card.mirage_shadows",
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
    "relic.warm_granite",
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
PRIVATE_CARD_IDS.extend([
    'card.curse.region_lock', 'card.machine_rush',
    'card.convolutional_neural_network', 'card.transformer',
    'card.rock_forming_action', 'card.radiant_crystal_reflection',
])
PRIVATE_RELIC_IDS.extend([
    'relic.doubao', 'relic.ant_afu', 'relic.claude', 'relic.gpt',
    'relic.gemini', 'relic.deepseek',
    'relic.four_color_nectar',
])
PRIVATE_EVENT_IDS = ['event.software_shop']
PRIVATE_POTION_IDS = ['potion.saturated_calcium_carbonate_solution']

# Confirmed provenance: the added Ironclad cards and colorless Amplify are STS2.
# X Potion, Dragon Fruit, Miniature Tent, Ssserpent Head and White Star stay enabled.
# Xanthosis is the starting-relic replacement equivalent; Homunculus Prototype
# is the Circlet equivalent. Holy Water (the event) also stays enabled.
# Molten Fist, Enthralled and glass orbs must not be excluded as custom mechanics.

from data.card.character.lizhou_cards import LIZHOU_CARD_REGISTRY
PRIVATE_CARD_IDS.extend(LIZHOU_CARD_REGISTRY)
PRIVATE_RELIC_IDS.extend(['relic.anchored_eye', 'relic.twelve_zodiacs'])

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
    if kind == 'character':
        return content_id in PRIVATE_CHARACTER_IDS
    # Resolve lazily to avoid registry imports while those registries initialize.
    # New cards/relics/potions owned by a custom character inherit its provenance.
    if kind in ('card', 'relic', 'potion'):
        if kind == 'card':
            from data.card.AAAregistry import CARD_REGISTRY as registry
        elif kind == 'relic':
            from data.relic.AAAregistry import RELIC_REGISTRY as registry
        else:
            from data.potion.AAAregistry import POTION_REGISTRY as registry
        factory = registry.get(content_id)
        if factory is not None:
            template = factory()
            if (getattr(template, 'owner_character_id', '') in PRIVATE_CHARACTER_IDS
                    or getattr(template, 'quantity', '') == 'test'):
                return True
    if kind == "card":
        return content_id in PRIVATE_CARD_IDS or content_id.startswith('card.dance.')
    if kind == "relic":
        return content_id in PRIVATE_RELIC_IDS
    if kind == "event":
        return content_id in PRIVATE_EVENT_IDS
    if kind == "encounter":
        return content_id in PRIVATE_ENCOUNTER_IDS
    if kind == 'potion':
        return content_id in PRIVATE_POTION_IDS
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
