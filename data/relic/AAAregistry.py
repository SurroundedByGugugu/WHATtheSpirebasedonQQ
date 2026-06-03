# -*- coding: utf-8 -*-

from data.relic.yoirine_relic import SaturatedFissureRelic
from data.relic.armored_warrior_relic import BurningBloodRelic
from data.relic.placeholder_stone_relic import PlaceholderStoneRelic
from data.relic.Homunculus import HomunculusPrototypeRelic
from data.relic.shop_relics import XPotionRelic

RELIC_REGISTRY = {
    "relic.placeholder_stone": PlaceholderStoneRelic,
    "relic.burning_blood":BurningBloodRelic,
    "relic.homunculus_prototype":HomunculusPrototypeRelic,
    "relic.x_potion": XPotionRelic,
    "relic.saturated_fissure": SaturatedFissureRelic,
}


def create_relic(relic_id):
    relic_class = RELIC_REGISTRY.get(relic_id)

    if relic_class is None:
        raise ValueError("未知遗物 ID：{}".format(relic_id))

    return relic_class()


def create_relics(relic_ids):
    return [create_relic(relic_id) for relic_id in relic_ids]


