"""Behavioral checks for STS1 Defect content and existing combat integration."""
import copy
from types import SimpleNamespace
import pytest
from data.card.character.defect_cards import SPECS, DEFECT_REWARD_IDS
from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.character.AAAregistry import create_character
from data.relic.AAAregistry import create_relic
from data.potion.AAAregistry import create_potion
from game.engine import play_card, end_turn, use_potion, start_battle_with_player
from game.orbs import rack, channel, trigger_passives, evoke_orb
from game.defect import choose_cards
from game.card_cost import get_card_current_cost
from game.battle_context import BattleContext
from game.event_bus import dispatch_event
from game.damage import deal_damage
from test_py_save.test_orbs import battle


def play(state,key,up=False,target=0):
    card = create_card('card.'+key)
    if up:
        card = upgrade_card(card)
    state.player.hand.insert(0,card)
    state.player.cost = max(20,state.player.cost)
    return card, play_card(state,0,target)


@pytest.mark.parametrize('key',list(SPECS))
@pytest.mark.parametrize('up',[False,True])
def test_every_card_resolves_and_upgrades(key,up):
    state, player = battle()
    player.hand = [create_card('card.strike_defect')]
    player.draw_pile = [create_card('card.defend_defect') for _ in range(8)]
    player.discard_pile = [create_card('card.claw')]
    channel(state,player,'frost')
    card, logs = play(state,key,up)
    if state.pending_choice is not None and state.pending_choice.kind == 'defect_select':
        logs += choose_cards(state, list(range(state.pending_choice.payload['count'])))
    assert not any(word in logs for word in ('未知效果','未处理','无法打出','未知卡牌','目标敌人无效'))
    assert card.upgraded == up
    if card.card_type == 'power':
        assert not any(c is card for c in player.discard_pile + player.hand)
    if 'exhaust' in card.keywords:
        assert any(c is card for c in player.exhaust_pile)


def test_starting_character_and_registry():
    from app.game_service import GameService
    from game.run_engine import create_player_for_battle
    character = create_character('character.defect')
    assert character.max_hp == 75 and len(character.starting_deck_ids) == 10
    service=GameService()
    service.handle_message('defect-test','tester','/card new 5')
    run = service.get_run('defect-test')
    assert run.character_id == 'character.defect'
    player = create_player_for_battle(run)
    state, logs = start_battle_with_player('defect-test','character.defect',player,enemy_ids=['enemy.test_dummy'],run_state=run)
    assert rack(player).capacity == 3
    assert [o.kind for o in rack(player).orbs] == ['lightning']
    assert len(player.hand) == 5 and len(player.draw_pile) == 5
    assert len(SPECS) == 78 and len(DEFECT_REWARD_IDS) == 74


def test_pool_ownership_and_frozen_core_replacement():
    from game.reward import get_card_reward_pool, get_available_potion_ids_by_quantity, get_available_boss_relic_ids
    run=SimpleNamespace(character_id='character.defect',relics=[create_relic('relic.cracked_core')])
    assert set(get_card_reward_pool(run)) == set(DEFECT_REWARD_IDS)
    pools=get_available_potion_ids_by_quantity(run)
    assert 'potion.focus' in pools['common'] and 'potion.capacity' in pools['uncommon']
    assert 'potion.essence_of_darkness' in pools['rare']
    assert 'relic.frozen_core' in get_available_boss_relic_ids(run)
    frozen=create_relic('relic.frozen_core')
    run.relics.append(frozen)
    frozen.on_obtained(run)
    assert [r.relic_id for r in run.relics] == ['relic.frozen_core']
    other=SimpleNamespace(character_id='character.armored_warrior',relics=[])
    assert not any(p in str(get_available_potion_ids_by_quantity(other)) for p in ('potion.focus','potion.capacity','potion.essence_of_darkness'))
    assert not any(c in get_card_reward_pool(other) for c in DEFECT_REWARD_IDS)


def test_damage_block_and_negative_focus_use_real_pipeline():
    state,p=battle()
    p.statuses.set('strength',2)
    play(state,'ball_lightning')
    assert state.enemies[0].hp == 991 and rack(p).orbs[0].kind == 'lightning'
    p.statuses.set('dexterity',2)
    play(state,'glacier')
    assert p.block == 9 and [o.kind for o in rack(p).orbs] == ['lightning','frost','frost']
    play(state,'reprogram',True)
    assert p.statuses.get('focus') == -2 and p.statuses.get('strength') == 4 and p.statuses.get('dexterity') == 4


