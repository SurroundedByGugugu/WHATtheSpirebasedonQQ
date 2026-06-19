# -*- coding: utf-8 -*-

from data.potion.test_potions import (
    create_test_strength_potion,
    create_test_fire_potion,
    create_test_dexterity_potion,
)
from data.potion.uncommon_potions import create_duplication_potion


POTION_REGISTRY = {
    "potion.test_strength": create_test_strength_potion,
    "potion.test_fire": create_test_fire_potion,
    "potion.test_dexterity": create_test_dexterity_potion,
    "potion.duplication": create_duplication_potion,
}


def create_potion(potion_id):
    create_func = POTION_REGISTRY.get(potion_id)

    if create_func is None:
        raise ValueError("未知药水 ID：{}".format(potion_id))

    return create_func()


def create_potions(potion_ids):
    return [
        create_potion(potion_id)
        for potion_id in potion_ids
    ]