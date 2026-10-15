"""李昼：经设计确认的卡牌目录。数值对为（基础，升级）。"""
from functools import partial
from data.card.base_card import CardTemplate

SPECS = {}


def define(key, name, kind, rarity, cost, text, plus, *, target='self', keywords=(), **values):
    SPECS[key] = dict(name=name, kind=kind, rarity=rarity, cost=cost,
                      text=text, plus=plus, target=target, keywords=keywords, values=values)


define('strike', '打击', 'attack', 'starting', 1, '造成6点伤害。', '造成9点伤害。', target='enemy', damage=(6, 9))
define('blunt_bullet', '钝气弹', 'attack', 'starting', 1, '造成6点伤害。调序2：追加1次6点伤害。', '造成6点伤害。调序1：追加1次6点伤害。', target='enemy', damage=6, order=(2, 1))
define('meteor_fall', '流星坠击', 'attack', 'common', 1, '造成10点伤害。', '造成10点伤害。抽1张牌。', target='enemy', damage=10)
define('stellar_impact', '星辰冲击', 'attack', 'common', 1, '给予1层易伤，造成12点伤害。', '给予2层易伤，造成12点伤害。', target='enemy', damage=12, amount=(1, 2))
define('dust_wave', '气尘海浪', 'attack', 'common', 1, '调序1：对所有敌人造成8点伤害，每攻击到1个敌人，获得1调序。', '调序0：对所有敌人造成8点伤害，每攻击到1个敌人，获得1调序。', target='all_enemies', damage=8, order=(1, 0))
define('broken_hope', '奢望破灭', 'attack', 'common', 2, '失去所有调序。造成16点伤害。', '失去所有调序。造成20点伤害。', target='enemy', damage=(16, 20))
define('star_warning', '星之预警', 'attack', 'common', 1, '检视抽牌堆顶部3张牌，选择最多2张获得保留。获得1层抗衡，造成6点伤害。', '检视抽牌堆顶部5张牌，选择最多3张获得保留。获得1层抗衡，造成6点伤害。', target='enemy', damage=6, inspect=(3, 5), count=(2, 3))
define('gliding_punishment', '滑行惩戒', 'attack', 'uncommon', 1, '对所有敌人造成4点伤害，抽2张牌。', '对所有敌人造成4点伤害，抽3张牌。', target='all_enemies', damage=4, count=(2, 3))
define('diamond_dust', '钻石尘', 'attack', 'uncommon', 1, '手牌中所有牌获得2浮动、2锚定。对所有敌人造成12点伤害。', '手牌中所有牌获得1浮动、2锚定。对所有敌人造成12点伤害。', target='all_enemies', damage=12, floating=(2, 1))
define('wandering_star', '浮游之星', 'attack', 'uncommon', 3, '弃牌堆所有牌获得1浮动。造成26点伤害，从抽牌堆随机免费打出2张牌。', '弃牌堆所有牌获得1浮动。造成36点伤害，从抽牌堆随机免费打出2张牌。', target='enemy', damage=(26, 36))
define('rusted_thing', '锈蚀之物', 'attack', 'uncommon', 1, '手牌中所有牌失去保留和所有锚定。每移除一张牌的保留或锚定，随机攻击1次，每次9点伤害。', '手牌中所有牌失去保留和所有锚定。每移除一张牌的保留或锚定，随机攻击2次，每次9点伤害。', target='random_enemy', damage=9, amount=(1, 2))
define('spinning_stardust', '旋转星尘', 'attack', 'uncommon', 1, '造成8点伤害。本牌本回合每已打出2次，多攻击1次。返回手牌。', '造成8点伤害。本牌本回合每已打出1次，多攻击1次。返回手牌。', target='enemy', damage=8, interval=(2, 1))
define('dark_sky', '晦暗的星空', 'attack', 'uncommon', 0, '获得1层固强，给予1层易伤，造成4点伤害。', '获得2层固强，给予2层易伤，造成4点伤害。', target='enemy', damage=4, amount=(1, 2))
define('star_memory', '星的记忆体', 'attack', 'uncommon', 1, '对所有敌人造成3点伤害。选择消耗牌堆中的1张牌加入手牌。', '对所有敌人造成6点伤害。选择消耗牌堆中的1张牌加入手牌。', target='all_enemies', damage=(3, 6))
define('curtain_fall', '结界落幕', 'attack', 'uncommon', (3, 2), '失去所有调序，所有牌的锚定和浮动清零。对所有敌人造成20点伤害，消耗至多4张手牌。', '失去所有调序，所有牌的锚定和浮动清零。对所有敌人造成20点伤害，消耗至多4张手牌。', target='all_enemies', damage=20)
define('sharp_bullet', '锐气弹', 'attack', 'rare', 2, '造成2次8点伤害。调序3：追加6次8点伤害。', '造成2次8点伤害。调序1：追加6次8点伤害。', target='enemy', damage=8, order=(3, 1))
define('dinosaur_buster', '恐龙毁灭弹', 'attack', 'rare', (3, 2), '造成36点伤害，给予3层易伤。', '造成36点伤害，给予3层易伤。', target='enemy', damage=36)
define('star_breath', '星之吐息', 'attack', 'rare', (3, 2), '清除所有敌人的格挡，对所有敌人造成20点伤害。失去3调序。', '清除所有敌人的格挡，对所有敌人造成20点伤害。失去3调序。', target='all_enemies', damage=20)
define('star_bloom', '星花怒放', 'attack', 'rare', 'X', '清空所有星之花的锚定，获得X倍清除层数的能量。失去所有能量，每失去1点，所有敌人失去4点生命。', '清空所有星之花的锚定，获得(X+2)倍清除层数的能量。失去所有能量，每失去1点，所有敌人失去4点生命。', target='all_enemies')
define('tiny_annihilation', '微小湮灭', 'attack', 'rare', 92, '每获得或消耗1调序、每张牌获得锚定或浮动，本牌费用降低3。晕眩所有敌人，对单体造成本次支付时实际降费差的伤害。', '每获得或消耗1调序、每张牌获得锚定或浮动，本牌费用降低6。晕眩所有敌人，对单体造成本次支付时实际降费差的伤害。', target='enemy', reduction=(3, 6))
define('self_destroying_sun', '自灭的西太阳', 'attack', 'rare', 4, '失去所有调序，所有牌锚定和浮动清零。对施放者以外的所有人造成92点伤害。', '失去所有调序，所有牌锚定和浮动清零。对施放者以外的所有人造成133点伤害。', target='all_enemies', damage=(92, 133))

