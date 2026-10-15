from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from test_py_save.test_orbs import battle
from test_py_save.test_lizhou import card, play, finish
from data.card.AAAregistry import CARD_REGISTRY, create_card
from data.relic.AAAregistry import create_relic
from data.potion.AAAregistry import create_potion
from data.enemy.AAAregistry import create_enemy
from game.engine import play_card, end_turn, use_potion, choose_pending_potion_card, apply_turn_start_hand_ready_effects, process_enemy_action
from game.event_bus import dispatch_event
from game.battle_context import BattleContext
from game.damage import deal_damage
from game.lizhou import anchor, choose_cards
from game.card_cost import get_card_current_cost
from game.zone.zone_utils import tick_zone_turn_end


def test_removed_cards_and_retained_cards():
    for key in ('human_dream', 'infinity_void', 'star_sequence', 'moonlight'):
        assert 'card.lizhou.'+key not in CARD_REGISTRY
    for key in ('collision', 'aye_captain'):
        assert 'retain' in card(key).keywords and 'retain' in card(key, True).keywords


def test_random_remove_filters_and_does_not_charge_when_none():
    from game.node.node_shop import random_remove_card
    from game.deck_utils import remove_card_from_master_deck
    # Minimal shop state is enough for the no-candidate case.
    run = SimpleNamespace(master_deck=[card('star_flower')], pending_shop=SimpleNamespace(remove_used=False), gold=999, relics=[], card_remove_price=50)
    assert remove_card_from_master_deck(run, 0)[0] is None
    assert '没有可以删除' in random_remove_card(run)
    assert run.gold == 999 and not run.pending_shop.remove_used


def test_armor_timing_for_both_sides():
    state, p = battle()
    enemy = state.enemies[0]
    p.statuses.set('plated_armor', 4)
    enemy.statuses.set('plated_armor', 3)
    ctx = BattleContext(state, player=p)
    dispatch_event(state, 'turn_start', ctx)
    assert p.block == enemy.block == 0
    dispatch_event(state, 'player_turn_end', ctx)
    assert p.block == 4 and enemy.block == 0
    dispatch_event(state, 'turn_end', ctx)
    assert p.block == 4 and enemy.block == 3


def test_champ_immediate_burst_and_once_only():
    state, p = battle()
    enemy = create_enemy('enemy.champ')
    state.enemies = [enemy]
    enemy.get_current_intent()
    deal_damage(state, p, enemy, 211)
    assert enemy.get_current_intent().kind == 'champ_burst'
    enemy.statuses.set('weak', 3)
    process_enemy_action(state, enemy)
    assert enemy.statuses.get('weak') == 0 and enemy.statuses.get('strength') == 6
    assert enemy.get_current_intent().kind == 'attack'


def test_nemesis_never_repeats_burn():
    enemy = create_enemy('enemy.nemesis')
    enemy._history = ['a']
    for _ in range(100):
        assert enemy._choose_key() != 'a'


def test_anchor_extra_damage_and_floating_blocked_attack():
    state, p = battle()
    enemy = state.enemies[0]
    enemy.statuses.set('enemy_anchor', 3)
    deal_damage(state, p, enemy, 6)
    assert enemy.hp == 991
    enemy.statuses.set('enemy_floating', 2)
    p.block = 10
    p.draw_pile = [card('defend'), card('defend')]
    deal_damage(state, enemy, p, 5)
    assert len(p.hand) == 1 and enemy.statuses.get('enemy_floating') == 1
    deal_damage(state, enemy, p, 9)
    assert len(p.hand) == 1 and enemy.statuses.get('enemy_floating') == 1


def test_domain_upgrade_duration_and_no_recursive_plays():
    from data.zones.star_zone import deploy_star
    state, p = battle()
    deploy_star(state)
    assert not state.active_zone.is_extreme and state.active_zone.duration == 3
    tick_zone_turn_end(state)
    assert state.active_zone.duration == 2
    deploy_star(state)
    assert state.active_zone.is_extreme and state.active_zone.duration == 3
    deploy_star(state, True)
    assert state.active_zone.duration == 5
    with patch('random.choice', return_value='aries'):
        play(state, 'defend')
    assert p.statuses.get('buffer') == 2
    for _ in range(5):
        tick_zone_turn_end(state)
    assert state.active_zone is None


def test_focus_discount_per_anchor_event_and_star_sea():
    state, p = battle()
    c = card('focus')
    p.draw_pile = [card('defend') for _ in range(8)]
    anchor(state, c, 5)
    p.hand = [c]
    p.statuses.set('lizhou_order', 1)
    p.cost = 0
    play_card(state, 0)
    assert len(p.hand) == 4 and p.cost == 1 and p.statuses.get('lizhou_order') == 0
    p.statuses.set('lizhou_order', 3)
    play(state, 'star_sea')
    p.statuses.set('strength', 0)
    p.statuses.set('dexterity', 0)
    c = card('collision')
    c.lizhou_anchor = 6
    p.hand = [c]
    p.cost = 1
    play_card(state, 0, 0)
    assert p.statuses.get('strength') == p.statuses.get('dexterity') == 2


