"""李昼的设计契约回归：实体状态、支付、暂停恢复及连锁。"""
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from data.card.AAAregistry import create_card
from data.card.character.lizhou_cards import SPECS, ZODIACS, LIZHOU_REWARD_IDS
from data.card.upgrade_rules import upgrade_card
from data.character.AAAregistry import create_character
from data.relic.AAAregistry import create_relic
from game.engine import play_card, end_turn, move_card_to_exhaust_pile, resolve_discarded_card
from game.lizhou import anchor, floating, order, auto_play, choose_cards, before_cleanup, after_cleanup, powers
from game.card_cost import get_card_current_cost
from test_py_save.test_orbs import battle


def card(k, up=False):
    c = create_card('card.lizhou.'+k)
    return upgrade_card(c) if up else c


def finish(state):
    logs = []
    for _ in range(100):
        choice = state.pending_choice
        if choice is None:
            return '\n'.join(logs)
        assert choice.kind == 'lizhou_select'
        logs.append(choose_cards(state, list(range(choice.payload['minimum']))))
    pytest.fail('choice loop')


def play(state, k, up=False):
    c = card(k, up)
    state.player.hand.insert(0, c)
    state.player.cost = 100
    c.lizhou_anchor = 3
    text = play_card(state, 0, 0)
    return c, text+finish(state)


@pytest.mark.parametrize('k', list(SPECS))
@pytest.mark.parametrize('up', [False, True])
def test_every_card_resolves(k, up):
    state, p = battle()
    p.statuses.set('lizhou_order', 20)
    p.draw_pile = [card('defend') for _ in range(8)]
    p.hand = [card('defend') for _ in range(3)]
    p.exhaust_pile = [card('defend')]
    c, text = play(state, k, up)
    assert c.upgraded == up
    assert not any(x in text for x in ('未知效果', '未处理', '未知卡牌', '费用不足', '锚定不足', '目标敌人无效'))
    assert not getattr(state, 'lizhou_resolving', [])


def test_character_and_pool():
    from game.reward import get_card_reward_pool
    from data.content_gate import is_private_content
    c = create_character('character.lizhou')
    assert (c.name, c.max_hp, c.starting_gold, len(c.starting_deck_ids)) == ('李昼', 75, 99, 11)
    assert len(c.starting_relic_ids) == 2
    assert set(get_card_reward_pool(SimpleNamespace(character_id=c.character_id, relics=[]))) == set(LIZHOU_REWARD_IDS)
    assert all(is_private_content('card', 'card.lizhou.'+k) for k in SPECS)


def test_order_payment_after_base_and_floor():
    state, p = battle()
    p.hand = [card('sharp_bullet')]
    p.cost = 2
    order(state, 3)
    play_card(state, 0, 0)
    assert state.enemies[0].hp == 1000-8*8
    assert p.statuses.get('lizhou_order') == 0
    p.hand = [card('blunt_bullet')]
    p.cost = 1
    order(state, 1)
    play_card(state, 0, 0)
    assert state.enemies[0].hp == 930
    assert p.statuses.get('lizhou_order') == 1
    order(state, -3)
    assert p.statuses.get('lizhou_order') == 0


def test_automatic_fixed_gate_does_not_waive_optional_order_clause():
    state, p = battle()
    c = card('earth')
    auto_play(state, c, c)
    assert not powers(state, 'earth')
    c = card('earth')
    p.statuses.set('lizhou_order', 1)
    auto_play(state, c, c)
    assert len(powers(state, 'earth')) == 1 and p.statuses.get('lizhou_order') == 0
    c = card('earth')
    auto_play(state, c, c, free_order=True)
    assert len(powers(state, 'earth')) == 2


def test_annihilation_counts_order_spending_but_not_resource_loss():
    state, p = battle()
    c = card('tiny_annihilation')
    p.draw_pile = [c]
    order(state, 3)
    assert get_card_current_cost(state, c) == 83
    order(state, -1, spend=True)
    assert get_card_current_cost(state, c) == 80
    order(state, -2)
    assert get_card_current_cost(state, c) == 80


