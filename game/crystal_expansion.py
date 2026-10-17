"""Stored energy crystals and non-exhaust-pile retention choices."""
from game.resolution import resumable


def crystal_energy(card):
    return max(0, int(card.card_vars.get('stored_energy', 0))) // 2


def add_crystal(state, energy):
    from data.card.AAAregistry import create_card
    from game.defect import put_in_hand
    card = create_card('card.full_crystal')
    card.card_vars['stored_energy'] = max(0, int(energy))
    card.description = '记录X={}，获得{}点能量。消耗。'.format(card.card_vars['stored_energy'], crystal_energy(card))
    logs = []
    put_in_hand(state, card, logs)
    return logs


def on_event(state, event):
    if state.battle_over or not state.player.is_alive():
        return []
    if event == 'player_turn_end' and state.player.statuses.get('autocrystallization'):
        state.crystal_energy_pending = state.player.cost if state.player.cost >= 2 else None
        return ['自成结晶：记录剩余能量{}。'.format(state.player.cost)] if state.crystal_energy_pending is not None else []
    if event == 'turn_start':
        stored = getattr(state, 'crystal_energy_pending', None)
        state.crystal_energy_pending = None
        if stored is not None:
            return add_crystal(state, stored)
    return []


@resumable()
def resolve(state, card, spec, target_index, context):
    from game.effects import apply_card_effect
    player = state.player
    action = spec['action']
    if action == 'power':
        player.statuses.set('autocrystallization', 1)
        return ['自成结晶生效（不叠加）。']
    if action == 'energy':
        return apply_card_effect(state, card, {'op': 'gain_energy', 'amount': crystal_energy(card)}, None, context)
    if action == 'retain':
        from game.pending_choice import PendingChoice, enqueue_pending_choice
        options = [dict(pile_name=name, pile_label=label, card=item)
                   for name, label in [('hand', '手牌'), ('draw_pile', '抽牌堆'), ('discard_pile', '弃牌堆')]
                   for item in getattr(player, name)
                   if item is not card and 'retain' not in item.keywords]
        count = min(spec['count'], len(options))
        if not count:
            return ['没有可添加保留的牌。']
        prompt = '重结晶：选择{}张牌添加保留，使用 /card pick 编号。\n'.format(count)
        prompt += '\n'.join('[{}] {}：{}'.format(i, item['pile_label'], item['card'].name) for i, item in enumerate(options))
        enqueue_pending_choice(state, PendingChoice(kind='crystal_retain', source=card.name, prompt=prompt,
                               options=options, payload={'count': count, 'pause_resolution': True}))
        return [prompt]
    if action == 'overcharge':
        crystals = [(pile, item) for pile in ('hand', 'draw_pile', 'discard_pile')
                    for item in list(getattr(player, pile)) if item.card_id == 'card.full_crystal']
        if not crystals:
            return add_crystal(state, context.get('spent_cost', 0))
        repeats = sum(crystal_energy(item) for _, item in crystals)
        from game.engine import move_card_to_exhaust_pile
        for _, item in crystals:
            # Exhaust listeners may draw or move a later crystal between piles.
            location = next(((getattr(player, name), i)
                             for name in ('hand', 'draw_pile', 'discard_pile')
                             for i, value in enumerate(getattr(player, name)) if value is item), None)
            if location is None:
                continue
            pile, index = location
            pile.pop(index)
            yield move_card_to_exhaust_pile(state, item, reason='过充')
            if state.battle_over or not player.is_alive():
                return []
        yield ['过充：总能量{}，对全体造成{}次伤害。'.format(repeats, repeats)]
        for _ in range(repeats):
            if state.battle_over or not player.is_alive():
                break
            yield apply_card_effect(state, card, {'op': 'deal_damage_all_enemies', 'target': 'all_enemies',
                                    'amount': {'base_var': 'damage', 'modifier_profile': 'attack_damage'}}, None, context)
    return []


def choose_retain(state, indices):
    from game.pending_choice import get_pending_choice, clear_pending_choice
    choice = get_pending_choice(state)
    if choice is None or choice.kind != 'crystal_retain':
        return '当前没有重结晶选择。'
    if len(indices) != choice.payload['count'] or len(set(indices)) != len(indices) or any(i < 0 or i >= len(choice.options) for i in indices):
        return choice.prompt
    selected = [choice.options[i] for i in indices]
    if any(not any(c is item['card'] for c in getattr(state.player, item['pile_name'])) for item in selected):
        return '选项已变化，请重新选择。'
    logs = []
    for item in selected:
        card = item['card']
        if 'retain' not in card.keywords:
            card.keywords.append('retain')
        logs.append('【{}】获得保留。'.format(card.name))
    clear_pending_choice(state, 'crystal_retain')
    from game.resolution import resume
    logs.extend(resume(state))
    return '\n'.join(logs)
