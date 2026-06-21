# -*- coding: utf-8 -*-

from data.relic.lumine_relic import CrossEarringRelic
from data.relic.yoirine_relic import SaturatedFissureRelic
from data.relic.armored_warrior_relic import (BurningBloodRelic, CharonAshesRelic)
from data.relic.common_relics import JuzuBraceletRelic, TinyChestRelic

from data.relic.placeholder_stone_relic import PlaceholderStoneRelic
from data.relic.Homunculus import HomunculusPrototypeRelic

from data.relic.shop_relics import XPotionRelic

from data.relic.uncommon_relics import EtherMediumRelic, BottledLightningRelic, BottledFlameRelic, BottledTornadoRelic
from data.relic.rare_relics import CalipersRelic, KeystoneOfTheTombRelic
from data.relic.event_relics import GoldenIdolRelic, OddMushroomRelic, SsserpentHeadRelic, WarpedTongsRelic, SpiritPoopRelic

RELIC_REGISTRY = {
    "relic.homunculus_prototype":HomunculusPrototypeRelic,
    
    "relic.burning_blood":BurningBloodRelic,
    "relic.saturated_fissure": SaturatedFissureRelic,
    "relic.cross_earring": CrossEarringRelic,

    "relic.placeholder_stone": PlaceholderStoneRelic,
    "relic.charon_ashes":CharonAshesRelic,
    "relic.x_potion": XPotionRelic,
    "relic.ether_medium": EtherMediumRelic,
    "relic.juzu_bracelet": JuzuBraceletRelic,
    "relic.tiny_chest": TinyChestRelic,
    "relic.bottled_lightning": BottledLightningRelic,
    "relic.bottled_flame": BottledFlameRelic,
    "relic.bottled_tornado": BottledTornadoRelic,
    "relic.calipers": CalipersRelic,
    "relic.keystone_of_the_tomb": KeystoneOfTheTombRelic,
    
    "relic.golden_idol": GoldenIdolRelic,
    "relic.odd_mushroom": OddMushroomRelic,
    "relic.ssserpent_head": SsserpentHeadRelic,
    "relic.warped_tongs": WarpedTongsRelic,
    "relic.spirit_poop": SpiritPoopRelic,
}


def create_relic(relic_id):
    relic_class = RELIC_REGISTRY.get(relic_id)

    if relic_class is None:
        raise ValueError("未知遗物 ID：{}".format(relic_id))

    return relic_class()


def create_relics(relic_ids):
    return [create_relic(relic_id) for relic_id in relic_ids]