def test_recursion_preserves_dark_and_counts_generation():
    state,p=battle()
    channel(state,p,'dark')
    rack(p).orbs[0].value=30
    channel(state,p,'frost')
    play(state,'recursion')
    assert [o.kind for o in rack(p).orbs] == ['frost','dark']
    assert rack(p).orbs[1].value == 30 and rack(p).channeled['dark'] == 2
    assert sum(e.hp for e in state.enemies) == 1970


def test_claw_all_instances_and_force_field_discount():
    state,p=battle()
    first=create_card('card.claw');second=upgrade_card(create_card('card.claw'))
    p.hand=[first,second]
    play_card(state,0,0)
    play_card(state,0,0)
    assert state.enemies[0].hp == 990
    play(state,'claw') # newly created cards have no earlier claw bonus
    assert state.enemies[0].hp == 987
    field=create_card('card.force_field')
    assert get_card_current_cost(state,field) == 4
    play(state,'defragment')
    assert get_card_current_cost(state,field) == 3


def test_echo_and_amplify_power_triggers():
    state,p=battle()
    play(state,'heatsinks')
    play(state,'storm')
    play(state,'echo_form')
    count = rack(p).channeled.get('lightning',0)
    p.draw_pile=[create_card('card.defend_defect') for _ in range(10)]
    before=len(p.hand)
    play(state,'defragment')
    assert p.statuses.get('focus') == 2
    assert rack(p).channeled['lightning'] == count+2
    assert len(p.hand) == before+2
    play(state,'amplify_defect',True)
    play(state,'defragment')
    assert p.statuses.get('focus') == 4
    assert p.statuses.get('amplify') == 1


def test_bias_artifact_and_static_discharge_buffer():
    state,p=battle()
    p.statuses.set('artifact',1)
    play(state,'biased_cognition')
    assert p.statuses.get('focus') == 4 and p.statuses.get('bias') == 0
    play(state,'static_discharge',True)
    p.statuses.set('buffer',1)
    deal_damage(state,state.enemies[0],p,3)
    assert p.hp == 100 and not rack(p).orbs
    deal_damage(state,state.enemies[0],p,3)
    assert p.hp == 97 and rack(p).channeled['lightning'] == 2


def test_genetic_growth_is_per_card_and_survives_upgrade():
    state,p=battle()
    master=create_card('card.genetic_algorithm'); master._master_deck_uid=1
    another=create_card('card.genetic_algorithm'); another._master_deck_uid=2
    state.run_state=SimpleNamespace(master_deck=[master,another])
    active=copy.deepcopy(master)
    p.hand=[active];play_card(state,0)
    assert p.block == 1 and master.card_vars['block'] == 3
    assert another.card_vars['block'] == 1
    upgraded=upgrade_card(master)
    assert upgraded.card_vars['block'] == 3 and '3 点格挡' in upgraded.description


def test_hologram_and_seek_selection_identity_and_no_draw_trigger():
    state,p=battle()
    first=create_card('card.claw'); second=create_card('card.claw')
    p.discard_pile=[first,second]
    card,log=play(state,'hologram',True)
    assert state.pending_choice.kind == 'defect_select'
    assert '有效编号' in choose_cards(state,[99])
    choose_cards(state,[1])
    assert any(c is second for c in p.hand) and any(c is first for c in p.discard_pile)
    assert any(c is card for c in p.discard_pile)
    p.draw_pile=[create_card('card.status.void'),create_card('card.claw')]
    play(state,'seek',True)
    energy=p.cost
    choose_cards(state,[0,1])
    assert p.cost == energy and not p.draw_pile


def test_recycle_cost_and_exhaust_event():
    state,p=battle()
    item=create_card('card.meteor_strike');item.temporary_cost_override=0
    p.hand=[item]
    play(state,'recycle')
    energy=p.cost
    choose_cards(state,[0])
    assert p.cost == energy and any(c is item for c in p.exhaust_pile)


def test_rebound_and_equilibrium():
    state,p=battle()
    rebound,_=play(state,'rebound')
    strike,_=play(state,'strike_defect')
    assert p.draw_pile[-1] is strike and rebound in p.discard_pile
    play(state,'equilibrium')
    retained=create_card('card.strike_defect');ethereal=create_card('card.echo_form')
    p.hand=[retained,ethereal]
    end_turn(state)
    assert any(c is retained for c in p.hand) and any(c is ethereal for c in p.exhaust_pile)
    assert p.statuses.get('defect_equilibrium') == 0


