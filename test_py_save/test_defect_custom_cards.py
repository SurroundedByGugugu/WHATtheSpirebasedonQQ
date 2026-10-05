import pytest

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.enemy.base_enemy import EnemyIntent
from data.enemy.pattern_enemy import PatternEnemy
from game.defect import choose_cards
from game.engine import end_turn, play_card
from game.event_bus import dispatch_event
from game.game_state import GameState
from game.orbs import channel, rack
from game.player_state import PlayerState


def battle():
    player = PlayerState('character.defect', '机器人', 100, 100, 3, 3)
    enemy = PatternEnemy('enemy.test', '目标', 1000, [EnemyIntent(kind='wait')])
    state = GameState('custom-defect', player.character_id, player, [enemy])
    rack(player).capacity = 3
    return state, player


def play(state, key, upgraded=False):
    card = create_card('card.' + key)
    if upgraded:
        card = upgrade_card(card)
    state.player.hand.insert(0, card)
    state.player.cost = 10
    return card, play_card(state, 0, 0)


@pytest.mark.parametrize('upgraded,cost', [(False, 1), (True, 0)])
def test_machine_rush_power_persists_and_stacks(upgraded, cost):
    state, player = battle()
    card, _ = play(state, 'machine_rush', upgraded)
    assert card.name == '猛机下山！' + ('+' if upgraded else '')
    assert card.card_type == 'power' and card.cost == cost and card.quantity == 'uncommon'
    play(state, 'machine_rush')
    player.draw_pile = [create_card('card.claw') for _ in range(10)]
    channel(state, player, 'frost', 2)
    assert len(player.hand) == 4
    dispatch_event(state, 'turn_end')
    channel(state, player, 'plasma')
    assert len(player.hand) == 6
    assert player.statuses.get('machine_rush') == 2


@pytest.mark.parametrize('kind', ['lightning', 'frost', 'dark', 'plasma', 'glass'])
def test_machine_rush_all_orb_types(kind):
    state, player = battle()
    play(state, 'machine_rush')
    player.draw_pile = [create_card('card.claw')]
    channel(state, player, kind)
    assert len(player.hand) == 1


def test_machine_rush_requires_successful_channel_and_respects_no_draw():
    state, player = battle()
    play(state, 'machine_rush')
    player.draw_pile = [create_card('card.claw')]
    rack(player).capacity = 0
    channel(state, player, 'frost')
    assert not player.hand
    rack(player).capacity = 1
    player.statuses.set('no_draw', 1)
    channel(state, player, 'frost')
    assert not player.hand and len(player.draw_pile) == 1


@pytest.mark.parametrize('upgraded,multiplier', [(False, 3), (True, 4)])
@pytest.mark.parametrize('selected,total', [(0, 3), (1, 6), (2, 9), (3, 7)])
def test_convolution_uses_selected_card_and_immediate_neighbors(upgraded, multiplier, selected, total):
    state, player = battle()
    cards = [create_card('card.claw') for _ in range(4)]
    for cost, card in enumerate(cards, 1):
        card.cost = cost
    player.hand = list(cards)
    play(state, 'convolutional_neural_network', upgraded)
    assert state.pending_choice.kind == 'defect_select'
    choose_cards(state, [selected])
    assert player.block == total * multiplier
    assert all(actual is expected for actual, expected in zip(player.hand, cards))
    assert len(player.hand) == 4 and state.pending_choice is None


def test_convolution_current_cost_x_cost_and_block_modifiers():
    state, player = battle()
    left = create_card('card.meteor_strike')
    left.temporary_cost_override = 0
    center = create_card('card.tempest')
    right = create_card('card.claw')
    right.cost = -1
    player.hand = [create_card('card.convolutional_neural_network'), left, center, right]
    player.cost = 3
    player.statuses.set('dexterity', 2)
    player.statuses.set('frail', 1)
    play_card(state, 0)
    choose_cards(state, [1])
    assert player.cost == 2
    assert player.block == 6  # (剩余能量2 × 3 + 敏捷2) × 脆弱0.75


