from data.card.base_card import CardTemplate


def create_recrystallization():
    return CardTemplate('card.recrystallization', '重结晶', 'skill', 1, 'self',
                        '选择1张消耗堆以外的牌添加保留。消耗。', 'event', attack_element='earth',
                        effects=[{'op': 'crystal_expansion', 'action': 'retain', 'count': 1}], keywords=['exhaust'],
                        upgrade_patch={'name': '重结晶+', 'description': '选择2张消耗堆以外的牌添加保留。消耗。',
                                       'effects': [{'op': 'crystal_expansion', 'action': 'retain', 'count': 2}]})


def create_autocrystallization():
    text = '回合结束时，若剩余能量至少为2，记录剩余能量X；下回合开始时将1张充盈晶体加入手牌。该状态无法叠加。'
    return CardTemplate('card.autocrystallization', '自成结晶', 'power', 1, 'self', text, 'rare',
                        attack_element='earth', owner_character_id='character.yoirine',
                        effects=[{'op': 'crystal_expansion', 'action': 'power'}],
                        upgrade_patch={'name': '自成结晶+', 'cost': 0})


def create_full_crystal():
    return CardTemplate('card.full_crystal', '充盈晶体', 'skill', 0, 'self',
                        '获得⌊X/2⌋点能量。消耗。', 'event', attack_element='earth',
                        card_vars={'stored_energy': 0}, keywords=['exhaust'],
                        effects=[{'op': 'crystal_expansion', 'action': 'energy'}])


def create_overcharge():
    text = ('消耗。晶 Zone 下费用-1。消耗手牌、抽牌堆、弃牌堆的全部充盈晶体，'
            '对所有敌人造成{}点伤害X次，X为这些晶体能提供的能量总和。'
            '若没有充盈晶体，改为获得1张记录本牌实际消耗费用的充盈晶体。不会因晶效果重放。')
    return CardTemplate('card.overcharge', '过充', 'skill', 2, 'all_enemies', text.format(3), 'uncommon',
                        attack_element='crystal', owner_character_id='character.yoirine', ignore_zone_replay=True,
                        card_vars={'damage': 3}, keywords=['exhaust'],
                        cost_rules=[{'op': 'reduce_if_active_zone', 'element': 'crystal', 'amount': 1}],
                        effects=[{'op': 'crystal_expansion', 'action': 'overcharge'}],
                        upgrade_patch={'name': '过充+', 'description': text.format(4), 'card_vars': {'damage': 4}})


CRYSTAL_CARD_REGISTRY = {
    'card.recrystallization': create_recrystallization,
    'card.autocrystallization': create_autocrystallization,
    'card.full_crystal': create_full_crystal,
    'card.overcharge': create_overcharge,
}
