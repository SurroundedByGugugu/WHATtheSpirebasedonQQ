# -*- coding: utf-8 -*-

from data.zones.base_zone import ZoneTemplate
from data.zones.AAAregistry import register_zone


@register_zone("zone.test")
class TestZone(ZoneTemplate):
    def __init__(self):
        ZoneTemplate.__init__(
            self,
            zone_id="zone.test",
            name="测试区域",
            description="占位用 Zone。"
        )