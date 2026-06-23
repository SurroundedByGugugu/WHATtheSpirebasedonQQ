# -*- coding: utf-8 -*-

from data.relic.lumine_relic import CrossEarringRelic
from data.relic.yoirine_relic import SaturatedFissureRelic
from data.relic.armored_warrior_relic import (BurningBloodRelic, CharonAshesRelic)
from data.relic.common_relics import (
    JuzuBraceletRelic, TinyChestRelic,
    BagOfMarblesRelic, BloodVialRelic, BronzeScalesRelic, CentennialPuzzleRelic,
    TheBootRelic, DreamCatcherRelic, HappyFlowerRelic, LanternRelic,
    OddlySmoothStoneRelic, VajraRelic, OmamoriRelic, OrichalcumRelic,
    RedSkullRelic, RegalPillowRelic, SmilingMaskRelic, SnakeSkullRelic,
    StrawberryRelic, PotionBeltRelic, MealTicketRelic, WhetstoneRelic,
    MawBankRelic, NunchakuRelic, PreservedInsectRelic, CeramicFishRelic,
    AkabekoRelic, PenNibRelic, ToyOrnithopterRelic, BagOfPreparationRelic,
    AncientTeaSetRelic, ArtOfWarRelic, AnchorRelic,
)

from data.relic.placeholder_stone_relic import PlaceholderStoneRelic
from data.relic.Homunculus import HomunculusPrototypeRelic

from data.relic.shop_relics import XPotionRelic, TwistedFunnelRelic, MembershipCardRelic, DragonFruitRelic, MedicalKitRelic

