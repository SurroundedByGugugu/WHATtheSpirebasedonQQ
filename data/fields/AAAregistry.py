# -*- coding: utf-8 -*-

FIELD_REGISTRY = {}


def register_field(field_id):
    def decorator(cls):
        FIELD_REGISTRY[field_id] = cls
        return cls
    return decorator


def create_field(field_id, duration=1):
    cls = FIELD_REGISTRY.get(field_id)

    if cls is None:
        raise ValueError("未知 Field：{}".format(field_id))

    return cls(duration=duration)