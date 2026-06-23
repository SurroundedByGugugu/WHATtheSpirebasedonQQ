# -*- coding: utf-8 -*-
# 火堆节点：休息回血、锻造升级，以及若干火堆遗物选项。

from dataclasses import dataclass, field

from data.card.upgrade_rules import has_upgrade, upgrade_card
from game.command_help import command_tip
from game.relic_logic.bottle_utils import copy_bottled_flags
from game.relic_logic.run_relic_utils import has_run_relic


REST_HEAL_RATIO = 0.30


@dataclass
class RestState:
    used: bool = False
    source_node_type: str = "rest"
    used_actions: set = field(default_factory=set)


def create_rest_state(source_node_type="rest"):
    return RestState(source_node_type=source_node_type)


def has_miniature_tent(run_state):
    return has_run_relic(run_state, "relic.miniature_tent")


def get_girya_relic(run_state):
    for relic in getattr(run_state, "relics", []) or []:
        if getattr(relic, "relic_id", "") == "relic.girya":
            return relic
    return None


def is_action_available(run_state, action):
    rest_state = run_state.pending_rest
    if rest_state is None:
        return False
    if has_miniature_tent(run_state):
        return action not in getattr(rest_state, "used_actions", set())
    return not rest_state.used


def consume_rest_action(run_state, action):
    rest_state = run_state.pending_rest
    if rest_state is None:
        return
    if has_miniature_tent(run_state):
        rest_state.used_actions.add(action)
        return
    rest_state.used = True


def get_rest_options(run_state):
    options = []
    options.append(("rest", "休息"))
    options.append(("smith", "锻造"))
    girya = get_girya_relic(run_state)
    if girya is not None and int(getattr(girya, "lifts", 0)) < 3:
        options.append(("girya", "壶铃"))
    if has_run_relic(run_state, "relic.peace_pipe"):
        options.append(("pipe", "宁静烟斗"))
    if has_run_relic(run_state, "relic.shovel"):
        options.append(("shovel", "铲子"))
    if has_miniature_tent(run_state):
        options.append(("leave", "离开"))
    return options


def format_rest(run_state):
    heal_amount = int(run_state.max_hp * REST_HEAL_RATIO)
    if heal_amount < 1:
        heal_amount = 1
    if has_run_relic(run_state, "relic.regal_pillow"):
        heal_amount += 15

    lines = []
    lines.append("=== 火堆 ===")
    lines.append("HP：{}/{}".format(run_state.hp, run_state.max_hp))
    if has_miniature_tent(run_state):
        used = getattr(run_state.pending_rest, "used_actions", set()) if run_state.pending_rest else set()
        lines.append("【微型帐篷】生效：可选择多个火堆选项，完成后使用 leave 离开。已使用：{}".format("，".join(sorted(used)) if used else "无"))
    lines.append("")

    for index, (action, name) in enumerate(get_rest_options(run_state)):
        suffix = ""
        if action != "leave" and not is_action_available(run_state, action):
            suffix = "（已使用）"
        if action == "rest":
            lines.append("[{}] 休息：恢复最大生命值 {}% ({}) 的生命。{}".format(index, int(REST_HEAL_RATIO*100), heal_amount, suffix))
        elif action == "smith":
            lines.append("[{}] 锻造：升级一张可升级的牌。{}".format(index, suffix))
        elif action == "girya":
            girya = get_girya_relic(run_state)
            lines.append("[{}] 壶铃：锻炼，后续战斗开始时额外获得 1 点力量。（{}/3）{}".format(index, int(getattr(girya, "lifts", 0)), suffix))
        elif action == "pipe":
            lines.append("[{}] 宁静烟斗：移除一张牌。{}".format(index, suffix))
        elif action == "shovel":
            lines.append("[{}] 铲子：挖掘一件遗物。{}".format(index, suffix))
        elif action == "leave":
            lines.append("[{}] 离开火堆。".format(index))

    lines.append("")
    lines.append(command_tip("rest", "使用 /card rest 0 选择火堆选项。"))
    lines.append(command_tip("smith", "锻造查看后，使用 /card smith 0 升级对应牌。"))
    lines.append(command_tip("rest_remove", "宁静烟斗查看后，使用 /card rest_remove 0 移除对应牌。"))
    if has_miniature_tent(run_state):
        lines.append(command_tip("leave", "使用 /card leave 离开火堆。"))
    return "\n".join(lines)


def rest_heal(run_state):
    rest_state = run_state.pending_rest
    if rest_state is None:
        return False, "当前不在火堆。"
    if not is_action_available(run_state, "rest"):
        return False, "本次火堆不能再次休息。"

    heal_amount = int(run_state.max_hp * REST_HEAL_RATIO)
    if heal_amount < 1:
        heal_amount = 1

    extra_text = ""
    if has_run_relic(run_state, "relic.regal_pillow"):
        heal_amount += 15
        extra_text = "【皇家枕头】额外回复 15 点生命。"

    old_hp = run_state.hp
    run_state.hp = min(run_state.max_hp, run_state.hp + heal_amount)
    consume_rest_action(run_state, "rest")

    if extra_text:
        return True, "你在火堆旁休息。{} HP：{} -> {}。".format(extra_text, old_hp, run_state.hp)
    return True, "你在火堆旁休息。HP：{} -> {}。".format(old_hp, run_state.hp)


