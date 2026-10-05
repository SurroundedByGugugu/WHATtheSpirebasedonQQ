"""STS1 Watcher cards; paired values are base/upgraded. Generated cards are special."""
from functools import partial
from data.card.base_card import CardTemplate

SPECS = {}


def card(key, name, kind, cost, rarity, text, *, target=None, keywords=(), upgraded_keywords=None, **variables):
    SPECS[key] = dict(name=name, kind=kind, cost=cost, rarity=rarity, text=text,
        target=target or ('enemy' if kind == 'attack' else 'self'), keywords=list(keywords),
        upgraded_keywords=upgraded_keywords, variables=variables)


card('strike_watcher','打击','attack',1,'starting','造成 {damage} 点伤害。',damage=(6,9))
card('defend_watcher','防御','skill',1,'starting','获得 {block} 点格挡。',block=(5,8))
card('eruption','暴怒','attack',(2,1),'starting','造成9点伤害，然后进入愤怒。',damage=9)
card('vigilance','警惕','skill',2,'starting','获得 {block} 点格挡，然后进入平静。',block=(8,12))
card('bowling_bash','碰撞连击','attack',1,'common','每名存活敌人使本次对目标造成 {damage} 点伤害。',damage=(7,10))
card('consecrate','供奉','attack',0,'common','对所有敌人造成 {damage} 点伤害。',damage=(5,8),target='all_enemies')
card('crescendo','渐强','skill',(1,0),'common','进入愤怒。',keywords=('retain','exhaust'))
card('crush_joints','粉碎关节','attack',1,'common','造成 {damage} 点伤害。上一张牌为技能时，施加 {amount} 层易伤。',damage=(8,10),amount=(1,2))
card('cut_through_fate','斩破命运','attack',1,'common','造成 {damage} 点伤害，预见 {amount}，然后抽1张牌。',damage=(7,9),amount=(2,3))
card('empty_body','化体为空','skill',1,'common','获得 {block} 点格挡，退出姿态。',block=(7,10))
card('empty_fist','化拳为空','attack',1,'common','造成 {damage} 点伤害，退出姿态。',damage=(9,14))
card('evaluate','评估','skill',1,'common','获得 {block} 点格挡，将1张洞见随机放入抽牌堆。',block=(6,10))
card('flurry_of_blows','疾风连击','attack',0,'common','造成 {damage} 点伤害。切换姿态时从弃牌堆回到手牌。',damage=(4,6))
card('flying_sleeves','流云飞袖','attack',1,'common','造成 {damage} 点伤害2次。',damage=(4,6),keywords=('retain',))
card('follow_up','追击','attack',1,'common','造成 {damage} 点伤害。上一张牌为攻击时获得1c。',damage=(7,11))
card('halt','停顿','skill',0,'common','获得 {block} 点格挡。愤怒时额外获得 {amount} 点格挡。',block=(3,4),amount=(9,14))
card('just_lucky','幸运一击','attack',0,'common','预见 {amount}，获得 {block} 点格挡，造成 {damage} 点伤害。',amount=(1,2),block=(2,3),damage=(3,4))
card('pressure_points','点穴','skill',1,'common','施加 {amount} 层印记，然后所有敌人失去等于自身印记的生命。',amount=(8,11),target='enemy')
card('prostrate','五体投地','skill',0,'common','获得 {amount} 层真言，获得4点格挡。',amount=(2,3),block=4)
card('protect','护身','skill',2,'common','获得 {block} 点格挡。',block=(12,16),keywords=('retain',))
card('sash_whip','腰带抽打','attack',1,'common','造成 {damage} 点伤害。上一张牌为攻击时施加 {amount} 层虚弱。',damage=(8,10),amount=(1,2))
card('third_eye','天眼','skill',1,'common','获得 {block} 点格挡，然后预见 {amount}。',block=(7,9),amount=(3,5))
card('tranquility','安宁','skill',(1,0),'common','进入平静。',keywords=('retain','exhaust'))
card('battle_hymn','战歌','power',1,'uncommon','每回合开始时将1张惩恶加入手牌。',upgraded_keywords=['innate'])
card('carve_reality','改造现实','attack',1,'uncommon','造成 {damage} 点伤害，将1张惩恶加入手牌。',damage=(6,10))
card('collect','收集','skill','X','uncommon','在接下来 X+{amount} 个回合开始时将1张奇迹+加入手牌。',amount=(0,1),keywords=('exhaust',))
card('conclude','结末','attack',1,'uncommon','对所有敌人造成 {damage} 点伤害，结束回合。',damage=(12,16),target='all_enemies')
card('deceive_reality','欺瞒现实','skill',1,'uncommon','获得 {block} 点格挡，将1张平安加入手牌。',block=(4,7))
card('empty_mind','化智为空','skill',1,'uncommon','抽 {amount} 张牌，然后退出姿态。',amount=(2,3))
card('fasting','斋戒','power',2,'uncommon','获得 {amount} 力量与敏捷，此后每回合少获得1c。',amount=(3,4))
card('fear_no_evil','不惧妖邪','attack',1,'uncommon','造成 {damage} 点伤害。目标意图为攻击时进入平静。',damage=(8,11))
card('foreign_influence','他山之石','skill',0,'uncommon',('从3张任意颜色攻击牌中选择1张加入手牌。','从3张任意颜色攻击牌中选择1张加入手牌，本回合费用为0。'),keywords=('exhaust',))
card('foresight','先见之明','power',1,'uncommon','每回合开始、抽牌前预见 {amount}。',amount=(3,4))
card('indignation','义愤填膺','skill',1,'uncommon','愤怒时对所有敌人施加 {amount} 层易伤，否则进入愤怒。',amount=(3,5))
card('inner_peace','内心宁静','skill',1,'uncommon','平静时抽 {amount} 张牌，否则进入平静。',amount=(3,4))
card('like_water','如水','power',1,'uncommon','回合结束时，若处于平静，获得 {amount} 格挡。',amount=(5,7))
card('meditate','冥想','skill',1,'uncommon','从弃牌堆选择 {amount} 张牌加入手牌并保留。进入平静，结束回合。',amount=(1,2))
card('mental_fortress','心灵堡垒','power',1,'uncommon','每次切换姿态获得 {amount} 格挡。',amount=(4,6))
card('nirvana','涅槃','power',1,'uncommon','每次预见获得 {amount} 格挡。',amount=(3,4))
card('perseverance','坚韧','skill',1,'uncommon','获得 {block} 格挡。每次保留使本场战斗格挡增加 {amount}。',block=(5,7),amount=(2,3),keywords=('retain',))
card('pray','祈祷','skill',1,'uncommon','获得 {amount} 真言，将1张洞见随机放入抽牌堆。',amount=(3,4))
card('reach_heaven','立地升天','attack',2,'uncommon','造成 {damage} 伤害，将1张以暴易暴随机放入抽牌堆。',damage=(10,15))
card('rushdown','猛虎下山','power',(1,0),'uncommon','每次进入愤怒抽2张牌。',amount=2)
card('sanctity','圣洁','skill',1,'uncommon','获得 {block} 格挡。上一张牌为技能时抽2张牌。',block=(6,9))
card('sands_of_time','时之沙','attack',4,'uncommon','造成 {damage} 伤害。每次保留使本场战斗费用减少1。',damage=(20,26),keywords=('retain',))
card('signature_move','招牌技','attack',2,'uncommon','只有手中没有其他攻击牌时可打出。造成 {damage} 伤害。',damage=(30,40))
card('simmering_fury','怒火中烧','skill',1,'uncommon','下回合开始时进入愤怒并额外抽 {amount} 张牌。',amount=(2,3))
card('study','研习','power',(2,1),'uncommon','每回合结束时将1张洞见随机放入抽牌堆。')
card('swivel','旋身','skill',2,'uncommon','获得 {block} 格挡。下一张攻击牌免费。',block=(8,11))
card('talk_to_the_hand','以手拒之','attack',1,'uncommon','造成 {damage} 伤害。此后每次攻击该目标获得 {amount} 格挡。',damage=(5,7),amount=(2,3),keywords=('exhaust',))
card('tantrum','发泄','attack',1,'uncommon','造成3点伤害 {amount} 次，进入愤怒，此牌随机放回抽牌堆。',damage=3,amount=(3,4))
card('wallop','当头棒喝','attack',2,'uncommon','造成 {damage} 伤害，获得等于未被格挡伤害的格挡。',damage=(9,12))
card('wave_of_the_hand','摆手','skill',1,'uncommon','本回合每次获得格挡，对所有敌人施加 {amount} 层虚弱。',amount=(1,2))
card('weave','迂回','attack',0,'uncommon','造成 {damage} 伤害。预见时从弃牌堆回到手牌。',damage=(4,6))
card('wheel_kick','回环踢','attack',2,'uncommon','造成 {damage} 伤害，抽2张牌。',damage=(15,20))
card('windmill_strike','旋转打击','attack',2,'uncommon','造成 {damage} 伤害。每次保留使本场战斗伤害增加 {amount}。',damage=(7,10),amount=(4,5),keywords=('retain',))
card('worship','敬拜','skill',2,'uncommon','获得5层真言。',amount=5,upgraded_keywords=['retain'])
card('wreath_of_flame','火焰纹','skill',1,'uncommon','下一张攻击牌每段额外造成 {amount} 伤害。',amount=(5,8))
card('alpha','阿尔法','skill',1,'rare','将1张贝塔随机放入抽牌堆。',keywords=('exhaust',),upgraded_keywords=['innate','exhaust'])
card('blasphemy','渎神','skill',1,'rare','进入神格，下回合开始时受到致命伤害。',keywords=('exhaust',),upgraded_keywords=['retain','exhaust'])
card('brilliance','光辉','attack',1,'rare','造成 {damage} 伤害，额外增加本场战斗获得的真言总数。',damage=(12,16))
card('conjure_blade','聚能成刃','skill','X','rare','将1张攻击 X+{amount} 次的灭除之刃随机放入抽牌堆。',amount=(0,1),keywords=('exhaust',))
card('deva_form','天人形态','power',3,'rare','每回合开始获得1c，此效果每回合增加1c。',keywords=('ethereal',),upgraded_keywords=[])
card('deus_ex_machina','机械降神','skill',-2,'rare','抽到时将 {amount} 张奇迹加入手牌，然后消耗此牌。',amount=(2,3),keywords=('unplayable',))
card('devotion','虔信','power',1,'rare','每回合开始获得 {amount} 真言。',amount=(2,3))
card('establishment','确立基础','power',1,'rare','每次保留卡牌，使其本场战斗费用减少1。',upgraded_keywords=['innate'])
card('judgment','审判','skill',1,'rare','目标生命不超过 {amount} 时，将其生命设为0。',amount=(30,40),target='enemy')
card('lesson_learned','勤学精进','attack',2,'rare','造成 {damage} 伤害。斩杀非爪牙敌人时永久升级牌组中1张随机牌。',damage=(10,13),keywords=('exhaust',))
card('master_reality','操控现实','power',(1,0),'rare','战斗中生成的卡牌获得升级。')
card('ragnarok','诸神之黄昏','attack',3,'rare','对随机敌人造成 {damage} 点伤害 {amount} 次。',damage=(5,6),amount=(5,6),target='random_enemy')
card('omniscience','通晓万物','skill',(4,3),'rare','从抽牌堆选择1张牌，免费结算两次然后消耗。',keywords=('exhaust',))
card('scrawl','潦草急就','skill',(1,0),'rare','抽牌直到手牌满。',keywords=('exhaust',))
card('spirit_shield','精神护盾','skill',2,'rare','每张手牌使本次获得 {amount} 点格挡。',amount=(3,4))
card('vault','腾跃','skill',(3,2),'rare','结束回合，跳过敌人行动，开始你的额外回合。',keywords=('exhaust',))
card('wish','许愿','skill',3,'rare','选择获得 {armor} 多层护甲、{strength} 力量或 {gold} 金币。',armor=(6,8),strength=(3,4),gold=(25,30),keywords=('exhaust',))
card('miracle','奇迹','skill',0,'special','获得 {amount}c。',amount=(1,2),keywords=('retain','exhaust'))
card('insight','洞见','skill',0,'special','抽 {amount} 张牌。',amount=(2,3),keywords=('retain','exhaust'))
card('smite','惩恶','attack',1,'special','造成 {damage} 伤害。',damage=(12,16),keywords=('retain','exhaust'))
card('safety','平安','skill',1,'special','获得 {block} 格挡。',block=(12,16),keywords=('retain','exhaust'))
card('through_violence','以暴易暴','attack',0,'special','造成 {damage} 伤害。',damage=(20,30),keywords=('retain','exhaust'))
card('beta','贝塔','skill',(2,1),'special','将1张欧米伽随机放入抽牌堆。',keywords=('exhaust',))
card('omega','欧米伽','power',3,'special','每回合结束时对所有敌人造成 {amount} 点效果伤害。',amount=(50,60))
card('expunger','灭除之刃','attack',1,'special','造成 {damage} 伤害 {amount} 次。',damage=(9,15),amount=1)


