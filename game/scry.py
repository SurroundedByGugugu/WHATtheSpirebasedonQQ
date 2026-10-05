"""Scry moves selected draw-pile instances without hand-discard triggers."""
from game.pending_choice import PendingChoice, enqueue_pending_choice, get_pending_choice, clear_pending_choice


def complete_scry(state, cards):
    from game.event_bus import dispatch_event
    from game.battle_context import BattleContext
    return dispatch_event(state, 'scry_finished', BattleContext(
        game_state=state, player=state.player, source=state.player,
        extra={'discarded_cards': cards, 'discarded_count': len(cards)}))


def request_scry(state, count, source='预见'):
    count = max(0, int(count))
    if count == 0:
        return []
    if any(r.relic_id == 'relic.golden_eye' for r in state.player.relics):
        count += 2
    cards = list(reversed(state.player.draw_pile[-count:]))
    if not cards:
        return ['抽牌堆为空，预见结束。'] + complete_scry(state, [])
    prompt = '{}：预见 {}。选择置入弃牌堆的牌，其余保持顺序。\n'.format(source, len(cards))
    prompt += '\n'.join('[{}] {}{}'.format(i, c.summary_text(), ' ← 牌堆顶' if i == 0 else '') for i,c in enumerate(cards))
    prompt += '\n/card scry 0 2；全部保留：/card scry skip'
    enqueue_pending_choice(state, PendingChoice(kind='scry', source=source, prompt=prompt,
        options=cards, payload={'pause_resolution': True}))
    return [prompt]


def choose_scry(state, indices):
    choice = get_pending_choice(state)
    if choice is None or choice.kind != 'scry':
        return '当前没有预见选择。'
    if len(indices) != len(set(indices)) or any(i < 0 or i >= len(choice.options) for i in indices):
        return '请提供不重复的有效预见编号。\n' + choice.prompt
    pile = state.player.draw_pile
    if any(not any(c is item for item in pile) for c in choice.options):
        return '牌堆已变化，不能提交过期的预见选项。'
    cards = [c for i,c in enumerate(choice.options) if i in indices]
    for card in cards:
        pile.pop(next(i for i,c in enumerate(pile) if c is card))
        state.player.discard_pile.append(card)
    clear_pending_choice(state, 'scry')
    logs = ['预见完成：{}。'.format('、'.join(c.name for c in cards) + '进入弃牌堆' if cards else '全部保留')]
    logs.extend(complete_scry(state, cards))
    from game.resolution import resume
    logs.extend(resume(state))
    return '\n'.join(logs)
