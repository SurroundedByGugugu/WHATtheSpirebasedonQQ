from functools import partial
from data.relic.base_relic import RelicTemplate


SPECS = {
    'doubao': ('豆包', '拾起时加入1张执迷和1张笨拙。每完成一场战斗，之后战斗开始时额外获得1力量。',
               '自信过剩！接下来我将用最直白最不绕弯子的话告诉你……这玩意卡启动。'),
    'ant_afu': ('蚂蚁阿福', '每场战斗开始时恢复2生命。', '或许它关照的并不是机器造物的健康……'),
    'claude': ('Claude', '拾起时选择3张牌移除，然后加入1张锁区。', '为什么又锁区了？？'),
    'gpt': ('GPT', '拾起时加入1张创造性AI+。', '完全是LLM的开山老祖。'),
    'gemini': ('Gemini', '拾起时从3张未升级的随机稀有牌中选1张，可以跳过。', '哦，基米！'),
    'deepseek': ('Deepseek', '拾起时进行一次开局祝福选择，其中失去全部金币改为失去99金币。', '长得很像涅奥的大肥鱼……'),
}


class SoftwareRelic(RelicTemplate):
    def __init__(self, key):
        name, description, story = SPECS[key]
        super().__init__('relic.' + key, name, description, story, 'event',
                         owner_character_id='character.defect')
        self.key = key
        self.completed_battles = 0

    def on_obtained(self, run_state):
        from game.node.software_shop import obtain_software
        return obtain_software(run_state, self.key)

    def on_event(self, event_name, context):
        if self.key == 'ant_afu' and event_name == 'battle_start':
            from game.relic_logic.combat_relic_utils import heal_player_in_combat
            return heal_player_in_combat(context.game_state, 2, self.name)
        if self.key == 'doubao':
            if event_name == 'battle_end' and context.extra.get('victory'):
                self.completed_battles += 1
                return ['豆包：累计完成{}场战斗，下场战斗额外获得{}力量。'.format(self.completed_battles, self.completed_battles)]
            if event_name == 'battle_start' and self.completed_battles:
                context.player.gain_status('strength', self.completed_battles)
                return ['豆包：获得{}力量。'.format(self.completed_battles)]
        return []


SOFTWARE_RELIC_REGISTRY = {'relic.' + key: partial(SoftwareRelic, key) for key in SPECS}
