

from data.potion.base_potion import PotionTemplate


def create_fairy_in_a_bottle():
    return PotionTemplate(
        potion_id="potion.fairy_in_a_bottle",
        name="瓶中精灵",
        description="当你要被杀死时，免死并回复到最大生命值的 30%，丢弃这瓶药水。",
        target="self",
        quantity="rare",
        effects=[],
    )
