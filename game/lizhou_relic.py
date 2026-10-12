"""十二星座卡牌的长期牌组选择；与战斗中生成牌无关。"""
import random
from game.lizhou import key, PREFIX
from data.card.character.lizhou_cards import ZODIACS


def duplicates(run, card_id, upgraded):
    return [c for c in run.master_deck if c.card_id == card_id and c.upgraded == upgraded]


def check_gain(run, card):
    if key(card) not in ZODIACS or not any(r.relic_id == 'relic.twelve_zodiacs' for r in run.relics):
        return []
    if len(duplicates(run, card.card_id, card.upgraded)) < 2:
        return []
    if not hasattr(run, 'lizhou_zodiac_choices'):
        run.lizhou_zodiac_choices = []
    run.lizhou_zodiac_choices.append((card.card_id, card.upgraded))
    return [format_choice(run)]


def options(run):
    queue = getattr(run, 'lizhou_zodiac_choices', [])
    while queue:
        choices = duplicates(run, *queue[0])
        if len(choices) >= 2:
            return choices
        queue.pop(0)
    return []


def format_choice(run):
    cards = options(run)
    if not cards:
        return ''
    return '十二星座卡牌：选择一张重复牌随机转换，/card zodiac 编号；/card zodiac skip 放弃。\n' + '\n'.join(
        '[{}] {}（牌组位置{}）'.format(i, c.name, next(j for j, d in enumerate(run.master_deck) if d is c))
        for i, c in enumerate(cards))


def choose(run, index=None):
    cards = options(run)
    if not cards:
        return '当前没有星座转换。'
    if index is not None and not 0 <= index < len(cards):
        return '编号无效。\n'+format_choice(run)
    run.lizhou_zodiac_choices.pop(0)
    if index is None:
        return '已放弃本次星座转换。\n'+format_choice(run)
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card
    old = cards[index]
    new = create_card(PREFIX+random.choice(ZODIACS))
    if old.upgraded:
        new = upgrade_card(new)
    if hasattr(old, 'master_card_uid'):
        new.master_card_uid = old.master_card_uid
    i = next(i for i, c in enumerate(run.master_deck) if c is old)
    run.master_deck[i] = new
    if len(duplicates(run, new.card_id, new.upgraded)) >= 2:
        run.lizhou_zodiac_choices.insert(0, (new.card_id, new.upgraded))
    return '【{}】转换为【{}】。\n{}'.format(old.name, new.name, format_choice(run))