define('defend', '防御', 'skill', 'starting', 1, '获得5点格挡。', '获得8点格挡。', block=(5, 8))
define('star_flower', '绽放的星之花', 'skill', 'starting', 0, '固有。保留。抽到时抽1张牌。清空本牌锚定，获得等量能量。无法逃脱。返回手牌。失去保留或打出时立即获得保留。', '固有。保留。抽到时抽1张牌。清空本牌锚定，获得等量能量。本场战斗首次打出后获得2锚定。无法逃脱。返回手牌。失去保留或打出时立即获得保留。', keywords=('innate', 'retain'))
define('align_stars', '调正星位', 'skill', 'starting', 1, '获得3调序。', '获得4调序。', amount=(3, 4))
define('star_order', '星星调序', 'skill', 'common', 1, '抽1张牌，获得7点格挡。', '抽2张牌，获得10点格挡。', amount=(1, 2), block=(7, 10))
define('twinkle', '星光闪闪', 'skill', 'common', 0, '调序1：获得6点格挡，给予1层虚弱。', '调序1：获得6点格挡，给予2层虚弱。', target='enemy', order=1, block=6, amount=(1, 2))
define('stellar_rotation', '恒星回转', 'skill', 'common', 1, '获得3调序、3点格挡。', '获得3调序、7点格挡。', amount=3, block=(3, 7))
define('anchoring', '锚定作业', 'skill', 'common', 1, '选择1张手牌获得2锚定。', '选择1张手牌获得3锚定。', amount=(2, 3))
define('calculate_float', '计算浮动', 'skill', 'common', 0, '选择3张手牌获得1浮动，获得2能量。手牌不足时跳过浮动。', '选择1张手牌获得1浮动，获得2能量。手牌不足时跳过浮动。', count=(3, 1))
define('swallow_star', '闪光咽星', 'skill', 'common', 1, '消耗2张手牌，获得4点格挡。无牌可消耗时仍获得格挡。', '消耗2张手牌，获得7点格挡。无牌可消耗时仍获得格挡。', block=(4, 7))
define('fingertip_cosmos', '指尖宇宙', 'skill', 'common', 2, '获得2层固强、坚韧、抗衡。', '获得3层固强、坚韧、抗衡。', amount=(2, 3))
define('paint_sky', '描绘星空之幕', 'skill', 'uncommon', 1, '获得2层抗衡。', '获得3层抗衡。', amount=(2, 3))
define('decorate_stars', '点缀星辰之机', 'skill', 'uncommon', 1, '获得2层固强。', '获得3层固强。', amount=(2, 3))