def test_intuition_exhausts_before_burn_and_deletes_exact_curse():
    state, p = battle()
    play(state, 'intuition_luck', True)
    burn = create_card('card.status.burn_i')
    curse = create_card('card.curse.regret')
    curse._master_deck_uid = 7
    other = deepcopy(curse)
    other._master_deck_uid = 8
    state.run_state = SimpleNamespace(master_deck=[deepcopy(curse), other], hp=100, max_hp=100)
    p.hand = [burn, curse]
    p.draw_pile = [card('defend') for _ in range(10)]
    hp = p.hp
    end_turn(state)
    assert p.hp == hp and state.turn_count == 1
    choose_cards(state, [0, 1])
    assert any(c is burn for c in p.exhaust_pile) and any(c is curse for c in p.exhaust_pile)
    assert state.run_state.master_deck == [other]
    assert state.turn_count == 2 and len(p.hand) == 7


def test_bark_memories_retrieves_distinct_entities_and_zeroes_cost():
    state, p = battle()
    p.relics = [create_relic('relic.sacred_bark')]
    first, second = card('defend'), card('strike')
    p.discard_pile = [first, second]
    p.potions = [create_potion('potion.liquid_memories')]
    use_potion(state, 0)
    choose_pending_potion_card(state, 0)
    assert p.hand[0] is first and p.discard_pile[0] is second
    assert state.pending_potion_card_selection
    choose_pending_potion_card(state, 0)
    assert p.hand[1] is second and not p.discard_pile
    assert all(get_card_current_cost(state, c) == 0 for c in p.hand)


def test_relic_pool_camera_and_hand_ready():
    from game.reward import get_available_relic_ids, get_available_boss_relic_ids
    run = SimpleNamespace(character_id='character.lizhou', relics=[])
    assert 'relic.savior' in get_available_boss_relic_ids(run)
    assert {'relic.star_fireworks', 'relic.replica_camera', 'relic.telescope', 'relic.folder'} <= set(get_available_relic_ids(run))
    state, p = battle()
    p.relics = [create_relic('relic.replica_camera')]
    anchored, clean = card('defend'), card('strike')
    p.hand = [anchored, clean]
    for _ in range(3):
        anchor(state, anchored)
    assert state.pending_choice.options == [clean]
    choose_cards(state, [0])
    assert clean.replay_extra == 1
    p.relics = [create_relic('relic.telescope'), create_relic('relic.savior')]
    p.cost = 0
    p.draw_pile = [card('defend')]
    apply_turn_start_hand_ready_effects(state)
    assert anchored.upgraded and clean.upgraded and p.cost == 1 and len(p.hand) == 3
    choose_cards(state, [1])
    assert clean.lizhou_anchor == clean.lizhou_floating == 1


def test_potions_and_folder():
    state, p = battle()
    p.relics = [create_relic('relic.folder'), create_relic('relic.star_fireworks')]
    dispatch_event(state, 'battle_start', BattleContext(state, player=p))
    assert p.max_hand_size == 20 and p.statuses.get('lizhou_order') == 3
    p.hand = [card('defend'), card('strike')]
    p.potions = [create_potion('potion.anchor_nails'), create_potion('potion.floating'), create_potion('potion.star_sea')]
    use_potion(state, 0)
    choose_cards(state, [0, 1])
    assert all(c.lizhou_anchor == 1 for c in p.hand)
    use_potion(state, 0, 0)
    assert state.enemies[0].statuses.get('enemy_floating') == 5
    use_potion(state, 0)
    assert p.statuses.get('lizhou_order') == 9


def test_new_relic_rarity_pool_has_no_duplicates():
    from game.reward import COMMON_RELIC_POOL, UNCOMMON_RELIC_POOL, RARE_RELIC_POOL, BOSS_RELIC_POOL
    for rid, pool in [('relic.star_fireworks', COMMON_RELIC_POOL), ('relic.replica_camera', UNCOMMON_RELIC_POOL),
                      ('relic.telescope', RARE_RELIC_POOL), ('relic.savior', BOSS_RELIC_POOL)]:
        assert pool.count(rid) == 1
        assert sum(other.count(rid) for other in (COMMON_RELIC_POOL, UNCOMMON_RELIC_POOL, RARE_RELIC_POOL, BOSS_RELIC_POOL)) == 1
