# -*- coding: utf-8 -*-
# 火堆节点：休息回血、锻造升级

from dataclasses import dataclass

from data.card.upgrade_rules import has_upgrade, upgrade_card


REST_HEAL_RATIO = 0.30


@dataclass
class RestState:
    used: bool = False
    source_node_type: str = "rest"


def create_rest_state(source_node_type="rest"):
    return RestState(
        source_node_type=source_node_type
    )


def format_rest(run_state):
    heal_amount = int(run_state.max_hp * REST_HEAL_RATIO)
    if heal_amount < 1:
        heal_amount = 1
    lines = []
    lines.append("=== 火堆 ===")
    lines.append("HP：{}/{}".format(run_state.hp, run_state.max_hp))
    lines.append("")
    lines.append("[0] 休息：恢复最大生命值 {}% ({}) 的生命。".format(int(REST_HEAL_RATIO*100),heal_amount))
    lines.append("[1] 锻造：升级一张可升级的牌。")
    lines.append("")
    lines.append("使用 /card rest 0 休息。")
    lines.append("使用 /card rest 1 查看可升级牌。")
    return "\n".join(lines)


def rest_heal(run_state):
    rest_state = run_state.pending_rest

    if rest_state is None:
        return False, "当前不在火堆。"

    if rest_state.used:
        return False, "本次火堆已经使用过。"

    heal_amount = int(run_state.max_hp * REST_HEAL_RATIO)

    if heal_amount < 1:
        heal_amount = 1

    old_hp = run_state.hp
    run_state.hp = min(run_state.max_hp, run_state.hp + heal_amount)
    rest_state.used = True

    return True, "你在火堆旁休息。HP：{} -> {}。".format(
        old_hp,
        run_state.hp
    )


def format_smith_choices(run_state):
    rest_state = run_state.pending_rest

    if rest_state is None:
        return "当前不在火堆。"

    if rest_state.used:
        return "本次火堆已经使用过。"

    upgradable = get_upgradable_cards(run_state)

    lines = []
    lines.append("=== 锻造 ===")

    if not upgradable:
        lines.append("当前没有可升级的牌。")
        return "\n".join(lines)

    for display_index, item in enumerate(upgradable):
        deck_index, card = item
        upgraded_card = upgrade_card(card)

        lines.append("[{}] 牌组编号 {}：【{}】 -> 【{}】".format(
            display_index,
            deck_index,
            card.name,
            upgraded_card.name
        ))
        lines.append("    当前：{}".format(card.description))
        lines.append("    升级：{}".format(upgraded_card.description))

    lines.append("")
    lines.append("使用 /card smith 0 升级对应牌。")

    return "\n".join(lines)


def smith_card(run_state, choice_index):
    rest_state = run_state.pending_rest

    if rest_state is None:
        return False, "当前不在火堆。"

    if rest_state.used:
        return False, "本次火堆已经使用过。"

    upgradable = get_upgradable_cards(run_state)

    if not upgradable:
        return False, "当前没有可升级的牌。"

    if choice_index < 0 or choice_index >= len(upgradable):
        return False, "锻造编号无效。"

    deck_index, card = upgradable[choice_index]
    upgraded_card = upgrade_card(card)

    run_state.master_deck[deck_index] = upgraded_card
    rest_state.used = True

    return True, "锻造完成：【{}】升级为【{}】。".format(
        card.name,
        upgraded_card.name
    )


def get_upgradable_cards(run_state):
    result = []

    for index, card in enumerate(getattr(run_state, "master_deck", [])):
        if getattr(card, "upgraded", False):
            continue

        if has_upgrade(card):
            result.append((index, card))

    return result