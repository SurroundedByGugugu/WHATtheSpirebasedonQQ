from dataclasses import replace
from types import SimpleNamespace

import pytest

from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.enemy.base_enemy import EnemyIntent
from data.relic.AAAregistry import create_relic
from data.status.AAAregistry import STATUS_DEFS
from data.zones.element_zones import ElementZone
from game.card_preview import format_card_actual_preview
from game.damage import deal_damage
from game.engine import end_turn, play_card
from game.reward import get_card_reward_pool
from test_py_save.test_abyss_combat_regressions import make_battle


KEYS = ['silent_slash', 'rising_wind', 'intercept', 'diving_strike', 'probing_strike',
        'vigilance_yoirine', 'sidestep_yoirine', 'crystal_blade', 'refraction',
        'barrier_break', 'Uturn', 'debride', 'shadow_crystallization',
        'retreat_yoirine', 'reverse_blood', 'surprise_assault', 'silent_execution']


def play(state, key, upgraded=False):
    card = create_card('card.' + key)
    if upgraded:
        card = upgrade_card(card)
    state.player.hand.insert(0, card)
    state.player.cost = 10
    reply = play_card(state, 0, 0)
    assert not any(text in reply for text in ('未知效果', '未处理', '无法打出'))
    return card, reply


def attacking(state):
    state.enemies[0]._locked_intent = EnemyIntent(kind='multi', actions=[
        EnemyIntent(kind='block', value=5), EnemyIntent(kind='attack', value=0),
    ])


@pytest.mark.parametrize('key', KEYS)
@pytest.mark.parametrize('upgraded', [False, True])
def test_definitions_registration_and_default_resolution(key, upgraded):
    state = make_battle()
    card, _ = play(state, key, upgraded)
    assert card.owner_character_id == 'character.yoirine'
    assert card.upgraded is upgraded
    assert card.attack_type == ''
    assert card.attack_element == ({'crystal_blade': 'crystal', 'refraction': 'crystal',
                                    'shadow_crystallization': 'shade'}.get(key, ''))
    assert card.quantity == ('common' if KEYS.index(key) < 8 else 'rare' if key in KEYS[-2:] else 'uncommon')
    assert card.cost == (0 if key in ('sidestep_yoirine', 'Uturn') else 2 if key in KEYS[-2:] else 1)


def test_reward_pool_ownership():
    ids = {'card.' + key for key in KEYS}
    assert ids <= set(get_card_reward_pool(SimpleNamespace(character_id='character.yoirine', relics=[])))
    assert not ids.intersection(get_card_reward_pool(SimpleNamespace(character_id='character.defect', relics=[])))


@pytest.mark.parametrize('key,base,up,condition,enhanced,enhanced_up', [
    ('silent_slash', 9, 12, '', 9, 12),
    ('intercept', 7, 9, 'intent', 12, 16),
    ('diving_strike', 8, 10, 'flying', 13, 16),
    ('crystal_blade', 8, 11, 'block', 12, 16),
    ('reverse_blood', 8, 10, 'self_loss', 15, 18),
    ('silent_execution', 20, 24, 'low_hp', 40, 48),
])
@pytest.mark.parametrize('upgraded', [False, True])
@pytest.mark.parametrize('matched', [False, True])
def test_conditional_damage_and_preview(key, base, up, condition, enhanced, enhanced_up, upgraded, matched):
    state = make_battle()
    enemy = state.enemies[0]
    if matched:
        if condition == 'intent': attacking(state)
        elif condition == 'flying': state.player.statuses.set('flying', 1)
        elif condition == 'block': enemy.block = 1
        elif condition == 'self_loss': state.player_self_action_hp_loss_count_this_turn = 1
        elif condition == 'low_hp': enemy.hp = enemy.max_hp // 4
    expected = (enhanced_up if upgraded else enhanced) if matched else (up if upgraded else base)
    card = create_card('card.' + key)
    if upgraded: card = upgrade_card(card)
    assert '[0]{}'.format(expected) in format_card_actual_preview(state, card)
    before = enemy.hp + enemy.block
    play(state, key, upgraded)
    assert before - enemy.hp - enemy.block == expected


