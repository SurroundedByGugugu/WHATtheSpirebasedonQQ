from data.status.base_status import StatusDef
from data.status.AAAregistry import register_status_def

register_status_def(StatusDef('lizhou_order', '调序', '星座及部分卡牌的附加燃料，跨回合保留。', category='buff'))
for key, name, description, category in [
    ('lizhou_fortify', '固强', '持续回合内造成伤害增加25%。', 'buff'),
    ('lizhou_tenacity', '坚韧', '持续回合内获得格挡增加25%。', 'buff'),
    ('lizhou_counterbalance', '抗衡', '持续回合内受到伤害减少50%。', 'buff'),
    ('lizhou_double_hurt', '双倍受伤', '受到伤害翻倍，层数表示持续回合，可被人工制品抵挡。', 'debuff'),
]:
    register_status_def(StatusDef(key, name, description, category=category, display_mode='turns',
        decay_timing='turn_end', decay_amount=1))

from data.card.character.lizhou_cards import SPECS
for key, spec in SPECS.items():
    if spec['kind'] == 'power' and key != 'time_master':
        register_status_def(StatusDef('lizhou_power_'+key, spec['name'], spec['text'], category='buff'))
