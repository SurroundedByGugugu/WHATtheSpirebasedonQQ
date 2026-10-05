from functools import partial
from data.potion.base_potion import PotionTemplate

SPECS = {
    'bottled_miracle': ('瓶装奇迹','common','将2张奇迹加入手牌。'),
    'stance': ('姿态药水','uncommon','选择进入平静或愤怒。'),
    'ambrosia': ('仙馔密酒','rare','进入神格。'),
}


def make_potion(key):
    name, rarity, description = SPECS[key]
    return PotionTemplate('potion.'+key,name,description,quantity=rarity,owner_character_id='character.watcher',
        effects=[{'op':'watcher_potion','action':key}])


WATCHER_POTION_REGISTRY = {'potion.'+key:partial(make_potion,key) for key in SPECS}
