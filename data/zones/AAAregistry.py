# -*- coding: utf-8 -*-

ZONE_REGISTRY = {}


def register_zone(zone_id):
    def decorator(cls):
        ZONE_REGISTRY[zone_id] = cls
        return cls
    return decorator


def create_zone(zone_id):
    cls = ZONE_REGISTRY.get(zone_id)

    if cls is None:
        raise ValueError("未知 Zone：{}".format(zone_id))

    return cls()