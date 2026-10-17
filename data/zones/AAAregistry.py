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
from data.zones import star_zone

# Elemental zones use a parameterized template rather than decorated classes.
# Register both forms so every zone can be created and browsed by its own ID.
from functools import partial
from data.zones.element_zones import ElementZone, ELEMENT_NAME_MAP

for element in ELEMENT_NAME_MAP:
    ZONE_REGISTRY['zone.element.' + element] = partial(ElementZone, element)
    ZONE_REGISTRY['zone.extreme_element.' + element] = partial(
        ElementZone, element, is_extreme=True, duration=3)