def test_anchor_per_entity_and_float_and_automatic_gate():
    state, p = battle()
    play(state, 'anchor_definition')
    play(state, 'ever_changing')
    p.block = 0
    p.cost = 0
    c = card('aye_captain')
    p.hand = [c]
    anchor(state, c, 5)
    assert (p.block, p.cost) == (5, 1)
    floating(state, c)
    assert '浮动' in play_card(state, 0)
    p.hand = []
    c.lizhou_anchor = 0
    auto_play(state, c, c)
    assert p.block == 21 and c.lizhou_anchor == 0


def test_flower_first_play_copy_and_exhaust_escape():
    state, p = battle()
    c = card('star_flower', True)
    c.lizhou_anchor = 3
    p.hand = [c]
    p.cost = 0
    play_card(state, 0)
    assert p.cost == 3 and c.lizhou_anchor == 2
    import copy
    clone = copy.deepcopy(c)
    p.hand = [clone]
    play_card(state, 0)
    assert p.cost == 5 and clone.lizhou_anchor == 0
    p.hand = []
    move_card_to_exhaust_pile(state, c)
    assert p.hand[0] is c and not p.exhaust_pile
    p.hand = [card('defend') for _ in range(10)]
    move_card_to_exhaust_pile(state, clone)
    assert any(x is clone for x in p.discard_pile)


def test_stardust_echo_reuses_paid_result_and_counts_play():
    state, p = battle()
    play(state, 'stardust_cancer')
    play(state, 'fit_stars')
    p.hand = [card('aries')]
    p.draw_pile = [card('defend'), card('defend')]
    p.statuses.set('lizhou_order', 3)
    p.block = 0
    play_card(state, 0)
    assert p.statuses.get('buffer') == 2
    assert p.statuses.get('lizhou_order') == 0
    assert p.block == 6 and len(p.hand) == 2
    assert p.lizhou_echo_used == 1


def test_tiny_annihilation_free_payment_snapshot():
    state, p = battle()
    c = card('tiny_annihilation')
    c.lizhou_free_turn = state.turn_count
    p.hand = [c]
    p.cost = 0
    assert get_card_current_cost(state, c) == 0
    play_card(state, 0, 0)
    assert state.enemies[0].hp == 908 and state.enemies[1].hp == 1000
    assert all(e.statuses.get('stun') == 1 for e in state.enemies)


def test_key_destination_and_no_draw_event():
    for up in (False, True):
        state, p = battle()
        a = card('aries')
        p.draw_pile = [a]
        c, text = play(state, 'key', up)
        assert any(x is a for x in p.hand)
        assert p.statuses.get('buffer') == 0
        assert any(x is c for x in (p.draw_pile if up else p.exhaust_pile))


def test_end_timing_and_paid_retain():
    state, p = battle()
    p.relics = [create_relic('relic.anchored_eye')]
    c = card('star_flower')
    p.hand = [c]
    before_cleanup(state)
    assert c.lizhou_anchor == 1
    after_cleanup(state)
    assert c.lizhou_anchor == 1
    before_cleanup(state)
    assert getattr(c, 'lizhou_floating', 0) == 0
    a = card('defend')
    a.lizhou_anchor = 1
    p.hand = [a]
    before_cleanup(state)
    choose_cards(state, [0])
    assert a.lizhou_anchor == 0 and a.temporary_retain_once


def test_void_world_original_block_artifact_and_each_hit():
    state, p = battle()
    play(state, 'void_world')
    enemy = state.enemies[0]
    enemy.block = 10
    p.hand = [card('sharp_bullet')]
    p.cost = 2
    play_card(state, 0, 0)
    assert enemy.hp == 976  # first 8, second doubled 16
    assert enemy.statuses.get('lizhou_double_hurt') == 1
    enemy.statuses.remove('lizhou_double_hurt')
    enemy.statuses.set('artifact', 1)
    p.hand = [card('strike')]
    p.cost = 1
    play_card(state, 0, 0)
    assert enemy.hp == 970 and enemy.statuses.get('artifact') == 0


