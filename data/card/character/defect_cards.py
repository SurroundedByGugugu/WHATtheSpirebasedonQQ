"""Slay the Spire 1 blue cards. Numbers in pairs are base/upgraded."""
from functools import partial
from data.card.base_card import CardTemplate

SPECS = {}
def card(key, name, kind, cost, rarity, text, *, target=None, keywords=(), upgraded_keywords=None, **variables):
    SPECS[key] = dict(name=name, kind=kind, cost=cost, rarity=rarity, text=text,
                      target=target or ('enemy' if kind == 'attack' else 'self'),
                      keywords=list(keywords), upgraded_keywords=upgraded_keywords, variables=variables)

card('strike_defect','打击','attack',1,'starting','造成 {damage} 点伤害。',damage=(6,9))
card('defend_defect','格挡','skill',1,'starting','获得 {block} 点格挡。',block=(5,8))
card('zap','电击','skill',(1,0),'starting','生成1个闪电球。')
card('dualcast','双重释放','skill',(1,0),'starting','最前方充能球激发2次后移除。')
card('ball_lightning','球状闪电','attack',1,'common','造成 {damage} 点伤害，生成1个闪电球。',damage=(7,10))
card('barrage','弹幕齐射','attack',1,'common','每个充能球造成 {damage} 点伤害。',damage=(4,6))
card('beam_cell','光束射线','attack',0,'common','造成 {damage} 点伤害，施加 {amount} 层易伤。',damage=(3,4),amount=(1,2))
card('charge_battery','充电','skill',1,'common','获得 {block} 点格挡，下回合获得1能量。',block=(7,10))
card('claw','爪击','attack',0,'common','造成 {damage} 点伤害，本场战斗所有爪击伤害增加2。',damage=(3,5))
card('cold_snap','寒流','attack',1,'common','造成 {damage} 点伤害，生成1个冰霜球。',damage=(6,9))
card('compile_driver','编译冲击','attack',1,'common','造成 {damage} 点伤害，每种不同的充能球抽1张牌。',damage=(7,10))
card('coolheaded','冷静头脑','skill',1,'common','生成1个冰霜球，抽 {amount} 张牌。',amount=(1,2))
card('go_for_the_eyes','眼部攻击','attack',0,'common','造成 {damage} 点伤害；若敌人意图攻击，施加 {amount} 层虚弱。',damage=(3,4),amount=(1,2))
card('hologram','全息影像','skill',1,'common','获得 {block} 点格挡，选择弃牌堆1张牌加入手牌。',block=(3,5),keywords=('exhaust',),upgraded_keywords=[])
card('leap','飞跃','skill',1,'common','获得 {block} 点格挡。',block=(9,12))
card('rebound','弹回','attack',1,'common','造成 {damage} 点伤害，本回合下一张打出的牌放回抽牌堆顶。',damage=(9,12))
card('recursion','递归','skill',(1,0),'common','激发最前方充能球，再生成该球；保留其内部数值。')
card('stack','堆栈','skill',1,'common','获得等于弃牌堆张数加 {amount} 的格挡。',amount=(0,3))
card('steam_barrier','蒸汽护壁','skill',0,'common','获得 {block} 点格挡，本场战斗此牌格挡降低1。',block=(6,8))
card('streamline','精简改良','attack',2,'common','造成 {damage} 点伤害，本场战斗此牌费用降低1。',damage=(15,20))
card('sweeping_beam','扫荡射线','attack',1,'common','对所有敌人造成 {damage} 点伤害，抽1张牌。',damage=(6,9),target='all_enemies')
card('turbo','内核加速','skill',0,'common','获得 {amount} 能量，将1张虚空加入弃牌堆。',amount=(2,3))
card('aggregate','汇集','skill',1,'uncommon','抽牌堆每 {amount} 张牌获得1能量。',amount=(4,3))
card('auto_shields','自动护盾','skill',1,'uncommon','若没有格挡，获得 {block} 点格挡。',block=(11,15))
card('blizzard','暴雪','attack',1,'uncommon','对所有敌人造成本场战斗生成冰霜球数量×{amount} 的伤害。',amount=(2,3),target='all_enemies')
card('boot_sequence','启动流程','skill',0,'uncommon','获得 {block} 点格挡。',block=(10,13),keywords=('innate','exhaust'))
card('bullseye','瞄准靶心','attack',1,'uncommon','造成 {damage} 点伤害，施加 {amount} 层锁定（球伤害增加50%）。',damage=(8,11),amount=(2,3))
card('capacitor','扩容','power',1,'uncommon','增加 {amount} 个充能球栏位。',amount=(2,3))
card('chaos','混沌','skill',1,'uncommon','生成 {amount} 个随机原作充能球。',amount=(1,2))
card('chill','冰寒','skill',0,'uncommon','每名存活敌人生成1个冰霜球。',keywords=('exhaust',),upgraded_keywords=['innate','exhaust'])
card('consume','耗尽','skill',2,'uncommon','获得 {amount} 集中，失去1个充能球栏位。',amount=(2,3))
card('darkness','漆黑','skill',1,'uncommon',('生成1个黑暗球。','生成1个黑暗球，然后触发所有黑暗球的被动。'))
card('defragment','碎片整理','power',1,'uncommon','获得 {amount} 集中。',amount=(1,2))
card('doom_and_gloom','愁云惨淡','attack',2,'uncommon','对所有敌人造成 {damage} 点伤害，生成1个黑暗球。',damage=(10,14),target='all_enemies')
card('double_energy','双倍能量','skill',(1,0),'uncommon','将当前剩余能量翻倍。',keywords=('exhaust',))
card('equilibrium','均衡','skill',2,'uncommon','获得 {block} 点格挡，本回合保留所有手牌。',block=(13,16))
card('ftl','超越光速','attack',0,'uncommon','造成 {damage} 点伤害；此前本回合打出的牌少于 {amount} 张则抽1张牌。',damage=(5,6),amount=(3,4))
card('force_field','力场','skill',4,'uncommon','获得 {block} 点格挡，本场战斗每打出1张能力牌费用降低1。',block=(12,16))
card('fusion','聚变','skill',(2,1),'uncommon','生成1个等离子球。')
card('genetic_algorithm','遗传算法','skill',1,'uncommon','获得 {block} 点格挡，此牌格挡永久增加 {amount}。',block=1,amount=(2,3),keywords=('exhaust',))
card('glacier','冰川','skill',2,'uncommon','获得 {block} 点格挡，生成2个冰霜球。',block=(7,10))
card('heatsinks','散热片','power',1,'uncommon','每打出1张能力牌，抽 {amount} 张牌。',amount=(1,2))
card('hello_world','你好，世界','power',1,'uncommon','每回合开始时，将1张随机普通蓝色牌加入手牌。',upgraded_keywords=['innate'])
card('loop','循环','power',1,'uncommon','回合开始时，触发最前方充能球被动 {amount} 次。',amount=(1,2))
card('melter','熔化','attack',1,'uncommon','移除目标所有格挡，造成 {damage} 点伤害。',damage=(10,14))
card('overclock','超频','skill',0,'uncommon','抽 {amount} 张牌，将1张灼伤加入弃牌堆。',amount=(2,3))
card('recycle','回收','skill',(1,0),'uncommon','消耗1张手牌，获得等于其当前费用的能量。')
card('reinforced_body','硬化机体','skill','X','uncommon','获得 {block} 点格挡，重复X次。',block=(7,9))
card('reprogram','重编程','skill',1,'uncommon','失去 {amount} 集中，获得 {amount} 力量与敏捷。',amount=(1,2))
card('rip_and_tear','狂乱撕扯','attack',1,'uncommon','对随机敌人造成 {damage} 点伤害，重复2次。',damage=(7,9),target='random_enemy')
card('scrape','刮削','attack',1,'uncommon','造成 {damage} 点伤害，抽 {amount} 张牌，丢弃这些牌中当前费用不为0的牌。',damage=(7,10),amount=(4,5))
card('self_repair','自我修复','power',1,'uncommon','战斗胜利时回复 {amount} 生命。',amount=(7,10))
card('skim','快速检索','skill',1,'uncommon','抽 {amount} 张牌。',amount=(3,4))
card('static_discharge','静电释放','power',1,'uncommon','每次受到攻击造成的生命损失，生成 {amount} 个闪电球。',amount=(1,2))
card('storm','雷暴','power',1,'uncommon','每打出1张能力牌，生成1个闪电球。',upgraded_keywords=['innate'])
card('sunder','分离','attack',3,'uncommon','造成 {damage} 点伤害；击杀敌人时获得3能量。',damage=(24,32))
card('tempest','暴风雨','skill','X','uncommon','生成 X+{amount} 个闪电球。',amount=(0,1),keywords=('exhaust',))
card('white_noise','白噪声','skill',(1,0),'uncommon','将1张随机蓝色能力牌加入手牌，本回合费用为0。',keywords=('exhaust',))
card('machine_rush','猛机下山！','power',(1,0),'uncommon','每生成1个充能球，抽1张牌。')
card('convolutional_neural_network','卷积神经网络','skill',1,'uncommon','选择1张手牌，获得等于该牌及其左右相邻牌当前费用之和×{multiplier}的格挡。X费按当前剩余能量计算。',multiplier=(3,4))
card('transformer','Transformer','power',1,'uncommon',('从下回合起，每回合抽取的第1张牌优先为上回合最后打出的牌的同类型牌。','每回合开始时，额外抽取1张上回合最后打出的牌的同类型牌。'))
card('all_for_one','万物一心','attack',2,'rare','造成 {damage} 点伤害，将弃牌堆当前0费牌加入手牌。',damage=(10,14))
card('amplify_defect','增幅','skill',1,'rare','本回合接下来 {amount} 张能力牌额外结算一次。',amount=(1,2))
card('biased_cognition','偏差认知','power',1,'rare','获得 {amount} 集中，此后每回合开始失去1集中。',amount=(4,5))
card('buffer_defect','缓冲','power',2,'rare','阻止接下来 {amount} 次生命损失。',amount=(1,2))
card('core_surge','核心电涌','attack',1,'rare','造成 {damage} 点伤害，获得1层人工制品。',damage=(11,15),keywords=('exhaust',))
card('creative_ai','创造性AI','power',(3,2),'rare','每回合开始时，将1张随机蓝色能力牌加入手牌。')
card('echo_form','回响形态','power',3,'rare','每回合首张牌额外结算一次；多层使前多张牌生效。',keywords=('ethereal',),upgraded_keywords=[])
card('electrodynamics','电动力学','power',2,'rare','闪电球攻击所有敌人，生成 {amount} 个闪电球。',amount=(2,3))
card('fission','裂变','skill',0,'rare',('移除所有球，每移除1个球获得1能量并抽1张牌。','激发所有球，每激发1个球获得1能量并抽1张牌。'),keywords=('exhaust',))
card('hyperbeam','超能光束','attack',2,'rare','对所有敌人造成 {damage} 点伤害，失去3集中。',damage=(26,34),target='all_enemies')
card('machine_learning','机器学习','power',1,'rare','每回合开始时额外抽1张牌。',upgraded_keywords=['innate'])
card('meteor_strike','陨石打击','attack',5,'rare','造成 {damage} 点伤害，生成3个等离子球。',damage=(24,30))
card('multi_cast','多重释放','skill','X','rare','最前方充能球激发 X+{amount} 次后移除。',amount=(0,1))
card('rainbow','彩虹','skill',2,'rare','依次生成闪电、冰霜、黑暗球各1个。',keywords=('exhaust',),upgraded_keywords=[])
card('reboot','重启','skill',0,'rare','将手牌与弃牌堆洗入抽牌堆，抽 {amount} 张牌。',amount=(4,6),keywords=('exhaust',))
card('seek','搜寻','skill',0,'rare','从抽牌堆选择 {amount} 张牌加入手牌。',amount=(1,2),keywords=('exhaust',))
card('thunder_strike','雷霆打击','attack',3,'rare','每个本场战斗生成过的闪电球，对随机敌人造成 {damage} 点伤害。',damage=(7,9),target='random_enemy')