@pytest.mark.parametrize('upgraded,damage', [(False, 6), (True, 9)])
def test_rising_wind_hits_all_and_probing_strike_draws(upgraded, damage):
    state = make_battle()
    state.enemies.append(make_battle().enemies[0])
    play(state, 'rising_wind', upgraded)
    assert [enemy.hp for enemy in state.enemies] == [1000 - damage] * 2
    drawn = create_card('card.defend_yoirine')
    state.player.draw_pile = [drawn]
    play(state, 'probing_strike', upgraded)
    assert state.player.hand[0] is drawn


@pytest.mark.parametrize('upgraded,base,bonus', [(False, 8, 3), (True, 12, 4)])
@pytest.mark.parametrize('matched', [False, True])
def test_vigilance_combines_block_before_dexterity(upgraded, base, bonus, matched):
    state = make_battle()
    if matched: attacking(state)
    state.player.statuses.set('dexterity', 2)
    play(state, 'vigilance_yoirine', upgraded)
    assert state.player.block == base + (bonus if matched else 0) + 2


@pytest.mark.parametrize('key,base,up', [('sidestep_yoirine', 6, 8), ('debride', 5, 8), ('retreat_yoirine', 7, 10)])
@pytest.mark.parametrize('upgraded', [False, True])
def test_block_and_keywords(key, base, up, upgraded):
    state = make_battle()
    card, _ = play(state, key, upgraded)
    assert state.player.block == (up if upgraded else base)
    assert (card in state.player.exhaust_pile) == (key != 'retreat_yoirine')
    if key == 'retreat_yoirine':
        state.player.discard_pile.remove(card)
        state.player.hand = [card]
        state.player.draw_pile = [create_card('card.claw') for _ in range(6)]
        end_turn(state)
        assert any(item is card for item in state.player.hand)


@pytest.mark.parametrize('matched', [False, True])
@pytest.mark.parametrize('upgraded', [False, True])
def test_refraction_and_barrier_break_use_pre_attack_conditions(matched, upgraded):
    state = make_battle()
    if matched: attacking(state)
    play(state, 'refraction', upgraded)
    assert state.enemies[0].statuses.get('weak') == int(matched)
    state.enemies[0].block = int(matched)
    play(state, 'barrier_break', upgraded)
    assert state.enemies[0].block == 0
    assert state.player.cost == 9 + int(matched)


def test_barrier_break_refunds_even_on_kill():
    state = make_battle()
    state.enemies[0].hp = state.enemies[0].block = 1
    play(state, 'barrier_break')
    assert state.player.cost == 10


def test_barrier_break_rechecks_block_for_each_replay():
    state = make_battle()
    state.enemies[0].block = 1
    state.player.statuses.set('double_tap', 1)
    play(state, 'barrier_break')
    assert state.player.cost == 10  # 仅第一次攻击前有格挡。


@pytest.mark.parametrize('hp,damage', [(25, 40), (26, 20)])
def test_silent_execution_uses_exact_quarter_hp_threshold(hp, damage):
    state = make_battle()
    enemy = state.enemies[0]
    enemy.max_hp = 101
    enemy.hp = hp
    enemy.block = 100
    play(state, 'silent_execution')
    assert enemy.block == 100 - damage


@pytest.mark.parametrize('upgraded', [False, True])
@pytest.mark.parametrize('flying', [False, True])
def test_uturn_draw_and_exhaust_are_conditional(upgraded, flying):
    state = make_battle()
    state.player.statuses.set('flying', int(flying))
    state.player.draw_pile = [create_card('card.claw')]
    card, _ = play(state, 'Uturn', upgraded)
    assert len(state.player.hand) == int(flying)
    assert (card in state.player.exhaust_pile) == (flying and not upgraded)
    assert not getattr(card, 'exhaust_this_play', False)
    if flying and not upgraded:
        state.player.exhaust_pile.remove(card)
        state.player.hand = [card]
        state.player.statuses.remove('flying')
        play_card(state, 0, 0)
        assert card in state.player.discard_pile


