"""角色调整的实际出牌、选择恢复与回合边界回归。"""
import copy
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.zones.element_zones import ElementZone
from game.damage import deal_damage
from game.engine import play_card, end_turn, choose_pending_element_plating, start_battle
from game.lizhou import anchor, before_cleanup, choose_cards, free, on_event
from game.battle_context import BattleContext
from game.yoirine import after_enemy_actions
from test_py_save.test_orbs import battle


def card(key, up=False):
    result = create_card('card.' + key)
    return upgrade_card(result) if up else result


def play(state, key, up=False):
    result = card(key, up)
    state.player.hand.insert(0, result)
    state.player.cost = 20
    text = play_card(state, 0, 0)
    assert '未知' not in text
    return result


@pytest.mark.parametrize('element', ['fire', 'water', 'wind', 'earth', 'crystal', 'shade'])
@pytest.mark.parametrize('extreme', [False, True])
def test_precipitate_destroys_any_real_zone(element, extreme):
    state, player = battle()
    state.active_zone = ElementZone(element, extreme, duration=2)
    play(state, 'precipitate')
    assert state.active_zone is None
    assert len(player.draw_pile) == (1 if element in ('crystal', 'shade') else 0)
    if player.draw_pile:
        assert player.draw_pile[0].upgraded == extreme
        assert player.draw_pile[0].card_id == ('card.crystal_plating' if element == 'crystal' else 'card.abyss_plating')


@pytest.mark.parametrize('zone_kind', ['none', 'virtual', 'expired'])
def test_precipitate_requires_real_live_zone(zone_kind):
    state, player = battle()
    if zone_kind != 'none':
        state.active_zone = ElementZone('crystal', zone_kind == 'expired', duration=0)
        state.active_zone.is_virtual_mist_zone = zone_kind == 'virtual'
    player.hand = [card('precipitate')]
    player.cost = 2
    play_card(state, 0)
    assert len(player.hand) == 1 and player.cost == 2


def test_dust_sums_block_once_per_turn_only_for_crystal_replay():
    state, player = battle()
    play(state, 'crystal_dust')
    play(state, 'crystal_dust', True)
    assert player.statuses.get('crystal_dust') == 5
    replayed = card('lizhou.defend')
    replayed.replay_extra = 1
    player.hand = [replayed]
    play_card(state, 0)
    assert player.block == 10
    player.block = 0
    state.active_zone = ElementZone('crystal')
    play(state, 'crystal_reflection')
    assert player.block == 14 + 5
    play(state, 'crystal_reflection')
    assert player.block == 28 + 5
    state.turn_count += 1
    player.block = 0
    play(state, 'crystal_reflection')
    assert player.block == 19


def test_reflection_runs_once_after_all_enemies_and_rounds_up():
    state, player = battle()
    state.enemies.append(copy.deepcopy(state.enemies[0]))
    state.active_zone = ElementZone('crystal')
    play(state, 'crystal_reflection')
    play(state, 'crystal_reflection', True)
    player.block = 20
    player.statuses.set('strength', 100)
    player.statuses.set('barricade', 1)
    observed = []

    def attack(s, enemy):
        observed.append(player.block)
        return deal_damage(s, enemy, player, 0)

    with patch('game.engine.process_enemy_action', side_effect=attack):
        text = end_turn(state)
    assert observed == [20, 20, 20]
    assert [e.hp for e in state.enemies] == [993, 993, 993]
    assert player.block == 0
    assert text.count('【晶面反射】失去') == 1


def test_reflection_requires_attack_not_hp_loss_and_expires():
    state, player = battle()
    play(state, 'crystal_reflection')
    deal_damage(state, player, player, 1, damage_kind='hp_loss', ignore_block=True)
    after_enemy_actions(state)
    assert player.block == 7
    deal_damage(state, state.enemies[0], player, 1)
    after_enemy_actions(state)
    assert player.block == 6
    assert all(e.hp == 1000 for e in state.enemies)


