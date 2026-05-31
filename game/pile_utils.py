# -*- coding: utf-8 -*-
# 抽牌堆/弃牌堆/消耗堆/手牌的通用移动逻辑


import random


def get_pile(player, pile_name):
    return getattr(player, pile_name)


def move_card(card, source_pile, target_pile):
    if card in source_pile:
        source_pile.remove(card)
        target_pile.append(card)
        return True

    return False


def shuffle_discard_into_draw(player):
    if not player.discard_pile:
        return False

    player.draw_pile = player.discard_pile
    player.discard_pile = []
    random.shuffle(player.draw_pile)
    return True


def pile_text(player, pile_name, title):
    pile = getattr(player, pile_name)

    lines = []
    lines.append("=== {} ===".format(title))
    lines.append("数量：{}".format(len(pile)))

    if not pile:
        lines.append("空。")
        return "\n".join(lines)

    for index, card in enumerate(pile):
        lines.append("[{}] {}".format(index, card.summary_text()))

    return "\n".join(lines)


def draw_pile_text(player):
    return pile_text(player, "draw_pile", "抽牌堆")


def discard_pile_text(player):
    return pile_text(player, "discard_pile", "弃牌堆")


def exhaust_pile_text(player):
    return pile_text(player, "exhaust_pile", "消耗堆")