# data/card/keyword_rules.py
# -*- coding: utf-8 -*-

from game.constants import (
    KEYWORD_EXHAUST,
    KEYWORD_ETHEREAL,
    KEYWORD_RETAIN,
    KEYWORD_CLEVER,
    KEYWORD_INNATE,
    KEYWORD_UNPLAYABLE,
)


KEYWORD_DISPLAY_NAMES = {
    KEYWORD_EXHAUST: "消耗",
    KEYWORD_ETHEREAL: "虚无",
    KEYWORD_RETAIN: "保留",
    KEYWORD_CLEVER: "奇巧",
    KEYWORD_INNATE: "固有",
    KEYWORD_UNPLAYABLE: "不能被打出"
}


# 数值越大，优先级越高。
# 虚无高于其他：回合结束时，虚无先判定，直接进入消耗堆。
KEYWORD_PRIORITIES = {
    KEYWORD_UNPLAYABLE: 200,
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

def normalize_card_play_permission_result(result):
    """
    统一解析未来遗物 / 能力 / 状态返回的可打出判断。

    支持：
    None：无意见，继续走默认规则
    True：允许打出
    False：禁止打出，使用默认提示
    (True, "提示")：允许打出，可附带提示
    (False, "提示")：禁止打出，并使用指定提示
    """
    if result is None:
        return None

    if isinstance(result, tuple):
        if len(result) >= 2:
            return bool(result[0]), str(result[1])
        if len(result) == 1:
            return bool(result[0]), ""

    if isinstance(result, bool):
        return result, ""

    return None

def iter_card_play_permission_sources(game_state):
    """
    预留接口：
    后续遗物、能力、场地、Zone 等都可以通过 can_play_card() 改写是否可打出。

    例如以后某个遗物允许打出状态牌，可以在遗物类里写：
    def can_play_card(self, game_state, card, play_reason):
        if card.card_type == "status":
            return True, "某遗物使状态牌可以被打出。"
        return None
    """
    if game_state is None:
        return

    player = getattr(game_state, "player", None)

    if player is not None:
        for relic in getattr(player, "relics", []):
            yield relic

        yield player

    active_zone = getattr(game_state, "active_zone", None)
    if active_zone is not None:
        yield active_zone

    for active_field in getattr(game_state, "active_fields", []):
        yield active_field

def check_card_play_conditions(game_state, card, play_reason="normal"):
    """
    检查卡牌自己的出牌条件。

    当前支持：
    - hand_all_cards_are_type：手牌中的所有牌必须都是指定类型
    """
    conditions = getattr(card, "play_conditions", [])

    if not conditions:
        return True, ""

    player = getattr(game_state, "player", None)
    if player is None:
        return True, ""

    for condition in conditions:
        op = condition.get("op")

        if op == "hand_all_cards_are_type":
            required_type = condition.get("card_type", "attack")

            for hand_card in player.hand:
                if getattr(hand_card, "card_type", "") != required_type:
                    return False, "【{}】不能被打出：手牌中存在非{}牌【{}】。".format(
                        card.name,
                        required_type,
                        hand_card.name
                    )

            continue

        return False, "【{}】存在未知出牌条件：{}。".format(
            card.name,
            op
        )

    return True, ""

def can_play_card(game_state, card, play_reason="normal"):
    """
    统一出牌许可判断。
    后续遗物、能力、状态牌可打出等机制都建议接入这里。
    """
    allowed, message = check_card_play_conditions(
        game_state=game_state,
        card=card,
        play_reason=play_reason
    )

    if not allowed:
        return allowed, message

    player = getattr(game_state, "player", None)

    if player is not None:
        from game.modifiers import get_status_value

        if (
            get_status_value(player, "entangled") > 0
            and getattr(card, "card_type", "") == "attack"
        ):
            return False, "你受到缠身影响，本回合不能打出攻击牌。"

    # 遗物 / 状态等可以覆盖“不能被打出”，例如蓝蜡烛、医药箱。
    for source in iter_card_play_permission_sources(game_state):
        checker = getattr(source, "can_play_card", None)
        if checker is None:
            continue
        result = normalize_card_play_permission_result(checker(game_state, card, play_reason))
        if result is None:
            continue
        allowed_by_source, source_message = result
        if allowed_by_source:
            return True, source_message
        return False, source_message or "【{}】不能被打出。".format(card.name)

    if card.has_keyword("unplayable"):
        return False, "【{}】不能被打出。".format(card.name)

    return True, ""



'''
事已至此先占位符吧，想做某某zone下，抽到就中自动打出的词条：X之祈祷 pary_of_[element]
(画大饼.jpg)
'''