def test_convolution_empty_hand_and_replayed_choices():
    state, player = battle()
    _, reply = play(state, 'convolutional_neural_network')
    assert '没有可选择的牌' in reply and state.pending_choice is None
    player.hand = [create_card('card.defend_defect')]
    player.statuses.set('burst', 1)
    play(state, 'convolutional_neural_network')
    assert not state.pending_choice_queue  # The second resolution has not started yet.
    choose_cards(state, [0])
    choose_cards(state, [0])
    assert player.block == 6 and len(player.hand) == 1


@pytest.mark.parametrize('upgraded,count', [(False, 5), (True, 6)])
def test_transformer_matching_draw_and_total_count(upgraded, count):
    state, player = battle()
    play(state, 'transformer', upgraded)
    play(state, 'claw')
    matching = create_card('card.claw')
    player.draw_pile = [matching] + [create_card('card.defend_defect') for _ in range(12)]
    end_turn(state)
    assert len(player.hand) == count
    assert player.hand[0] is matching
    assert player.statuses.get('transformer_plus' if upgraded else 'transformer') == 1


def test_transformer_tracks_each_turn_and_does_not_reuse_an_idle_turn():
    state, player = battle()
    play(state, 'transformer')
    play(state, 'claw')
    for last_key, expected in [('defend_defect', 'skill'), ('claw', 'attack')]:
        play(state, last_key)
        matching = create_card('card.' + last_key)
        player.draw_pile = [matching] + [create_card('card.capacitor') for _ in range(10)]
        end_turn(state)
        assert player.hand[0] is matching and matching.card_type == expected
    # 本回合不出牌，下回合不沿用更早的攻击类型。
    top = create_card('card.defend_defect')
    player.draw_pile = [create_card('card.claw') for _ in range(10)] + [top]
    end_turn(state)
    assert player.hand[0] is top


@pytest.mark.parametrize('upgraded,count', [(False, 5), (True, 5)])
def test_transformer_without_matching_type_falls_back_or_skips_bonus(upgraded, count):
    state, player = battle()
    play(state, 'transformer', upgraded)
    play(state, 'claw')
    player.draw_pile = [create_card('card.defend_defect') for _ in range(10)]
    end_turn(state)
    assert len(player.hand) == count
    assert all(card.card_type == 'skill' for card in player.hand)


def test_transformer_first_draw_only_and_reshuffle():
    state, player = battle()
    play(state, 'transformer')
    play(state, 'claw')
    state.turn_count += 1
    first, second = create_card('card.claw'), create_card('card.claw')
    top = create_card('card.defend_defect')
    player.draw_pile = [first, second, top]
    player.draw_cards(2, state)
    assert player.hand == [second, top]
    player.hand.clear()
    player.draw_pile.clear()
    player.discard_pile = [first, top]
    state.defect_first_draw_turn = 1
    player.draw_cards(1, state)
    assert player.hand[0] is first


def test_transformer_plus_multiple_copies_and_power_as_last_type():
    state, player = battle()
    play(state, 'transformer', True)
    play(state, 'transformer', True)
    powers = [create_card('card.capacitor'), create_card('card.loop')]
    player.draw_pile = powers + [create_card('card.claw') for _ in range(10)]
    end_turn(state)
    assert len(player.hand) == 7
    assert all(card.card_type == 'power' for card in player.hand[:2])


def test_transformer_does_not_reorder_draws_on_the_turn_it_is_played():
    state, player = battle()
    play(state, 'claw')
    state.turn_count = 2
    play(state, 'transformer')
    top = create_card('card.defend_defect')
    player.draw_pile = [create_card('card.claw'), top]
    player.draw_cards(1, state)
    assert player.hand[0] is top
