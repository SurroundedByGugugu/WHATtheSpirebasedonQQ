from data.status.base_status import StatusDef
from data.status.AAAregistry import register_status_def

for key, name, description in [
    ('mantra','真言','累计10层时消耗10层并进入神格。'),
    ('w_battle_hymn','战歌','回合开始时生成惩恶。'),
    ('w_foresight','先见之明','回合开始、抽牌前预见。'),
    ('w_fasting','斋戒','回合开始时减少能量。'),
    ('w_like_water','如水','回合结束时处于平静则获得格挡。'),
    ('w_mental_fortress','心灵堡垒','切换姿态时获得格挡。'),
    ('w_nirvana','涅槃','预见时获得格挡。'),
    ('w_rushdown','猛虎下山','进入愤怒时抽牌。'),
    ('w_study','研习','回合结束时生成洞见。'),
    ('w_swivel','旋身','下一张攻击牌免费。'),
    ('w_wave','摆手','本回合获得格挡时施加虚弱。'),
    ('w_simmer','怒火中烧','下回合进入愤怒并抽牌。'),
    ('w_collect','收集','接下来若干回合开始时生成奇迹+。'),
    ('w_devotion','虔信','每回合开始时获得真言。'),
    ('w_establishment','确立基础','保留卡牌时降低费用。'),
    ('w_master_reality','操控现实','战斗中新生成的卡牌升级。'),
    ('w_omega','欧米伽','回合结束时造成效果伤害。'),
]:
    register_status_def(StatusDef(key,name,description,category='buff',display_mode='stack'))

register_status_def(StatusDef('mark','印记','点穴使所有拥有印记的敌人失去对应生命。',category='debuff'))
register_status_def(StatusDef('talk_to_the_hand','以手拒之','每次受到攻击时使攻击者获得格挡。',category='debuff'))
