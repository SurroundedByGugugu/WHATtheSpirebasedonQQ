"""Exclusive per-player combat stances, shared by cards and consumables."""
NAMES = {'none': '无', 'calm': '平静', 'wrath': '愤怒', 'divinity': '神格'}


def stance_of(player):
    return getattr(player, 'stance', 'none')


def attack_multiplier(source, target):
    outgoing = {'wrath': 2, 'divinity': 3}.get(stance_of(source), 1)
    return outgoing * (2 if stance_of(target) == 'wrath' else 1)


def change_stance(state, new_stance, player=None):
    from game.event_bus import dispatch_event
    from game.battle_context import BattleContext
    player = player or state.player
    if new_stance not in NAMES:
        raise ValueError('未知姿态：' + str(new_stance))
    old = stance_of(player)
    if old == new_stance:
        return []
    logs = []
    if old == 'calm':
        energy = 3 if any(r.relic_id == 'relic.violet_lotus' for r in player.relics) else 2
        player.cost += energy
        logs.append('离开平静，获得 {}c。'.format(energy))
    player.stance = new_stance
    player.divinity_expires_turn = state.turn_count + 1 if new_stance == 'divinity' else None
    if new_stance == 'divinity':
        player.cost += 3
        logs.append('进入神格，获得 3c。')
    logs.append('姿态：{} → {}。'.format(NAMES[old], NAMES[new_stance]))
    logs.extend(dispatch_event(state, 'stance_changed', BattleContext(
        game_state=state, player=player, source=player,
        extra={'old_stance': old, 'new_stance': new_stance})))
    return logs


def expire_divinity(state, player=None):
    player = player or state.player
    due = getattr(player, 'divinity_expires_turn', None)
    if stance_of(player) == 'divinity' and due is not None and state.turn_count >= due:
        return change_stance(state, 'none', player)
    return []


def gain_mantra(state, amount):
    player = state.player
    amount = max(0, int(amount))
    player.mantra_total = getattr(player, 'mantra_total', 0) + amount
    total = player.statuses.get('mantra') + amount
    player.statuses.set('mantra', total % 10)
    logs = ['获得 {} 层真言，当前 {}。'.format(amount, total % 10)]
    if total >= 10:
        logs.extend(change_stance(state, 'divinity'))
    return logs