def test_debride_removes_one_debuff_before_block_and_preserves_buffs(monkeypatch):
    state = make_battle()
    state.player.statuses.set('frail', 3)
    state.player.statuses.set('weak', 2)
    state.player.statuses.set('dexterity', 2)
    monkeypatch.setattr('game.effects.random.choice', lambda choices: 'frail')
    play(state, 'debride')
    assert state.player.block == 7
    assert state.player.statuses.get('frail') == 0
    assert state.player.statuses.get('weak') == 2
    assert state.player.statuses.get('dexterity') == 2


def test_debride_respects_unremovable_and_cleanses_negative_stats(monkeypatch):
    state = make_battle()
    state.player.statuses.set('weak', 2)
    state.player.statuses.set('strength', -2)
    monkeypatch.setitem(STATUS_DEFS, 'weak', replace(STATUS_DEFS['weak'], removable=False))
    play(state, 'debride')
    assert state.player.statuses.get('weak') == 2
    assert state.player.statuses.get('strength') == 0


@pytest.mark.parametrize('upgraded,first,ordinary', [(False, 30, 22), (True, 36, 26)])
def test_surprise_assault_counts_all_card_types_and_keeps_first_bonus_on_replay(upgraded, first, ordinary):
    state = make_battle()
    state.player.statuses.set('double_tap', 1)
    play(state, 'surprise_assault', upgraded)
    assert state.enemies[0].hp == 1000 - first * 2
    play(state, 'surprise_assault', upgraded)
    assert state.enemies[0].hp == 1000 - first * 2 - ordinary
    state = make_battle()
    play(state, 'sidestep_yoirine')
    play(state, 'surprise_assault', upgraded)
    assert state.enemies[0].hp == 1000 - ordinary


@pytest.mark.parametrize('upgraded,block', [(False, 4), (True, 6)])
def test_shadow_crystallization_once_per_turn_for_real_self_action_loss(upgraded, block):
    state = make_battle()
    player = state.player
    play(state, 'shadow_crystallization', upgraded)
    deal_damage(state, state.enemies[0], player, 1)
    assert player.block == 0
    deal_damage(state, player, player, 0, ignore_block=True, count_as_player_self_action_hp_loss=True)
    assert player.block == 0
    for _ in range(2):
        deal_damage(state, player, player, 1, damage_kind='hp_loss', ignore_block=True,
                    count_as_player_self_action_hp_loss=True)
    assert player.block == block
    state.turn_count += 1
    deal_damage(state, player, player, 1, damage_kind='hp_loss', ignore_block=True,
                count_as_player_self_action_hp_loss=True)
    assert player.block == block * 2


def test_shadow_and_reverse_blood_ignore_prevented_self_damage():
    state = make_battle()
    play(state, 'shadow_crystallization')
    state.player.relics = [create_relic('relic.tungsten_rod')]
    deal_damage(state, state.player, state.player, 1, damage_kind='hp_loss', ignore_block=True,
                count_as_player_self_action_hp_loss=True)
    assert state.player.block == 0
    play(state, 'reverse_blood')
    assert state.enemies[0].hp == 992


def test_shadow_crystallization_triggers_on_zone_backlash():
    state = make_battle()
    play(state, 'shadow_crystallization')
    state.active_zone = ElementZone('shade', is_extreme=True, duration=3)
    play(state, 'reverse_blood')  # 无属性，不触发阴 Zone。
    assert state.player.block == 0
    play(state, 'lightless_prayer')
    assert state.player.block == 4