def get_upgradable_cards(run_state):
    result = []
    for index, card in enumerate(getattr(run_state, "master_deck", [])):
        if getattr(card, "upgraded", False) and not getattr(card, "multi_upgrade", False):
            continue
        if has_upgrade(card):
            result.append((index, card))
    return result


def format_smith_choices(run_state):
    if run_state.pending_rest is None:
        return "当前不在火堆。"
    if not is_action_available(run_state, "smith"):
        return "本次火堆不能再次锻造。"
    upgradable = get_upgradable_cards(run_state)
    lines = ["=== 锻造 ==="]
    if not upgradable:
        lines.append("当前没有可升级的牌。")
        return "\n".join(lines)
    for display_index, item in enumerate(upgradable):
        deck_index, card = item
        upgraded_card = upgrade_card(card)
        lines.append("[{}] 牌组编号 {}：【{}】 -> 【{}】".format(display_index, deck_index, card.name, upgraded_card.name))
        lines.append("    当前：{}".format(card.description))
        lines.append("    升级：{}".format(upgraded_card.description))
    lines.append("")
    lines.append(command_tip("smith", "使用 /card smith 0 升级对应牌。"))
    return "\n".join(lines)


def smith_card(run_state, choice_index):
    if run_state.pending_rest is None:
        return False, "当前不在火堆。"
    if not is_action_available(run_state, "smith"):
        return False, "本次火堆不能再次锻造。"
    upgradable = get_upgradable_cards(run_state)
    if not upgradable:
        return False, "当前没有可升级的牌。"
    if choice_index < 0 or choice_index >= len(upgradable):
        return False, "锻造编号无效。"
    deck_index, card = upgradable[choice_index]
    upgraded_card = upgrade_card(card)
    upgraded_card = copy_bottled_flags(card, upgraded_card)
    run_state.master_deck[deck_index] = upgraded_card
    consume_rest_action(run_state, "smith")
    return True, "锻造完成：【{}】升级为【{}】。".format(card.name, upgraded_card.name)


def lift_girya(run_state):
    if run_state.pending_rest is None:
        return False, "当前不在火堆。"
    if not is_action_available(run_state, "girya"):
        return False, "本次火堆不能再次锻炼。"
    girya = get_girya_relic(run_state)
    if girya is None:
        return False, "你没有【壶铃】。"
    if int(getattr(girya, "lifts", 0)) >= 3:
        return False, "【壶铃】已经锻炼到上限。"
    girya.lifts = int(getattr(girya, "lifts", 0)) + 1
    consume_rest_action(run_state, "girya")
    return True, "【壶铃】锻炼完成：后续战斗开始时额外力量 +1。（{}/3）".format(girya.lifts)


def dig_relic(run_state, seed=None):
    if run_state.pending_rest is None:
        return False, "当前不在火堆。"
    if not is_action_available(run_state, "shovel"):
        return False, "本次火堆不能再次挖掘。"
    if not has_run_relic(run_state, "relic.shovel"):
        return False, "你没有【铲子】。"
    import random
    from game.reward import get_available_relic_ids
    from data.relic.AAAregistry import create_relic
    rng = random.Random(seed)
    available = get_available_relic_ids(run_state)
    if not available:
        return False, "没有可挖掘的遗物。"
    relic = create_relic(rng.choice(available))
    run_state.relics.append(relic)
    consume_rest_action(run_state, "shovel")
    logs = ["【铲子】挖掘：获得遗物【{}】。".format(relic.name)]
    if hasattr(relic, "on_obtained"):
        logs.extend(relic.on_obtained(run_state))
    return True, "\n".join(logs)


def format_rest_remove_choices(run_state):
    if run_state.pending_rest is None:
        return "当前不在火堆。"
    if not is_action_available(run_state, "pipe"):
        return "本次火堆不能再次使用宁静烟斗。"
    if not has_run_relic(run_state, "relic.peace_pipe"):
        return "你没有【宁静烟斗】。"
    lines = ["=== 宁静烟斗：移除卡牌 ==="]
    deck = getattr(run_state, "master_deck", []) or []
    if not deck:
        lines.append("牌组为空。")
        return "\n".join(lines)
    for index, card in enumerate(deck):
        lines.append("[{}] {}".format(index, card.summary_text()))
    lines.append("")
    lines.append(command_tip("rest_remove", "使用 /card rest_remove 0 移除对应牌。"))
    return "\n".join(lines)


def rest_remove_card(run_state, card_index):
    if run_state.pending_rest is None:
        return False, "当前不在火堆。"
    if not is_action_available(run_state, "pipe"):
        return False, "本次火堆不能再次使用宁静烟斗。"
    if not has_run_relic(run_state, "relic.peace_pipe"):
        return False, "你没有【宁静烟斗】。"
    from game.deck_utils import remove_card_from_master_deck
    removed_card, remove_logs = remove_card_from_master_deck(run_state, card_index, reason="peace_pipe")
    if removed_card is None:
        return False, "\n".join(remove_logs)
    consume_rest_action(run_state, "pipe")
    return True, "【宁静烟斗】移除卡牌。\n" + "\n".join(remove_logs)
