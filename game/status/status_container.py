# -*- coding: utf-8 -*-

from game.status.status_defs import get_status_def


class StatusContainer:
    """
    运行时状态容器。

    例如：
    {
        "strength": 2,
        "vulnerable": 1,
        "poison": 5,
    }
    """

    def __init__(self):
        self.values = {}
        self._decay_skip_once = {}

    def get(self, key):
        return int(self.values.get(key, 0))

    def set(self, key, value):
        value = int(value)

        status_def = get_status_def(key)

        if status_def is not None:
            if value < 0 and not status_def.can_be_negative:
                value = 0

            if value == 0 and status_def.remove_at_zero:
                self.values.pop(key, None)
                self._clear_decay_skip(key)
                return 0

        if value == 0:
            self.values.pop(key, None)
            self._clear_decay_skip(key)
            return 0

        self.values[key] = value
        return value

    def add(self, key, amount):
        old_value = self.get(key)
        new_value = old_value + int(amount)
        return self.set(key, new_value)

    def remove(self, key):
        self.values.pop(key, None)
        self._clear_decay_skip(key)

    def _clear_decay_skip(self, key):
        for timing in list(self._decay_skip_once.keys()):
            timing_skips = self._decay_skip_once.get(timing, {})
            timing_skips.pop(key, None)
            if not timing_skips:
                self._decay_skip_once.pop(timing, None)

    def skip_next_decay(self, key, timing):
        timing_skips = self._decay_skip_once.setdefault(timing, {})
        timing_skips[key] = 1

    def has(self, key):
        return self.get(key) != 0

    def all_active(self):
        return {
            key: value
            for key, value in self.values.items()
            if value != 0
        }

    def decay_by_timing(self, timing):
        """
        预留：按时机衰减状态。
        例如 turn_end 时，易伤/虚弱回合数 -1。
        """
        logs = []

        active = list(self.values.items())

        for key, value in active:
            status_def = get_status_def(key)

            if status_def is None:
                continue

            if status_def.decay_timing != timing:
                continue

            if status_def.decay_amount <= 0:
                continue

            timing_skips = self._decay_skip_once.get(timing, {})
            if timing_skips.get(key, 0) > 0:
                timing_skips[key] -= 1
                if timing_skips[key] <= 0:
                    timing_skips.pop(key, None)
                if not timing_skips:
                    self._decay_skip_once.pop(timing, None)
                continue

            new_value = self.add(key, -status_def.decay_amount)

            logs.append("{} 减少 {}，当前为 {}。".format(
                status_def.name,
                status_def.decay_amount,
                new_value
            ))

        return logs
