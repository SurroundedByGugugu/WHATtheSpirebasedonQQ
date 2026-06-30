# -*- coding: utf-8 -*-
# 按实体类型包装显示名，集中维护中文括号样式。

CARD_TYPE_BRACKETS = {
    "attack": ("［", "］"),
    "skill": ("「", "」"),
    "power": ("｛", "｝"),
    "curse": ("【", "】"),
    "status": ("〖", "〗"),
}
CARD_FALLBACK_BRACKETS = ("『", "』")

POTION_BRACKETS = ("〔", "〕")
RELIC_BRACKETS = ("〈", "〉")


def wrap_display_name(name, brackets):
    left, right = brackets
    return "{}{}{}".format(left, name, right)


def get_card_type_brackets(card_type):
    return CARD_TYPE_BRACKETS.get(str(card_type or ""), CARD_FALLBACK_BRACKETS)


def format_card_display_name(card_or_name, card_type=None):
    if card_type is None and not isinstance(card_or_name, str):
        card_type = getattr(card_or_name, "card_type", "")
        name = getattr(card_or_name, "name", "未知卡牌")
    else:
        name = card_or_name
    return wrap_display_name(name, get_card_type_brackets(card_type))


def format_potion_display_name(potion_or_name):
    if isinstance(potion_or_name, str):
        name = potion_or_name
    else:
        name = getattr(potion_or_name, "name", "药水")
    return wrap_display_name(name, POTION_BRACKETS)


def format_relic_display_name(relic_or_name):
    if isinstance(relic_or_name, str):
        name = relic_or_name
    else:
        name = getattr(relic_or_name, "name", "遗物")
    return wrap_display_name(name, RELIC_BRACKETS)
