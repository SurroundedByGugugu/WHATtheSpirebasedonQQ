from functools import partial
from data.relic.base_relic import RelicTemplate

SPECS = {
    'pure_water': ('至纯之水','starting','战斗开始时额外将1张奇迹加入手牌。'),
    'damaru': ('手摇鼓','common','每回合开始时获得1层真言。'),
    'duality': ('两仪','uncommon','每打出1张攻击牌，获得1点临时敏捷。'),
    'teardrop_locket': ('泪滴吊坠','uncommon','每场战斗开始时进入平静。'),
    'cloak_clasp': ('斗篷扣','rare','回合结束时每张手牌使你获得1点格挡。'),
    'golden_eye': ('黄金眼','rare','每次预见额外检视2张牌。'),
    'melange': ('美琅脂','shop','每次洗牌后预见3。'),
    'holy_water': ('圣水','boss','替换至纯之水。战斗开始时额外将3张奇迹加入手牌。'),
    'violet_lotus': ('紫色莲花','boss','离开平静额外获得1c。'),
}


class WatcherRelic(RelicTemplate):
    def __init__(self, key):
        name, rarity, description = SPECS[key]
        super().__init__('relic.'+key,name,description,'',rarity,owner_character_id='character.watcher')
        self.key = key

    def on_obtained(self, run_state):
        if self.key == 'holy_water':
            run_state.relics[:] = [r for r in run_state.relics if r.relic_id != 'relic.pure_water']
            return ['圣水替换至纯之水。']
        return []

    def on_shuffle(self, state, player):
        if self.key == 'melange' and state is not None:
            from game.scry import request_scry
            return request_scry(state,3,self.name)
        return []

    def on_event(self, event, context):
        from game.watcher import generate, passive_block, status
        from game.stances import change_stance, gain_mantra
        state, player = context.game_state, context.player
        if event == 'battle_start':
            if self.key in ('pure_water','holy_water'):
                # Generated after the opening draw so it does not replace a drawn card.
                state.watcher_opening_miracles = 3 if self.key == 'holy_water' else 1
            if self.key == 'teardrop_locket':
                return change_stance(state,'calm')
        if event == 'turn_start' and self.key == 'damaru':
            return gain_mantra(state,1)
        if event == 'card_play_after' and self.key == 'duality' and getattr(context.card,'card_type','') == 'attack':
            logs = status(state,'dexterity',1)
            player.watcher_temp_dexterity = getattr(player,'watcher_temp_dexterity',0) + 1
            return logs
        if event == 'turn_end' and self.key == 'duality':
            amount = getattr(player,'watcher_temp_dexterity',0)
            player.statuses.add('dexterity',-amount)
            player.watcher_temp_dexterity = 0
        if event == 'player_turn_end' and self.key == 'cloak_clasp':
            return passive_block(state,len(player.hand))
        return []


WATCHER_RELIC_REGISTRY = {'relic.'+key:partial(WatcherRelic,key) for key in SPECS}
