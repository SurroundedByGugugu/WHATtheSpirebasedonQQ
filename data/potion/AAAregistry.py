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
    create_block_potion,
    create_blood_potion,
    create_energy_potion,
    create_explosive_potion,
    create_fear_potion,
    create_poison_potion,
    create_speed_potion,
    create_steroid_potion,
    create_weak_potion,
    create_swift_potion,
    create_colorless_potion,
)
from data.potion.uncommon_potions import (
    create_duplication_potion,
    create_liquid_memories,
    create_cunning_potion,
    create_elixir,
    create_ancient_potion,
    create_distilled_chaos,
    create_liquid_bronze,
    create_regen_potion,
    create_gamblers_brew,
    create_essence_of_steel,
)
from data.potion.rare_potions import (
    create_fairy_in_a_bottle,
    create_chaos_potion,
    create_smoke_bomb,
    create_cultist_potion,
    create_fruit_juice,
    create_ghost_in_a_jar,
    create_heart_of_iron,
    create_snecko_oil,
    create_saturated_calcium_carbonate_solution,
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
    
    "potion.block": create_block_potion,
    "potion.blood": create_blood_potion,
    "potion.energy": create_energy_potion,
    "potion.explosive": create_explosive_potion,
    "potion.fear": create_fear_potion,
    "potion.poison": create_poison_potion,
    "potion.speed": create_speed_potion,
    "potion.steroid": create_steroid_potion,
    "potion.weak": create_weak_potion,
    "potion.swift": create_swift_potion,
    "potion.colorless": create_colorless_potion,

    "potion.ancient": create_ancient_potion,
    "potion.distilled_chaos": create_distilled_chaos,
    "potion.liquid_bronze": create_liquid_bronze,
    "potion.regen": create_regen_potion,
    "potion.gamblers_brew": create_gamblers_brew,
    "potion.essence_of_steel": create_essence_of_steel,

    "potion.cultist": create_cultist_potion,
    "potion.fruit_juice": create_fruit_juice,
    "potion.ghost_in_a_jar": create_ghost_in_a_jar,
    "potion.heart_of_iron": create_heart_of_iron,
    "potion.snecko_oil": create_snecko_oil,
    "potion.saturated_calcium_carbonate_solution": create_saturated_calcium_carbonate_solution,
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
