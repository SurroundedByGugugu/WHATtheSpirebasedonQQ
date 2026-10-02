import copy
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from game.player_state import PlayerState
from game.game_state import GameState
from data.enemy.test_dummy_enemy import TestDummyEnemy as Dummy
from data.zones.element_zones import ElementZone
from game.orbs import channel, evoke_orb, trigger_passives, set_slots, rack, values, trigger
from game.orbs.ctrl import handle_orb_ctrl
from game.engine import end_turn


def battle():
    player = PlayerState('test', '测试', 100, 100, 3, 3)
    enemies = [Dummy(), Dummy()]
    for enemy in enemies:
        enemy.hp = enemy.max_hp = 1000
    state = GameState('test', 'test', player, enemies)
    set_slots(player, 5)
    return state, player


@pytest.mark.parametrize('kind,expected', [('lightning',(5,10)), ('frost',(4,7)), ('dark',(8,6)), ('glass',(6,12)), ('plasma',(1,2))])
def test_focus_values(kind, expected):
    state, player = battle()
    player.statuses.set('focus', 2)
    channel(state, player, kind)
    assert values(state, player, rack(player).orbs[0]) == expected


def test_fifo_double_evoke_same_orb_and_zero_slots():
    state, player = battle()
    set_slots(player, 2)
    channel(state, player, 'frost')
    channel(state, player, 'dark')
    evoke_orb(state, player, times=2)
    assert player.block == 10
    assert [o.kind for o in rack(player).orbs] == ['dark']
    channel(state, player, 'frost', 2)
    assert [o.kind for o in rack(player).orbs] == ['frost', 'frost']
    assert sum(e.hp for e in state.enemies) == 1994
    set_slots(player, 0)
    channel(state, player, 'lightning')
    assert not rack(player).orbs
    assert sum(e.hp for e in state.enemies) == 1994


@pytest.mark.parametrize('extreme,growth', [(False,10), (True,14)])
def test_shade_growth_and_stored_damage(extreme, growth):
    state, player = battle()
    state.active_zone = ElementZone('shade', extreme)
    player.statuses.set('focus', 1)
    channel(state, player, 'dark')
    trigger_passives(state, player)
    orb = rack(player).orbs[0]
    assert orb.value == 6 + growth
    state.enemies[1].hp = 100
    player.statuses.set('focus', -99)
    evoke_orb(state, player)
    assert state.enemies[1].hp == 100 - 6 - growth
    assert player.hp == 100


@pytest.mark.parametrize('element,extreme,base', [('',False,3), ('crystal',False,4), ('crystal',True,5)])
def test_glass_decay_after_damage(element, extreme, base):
    state, player = battle()
    if element:
        state.active_zone = ElementZone(element, extreme)
    player.statuses.set('focus', 2)
    channel(state, player, 'glass')
    trigger_passives(state, player)
    assert [e.hp for e in state.enemies] == [994,994]
    assert rack(player).orbs[0].value == base
    evoke_orb(state, player)
    assert [e.hp for e in state.enemies] == [994 - 2*(base+2)]*2


@pytest.mark.parametrize('extreme,regen', [(False,3), (True,5)])
def test_water_frost_no_dexterity_modifiers(extreme, regen):
    state, player = battle()
    state.active_zone = ElementZone('water', extreme)
    player.statuses.set('dexterity', 99)
    player.statuses.set('frail', 99)
    channel(state, player, 'frost')
    trigger_passives(state, player)
    evoke_orb(state, player)
    assert player.block == 7
    assert player.statuses.get('regeneration') == regen


def test_thunder_no_replay_or_attack_modifiers():
    state, player = battle()
    state.active_zone = ElementZone('thunder', True)
    player.statuses.set('strength', 99)
    player.statuses.set('weak', 99)
    for enemy in state.enemies:
        enemy.statuses.set('vulnerable', 99)
    channel(state, player, 'lightning')
    trigger_passives(state, player)
    evoke_orb(state, player)
    assert [e.hp for e in state.enemies] == [989,989]


def test_negative_focus_and_glass_floor():
    state, player = battle()
    player.statuses.set('focus', -99)
    channel(state, player, 'dark')
    channel(state, player, 'glass')
    for _ in range(6):
        trigger_passives(state, player)
    assert [o.value for o in rack(player).orbs] == [6,0]
    player.statuses.set('focus', 2)
    assert values(state, player, rack(player).orbs[1]) == (2,4)


def test_new_orbs_excluded_from_passive_snapshot():
    state, player = battle()
    channel(state, player, 'frost')
    def event(state, player, name, orb):
        if name == 'orb_passive':
            return channel(state, player, 'dark')
        return []
    with patch('game.orbs.emit', side_effect=event):
        trigger_passives(state, player)
    assert [o.value for o in rack(player).orbs] == [0,6]


def test_victory_stops_later_orbs_and_full_slot_channel():
    state, player = battle()
    state.enemies[0].hp = 1
    state.enemies[1].is_minion = True
    channel(state, player, 'glass')
    channel(state, player, 'frost')
    trigger_passives(state, player)
    assert state.victory and state.battle_over
    assert player.block == 0
    assert state.enemies[1].hp == 0
    assert rack(player).orbs[0].value == 4

    state, player = battle()
    state.enemies = state.enemies[:1]
    state.enemies[0].hp = 1
    set_slots(player, 1)
    channel(state, player, 'lightning')
    channel(state, player, 'frost')
    assert state.victory and not rack(player).orbs