ZODIACS = ('aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces')
for key, name, text, plus in [
    ('aries', '白羊座', '获得1层缓冲。', '获得2层缓冲。'),
    ('taurus', '金牛座', '获得3层固强。', '获得5层固强。'),
    ('gemini', '双子座', '打出所有星之花，将所有能量转换为调序，再消耗调序依次打出手牌、消耗牌堆的星座牌，付不起时停止。', '仅触发所有星之花获得能量的效果，将所有能量转换为调序，再消耗调序依次打出手牌、消耗牌堆的星座牌，付不起时停止。'),
    ('cancer', '巨蟹座', '复制1张手牌中的星座牌。', '复制1张手牌中的星座牌2张。'),
    ('leo', '狮子座', '获得1层无实体。', '获得1层无实体。'),
    ('virgo', '室女座', '获得6调序。', '获得9调序。'),
    ('libra', '天秤座', '获得3能量。', '获得5能量。'),
    ('scorpio', '天蝎座', '获得5点活力。', '获得8点活力。'),
    ('sagittarius', '射手座', '恢复9点生命。', '恢复18点生命。'),
    ('capricorn', '摩羯座', '给予单个敌人3层虚弱、易伤、脆弱。', '给予所有敌人3层虚弱、易伤、脆弱。'),
    ('aquarius', '宝瓶座', '抽3张牌。', '抽4张牌。'),
    ('pisces', '双鱼座', '生成1张带消耗的随机星座牌到手牌，本回合调序门槛及消耗为0。', '生成1张带消耗的随机星座牌到手牌，本场战斗调序门槛及消耗为0。'),
]:
    define(key, name, 'skill', 'uncommon', 0, '抽1张牌。调序3：'+text,
           '抽1张牌。'+('获得15点格挡。' if key == 'leo' else '')+'调序3：'+plus,
           target='enemy' if key == 'capricorn' else 'self', order=3)

define('meteor_shower', '释放流星雨', 'skill', 'rare', 3, '消耗所有手牌，生成等量随机星座牌加入手牌，本回合免费。', '消耗所有手牌，生成等量升级后的随机星座牌加入手牌，本回合免费。')
define('colonize_orbit', '殖民星轨道', 'skill', 'rare', 1, '获得6调序。', '获得12调序。', amount=(6, 12))
define('collision', '碰撞·星星·膨胀', 'skill', 'rare', 1, '需要并消耗2锚定。给予所有敌人3层虚弱、易伤。', '需要并消耗1锚定。给予所有敌人3层虚弱、易伤。', target='all_enemies', anchor_gate=(2, 1))
define('aye_captain', '是的，船长', 'skill', 'rare', 1, '需要并消耗2锚定。获得1点格挡16次。', '需要并消耗1锚定。获得1点格挡16次。', anchor_gate=(2, 1))
define('phantasm', '幻魔', 'skill', 'rare', 1, '本回合结束时，可消耗任意张有锚定的手牌。消耗。', '本回合结束时，可消耗任意张有锚定的手牌。', keywords=('exhaust',))
define('key', '钥匙', 'skill', 'rare', 0, '选择抽牌堆中3张牌加入手牌。将除了手牌以外所有牌洗入抽牌堆并打乱顺序，将本牌置于抽牌堆底部，然后消耗本牌。', '选择抽牌堆中3张牌加入手牌。将除了手牌以外所有牌洗入抽牌堆并打乱顺序，将本牌置于抽牌堆底部。', keywords=('exhaust',))