@pytest.mark.parametrize('element,up', [('crystal', False), ('shade', False), ('crystal', True)])
def test_phase_plating_costs_fixed_damage_and_filters_candidates(element, up):
    state, player = battle()
    state.active_zone = ElementZone(element)
    attack, skill, power = card('lizhou.strike'), card('lizhou.defend'), card('lizhou.human_dream')
    player.hand = [attack, skill, power, card('crystal_reflection')]
    player.statuses.set('strength', 100)
    played = play(state, 'phase_plating', up)
    assert player.hp == (94 if up else 90)
    assert played in player.exhaust_pile
    assert state.pending_choice.options == ([attack, skill] if element == 'crystal' else [attack])
    choose_pending_element_plating(state, 0)
    assert attack.attack_element == element


@pytest.mark.parametrize('up,expected', [(False, 6), (True, 8)])
def test_phase_plating_fallback(up, expected):
    state, player = battle()
    state.active_zone = ElementZone('fire')
    play(state, 'phase_plating', up)
    assert player.block == expected and player.hp == 100
    assert state.pending_choice is None


def test_flower_normal_draw_and_innate_opening_draw():
    state, player = battle()
    player.draw_pile = [card('lizhou.defend'), card('lizhou.star_flower')]
    player.draw_cards(1, state)
    assert len(player.hand) == 2
    state, text = start_battle('flower-test', 'character.lizhou', ['enemy.test_dummy'])
    assert len(state.player.hand) == 6
    assert any(c.card_id == 'card.lizhou.star_flower' for c in state.player.hand)


@pytest.mark.parametrize('up,maximum', [(False, 2), (True, 3)])
def test_warning_can_skip_and_still_resolves(up, maximum):
    state, player = battle()
    player.draw_pile = [card('lizhou.defend') for _ in range(5)]
    play(state, 'lizhou.star_warning', up)
    assert state.pending_choice.payload['minimum'] == 0
    assert state.pending_choice.payload['count'] == maximum
    choose_cards(state, [])
    assert player.statuses.get('lizhou_counterbalance') == 1
    assert state.enemies[0].hp == 994


def test_key_shuffles_discard_and_exhaust_but_not_hand():
    state, player = battle()
    drawn, held = card('lizhou.defend'), card('lizhou.strike')
    discarded, exhausted = card('lizhou.twinkle'), card('lizhou.align_stars')
    player.hand, player.draw_pile = [held], [drawn]
    player.discard_pile, player.exhaust_pile = [discarded], [exhausted]
    key = play(state, 'lizhou.key', True)
    choose_cards(state, [0])
    assert player.hand == [held, drawn]
    assert not player.exhaust_pile and not player.discard_pile
    assert {id(c) for c in player.draw_pile} == {id(key), id(discarded), id(exhausted)}
    assert player.draw_pile[0] is key


@pytest.mark.parametrize('up', [False, True])
def test_meteor_shower_generated_cards_survive_and_free_only_this_turn(up):
    state, player = battle()
    player.hand = [card('lizhou.defend')]
    with patch('game.lizhou.random.choice', return_value='aries'):
        play(state, 'lizhou.meteor_shower', up)
    generated = player.hand[0]
    assert generated.upgraded == up and 'exhaust' not in generated.keywords
    assert free(state, generated)
    play_card(state, 0)
    assert generated in player.discard_pile
    assert player.statuses.get('buffer') == (2 if up else 1)
    state.turn_count += 1
    assert not free(state, generated)


def test_intuition_discards_retained_cards_but_excludes_paid_anchor():
    state, player = battle()
    play(state, 'lizhou.intuition_luck')
    retained, paid, ordinary = [card('lizhou.defend') for _ in range(3)]
    retained.keywords.append('retain')
    paid.lizhou_anchor = 1
    player.hand = [retained, paid, ordinary]
    before_cleanup(state)
    choose_cards(state, [0])
    assert state.pending_choice.options == [retained]
    choose_cards(state, [0])
    assert retained in player.discard_pile and paid in player.hand
    assert paid.lizhou_anchor == 0 and paid.temporary_retain_once


