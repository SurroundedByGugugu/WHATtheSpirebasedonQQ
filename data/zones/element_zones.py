# -*- coding: utf-8 -*-

from data.zones.base_zone import ZoneTemplate


ELEMENT_NAME_MAP = {
    "fire": "火",
    "earth": "地",
    "wind": "风",
    "water": "水",
    "thunder": "雷",
    "shade": "阴",
    "crystal": "晶",
}


def get_element_display_name(element):
    return ELEMENT_NAME_MAP.get(element, element)


ZONE_ABILITY_TEXT = {
    "crystal": ("重放 +1。", "重放 +2。"),
    "shade": ("效果 ×1.5，来源失去当前生命 5%。", "效果 ×2，来源失去当前生命 5%。"),
    "fire": ("攻击牌对目标附加 1 层烧伤。", "攻击牌对目标附加 2 层烧伤。"),
    "earth": ("获得格挡时，获得 0.5 倍临时荆棘。", "获得格挡时，获得 0.8 倍临时荆棘。"),
    "thunder": ("单体/随机敌人目标变为全体。", "单体/随机敌人目标变为全体，重放 +1。"),
    "water": ("打出水 tag 牌时获得 2 层再生。", "打出水 tag 牌时获得 3 层再生。"),
    "wind": ("攻击对格挡效果 ×1.3。", "攻击对格挡效果 ×1.5。"),
}


def get_zone_ability_text(element, is_extreme=False):
    base_text = "同属性牌造成的伤害和获得的格挡 ×{}。".format(
        "1.3" if is_extreme else "1.1"
    )

    pair = ZONE_ABILITY_TEXT.get(element)
    if pair is None:
        return base_text + "暂未定义特殊效果。"

    return base_text + (pair[1] if is_extreme else pair[0])


class ElementZone(ZoneTemplate):
    """
    通用属性 Zone。

    普通 Zone：持续到战斗结束或被覆盖。
    极 Zone：持续 3 回合，不可覆盖。
    """

    def __init__(self, element, is_extreme=False, duration=0):
        element_name = get_element_display_name(element)

        ability_text = get_zone_ability_text(element, is_extreme)

        if is_extreme:
            name = "极{}Zone".format(element_name)
            description = "场地上充满了{}元素。{}持续 {} 回合，不可覆盖。".format(
                element_name,
                ability_text,
                duration
            )
            multiplier = 1.3
        else:
            name = "{}Zone".format(element_name)
            description = "场地上弥漫着{}元素。{}".format(element_name, ability_text)
            multiplier = 1.1

        ZoneTemplate.__init__(
            self,
            zone_id="zone.element.{}".format(element),
            name=name,
            description=description,
            element=element,
            is_extreme=is_extreme,
            duration=duration,
            damage_multiplier=multiplier,
            base_amount_multiplier=multiplier
        )
        self.ability_text = ability_text

    def prompt_text(self):
        element_name = get_element_display_name(self.element)

        if self.is_extreme:
            return "场地上充满了{}元素。".format(element_name)

        return "场地上弥漫着{}元素。".format(element_name)