def test_x_cards_and_channel_history():
    state,p=battle()
    channel(state,p,'frost',2)
    p.hand=[create_card('card.multi_cast')];p.cost=3
    play_card(state,0)
    assert p.block == 15 and len(rack(p).orbs) == 1
    p.hand=[upgrade_card(create_card('card.tempest'))];p.cost=2
    play_card(state,0)
    assert rack(p).channeled['lightning'] == 3
    play(state,'thunder_strike')
    assert sum(e.hp for e in state.enemies) == 1979
    play(state,'blizzard')
    assert sum(e.hp for e in state.enemies) == 1971


def test_self_repair_and_generation_excludes_heal():
    from game.defect import random_blue
    state,p=battle();p.hp=50
    play(state,'self_repair',True)
    state.battle_over=True;state.victory=True
    dispatch_event(state,'battle_end',BattleContext(state,player=p,extra={'victory':True}))
    assert p.hp == 60
    for _ in range(100):
        random_blue(state,kind='power')
    assert all(c.card_id != 'card.self_repair' for c in p.hand+p.discard_pile)


@pytest.mark.parametrize('bark',[False,True])
def test_defect_potions_sacred_bark(bark):
    state,p=battle()
    if bark:p.relics=[create_relic('relic.sacred_bark')]
    p.potions=[create_potion('potion.focus'),create_potion('potion.capacity'),create_potion('potion.essence_of_darkness')]
    use_potion(state,0)
    assert p.statuses.get('focus') == (4 if bark else 2)
    use_potion(state,0)
    assert rack(p).capacity == (9 if bark else 7)
    use_potion(state,0)
    assert rack(p).channeled['dark'] == rack(p).capacity*(2 if bark else 1)
    assert not p.potions


def test_relic_start_slots_focus_plasma_and_frozen_end():
    from game.player_state import PlayerState
    p=PlayerState('character.defect','机器人',75,75,3,3,relics=[create_relic('relic.'+k) for k in ['cracked_core','symbiotic_virus','nuclear_battery','runic_capacitor','data_disk']])
    state,_=start_battle_with_player('test','character.defect',p,enemy_ids=['enemy.test_dummy'])
    assert rack(p).capacity == 6 and p.statuses.get('focus') == 1 and p.cost == 4
    assert [o.kind for o in rack(p).orbs] == ['lightning','dark','plasma']
    state,p=battle();p.relics=[create_relic('relic.frozen_core')]
    end_turn(state)
    assert rack(p).orbs[0].kind == 'frost'
    assert p.hp == 94 # two 4-damage attacks, 2 frost block


def test_lock_on_cables_loop_and_emotion_chip():
    state,p=battle()
    play(state,'bullseye')
    state.enemies=state.enemies[:1]
    channel(state,p,'lightning')
    trigger_passives(state,p)
    assert state.enemies[0].hp == 988 # 8 attack + floor(3*1.5)
    p.relics=[create_relic('relic.gold_plated_cables')]
    trigger_passives(state,p)
    assert state.enemies[0].hp == 980
    state,p=battle();channel(state,p,'dark')
    p.statuses.set('loop',2)
    dispatch_event(state,'turn_start',BattleContext(state,player=p))
    assert rack(p).orbs[0].value == 18
    p.relics=[create_relic('relic.emotion_chip')]
    deal_damage(state,state.enemies[0],p,1)
    p.statuses.remove('loop')
    dispatch_event(state,'turn_start',BattleContext(state,player=p))
    assert rack(p).orbs[0].value == 24
    dispatch_event(state,'turn_start',BattleContext(state,player=p))
    assert rack(p).orbs[0].value == 24


def test_echo_seek_queues_distinct_selections():
    state,p=battle()
    p.statuses.set('echo_form',1)
    p.draw_pile=[create_card('card.claw'),create_card('card.leap'),create_card('card.zap')]
    play(state,'seek')
    assert not state.pending_choice_queue  # Replay starts after the first choice resolves.
    choose_cards(state,[0])
    assert state.pending_choice is not None and len(state.pending_choice.options) == 2
    choose_cards(state,[0])
    assert state.pending_choice is None and len(p.draw_pile) == 1
    assert {c.card_id for c in p.hand} == {'card.claw','card.leap'}


def test_service_pick_blocks_play_and_completes_selection():
    from test_py_save.test_pending_toolbox_and_dance_regressions import make_service_battle
    service,state=make_service_battle()
    state.player.draw_pile=[create_card('card.claw')]
    state.player.hand=[create_card('card.seek'),create_card('card.zap')]
    service.handle_message(state.session_id,'tester','/card play 0')
    assert state.pending_choice.kind == 'defect_select'
    reply=service.handle_message(state.session_id,'tester','/card play 0')
    assert '/card pick' in reply
    reply=service.handle_message(state.session_id,'tester','/card pick 0')
    assert '爪击' in reply and state.pending_choice is None


