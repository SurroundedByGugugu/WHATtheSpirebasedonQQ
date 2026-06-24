# -*- coding: utf-8 -*-
# 塔3通用事件池。

from game.node.node_event_0 import build_mind_bloom_event


def get_event_builders(run_state, seed=None, source_node_type="event"):
    return [build_mind_bloom_event]