def make_card(key):
    spec = SPECS[key]
    def pick(v, up):
        return v[int(up)] if isinstance(v, tuple) else v
    def fields(up):
        values = {k: pick(v,up) for k,v in spec['variables'].items()}
        keywords = spec['upgraded_keywords'] if up and spec['upgraded_keywords'] is not None else spec['keywords']
        return dict(name=spec['name'] + ('+' if up else ''), cost=pick(spec['cost'],up),
            card_vars=values, description=pick(spec['text'],up).format(**values), keywords=list(keywords))
    base, upgrade = fields(False), fields(True)
    upgrade['set_keywords'] = upgrade.pop('keywords')
    if not isinstance(spec['cost'], tuple):
        upgrade.pop('cost')
    if key == 'expunger':
        upgrade['card_vars'].pop('amount')
    conditions = [{'op':'only_attack_in_hand'}] if key == 'signature_move' else []
    return CardTemplate(card_id='card.'+key, card_type=spec['kind'], quantity=spec['rarity'],
        target=spec['target'], owner_character_id='' if spec['rarity'] == 'special' else 'character.watcher', **base,
        effects=[{'op':'watcher_card','action':key}], upgrade_patch=upgrade, play_conditions=conditions)


WATCHER_CARD_REGISTRY = {'card.'+key: partial(make_card,key) for key in SPECS}
WATCHER_REWARD_IDS = ['card.'+key for key,s in SPECS.items() if s['rarity'] not in ('starting','special')]