def test_fission_removes_all_before_draw_and_upgraded_evokes():
    from unittest.mock import patch
    state,p=battle()
    channel(state,p,'frost',2)
    original=p.draw_cards
    def checked(count,*args,**kwargs):
        assert not rack(p).orbs
        return original(count,*args,**kwargs)
    with patch.object(p,'draw_cards',side_effect=checked):
        play(state,'fission')
    assert p.block == 0
    channel(state,p,'frost',2)
    with patch.object(p,'draw_cards',side_effect=checked):
        play(state,'fission',True)
    assert p.block == 10


def test_scrape_only_discards_direct_draws_and_actual_cost():
    state,p=battle()
    p.statuses.set('evolve',1)
    # Draw a status; evolve draws Leap, which Scrape must not discard.
    p.draw_pile=[create_card('card.claw'),create_card('card.zap'),create_card('card.leap'),create_card('card.status.wound')]
    play(state,'scrape')
    assert any(c.card_id == 'card.leap' for c in p.hand)
    assert any(c.card_id == 'card.zap' for c in p.discard_pile)
    assert any(c.card_id == 'card.claw' for c in p.hand)


def test_steam_and_claw_upgrade_preserve_combat_changes():
    from game.card_preview import format_card_actual_preview
    state,p=battle()
    card,_=play(state,'steam_barrier')
    upgraded=upgrade_card(card)
    assert '7 点格挡' in upgraded.description
    p.hand=[upgraded]
    play_card(state,0)
    assert p.block == 13
    claw,_=play(state,'claw')
    upgraded=upgrade_card(claw)
    assert '7 点伤害' in upgraded.description
    p.statuses.set('strength',2)
    assert '9' in format_card_actual_preview(state,upgraded)


def test_inserter_and_focus_loss_artifact():
    state,p=battle()
    relic=create_relic('relic.inserter');p.relics=[relic]
    context=BattleContext(state,player=p)
    dispatch_event(state,'turn_start',context)
    assert rack(p).capacity == 5
    dispatch_event(state,'turn_start',context)
    assert rack(p).capacity == 6
    p.statuses.set('artifact',1)
    play(state,'hyperbeam')
    assert p.statuses.get('focus') == 0 and p.statuses.get('artifact') == 0
    p.statuses.set('bias',1);p.statuses.set('artifact',1)
    logs=dispatch_event(state,'turn_start',context)
    assert any('人工制品抵挡' in log for log in logs)
    assert not any('失去 1' in log for log in logs)
    assert p.statuses.get('focus') == 0 and p.statuses.get('artifact') == 0


def test_sunder_kill_energy_and_aoe_actual_damage():
    state,p=battle()
    state.enemies[0].hp=20
    p.hand=[create_card('card.sunder')];p.cost=3
    play_card(state,0,0)
    assert p.cost == 3 and state.enemies[0].hp == 0
    play(state,'doom_and_gloom',True,1)
    assert state.enemies[1].hp == 986 and rack(p).orbs[0].kind == 'dark'


def test_self_repair_not_in_potion_or_random_combat_pool():
    from game.engine import get_potion_card_pool
    from game.effects import get_random_card_candidates
    state,p=battle()
    state.run_state=SimpleNamespace(character_id='character.defect',relics=[])
    assert 'card.self_repair' not in get_potion_card_pool(state,'power')
    assert 'card.self_repair' not in get_random_card_candidates(card_type='power')


def test_streamline_upgrade_preserves_reduced_cost():
    state,p=battle()
    card,_=play(state,'streamline')
    assert card.cost == 1
    upgraded=upgrade_card(card)
    assert upgraded.cost == 1 and upgraded.card_vars['damage'] == 20
    p.hand=[upgraded]
    play_card(state,0,0)
    assert upgraded.cost == 0
    assert state.enemies[0].hp == 965


def test_loop_victory_stops_turn_start_listeners_and_draw():
    from unittest.mock import patch
    state,p=battle()
    state.enemies=state.enemies[:1]
    state.enemies[0].hp=4
    channel(state,p,'lightning')
    p.statuses.set('loop',1)
    seen=[]
    state.active_fields=[SimpleNamespace(on_event=lambda event,context: seen.append(event))]
    p.draw_pile=[create_card('card.leap') for _ in range(5)]
    with patch.object(p,'draw_cards',wraps=p.draw_cards) as draw:
        end_turn(state)
    assert state.battle_over and state.enemies[0].hp == 0
    assert 'turn_start' not in seen
    draw.assert_not_called()
