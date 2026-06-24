# -*- coding: utf-8 -*-

from data.potion.test_potions import (
    create_test_strength_potion,
    create_test_fire_potion,
    create_test_dexterity_potion,
)
from data.potion.common_potions import (
    create_attack_potion,
    create_skill_potion,
    create_power_potion,
    create_forges_blessing,
)
from data.potion.uncommon_potions import (
    create_duplication_potion,
    create_liquid_memories,
    create_cunning_potion,
    create_elixir,
)
from data.potion.rare_potions import (
    create_fairy_in_a_bottle,
    create_chaos_potion,
    create_smoke_bomb,
)


POTION_REGISTRY = {
    "potion.test_strength": create_test_strength_potion,
    "potion.test_fire": create_test_fire_potion,
    "potion.test_dexterity": create_test_dexterity_potion,
    "potion.attack": create_attack_potion,
    "potion.skill": create_skill_potion,
    "potion.power": create_power_potion,
    "potion.forges_blessing": create_forges_blessing,
    "potion.duplication": create_duplication_potion,
    "potion.liquid_memories": create_liquid_memories,
    "potion.cunning": create_cunning_potion,
    "potion.elixir": create_elixir,
    "potion.fairy_in_a_bottle": create_fairy_in_a_bottle,
    "potion.chaos": create_chaos_potion,
    "potion.smoke_bomb": create_smoke_bomb,
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
