from functools import partial
from data.potion.base_potion import PotionTemplate
LIZHOU_POTION_REGISTRY = {}
for key, name, text, target in [
    ('anchor_nails', '钉子药水', '选择任意张手牌各获得1层锚定。', 'self'),
    ('floating', '漂浮药水', '给予1名敌人5层浮动。', 'enemy'),
    ('star_sea', '星海之水', '获得6调序。', 'self'),
]:
    LIZHOU_POTION_REGISTRY['potion.'+key] = partial(PotionTemplate, potion_id='potion.'+key,
        name=name, description=text, target=target, owner_character_id='character.lizhou')
