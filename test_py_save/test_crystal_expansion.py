import pytest

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.relic.AAAregistry import create_relic
from data.zones.element_zones import ElementZone
from game.crystal_expansion import add_crystal, choose_retain, crystal_energy
from game.effects import apply_card_effects
from game.engine import play_card, end_turn
from game.event_bus import dispatch_event
from test_py_save.test_abyss_combat_regressions import make_battle, strike


@pytest.mark.parametrize('upgraded', [False, True])
@pytest.mark.parametrize('extreme', [False, True])
def test_shade_power_hp_rules(upgraded, extreme):
    for cid, status, expected in [('phantom_form', 'phantom_form', 1),
                                  ('abyss_hunt', 'abyss_hunt', 2 if upgraded else 1),
                                  ('abyss_symbiosis', 'abyss_symbiosis', 4 if upgraded else 3),
                                  ('shadow_crystallization', 'shadow_crystallization',
                                   int((6 if upgraded else 4) * (2 if extreme else 1.5)))]:
        game = make_battle()
        game.active_zone = ElementZone('shade', is_extreme=extreme, duration=3)
        card = create_card('card.' + cid)
        if upgraded:
            card = upgrade_card(card)
        apply_card_effects(game, card, None, {'x': 3})
        assert game.player.statuses.get(status) == expected
        assert game.player.hp == (95 if cid == 'shadow_crystallization' else 100)


@pytest.mark.parametrize('upgraded', [False, True])
@pytest.mark.parametrize('zone', [None, 'shade'])
def test_fleeting_shadow_fixed_loss(upgraded, zone):
    game = make_battle()
    game.player.draw_pile = [create_card('card.defend_yoirine') for _ in range(6)]
    game.active_zone = ElementZone(zone, duration=3) if zone else None
    card = create_card('card.fleeting_shadow')
    if upgraded:
        card = upgrade_card(card)
    assert card.attack_element == ''
    apply_card_effects(game, card, None)
    assert game.player.hp == 99
    assert len(game.player.hand) == (4 if upgraded else 3)


def test_form_upgrade_and_cross_replay_hp():
    game = make_battle()
    card = upgrade_card(create_card('card.abyssal_form'))
    assert card.cost == 3
    apply_card_effects(game, card, None)
    assert game.player.block == 8
    game.active_zone = ElementZone('shade', duration=3)
    attack = strike('crystal')
    attack.replay_extra = 1
    apply_card_effects(game, attack, 0)
    assert game.player.hp == 91
    assert game.enemies[0].hp == 970


@pytest.mark.parametrize('upgraded', [False, True])
def test_recrystallization_pauses_and_selects_non_exhaust_piles(upgraded):
    game = make_battle()
    card = create_card('card.recrystallization')
    if upgraded:
        card = upgrade_card(card)
    candidates = [create_card('card.defend_yoirine') for _ in range(4)]
    game.player.hand = [card, candidates[0]]
    game.player.draw_pile = [candidates[1]]
    game.player.discard_pile = [candidates[2]]
    game.player.exhaust_pile = [candidates[3]]
    play_card(game, 0)
    assert len(game.pending_choice.options) == 3
    from web.bridge import battle_selection
    selection = battle_selection(game)
    assert selection['minimum'] == selection['maximum'] == (2 if upgraded else 1)
    choose_retain(game, [0, 2] if upgraded else [2])
    assert game.pending_choice is None
    assert 'retain' in candidates[2].keywords
    assert ('retain' in candidates[0].keywords) == upgraded
    assert 'retain' not in candidates[3].keywords
    assert any(item is card for item in game.player.exhaust_pile)


@pytest.mark.parametrize('energy', [1, 2, 5])
def test_power_records_remaining_energy_and_generates_next_turn(energy):
    game = make_battle()
    power = create_card('card.autocrystallization')
    apply_card_effects(game, power, None)
    apply_card_effects(game, power, None)
    assert game.player.statuses.get('autocrystallization') == 1
    game.player.cost = energy
    end_turn(game)
    crystals = [c for c in game.player.hand if c.card_id == 'card.full_crystal']
    assert len(crystals) == (1 if energy >= 2 else 0)
    if crystals:
        assert crystals[0].card_vars['stored_energy'] == energy
        before = game.player.cost
        play_card(game, game.player.hand.index(crystals[0]))
        assert game.player.cost == before + energy // 2
        assert any(c is crystals[0] for c in game.player.exhaust_pile)
    dispatch_event(game, 'turn_start')
    assert not any(c.card_id == 'card.full_crystal' for c in game.player.hand)


@pytest.mark.parametrize('zone,free,stored', [(None, False, 2), ('crystal', False, 1), (None, True, 0)])
def test_overcharge_fallback_uses_actual_paid_cost(zone, free, stored):
    game = make_battle()
    game.active_zone = ElementZone(zone, duration=3) if zone else None
    card = create_card('card.overcharge')
    if free:
        game.player.statuses.set('corruption', 1)
    game.player.hand = [card]
    play_card(game, 0)
    assert len(game.player.hand) == 1
    crystal = game.player.hand[0]
    assert crystal.card_vars['stored_energy'] == stored
    assert crystal_energy(crystal) == stored // 2
    assert game.enemies[0].hp == 1000


@pytest.mark.parametrize('upgraded', [False, True])
def test_overcharge_consumes_all_piles_without_zone_replay(upgraded):
    game = make_battle()
    game.active_zone = ElementZone('crystal', duration=3)
    game.enemies.append(make_battle().enemies[0])
    card = create_card('card.overcharge')
    if upgraded:
        card = upgrade_card(card)
    game.player.hand = [card]
    for name, energy in [('hand', 5), ('draw_pile', 6), ('discard_pile', 1)]:
        crystal = create_card('card.full_crystal')
        crystal.card_vars['stored_energy'] = energy
        getattr(game.player, name).append(crystal)
    play_card(game, 0)
    assert not game.player.hand and not game.player.draw_pile and not game.player.discard_pile
    assert len(game.player.exhaust_pile) == 4
    assert [e.hp for e in game.enemies] == [1000 - 5 * (4 if upgraded else 3)] * 2


def test_zero_energy_crystal_is_consumed_without_fallback():
    game = make_battle()
    add_crystal(game, 1)
    apply_card_effects(game, create_card('card.overcharge'), None, {'spent_cost': 2})
    assert not game.player.hand
    assert len(game.player.exhaust_pile) == 1
    assert game.enemies[0].hp == 1000


def test_relic_and_content_pools():
    from game.run_state import RunState
    from game.reward import CARD_REWARD_POOL, RELIC_REWARD_POOL
    from data.content_gate import private_content_session, set_private_content_enabled, is_content_enabled
    run = RunState('test:granite', 'character.ironclad')
    create_relic('relic.warm_granite').on_obtained(run)
    assert run.master_deck[-1].card_id == 'card.recrystallization'
    assert 'card.recrystallization' not in CARD_REWARD_POOL
    assert 'card.full_crystal' not in CARD_REWARD_POOL
    assert 'relic.warm_granite' in RELIC_REWARD_POOL
    assert upgrade_card(create_card('card.autocrystallization')).cost == 0
    set_private_content_enabled(False, run.session_id)
    try:
        with private_content_session(run.session_id):
            for cid in ['recrystallization', 'full_crystal', 'autocrystallization', 'overcharge']:
                assert not is_content_enabled('card', 'card.' + cid)
            assert not is_content_enabled('relic', 'relic.warm_granite')
    finally:
        set_private_content_enabled(True, run.session_id)
