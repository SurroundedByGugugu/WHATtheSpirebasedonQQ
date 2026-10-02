from data.character.base_character import CharacterTemplate

class DefectCharacter(CharacterTemplate):
    def __init__(self):
        super().__init__(character_id='character.defect', name='故障机器人', max_hp=75, max_cost=3,
            starting_relic_ids=['relic.cracked_core'],
            starting_deck_ids=['card.strike_defect']*4 + ['card.defend_defect']*4 + ['card.zap','card.dualcast'])
        self.starting_orb_slots = 3
