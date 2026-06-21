# -*- coding: utf-8 -*-
# 先古之民节点

import random
from dataclasses import dataclass, field
from typing import Any, List

from data.card.AAAregistry import create_card
from data.relic.AAAregistry import create_relic
from game.command_help import command_tip
from game.reward import CARD_REWARD_POOL, get_available_relic_ids


@dataclass
class AncientChoice:
    title: str
    effect_type: str
    amount: int = 0
    payload: Any = None


@dataclass
class AncientState:
    title: str = "？？？"
    description: str = "沉默的存在注视着你。"
    choices: List[AncientChoice] = field(default_factory=list)


def create_ancient_state(run_state, seed=None):
    node = run_state.get_current_node()
    node_id = getattr(node, "node_id", "")

    # Boss 后的下一层先古之民，第一版先做过渡。
    if node_id.startswith("act2") or "after_boss" in node_id:
        return AncientState(
            description="先古之民站在通往下一层的门前。",
            choices=[
                AncientChoice("继续前进。", "continue")
            ]
        )

    # 开局先古之民。
    return AncientState(
        description="‘僚机’所予之物。",
        choices=[
            AncientChoice("获得 100 金币。", "gain_gold", amount=100),
            AncientChoice("获得一张随机卡牌。", "gain_random_card"),
            AncientChoice("获得一件随机遗物。", "gain_random_relic"),
            AncientChoice("最大生命 +8，并恢复 8 点生命。", "gain_max_hp", amount=8),
        ]
    )


def format_ancient(run_state):
    state = run_state.pending_ancient

    if state is None:
        return "当前没有先古之民事件。"

    lines = []
    lines.append("=== {} ===".format(state.title))
    lines.append(state.description)
    lines.append("")

    for index, choice in enumerate(state.choices):
        lines.append("[{}] {}".format(index, choice.title))

    lines.append("")
    lines.append(command_tip("ancient", "使用 /card ancient 0 选择。"))

    return "\n".join(lines)


def choose_ancient_option(run_state, choice_index, seed=None):
    state = run_state.pending_ancient

    if state is None:
        return False, "当前没有先古之民事件。"

    if choice_index < 0 or choice_index >= len(state.choices):
        return False, "选项编号无效。"

    choice = state.choices[choice_index]
    rng = random.Random(seed)

    if choice.effect_type == "continue":
        return True, "继续前进。"

    if choice.effect_type == "gain_gold":
        run_state.gold += choice.amount
        return True, "获得 {} 金币。当前金币：{}。".format(
            choice.amount,
            run_state.gold
        )

    if choice.effect_type == "gain_random_card":
        card_id = rng.choice(CARD_REWARD_POOL)
        card = create_card(card_id)
        run_state.master_deck.append(card)
        return True, "获得卡牌：【{}】。".format(card.name)

    if choice.effect_type == "gain_random_relic":
        relic_ids = get_available_relic_ids(run_state)

        if not relic_ids:
            return True, "没有可获得的遗物。"

        relic = create_relic(rng.choice(relic_ids))
        run_state.relics.append(relic)

        logs = []
        logs.append("获得遗物：【{}】。".format(relic.name))

        if hasattr(relic, "on_obtained"):
            logs.extend(relic.on_obtained(run_state))

        return True, "\n".join(logs)

    if choice.effect_type == "gain_max_hp":
        run_state.max_hp += choice.amount
        run_state.hp = min(run_state.max_hp, run_state.hp + choice.amount)

        return True, "最大生命 +{}。当前 HP：{}/{}。".format(
            choice.amount,
            run_state.hp,
            run_state.max_hp
        )

    return False, "未知先古之民效果：{}。".format(choice.effect_type)