def test_real_turn_order_and_plasma_after_reset():
    state, player = battle()
    channel(state, player, 'plasma')
    channel(state, player, 'dark')
    state.enemies[0].statuses.set('poison', 2)
    player.cost = 0
    seen = []
    def cleanup(s):
        seen.append('hand')
        assert state.enemies[0].hp == 1000
        return ['hand-marker']
    def enemy_action(s, e):
        seen.append('enemy')
        assert state.enemies[0].hp == 998
        assert rack(player).orbs[1].value == 12
        return []
    with patch('game.engine.end_player_turn_hand_cleanup', side_effect=cleanup), patch('game.engine.process_enemy_action', side_effect=enemy_action):
        end_turn(state)
    assert seen == ['hand','enemy','enemy']
    assert player.cost == 4
    assert state.enemies[0].statuses.get('poison') == 1


def test_poison_phase_new_orb_not_triggered_and_kill_stops():
    state, player = battle()
    class Relic:
        def on_event(self, name, context):
            if name == 'before_enemy_actions':
                return channel(state, player, 'dark')
            return []
    player.relics = [Relic()]
    end_turn(state)
    assert rack(player).orbs[0].value == 6
    state, player = battle()
    state.enemies = state.enemies[:1]
    state.enemies[0].hp = 1
    state.enemies[0].statuses.set('poison', 1)
    channel(state, player, 'dark')
    end_turn(state)
    assert state.victory and rack(player).orbs[0].value == 6


def test_ctrl_validation_and_copy():
    state, player = battle()
    run = SimpleNamespace(current_battle=state)
    assert '球槽' in handle_orb_ctrl(run, ['channel','黑暗','2'])
    assert '参数错误' in handle_orb_ctrl(run, ['evoke','0','2'])
    assert '参数错误' in handle_orb_ctrl(run, ['channel','闪电','-1'])
    assert len(rack(player).orbs) == 2
    handle_orb_ctrl(run, ['value','1','18'])
    handle_orb_ctrl(run, ['focus','-2'])
    assert rack(player).orbs[0].value == 18 and player.statuses.get('focus') == -2
    cloned = copy.deepcopy(player)
    cloned.orb_rack.orbs[0].value = 99
    assert rack(player).orbs[0].value == 18
    handle_orb_ctrl(run, ['slots','1'])
    assert len(rack(player).orbs) == 1
    handle_orb_ctrl(run, ['clear'])
    assert not rack(player).orbs


def test_service_prefixes_and_help():
    from test_py_save.test_test_room import start_debug_run
    for prefix in ('/', '.', '。'):
        service, session_id, user_id, run = start_debug_run()
        service.handle_message(session_id, user_id, '/ctrl testroom battle')
        service.handle_message(session_id, user_id, prefix + 'ctrl orb slots 3')
        reply = service.handle_message(session_id, user_id, prefix + 'ctrl orb channel 玻璃')
        assert '玻璃球' in reply and '1/3' in reply
        assert 'orb' in service.handle_message(session_id, user_id, prefix + 'ctrl help')


def test_retention_pause_does_not_trigger_poison_or_orbs_twice():
    from data.card.AAAregistry import create_card
    from game.engine import choose_pending_well_laid_plans_cards
    from game.pending_choice import pending_choice_is
    state, player = battle()
    player.hand = [create_card('card.strike'), create_card('card.defend')]
    player.statuses.set('well_laid_plans', 1)
    state.enemies[0].statuses.set('poison', 2)
    channel(state, player, 'dark')
    end_turn(state)
    assert pending_choice_is(state, 'well_laid_plans')
    assert state.enemies[0].hp == 1000
    assert rack(player).orbs[0].value == 6
    choose_pending_well_laid_plans_cards(state, skip=True)
    assert state.enemies[0].hp == 998
    assert rack(player).orbs[0].value == 12


def test_double_dark_retargets_after_kill():
    state, player = battle()
    state.enemies[0].hp = 5
    channel(state, player, 'dark')
    channel(state, player, 'frost')
    evoke_orb(state, player, times=2)
    assert [e.hp for e in state.enemies] == [0,994]
    assert [o.kind for o in rack(player).orbs] == ['frost']
    assert player.block == 0


def test_poison_victory_stops_later_event_listeners():
    state, player = battle()
    state.enemies[0].hp = 1
    state.enemies[0].statuses.set('poison', 1)
    state.enemies[1].is_minion = True
    called = []
    state.enemies[1].on_event = lambda event, context: called.append(event) or []
    end_turn(state)
    assert state.victory
    assert 'before_enemy_actions' not in called


def test_ice_cream_retains_then_plasma_adds_energy():
    from data.relic.AAAregistry import create_relic
    state, player = battle()
    player.relics = [create_relic('relic.ice_cream')]
    player.cost = 2
    channel(state, player, 'plasma')
    end_turn(state)
    assert player.cost == 6
