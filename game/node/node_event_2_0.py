# -*- coding: utf-8 -*-
# 塔2通用事件池。

from game.node.node_event_0 import (
    build_cursed_tome_event,
    build_face_trader_event,
    build_augmenter_event,
)


def get_event_builders(run_state, seed=None, source_node_type="event"):
    return [
        build_cursed_tome_event,
        build_face_trader_event,
        build_augmenter_event,
    ]
