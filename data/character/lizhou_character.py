from data.character.base_character import CharacterTemplate


class LizhouCharacter(CharacterTemplate):
    def __init__(self):
        super().__init__(character_id='character.lizhou', name='李昼', max_hp=75, max_cost=3,
            starting_gold=99, starting_relic_ids=['relic.anchored_eye', 'relic.twelve_zodiacs'],
            starting_deck_ids=['card.lizhou.strike']*4 + ['card.lizhou.defend']*4 +
                              ['card.lizhou.blunt_bullet', 'card.lizhou.star_flower', 'card.lizhou.align_stars'])
