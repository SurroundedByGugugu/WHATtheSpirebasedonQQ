# -*- coding: utf-8 -*-
# 普通事件节点 / mystery 随机出的事件

import random
from dataclasses import dataclass, field
from typing import Any, List

from data.card.AAAregistry import create_card
from game.reward import CARD_REWARD_POOL


@dataclass
class EventChoice:
    title: str
    effect_type: str
    amount: int = 0
    payload: Any = None


@dataclass
class EventState:
    title: str
    description: str
    choices: List[EventChoice] = field(default_factory=list)


EVENT_POOL = [
    "event.free_gold",
    "event.heal_or_gold",
    "event.card_or_leave",
]


def create_event_state(run_state, seed=None, source_node_type="event"):
    rng = random.Random(seed)
    event_id = rng.choice(EVENT_POOL)

    if event_id == "event.free_gold":
        return EventState(
            title="无主钱袋",
            description="你在地上看见一个无人看管的钱袋。",
            choices=[
                EventChoice("拿走。获得 30 金币。", "gain_gold", amount=30),
                EventChoice("不碰奇怪的钱。", "nothing"),
            ]
        )

    if event_id == "event.heal_or_gold":
        return EventState(
            title="温热的裂缝",
            description="墙上的裂缝向外渗出温热的光。",
            choices=[
                EventChoice("靠近休息。恢复 12 点生命。", "heal", amount=12),
                EventChoice(
                    "掰下一块发光碎片。获得 20 金币，失去 5 HP。",
                    "gold_and_lose_hp",
                    amount=20,
                    payload={
                        "lose_hp": 5
                    }
                ),
            ]
        )

    return EventState(
        title="散落的结晶",
        description="几块结晶散落在灰尘里。表面有轻微的划痕。谁的记忆存档？",
        choices=[
            EventChoice("捡起结晶块，获得一张随机卡牌。", "gain_random_card"),
            EventChoice("离开。", "nothing"),
        ]
    )


def format_event(run_state):
    state = run_state.pending_event

    if state is None:
        return "当前没有事件。"

    lines = []
    lines.append("=== 事件：{} ===".format(state.title))
    lines.append(state.description)
    lines.append("")

    for index, choice in enumerate(state.choices):
        lines.append("[{}] {}".format(index, choice.title))

    lines.append("")
    lines.append("使用 /card event 0 选择。")

    return "\n".join(lines)


def choose_event_option(run_state, choice_index, seed=None):
    state = run_state.pending_event

    if state is None:
        return False, "当前没有事件。"

    if choice_index < 0 or choice_index >= len(state.choices):
        return False, "选项编号无效。"

    choice = state.choices[choice_index]
    rng = random.Random(seed)

    if choice.effect_type == "nothing":
        return True, "你离开了这里。"

    if choice.effect_type == "gain_gold":
        run_state.gold += choice.amount
        return True, "获得 {} 金币。当前金币：{}。".format(
            choice.amount,
            run_state.gold
        )

    if choice.effect_type == "heal":
        old_hp = run_state.hp
        run_state.hp = min(run_state.max_hp, run_state.hp + choice.amount)
        return True, "恢复生命：{} -> {}。".format(
            old_hp,
            run_state.hp
        )

    if choice.effect_type == "gold_and_lose_hp":
        lose_hp = choice.payload.get("lose_hp", 0)

        run_state.gold += choice.amount

        old_hp = run_state.hp
        run_state.hp = max(1, run_state.hp - lose_hp)

        return True, "获得 {} 金币，HP：{} -> {}。当前金币：{}。".format(
            choice.amount,
            old_hp,
            run_state.hp,
            run_state.gold
        )

    if choice.effect_type == "gain_random_card":
        card = create_card(rng.choice(CARD_REWARD_POOL))
        run_state.master_deck.append(card)
        return True, "获得卡牌：【{}】。".format(card.name)

    return False, "未知事件效果：{}。".format(choice.effect_type)