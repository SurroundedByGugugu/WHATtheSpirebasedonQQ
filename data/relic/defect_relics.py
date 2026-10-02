from functools import partial
from data.relic.base_relic import RelicTemplate
from game.orbs import rack, channel, set_slots, trigger_passives

SPECS = {
 'cracked_core':('破损核心','starting','战斗开始时生成1个闪电球。'),
 'data_disk':('数据磁盘','common','战斗开始时获得1集中。'),
 'gold_plated_cables':('镀金缆线','uncommon','最前方充能球的被动额外触发一次。'),
 'symbiotic_virus':('共生病毒','uncommon','战斗开始时生成1个黑暗球。'),
 'emotion_chip':('情感芯片','rare','若上回合失去生命，下回合开始触发所有球的被动。'),
 'runic_capacitor':('符文电容器','shop','战斗开始时增加3个球槽。'),
 'inserter':('机械臂','boss','每2个回合增加1个球槽。'),
 'nuclear_battery':('核能电池','boss','战斗开始时生成1个等离子球。'),
 'frozen_core':('冰冻核心','myth','替换破损核心。玩家回合结束时若有空球槽，生成1个冰霜球。'),
}

class DefectRelic(RelicTemplate):
    def __init__(self,key):
        name,rarity,description = SPECS[key]
        super().__init__('relic.'+key,name,description,'',rarity,owner_character_id='character.defect')
        self.key = key
        self.turn_counter = 0
        self.damaged = False

    def on_obtained(self,run_state):
        if self.key == 'frozen_core':
            run_state.relics[:] = [r for r in run_state.relics if r.relic_id != 'relic.cracked_core']
            return ['冰冻核心替换了破损核心。']
        return []

    def on_event(self,event,context):
        state, player = context.game_state, context.player
        if event == 'battle_start':
            self.damaged = False
            kind = {'cracked_core':'lightning','symbiotic_virus':'dark','nuclear_battery':'plasma'}.get(self.key)
            if kind:
                return channel(state,player,kind)
            if self.key == 'data_disk':
                player.gain_status('focus',1)
                return ['数据磁盘：获得1集中。']
        if state.battle_over:
            return []
        if self.key == 'frozen_core' and event == 'player_turn_end' and len(rack(player).orbs) < rack(player).capacity:
            return channel(state,player,'frost')
        if self.key == 'inserter' and event == 'turn_start':
            self.turn_counter += 1
            if self.turn_counter % 2 == 0:
                set_slots(player,rack(player).capacity+1)
                return ['机械臂：增加1个球槽。']
        if self.key == 'emotion_chip':
            if event == 'damage_after' and context.target is player and context.extra.get('real_damage',0) > 0:
                self.damaged = True
            if event == 'turn_start':
                damaged, self.damaged = self.damaged, False
                if damaged:
                    return ['情感芯片触发。'] + trigger_passives(state,player)
        return []

DEFECT_RELIC_REGISTRY = {'relic.'+key:partial(DefectRelic,key) for key in SPECS}