from data.relic.uncommon_relics import (EtherMediumRelic, BottledLightningRelic, BottledFlameRelic, BottledTornadoRelic, PearRelic, WarPaintRelic, TheCourierRelic, HornCleatRelic, BlueCandleRelic, EternalFeatherRelic, FrozenEggRelic, ToxicEggRelic, MoltenEggRelic, DarkstonePeriaptRelic, GremlinHornRelic, KunaiRelic, ShurikenRelic, OrnamentalFanRelic, LetterOpenerRelic, MatryoshkaRelic, MeatOnTheBoneRelic, MercuryHourglassRelic, MummifiedHandRelic, NinjaScrollRelic, PantographRelic, PaperCraneRelic, PaperFrogRelic, QuestionCardRelic, SelfFormingClayRelic, SingingBowlRelic, WhiteBeastStatueRelic, InkBottleRelic, StrikeDummyRelic, SundialRelic)
from data.relic.rare_relics import (CalipersRelic, KeystoneOfTheTombRelic, MangoRelic, CaptainsWheelRelic, IceCreamRelic, IncenseBurnerRelic, StoneCalendarRelic, PocketwatchRelic, FossilizedHelixRelic, CloakClaspRelic, TungstenRodRelic, GamblingChipRelic, BirdFacedUrnRelic, ChampionBeltRelic, DuVuDollRelic, DeadBranchRelic, GingerRelic, TurnipRelic, CabbageRelic, GiryaRelic, PeacePipeRelic, ShovelRelic, MiniatureTentRelic, LizardTailRelic, MagicFlowerRelic, OldCoinRelic, PrayerWheelRelic, TheSpecimenRelic, ThreadAndNeedleRelic, TingshaRelic, ToriiRelic, ToughBandagesRelic, UnceasingTopRelic)
from data.relic.event_relics import GoldenIdolRelic, OddMushroomRelic, SsserpentHeadRelic, WarpedTongsRelic, SpiritPoopRelic, RedMaskRelic

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

    "relic.bag_of_marbles": BagOfMarblesRelic,
    "relic.blood_vial": BloodVialRelic,
    "relic.bronze_scales": BronzeScalesRelic,
    "relic.centennial_puzzle": CentennialPuzzleRelic,
    "relic.the_boot": TheBootRelic,
    "relic.dream_catcher": DreamCatcherRelic,
    "relic.happy_flower": HappyFlowerRelic,
    "relic.lantern": LanternRelic,
    "relic.oddly_smooth_stone": OddlySmoothStoneRelic,
    "relic.vajra": VajraRelic,
    "relic.omamori": OmamoriRelic,
    "relic.orichalcum": OrichalcumRelic,
    "relic.red_skull": RedSkullRelic,
    "relic.regal_pillow": RegalPillowRelic,
    "relic.smiling_mask": SmilingMaskRelic,
    "relic.snake_skull": SnakeSkullRelic,
    "relic.strawberry": StrawberryRelic,
    "relic.potion_belt": PotionBeltRelic,
    "relic.meal_ticket": MealTicketRelic,
    "relic.whetstone": WhetstoneRelic,
    "relic.maw_bank": MawBankRelic,
    "relic.nunchaku": NunchakuRelic,
    "relic.preserved_insect": PreservedInsectRelic,
    "relic.ceramic_fish": CeramicFishRelic,
    "relic.akabeko": AkabekoRelic,
    "relic.pen_nib": PenNibRelic,
    "relic.toy_ornithopter": ToyOrnithopterRelic,
    "relic.bag_of_preparation": BagOfPreparationRelic,
    "relic.ancient_tea_set": AncientTeaSetRelic,
    "relic.art_of_war": ArtOfWarRelic,
    "relic.anchor": AnchorRelic,

    "relic.pear": PearRelic,
    "relic.war_paint": WarPaintRelic,
    "relic.the_courier": TheCourierRelic,
    "relic.horn_cleat": HornCleatRelic,

    "relic.blue_candle": BlueCandleRelic,
    "relic.eternal_feather": EternalFeatherRelic,
    "relic.frozen_egg": FrozenEggRelic,
    "relic.toxic_egg": ToxicEggRelic,
    "relic.molten_egg": MoltenEggRelic,
    "relic.darkstone_periapt": DarkstonePeriaptRelic,
    "relic.gremlin_horn": GremlinHornRelic,
    "relic.kunai": KunaiRelic,
    "relic.shuriken": ShurikenRelic,
    "relic.ornamental_fan": OrnamentalFanRelic,
    "relic.letter_opener": LetterOpenerRelic,
    "relic.matryoshka": MatryoshkaRelic,
    "relic.meat_on_the_bone": MeatOnTheBoneRelic,
    "relic.mercury_hourglass": MercuryHourglassRelic,
    "relic.mummified_hand": MummifiedHandRelic,
    "relic.ninja_scroll": NinjaScrollRelic,
    "relic.pantograph": PantographRelic,
    "relic.paper_crane": PaperCraneRelic,
    "relic.paper_frog": PaperFrogRelic,
    "relic.question_card": QuestionCardRelic,
    "relic.self_forming_clay": SelfFormingClayRelic,
    "relic.singing_bowl": SingingBowlRelic,
    "relic.white_beast_statue": WhiteBeastStatueRelic,
    "relic.ink_bottle": InkBottleRelic,
    "relic.strike_dummy": StrikeDummyRelic,
    "relic.sundial": SundialRelic,
    "relic.medical_kit": MedicalKitRelic,
    "relic.ice_cream": IceCreamRelic,
    "relic.mango": MangoRelic,
    "relic.captains_wheel": CaptainsWheelRelic,
    "relic.incense_burner": IncenseBurnerRelic,
    "relic.stone_calendar": StoneCalendarRelic,
    "relic.pocketwatch": PocketwatchRelic,
    "relic.fossilized_helix": FossilizedHelixRelic,
    "relic.cloak_clasp": CloakClaspRelic,
    "relic.tungsten_rod": TungstenRodRelic,
    "relic.gambling_chip": GamblingChipRelic,
    "relic.bird_faced_urn": BirdFacedUrnRelic,
    "relic.champion_belt": ChampionBeltRelic,
    "relic.du_vu_doll": DuVuDollRelic,
    "relic.dead_branch": DeadBranchRelic,
    "relic.ginger": GingerRelic,
    "relic.turnip": TurnipRelic,
    "relic.cabbage": CabbageRelic,
    "relic.girya": GiryaRelic,
    "relic.peace_pipe": PeacePipeRelic,
    "relic.shovel": ShovelRelic,
    "relic.miniature_tent": MiniatureTentRelic,
    "relic.lizard_tail": LizardTailRelic,
    "relic.magic_flower": MagicFlowerRelic,
    "relic.old_coin": OldCoinRelic,
    "relic.prayer_wheel": PrayerWheelRelic,
    "relic.the_specimen": TheSpecimenRelic,
    "relic.thread_and_needle": ThreadAndNeedleRelic,
    "relic.tingsha": TingshaRelic,
    "relic.torii": ToriiRelic,
    "relic.tough_bandages": ToughBandagesRelic,
    "relic.unceasing_top": UnceasingTopRelic,

    "relic.red_mask": RedMaskRelic,
    "relic.twisted_funnel": TwistedFunnelRelic,
    "relic.membership_card": MembershipCardRelic,
    "relic.dragon_fruit": DragonFruitRelic,
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


