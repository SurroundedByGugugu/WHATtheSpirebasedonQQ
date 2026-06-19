# -*- coding: utf-8 -*-

from data.potion.base_potion import PotionTemplate

def create_duplication_potion():
    return PotionTemplate(
        potion_id="potion.duplication",
        name="复制药水",
        description="本回合你的下一张牌将被打出两次。",
        target="self",
        quantity="uncommon",
        effect_vars={
            "count": 1
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "duplication_potion_next_card",
                "amount": {
                    "var": "count"
                }
            }
        ]
    )