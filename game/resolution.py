"""Ordered resumable combat steps. A choice pauses children before their parents."""
from collections import deque
from functools import wraps


def is_paused(state):
    choice = getattr(state, 'pending_choice', None)
    return choice is not None and choice.payload.get('pause_resolution', False)


def defer(state, step):
    if not hasattr(state, '_resolution_steps'):
        state._resolution_steps = deque()
    state._resolution_steps.append(step)


def run_steps(state, steps):
    logs = []
    steps = list(steps)
    for index, step in enumerate(steps):
        if is_paused(state):
            defer(state, lambda rest=steps[index:]: run_steps(state, rest))
            break
        result = step()
        if isinstance(result, str):
            logs.append(result)
        elif isinstance(result, (list, tuple)):
            logs.extend(result)
    return logs


def resume(state):
    logs = []
    queue = getattr(state, '_resolution_steps', deque())
    while queue and not is_paused(state):
        # Steps created by a resumed child must precede its waiting parents.
        step = queue.popleft()
        state._resolution_steps = deque()
        result = step()
        if isinstance(result, str):
            logs.append(result)
        elif result:
            logs.extend(result)
        state._resolution_steps.extend(queue)
        queue = state._resolution_steps
    return logs


def resumable(*, text=False, state_arg=0, state_kw='game_state'):
    """Drive a generator to its next choice; retain the exact continuation.

    Callers yield their accumulated logs after an operation that may pause.
    Nested continuations queue before their callers, including replay loops.
    These transient generators are intentionally not part of run save data.
    """
    def decorate(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            state = kwargs.get(state_kw, args[state_arg] if len(args) > state_arg else None)
            generator = function(*args, **kwargs)
            def drive():
                output = []
                while True:
                    try:
                        from game.generated_cards import combat_creation_state
                        token = combat_creation_state.set(state)
                        try:
                            chunk = next(generator)
                        finally:
                            combat_creation_state.reset(token)
                    except StopIteration as stop:
                        chunk = stop.value
                        if chunk:
                            output.extend([chunk] if isinstance(chunk, str) else chunk)
                        return output
                    if chunk:
                        output.extend([chunk] if isinstance(chunk, str) else chunk)
                    if state is not None and is_paused(state):
                        defer(state, drive)
                        return output
            output = drive()
            return '\n'.join(output) if text else output
        return wrapped
    return decorate