def test_gemini_plus_does_not_reset_flowers_or_first_play():
    state, p = battle()
    flower = card('star_flower', True)
    flower.lizhou_anchor = 4
    p.discard_pile = [flower]
    p.hand = [card('gemini', True)]
    p.cost = 0
    p.statuses.set('lizhou_order', 3)
    play_card(state, 0)
    assert flower.lizhou_anchor == 4
    assert not getattr(flower, 'lizhou_flower_played', False)
    assert p.statuses.get('lizhou_order') == 0
    assert state.enemies[0].statuses.get('enemy_anchor') == 5
    assert state.enemies[0].statuses.get('enemy_floating') == 7


def test_zodiac_relic_upgrade_matching_and_chain():
    from game.lizhou_relic import check_gain, choose, options
    run = SimpleNamespace(master_deck=[card('aries'), card('aries', True)], relics=[create_relic('relic.twelve_zodiacs')])
    assert check_gain(run, run.master_deck[-1]) == []
    c = card('aries')
    run.master_deck.append(c)
    check_gain(run, c)
    assert len(options(run)) == 2
    with patch('game.lizhou_relic.random.choice', return_value='aries'):
        choose(run, 0)
    assert len(options(run)) == 2
    choose(run)
    assert not options(run)


def test_damage_block_buffs_are_duration_not_multiplier_stacks():
    from game.damage import deal_damage
    from game.block import gain_block_without_modifiers
    state, p = battle()
    p.statuses.set('lizhou_fortify', 4)
    p.statuses.set('lizhou_tenacity', 3)
    p.statuses.set('lizhou_counterbalance', 2)
    deal_damage(state, p, state.enemies[0], 20)
    assert state.enemies[0].hp == 975
    gain_block_without_modifiers(state, p, p, 20)
    assert p.block == 25
    p.block = 0
    deal_damage(state, state.enemies[0], p, 20)
    assert p.hp == 90
    p.statuses.decay_by_timing('turn_end')
    assert p.statuses.get('lizhou_fortify') == 3
    assert p.statuses.get('lizhou_tenacity') == 2
    assert p.statuses.get('lizhou_counterbalance') == 1


def test_energy_sources_trigger_once_per_gain_and_round_reset():
    from game.effects import apply_card_effect
    from game.event_bus import dispatch_event
    from game.battle_context import BattleContext
    state, p = battle()
    play(state, 'easy_battle')
    p.hp = 10
    p.block = 0
    apply_card_effect(state, card('defend'), {'op': 'gain_energy', 'amount': 5}, 0, {})
    assert (p.hp, p.block) == (14, 4)
    p.relics = [create_relic('relic.happy_flower')]
    p.relics[0].turn_counter = 2
    dispatch_event(state, 'turn_start', BattleContext(game_state=state, player=p, source=p))
    assert (p.hp, p.block) == (18, 8)
    p.start_turn(state)
    assert (p.hp, p.block) == (22, 4)
    p.statuses.set('barricade', 1)
    p.start_turn(state)
    assert (p.hp, p.block) == (26, 8)


def test_orderer_independent_counters_and_persistent_order():
    state, p = battle()
    first, _ = play(state, 'orderer')
    play(state, 'defend')
    second, _ = play(state, 'orderer', True)
    entries = powers(state, 'orderer')
    assert [v['counter'] for v in entries] == [2, 0]
    play(state, 'defend')
    play(state, 'defend')
    assert p.statuses.get('lizhou_order') == 2
    play(state, 'defend')
    assert p.statuses.get('lizhou_order') == 4
    end_turn(state)
    finish(state)
    assert p.statuses.get('lizhou_order') == 4