def make_card(key):
    spec = SPECS[key]
    def pick(value, upgraded):
        return value[int(upgraded)] if isinstance(value, tuple) else value
    def fields(upgraded):
        variables = {k: pick(v, upgraded) for k,v in spec['variables'].items()}
        keywords = spec['upgraded_keywords'] if upgraded and spec['upgraded_keywords'] is not None else spec['keywords']
        return dict(name=spec['name'] + ('+' if upgraded else ''), cost=pick(spec['cost'],upgraded),
                    card_vars=variables, description=pick(spec['text'],upgraded).format(**variables), keywords=list(keywords))
    base = fields(False)
    upgrade = fields(True)
    upgrade["set_keywords"] = upgrade.pop("keywords")
    # An upgrade without a cost change preserves combat cost reductions.
    if not isinstance(spec["cost"], tuple):
        upgrade.pop("cost")
    # Permanent genetic growth survives upgrading an existing card.
    if key == 'genetic_algorithm':
        upgrade['card_vars'].pop('block')
    return CardTemplate(card_id='card.'+key, card_type=spec['kind'], target=spec['target'],
        quantity=spec['rarity'], owner_character_id='character.defect', **base,
        effects=[{'op':'defect_card','action':key}], upgrade_patch=upgrade,
        cost_rules=[{'op':'defect_power_discount'}] if key == 'force_field' else [])

DEFECT_CARD_REGISTRY = {'card.'+key: partial(make_card,key) for key in SPECS}
DEFECT_REWARD_IDS = ['card.'+key for key,s in SPECS.items() if s['rarity'] != 'starting']
