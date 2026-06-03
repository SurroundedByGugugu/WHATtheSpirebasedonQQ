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


class ElementZone(ZoneTemplate):
    """
    通用属性 Zone。

    普通 Zone：持续到战斗结束或被覆盖。
    极 Zone：持续 3 回合，不可覆盖。
    """

    def __init__(self, element, is_extreme=False, duration=0):
        element_name = get_element_display_name(element)

        if is_extreme:
            name = "极{}Zone".format(element_name)
            description = "场地上充满了{}元素。同属性伤害 ×1.3，持续 {} 回合，不可覆盖。".format(
                element_name,
                duration
            )
            multiplier = 1.3
        else:
            name = "{}Zone".format(element_name)
            description = "场地上弥漫着{}元素。同属性伤害 ×1.1。".format(element_name)
            multiplier = 1.1

        ZoneTemplate.__init__(
            self,
            zone_id="zone.element.{}".format(element),
            name=name,
            description=description,
            element=element,
            is_extreme=is_extreme,
            duration=duration,
            damage_multiplier=multiplier
        )

    def prompt_text(self):
        element_name = get_element_display_name(self.element)

        if self.is_extreme:
            return "场地上充满了{}元素。".format(element_name)

        return "场地上弥漫着{}元素。".format(element_name)