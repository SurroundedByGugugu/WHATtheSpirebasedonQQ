# -*- coding: utf-8 -*-

from data.fields.base_field import FieldTemplate
from data.fields.AAAregistry import register_field


@register_field("field.test")
class TestField(FieldTemplate):
    def __init__(self, duration=1):
        FieldTemplate.__init__(
            self,
            field_id="field.test",
            name="测试场地",
            description="占位用 Field。",
            duration=duration
        )