def test_star_bloom_sums_all_piles_and_uses_payment_snapshot():
    state, p = battle()
    play(state, 'easy_battle')
    p.hp = 10
    flowers = [card('star_flower') for _ in range(4)]
    for f in flowers:
        f.lizhou_anchor = 2
    p.hand = [card('star_bloom', True), flowers[0]]
    p.draw_pile = [flowers[1]]
    p.discard_pile = [flowers[2]]
    p.exhaust_pile = [flowers[3]]
    p.cost = 3
    play_card(state, 0)
    assert p.cost == 0 and p.hp == 14
    assert all(f.lizhou_anchor == 0 for f in flowers)
    assert [e.hp for e in state.enemies] == [840, 840]


def test_first_constellation_only_trigger_and_echo_slots():
    from game.lizhou import trigger_constellation
    state, p = battle()
    play(state, 'stardust_cancer')
    play(state, 'stardust_cancer', True)
    play(state, 'fit_stars')
    p.block = 0
    trigger_constellation(state, 'aries')
    assert p.statuses.get('buffer') == 2 and p.block == 0
    trigger_constellation(state, 'aries')
    assert p.statuses.get('buffer') == 4
    trigger_constellation(state, 'aries')
    assert p.statuses.get('buffer') == 5


def test_paid_retain_choice_suspends_full_turn_before_enemy_action():
    state, p = battle()
    c = card('defend')
    c.lizhou_anchor = 1
    p.hand = [c]
    p.draw_pile = [card('defend') for _ in range(5)]
    hp = p.hp
    end_turn(state)
    assert state.turn_count == 1 and state.pending_choice.kind == 'lizhou_select'
    assert p.hp == hp
    choose_cards(state, [0])
    assert state.turn_count == 2 and any(x is c for x in p.hand)
    assert c.lizhou_anchor == 0


def test_meteor_shower_counts_flower_exhaust_even_when_it_returns():
    state, p = battle()
    flower = card('star_flower')
    p.hand = [card('meteor_shower'), flower, card('defend')]
    p.cost = 3
    play_card(state, 0)
    assert any(c is flower for c in p.hand)
    stars = [c for c in p.hand if c.card_id.split('.')[-1] in ZODIACS]
    assert len(stars) == 2
    assert all('exhaust' not in c.keywords and c.lizhou_free_turn == state.turn_count for c in stars)


def multi_room():
    from app.game_service import GameService
    service = GameService()
    service.handle_message('li-multi', 'a', '/card multi new 7')
    service.handle_message('li-multi', 'b', '/card multi join 0')
    service.handle_message('li-multi', 'a', '/card multi start')
    room = service.multiplayer_service.get_room('li-multi')
    from data.enemy.test_dummy_enemy import TestDummyEnemy
    room.battle.enemies = [TestDummyEnemy(), TestDummyEnemy()]
    for e in room.battle.enemies:
        e.hp = e.max_hp = 1000
    return service, room


def test_multiplayer_sun_hits_allies_and_preserves_caster():
    service, room = multi_room()
    p = room.players[0].player_state
    ally = room.players[1].player_state
    p.hand = [card('self_destroying_sun')]
    p.cost = 4
    hp = p.hp
    text = service.handle_message('li-multi', 'a', '/card multi play 0')
    assert '未处理' not in text
    assert ally.hp == 0 and p.hp == hp
    assert all(e.hp == 908 for e in room.battle.enemies)


def test_multiplayer_choices_and_extra_turn_do_not_run_enemies():
    service, room = multi_room()
    slot = room.players[0]
    p = slot.player_state
    p.hand = [card('anchoring'), card('defend')]
    p.cost = 3
    text = service.handle_message('li-multi', 'a', '/card multi play 0')
    assert '/card multi pick' in text
    service.handle_message('li-multi', 'a', '/card multi pick 0')
    assert p.hand[0].lizhou_anchor == 2
    p.hand = [card('time_master')]
    p.cost = 3
    hp = p.hp
    text = service.handle_message('li-multi', 'a', '/card multi play 0')
    assert '额外回合' in text
    assert p.hp == hp and room.battle.active_user_id == 'a'
    service.handle_message('li-multi', 'a', '/card multi end')
    if slot.lizhou_combat.pending_choice:
        service.handle_message('li-multi', 'a', '/card multi skip')
    assert room.battle.active_user_id == 'b'