define('orderer', '调序者', 'power', 'uncommon', 1, '每打出4张牌，获得2调序。计数跨回合保留，各副本独立计数。', '每打出3张牌，获得2调序。计数跨回合保留，各副本独立计数。', interval=(4, 3))
define('anchor_definition', '锚定义', 'power', 'uncommon', 1, '每张牌获得锚定时，获得5点格挡。', '每张牌获得锚定时，获得8点格挡。', amount=(5, 8))
define('floating_tide', '浮动潮汐', 'power', 'uncommon', (2, 1), '拥有浮动的牌现在可以被打出。重复获得无额外效果。', '拥有浮动的牌现在可以被打出。重复获得无额外效果。')
define('fit_stars', '切合星辰', 'power', 'uncommon', 1, '每打出星座牌，获得3点格挡。', '每打出星座牌，获得5点格挡。', amount=(3, 5))
define('cast_blades', '投刃皆虚', 'power', 'uncommon', 2, '每回合结束时，选择至多2张手牌各获得1锚定。', '每回合结束时，选择至多3张手牌各获得1锚定。', count=(2, 3))
define('time_master', '时间管理大师', 'power', 'uncommon', 3, '结束你的回合，获得1个额外回合，跳过敌方行动。', '结束你的回合，获得2个额外回合，跳过敌方行动。', count=(1, 2))
ELEMENTS = {'earth': ('taurus', 'virgo', 'capricorn'), 'water': ('cancer', 'scorpio', 'pisces'), 'air': ('gemini', 'libra', 'aquarius'), 'fire': ('aries', 'leo', 'sagittarius'), 'stargazer': ZODIACS}
for key, name in [('earth', '土象'), ('water', '水象'), ('air', '风象'), ('fire', '火象'), ('stargazer', '仰望星空者')]:
    constellation_names = '、'.join(SPECS[z]['name'] for z in ELEMENTS[key])
    define(key, name, 'power', 'rare' if key == 'stargazer' else 'uncommon', 4 if key == 'stargazer' else 1,
           '需要并消耗1调序。每回合开始时，选择（'+constellation_names+'）中一个星座的基础调序效果，无需调序触发，目标随机。',
           '需要0调序。每回合开始时，选择（'+constellation_names+'）中一个星座的基础调序效果，无需调序触发，目标随机。', order_gate=(1, 0))
define('void_world', '虚无世界', 'power', 'rare', 3, '虚无。每段攻击先检查敌人格挡，若原本没有格挡，施加1层双倍受伤；然后清空格挡并造成伤害。', '每段攻击先检查敌人格挡，若原本没有格挡，施加1层双倍受伤；然后清空格挡并造成伤害。', keywords=('ethereal',))
define('easy_battle', '战斗好像变得比呼吸还简单了', 'power', 'rare', 4, '每次获得能量时，恢复4点生命，获得4点格挡。', '每次获得能量时，恢复6点生命，获得6点格挡。', amount=(4, 6))
define('ever_changing', '瞬息万变', 'power', 'rare', (1, 0), '每次获得调序、每张牌获得锚定时，获得1能量。', '每次获得调序、每张牌获得锚定时，获得1能量。')
define('stardust_cancer', '星尘癌', 'power', 'rare', (3, 2), '每回合第1个星座效果额外触发1次。N份覆盖前N个，额外触发不占名额、不重复付费，沿用首次调序判断。', '每回合第1个星座效果额外触发1次。N份覆盖前N个，额外触发不占名额、不重复付费，沿用首次调序判断。')
define('anchor_kit', '船锚套件', 'power', 'rare', (3, 2), '每回合开始、抽牌前，选择任意张手牌各获得1锚定。', '每回合开始、抽牌前，选择任意张手牌各获得1锚定。')
define('astronomic_foresight', '天文的远见', 'power', 'rare', 1, '每当有牌被锚定时，额外增加1层锚定。', '每当有牌被锚定时，额外增加1层锚定，获得1点调序。')
define('anchor_sail', '抛锚起航', 'power', 'rare', 2, '每回合开始时，若不足6调序，额外获得6调序。', '固有。每回合开始时，若不足6调序，额外获得6调序。')


