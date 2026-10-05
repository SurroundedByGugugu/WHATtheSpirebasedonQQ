from data.character.base_character import CharacterTemplate


class WatcherCharacter(CharacterTemplate):
    def __init__(self):
        super().__init__(character_id='character.watcher', name='观者', max_hp=72, max_cost=3,
            starting_relic_ids=['relic.pure_water'],
            starting_deck_ids=['card.strike_watcher']*4 + ['card.defend_watcher']*4 + ['card.eruption','card.vigilance'])
