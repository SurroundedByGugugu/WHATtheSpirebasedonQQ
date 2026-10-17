"""Software shop curses; Enthralled follows STS2's 2-energy, priority-play rule."""
from data.card.base_card import CardTemplate
from game.constants import KEYWORD_UNPLAYABLE, KEYWORD_ETHEREAL


def create_enthralled():
    card = CardTemplate('card.curse.enthralled', '执迷', 'curse', 2, 'none',
                        '如果这张牌在手牌中，必须优先打出它。永恒（无法从牌组移除或变化）。', 'curse')
    card.unremovable = True
    card.untransformable = True
    return card


def create_clumsy():
    return CardTemplate('card.curse.clumsy', '笨拙', 'curse', 0, 'none',
                        '无法打出。虚无。', 'curse', keywords=[KEYWORD_UNPLAYABLE, KEYWORD_ETHEREAL])


def create_region_lock():
    return CardTemplate('card.curse.region_lock', '锁区', 'curse', 0, 'none',
                        '当这张牌在手牌中时，不能抽牌。无法打出。', 'curse', keywords=[KEYWORD_UNPLAYABLE])