define('domain', '领域展开', 'skill', 'rare', 4, '场地变为星；已有星时变为极·星，持续3回合。极·星期间再次使用延长2回合。', '场地变为极·星，持续3回合。极·星期间再次使用延长2回合。')
define('intuition_luck', '直觉与幸运', 'power', 'rare', 1, '回合结束时，可丢弃任意手牌。状态牌和诅咒牌改为消耗；诅咒牌额外从牌库删除。', '回合结束时，可丢弃任意手牌。状态牌和诅咒牌改为消耗；诅咒牌额外从牌库删除。下回合开始抽等量牌。')
define('gemini', '双子座', 'skill', 'uncommon', 0, '抽1张牌。调序3：给予敌人3层锚定、5层浮动。', '抽1张牌。调序3：给予敌人5层锚定、7层浮动。', target='enemy', order=3)
define('star_sea', '星海沉沦', 'power', 'uncommon', 1, '调序3：每打出1张被锚定的牌，获得其锚定层数三分之一（向下取整）的力量和敏捷。', '调序2：每打出1张被锚定的牌，获得其锚定层数三分之一（向下取整）的力量和敏捷。', order_gate=(3,2))
define('focus', '集中专注', 'skill', 'uncommon', 0, '抽1张牌。调序2：抽3张牌，获得1能量。每次被锚定，调序需求降低1。', '抽2张牌。调序2：抽3张牌，获得1能量。每次被锚定，调序需求降低1。', order=2, count=(1,2))
define('observe_stars', '观测星辰', 'skill', 'common', (1,0), '抽2张牌。调序1：抽2张牌。', '抽2张牌。调序1：抽2张牌。', order=1)
define('static_anchor', '静滞锚定', 'skill', 'common', 1, '给予敌人2层锚定。', '给予敌人3层锚定。', target='enemy', amount=(2,3))
define('reverse_gravity', '颠倒失重', 'skill', 'uncommon', 1, '给予敌人3层浮动。', '给予敌人6层浮动。', target='enemy', amount=(3,6))
define('freeze', '不许动', 'skill', 'uncommon', 1, '调序2：锚定所有手牌1层，给予敌人1层锚定。', '调序2：锚定所有手牌2层，给予敌人2层锚定。', target='enemy', order=2, amount=(1,2))
for retained in ('collision', 'aye_captain'):
    SPECS[retained]['keywords'] = ('retain',)
    SPECS[retained]['text'] = '保留。'+SPECS[retained]['text']
    SPECS[retained]['plus'] = '保留。'+SPECS[retained]['plus']


def create_lizhou_card(key, upgraded=False):
    spec = SPECS[key]
    def value(v):
        return v[int(upgraded)] if isinstance(v, tuple) else v
    keywords = list(spec['keywords'])
    if upgraded:
        if key in ('phantasm', 'key'):
            keywords.remove('exhaust')
        if key == 'void_world':
            keywords.remove('ethereal')
        if key in ('moonlight', 'anchor_sail'):
            keywords.append('innate')
    card = CardTemplate(card_id='card.lizhou.'+key, name=spec['name']+('+' if upgraded else ''),
        card_type=spec['kind'], quantity=spec['rarity'], cost=value(spec['cost']),
        target='all_enemies' if key == 'capricorn' and upgraded else spec['target'],
        description=spec['plus'] if upgraded else spec['text'], owner_character_id='character.lizhou',
        card_vars={k: value(v) for k, v in spec['values'].items()},
        effects=[{'op': 'lizhou_card', 'key': key}], keywords=keywords, upgraded=upgraded)
    if key == 'star_flower':
        card.unremovable = card.untransformable = card.inescapable = True
    if not upgraded:
        plus = create_lizhou_card(key, True)
        card.upgrade_patch = {k: getattr(plus, k) for k in ('name', 'cost', 'target', 'description', 'card_vars')}
        card.upgrade_patch['remove_keywords'] = [k for k in card.keywords if k not in plus.keywords]
        card.upgrade_patch['add_keywords'] = [k for k in plus.keywords if k not in card.keywords]
    return card


LIZHOU_CARD_REGISTRY = {'card.lizhou.'+key: partial(create_lizhou_card, key) for key in SPECS}
LIZHOU_REWARD_IDS = ['card.lizhou.'+key for key, spec in SPECS.items() if spec['rarity'] != 'starting']
