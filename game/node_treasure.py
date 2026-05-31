# -*- coding: utf-8 -*-
# 宝箱节点：当前直接获得遗物

import random

from data.relic.AAAregistry import create_relic
from game.reward import get_available_relic_ids


def open_treasure(run_state, seed=None):
    rng = random.Random(seed)
    relic_ids = get_available_relic_ids(run_state)

    if not relic_ids:
        run_state.gold += 80
        return "宝箱里没有新的遗物。你获得 80 金币。当前金币：{}。".format(
            run_state.gold
        )

    relic = create_relic(rng.choice(relic_ids))
    run_state.relics.append(relic)

    logs = []
    logs.append("打开宝箱，获得遗物：【{}】。".format(relic.name))

    if hasattr(relic, "on_obtained"):
        logs.extend(relic.on_obtained(run_state))

    return "\n".join(logs)