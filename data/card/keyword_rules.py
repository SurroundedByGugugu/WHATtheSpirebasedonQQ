# data/card/keyword_rules.py
# -*- coding: utf-8 -*-

from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE,
)


KEYWORD_DISPLAY_NAMES = {
    KEYWORD_EXHAUST: "消耗",
    KEYWORD_ETHEREAL: "虚无",
    KEYWORD_RETAIN: "保留",
    KEYWORD_CLEVER: "奇巧",
    KEYWORD_INNATE: "固有"
}


# 数值越大，优先级越高。
# 虚无高于其他：回合结束时，虚无先判定，直接进入消耗堆。
KEYWORD_PRIORITIES = {
    KEYWORD_ETHEREAL: 100,
    KEYWORD_EXHAUST: 50,
    KEYWORD_RETAIN: 50,
    KEYWORD_CLEVER: 50,
    KEYWORD_INNATE: 50
}


def get_keyword_priority(keyword):
    return KEYWORD_PRIORITIES.get(keyword, 0)


def get_keyword_display_name(keyword):
    return KEYWORD_DISPLAY_NAMES.get(keyword, keyword)


def get_sorted_keywords(card):
    return sorted(
        getattr(card, "keywords", []),
        key=lambda keyword: get_keyword_priority(keyword),
        reverse=True
    )


def get_card_keyword_display_text(card):
    keywords = get_sorted_keywords(card)

    if not keywords:
        return ""

    return "词条：{}".format("，".join([
        get_keyword_display_name(keyword)
        for keyword in keywords
    ]))


def should_exhaust_after_play(card):
    # 消耗 打出后是否进入消耗堆。
    return card.has_keyword(KEYWORD_EXHAUST)


def should_exhaust_at_turn_end(card):
    # 虚无 回合结束时是否因虚无进入消耗堆。
    return card.has_keyword(KEYWORD_ETHEREAL)


def should_retain_at_turn_end(card):
    # 保留 回合结束时是否保留在手牌。
    return card.has_keyword(KEYWORD_RETAIN)


def should_play_when_discarded(card):
    # 奇巧 被丢弃时是否免费打出。
    return card.has_keyword(KEYWORD_CLEVER)

def should_start_in_hand(card):
    # 固有 战斗开始时进入起始手牌。
    return card.has_keyword(KEYWORD_INNATE)

'''
事已至此先占位符吧，想做某某zone下，抽到就中自动打出的词条：X之祈祷 pary_of_[element]
(画大饼.jpg)
'''