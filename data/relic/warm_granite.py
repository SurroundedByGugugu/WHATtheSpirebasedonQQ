from data.relic.base_relic import RelicTemplate


class WarmGraniteRelic(RelicTemplate):
    def __init__(self):
        super().__init__('relic.warm_granite', '温热花岗岩', '拾起时获得一张【重结晶】。',
                         '握在手中时仍能感到微弱的余温。', 'uncommon')

    def on_obtained(self, run_state):
        from data.card.AAAregistry import create_card
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics
        return add_card_to_master_deck_with_relics(run_state, create_card('card.recrystallization'), source=self.name)
