# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class CalipersRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.calipers",
            name="外卡钳",
            description="在你的回合开始时，不再失去所有格挡，而是失去 15 点格挡。",
            story="",
            quantity="rare",
            owner_character_id=""
        )

    def get_turn_start_block_loss(self, game_state, player, old_block):
        return 15