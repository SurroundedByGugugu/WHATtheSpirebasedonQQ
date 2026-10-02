from data.potion.base_potion import PotionTemplate

def create_focus_potion():
    return PotionTemplate('potion.focus','集中药水','获得2集中。',quantity='common',owner_character_id='character.defect',
        effect_vars={'amount':2},effects=[{'op':'gain_status','target':'self','status':'focus','amount':{'var':'amount'}}])

def create_capacity_potion():
    return PotionTemplate('potion.capacity','扩容药水','增加2个球槽。',quantity='uncommon',owner_character_id='character.defect',
        effects=[{'op':'defect_potion','action':'capacity'}])

def create_darkness_potion():
    return PotionTemplate('potion.essence_of_darkness','黑暗精华','每个球槽生成1个黑暗球。',quantity='rare',owner_character_id='character.defect',
        effects=[{'op':'defect_potion','action':'darkness'}])

DEFECT_POTION_REGISTRY = {'potion.focus':create_focus_potion,'potion.capacity':create_capacity_potion,'potion.essence_of_darkness':create_darkness_potion}
