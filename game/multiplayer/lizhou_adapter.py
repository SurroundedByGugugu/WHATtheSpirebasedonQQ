"""Reuse the normal resumable combat runtime for 李昼 in the multiplayer room."""
from game.game_state import GameState
from game.resolution import resumable
from game.battle_context import BattleContext
from game.event_bus import dispatch_event


def combat(room, slot):
    state = getattr(slot, 'lizhou_combat', None)
    if state is None:
        state = GameState(room.session_id, slot.character_id, slot.player_state, room.battle.enemies)
        slot.lizhou_combat = state
        state.external_end_turn = lambda: end(room, slot)
    state.enemies = room.battle.enemies
    state.allied_players = [s.player_state for s in room.players if s.player_state is not None]
    return state


def command_text(text):
    return text.replace('/card pick', '/card multi pick').replace('/card skip', '/card multi skip')


@resumable()
def open_turn(state, opening=False):
    from game.engine import move_innate_cards_to_opening_hand, clear_turn_temporary_card_costs
    p = state.player
    if opening:
        yield dispatch_event(state, 'battle_start', BattleContext(game_state=state, player=p, source=p))
        yield move_innate_cards_to_opening_hand(p)
    else:
        state.turn_count += 1
        state.player_card_type_played_counts_this_turn = dict.fromkeys(('attack', 'skill', 'power', 'status', 'curse'), 0)
        clear_turn_temporary_card_costs(p)
        yield p.start_turn(state)
    yield dispatch_event(state, 'turn_start', BattleContext(game_state=state, player=p, source=p))
    yield p.draw_cards(max(0, 5-len(p.hand)) if opening else 5, state, draw_source='multi_turn_start')


def play(room, slot, index, target):
    from game.engine import play_card
    from game.multiplayer.engine import _check_battle_result, _sync_slot_from_player
    state = combat(room, slot)
    text = play_card(state, index, target)
    for member in room.players:
        _sync_slot_from_player(member)
    result = _check_battle_result(room)
    return command_text(text + ('\n'+result if result else ''))


def choose(room, user_id, indices):
    from game.multiplayer.engine import _active_slot, _check_battle_result
    from game.lizhou import choose_cards
    slot = _active_slot(room)
    if slot is None or str(slot.user_id) != str(user_id):
        return '还没轮到你行动。'
    state = combat(room, slot)
    text = choose_cards(state, indices)
    result = _check_battle_result(room)
    return command_text(text + ('\n'+result if result else ''))


@resumable(text=True)
def end_steps(state, room, slot):
    from game.engine import end_player_turn_hand_cleanup, decay_statuses_by_timing
    from game.lizhou import before_cleanup, after_cleanup
    from game.multiplayer.engine import end_player_turn
    if state.pending_choice is not None:
        return state.pending_choice.prompt
    yield dispatch_event(state, 'player_turn_end', BattleContext(game_state=state, player=state.player, source=state.player))
    yield before_cleanup(state)
    yield end_player_turn_hand_cleanup(state)
    yield after_cleanup(state)
    if getattr(state.player, 'lizhou_extra_turns', 0):
        state.player.lizhou_extra_turns -= 1
        yield dispatch_event(state, 'turn_end', BattleContext(game_state=state, player=state.player, source=state.player))
        yield decay_statuses_by_timing(state, 'turn_end')
        yield open_turn(state)
        return '获得额外回合，继续行动。'
    return end_player_turn(room, slot.user_id, _lizhou_cleaned=True)


def end(room, slot):
    return command_text(end_steps(combat(room, slot), room, slot))


def next_round(room, slot):
    state = combat(room, slot)
    # Enemy statuses are shared and decayed once by the room, player statuses per owner.
    logs = dispatch_event(state, 'turn_end', BattleContext(game_state=state, player=state.player, source=state.player))
    logs.extend(state.player.statuses.decay_by_timing('turn_end'))
    logs.extend(open_turn(state))
    return [command_text(line) for line in logs]