def test_foresight_adds_layers_without_recursive_anchor_triggers():
    state, player = battle()
    play(state, 'lizhou.astronomic_foresight')
    play(state, 'lizhou.astronomic_foresight', True)
    play(state, 'lizhou.anchor_definition')
    target = card('lizhou.defend')
    anchor(state, target, 2)
    assert target.lizhou_anchor == 4
    assert player.statuses.get('lizhou_order') == 1
    assert player.block == 5
    anchor(state, target, -1)
    assert target.lizhou_anchor == 3 and player.block == 5
    assert player.statuses.get('lizhou_order') == 1


@pytest.mark.parametrize('up', [False, True])
def test_star_order_draws_without_order_gain_and_dream_scales(up):
    state, player = battle()
    player.draw_pile = [card('lizhou.defend') for _ in range(3)]
    play(state, 'lizhou.star_order', up)
    assert len(player.hand) == (2 if up else 1)
    assert player.block == (10 if up else 7)
    assert player.statuses.get('lizhou_order') == 0
    dream = play(state, 'lizhou.human_dream', up)
    assert 'retain' not in dream.keywords
    on_event(state, 'turn_start', BattleContext(game_state=state, player=player))
    assert player.statuses.get('strength') == (3 if up else 2)
    assert player.statuses.get('dexterity') == (3 if up else 2)


def test_relic_exclusions_and_yoirine_reward_replacement():
    from game.reward import get_available_relic_ids, get_available_boss_relic_ids, get_card_reward_pool
    from game.relic_logic.run_relic_utils import is_relic_available_by_floor
    from data.relic.AAAregistry import create_relic
    state = SimpleNamespace(character_id='character.lizhou', relics=[])
    excluded = {'relic.runic_pyramid', 'relic.ink_bottle', 'relic.letter_opener'}
    assert not excluded.intersection(get_available_relic_ids(state) + get_available_boss_relic_ids(state))
    for rid in excluded:
        assert not is_relic_available_by_floor(state, create_relic(rid))
        assert is_relic_available_by_floor(SimpleNamespace(character_id='character.yoirine'), create_relic(rid))
    ids = get_card_reward_pool(SimpleNamespace(character_id='character.yoirine', relics=[]))
    assert 'card.crystal_mist' not in ids
    assert {'card.crystal_dust', 'card.phase_plating'} <= set(ids)


def test_multiplayer_flower_and_relic_restrictions():
    from test_py_save.test_lizhou import multi_room
    from game.multiplayer.engine import _multi_relic_candidates, choose_relic
    from game.multiplayer.state import MultiRewardState, ROOM_STATUS_REWARD
    from data.relic.AAAregistry import create_relic
    _, room = multi_room()
    lizhou = room.get_player('a')
    assert len(lizhou.player_state.hand) == 6
    room.status = ROOM_STATUS_REWARD
    room.reward = MultiRewardState(0, relic_options=[create_relic('relic.ink_bottle')])
    assert '不适用于李昼' in choose_relic(room, 'a', 0)
    assert 'a' not in room.reward.relic_choices
    assert 'relic.ink_bottle' in _multi_relic_candidates(room)
    room.get_player('b').character_id = 'character.lizhou'
    assert 'relic.ink_bottle' not in _multi_relic_candidates(room)


def test_crystal_turn_markers_do_not_leak_between_battles():
    from game.game_state import GameState
    from game.yoirine import after_crystal_replay
    state, player = battle()
    player.statuses.set('crystal_dust', 2)
    after_crystal_replay(state)
    assert player.block == 2
    next_battle = GameState('next', 'test', player, state.enemies)
    after_crystal_replay(next_battle)
    assert player.block == 4


@pytest.mark.parametrize('up,expected', [(False, 4), (True, 7)])
@pytest.mark.parametrize('hand_size', [0, 1, 3])
def test_swallow_star_exhausts_two_or_remaining_hand_before_block(up, expected, hand_size):
    state, player = battle()
    player.hand = [card('lizhou.defend') for _ in range(hand_size)]
    play(state, 'lizhou.swallow_star', up)
    if hand_size:
        assert player.block == 0
        choose_cards(state, list(range(min(2, hand_size))))
    assert len(player.exhaust_pile) == min(2, hand_size)
    assert player.block == expected
