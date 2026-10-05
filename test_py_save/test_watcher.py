"""Behavioral coverage of Watcher content, suspension and cross-character interactions."""
from types import SimpleNamespace
import pytest
from data.card.AAAregistry import create_card
from data.card.upgrade_rules import upgrade_card
from data.card.character.watcher_cards import SPECS, WATCHER_REWARD_IDS
from data.character.AAAregistry import create_character
from data.relic.AAAregistry import create_relic
from data.potion.AAAregistry import create_potion
from game.engine import play_card, end_turn, use_potion, start_battle_with_player
from game.stances import change_stance, gain_mantra
from game.scry import request_scry, choose_scry
from game.watcher import choose_cards
from game.event_bus import dispatch_event
from game.modifiers import apply_attack_damage_modifiers
from game.card_cost import get_card_current_cost
from test_py_save.test_orbs import battle


def play(state,key,up=False,target=0):
    card = create_card('card.'+key)
    if up:
        card = upgrade_card(card)
    state.player.hand.insert(0,card)
    state.player.cost = 20
    return card, play_card(state,0,target)


def finish_choices(state):
    logs = []
    for _ in range(30):
        choice = state.pending_choice
        if choice is None:
            return '\n'.join(logs)
        if choice.kind == 'scry':
            logs.append(choose_scry(state,[]))
        elif choice.kind == 'watcher_select':
            logs.append(choose_cards(state,list(range(choice.payload['count']))))
        elif choice.kind == 'defect_select':
            from game.defect import choose_cards as choose_blue
            logs.append(choose_blue(state,list(range(choice.payload['count']))))
        else:
            pytest.fail('unexpected choice '+choice.kind)
    pytest.fail('choice loop')


@pytest.mark.parametrize('key',list(SPECS))
@pytest.mark.parametrize('up',[False,True])
def test_all_cards_resolve_and_upgrade(key,up):
    state,p = battle()
    p.draw_pile = [create_card('card.defend_watcher') for _ in range(8)]
    p.discard_pile = [create_card('card.protect'),create_card('card.smite')]
    if key == 'deus_ex_machina':
        card = create_card('card.'+key)
        card = upgrade_card(card) if up else card
        p.draw_pile.append(card)
        p.draw_cards(1,state)
        assert sum(c.card_id == 'card.miracle' for c in p.hand) == (3 if up else 2)
        assert any(c is card for c in p.exhaust_pile)
        return
    card, logs = play(state,key,up)
    logs += finish_choices(state)
    assert not any(word in logs for word in ('未知效果','未处理','无法打出','未知卡牌','目标敌人无效'))
    assert card.upgraded == up
    if key not in ('conclude','meditate','vault'):
        if card.card_type == 'power':
            assert not any(c is card for c in p.hand+p.discard_pile)
        if 'exhaust' in card.keywords:
            assert any(c is card for c in p.exhaust_pile)


def test_character_pools_and_deva_returned():
    from app.game_service import GameService
    from game.run_engine import create_player_for_battle
    from game.reward import get_card_reward_pool, get_available_potion_ids_by_quantity, get_available_boss_relic_ids
    from data.content_gate import PRIVATE_CARD_IDS
    service = GameService()
    service.handle_message('watcher-test','tester','/card new 6')
    run = service.get_run('watcher-test')
    assert run.character_id == 'character.watcher'
    assert create_character(run.character_id).max_hp == 72
    p = create_player_for_battle(run)
    state, logs = start_battle_with_player('watcher-test',run.character_id,p,enemy_ids=['enemy.test_dummy'],run_state=run)
    assert len(p.hand) == 6 and len(p.draw_pile) == 5
    assert sum(c.card_id == 'card.miracle' for c in p.hand) == 1
    assert len(SPECS) == 83 and len(WATCHER_REWARD_IDS) == 71
    assert set(get_card_reward_pool(run)) == set(WATCHER_REWARD_IDS)
    assert 'card.deva_form' not in PRIVATE_CARD_IDS
    assert create_card('card.deva_form').owner_character_id == run.character_id
    assert 'card.deva_form' not in get_card_reward_pool(SimpleNamespace(character_id='character.lumine',relics=[]))
    assert 'potion.stance' in get_available_potion_ids_by_quantity(run)['uncommon']
    assert 'relic.holy_water' in get_available_boss_relic_ids(run)


def test_stances_energy_expiry_and_no_reentry():
    state,p = battle()
    change_stance(state,'calm')
    change_stance(state,'divinity')
    assert p.cost == 8
    change_stance(state,'divinity')
    assert p.cost == 8
    state.turn_count += 1
    p.start_turn(state)
    assert p.stance == 'none' and p.cost == 3
    change_stance(state,'divinity')
    change_stance(state,'calm')
    state.turn_count += 1
    p.start_turn(state)
    assert p.stance == 'calm'
    p.relics = [create_relic('relic.violet_lotus')]
    change_stance(state,'wrath')
    assert p.cost == 6


def test_attack_multiplier_rounding_block_and_nonattack():
    from game.damage import deal_damage
    from game.engine import process_enemy_action
    state,p = battle()
    change_stance(state,'wrath')
    p.statuses.set('weak',1)
    assert apply_attack_damage_modifiers(7,state,p,state.enemies[0],card=create_card('card.strike_watcher')) == 10
    p.block = 3
    process_enemy_action(state,state.enemies[0])
    assert p.hp == 95
    p.block = 0
    deal_damage(state,None,p,4,damage_kind='effect')
    assert p.hp == 91
    p.statuses.remove('weak')
    card,_ = play(state,'empty_fist')
    assert state.enemies[0].hp == 982 and p.stance == 'none'
    play(state,'eruption')
    assert state.enemies[0].hp == 973 and p.stance == 'wrath'


def test_scry_identity_order_invalid_and_not_discard_trigger():
    state,p = battle()
    a,b,c = [create_card('card.strike_watcher') for _ in range(3)]
    p.draw_pile = [a,b,c]
    p.relics = [create_relic('relic.tingsha')]
    request_scry(state,2)
    assert state.pending_choice.options[0] is c
    assert '有效' in choose_scry(state,[0,0])
    assert len(p.draw_pile) == 3
    choose_scry(state,[0])
    assert p.draw_pile[0] is a and p.draw_pile[1] is b
    assert p.discard_pile[0] is c
    assert state.player_discarded_cards_this_turn == 0
    assert state.enemies[0].hp == 1000


def test_scry_pauses_draw_replay_and_card_destination():
    state,p = battle()
    a,b,c,d = [create_card('card.defend_watcher') for _ in range(4)]
    p.draw_pile = [a,b,c,d]
    card = create_card('card.cut_through_fate')
    card.replay_extra = 1
    p.hand = [card,create_card('card.miracle')]
    play_card(state,0,0)
    assert len(p.hand) == 1 and not p.discard_pile
    cost = p.cost
    assert '预见' in play_card(state,0)
    assert p.cost == cost
    assert '预见' in end_turn(state)
    choose_scry(state,[0])
    assert any(item is c for item in p.hand)
    assert state.pending_choice.options[0] is b
    assert not any(item is card for item in p.discard_pile)
    choose_scry(state,[])
    assert any(item is b for item in p.hand)
    assert any(item is card for item in p.discard_pile)
    assert state.enemies[0].hp == 986


def test_scry_zero_and_short_pile_no_shuffle():
    state,p = battle()
    p.discard_pile = [create_card('card.strike_watcher')]
    request_scry(state,5)
    assert state.pending_choice is None and not p.draw_pile
    p.draw_pile = [create_card('card.defend_watcher')]
    request_scry(state,0)
    assert state.pending_choice is None
    request_scry(state,5)
    assert len(state.pending_choice.options) == 1


def test_foresight_before_draw_and_melange_resume():
    state,p = battle()
    p.statuses.set('w_foresight',3)
    p.draw_pile = [create_card('card.defend_watcher') for _ in range(8)]
    end_turn(state)
    assert state.pending_choice.kind == 'scry' and not p.hand
    choose_scry(state,[])
    assert len(p.hand) == 5
    p.statuses.remove('w_foresight')
    p.hand = []
    p.draw_pile = []
    p.discard_pile = [create_card('card.strike_watcher') for _ in range(4)]
    p.relics = [create_relic('relic.melange')]
    p.draw_cards(2,state)
    assert state.pending_choice.kind == 'scry' and not p.hand
    choose_scry(state,[])
    assert len(p.hand) == 2


def test_nested_omniscience_scry_and_replay():
    state,p = battle()
    cut = create_card('card.cut_through_fate')
    p.draw_pile = [cut]+[create_card('card.defend_watcher') for _ in range(6)]
    omni,_ = play(state,'omniscience')
    choose_cards(state,[0])
    assert state.pending_choice.kind == 'scry'
    assert not p.exhaust_pile
    choose_scry(state,[])
    assert state.pending_choice.kind == 'scry'
    choose_scry(state,[])
    assert any(c is cut for c in p.exhaust_pile)
    assert any(c is omni for c in p.exhaust_pile)
    assert len(p.hand) == 2


def test_retain_growth_deva_no_max_cost_growth():
    state,p = battle()
    p.statuses.set('w_establishment',1)
    p.hand = [create_card('card.perseverance'), create_card('card.windmill_strike'),create_card('card.sands_of_time')]
    cards = list(p.hand)
    from game.engine import end_player_turn_hand_cleanup
    end_player_turn_hand_cleanup(state)
    assert cards[0]._retained_block == 2 and cards[1]._retained_damage == 4
    assert [c.cost for c in cards] == [0,1,2]
    play(state,'deva_form')
    p.start_turn(state)
    dispatch_event(state,'turn_start')
    assert p.cost == 4 and p.max_cost == 3
    p.start_turn(state)
    dispatch_event(state,'turn_start')
    assert p.cost == 5 and p.max_cost == 3


def test_mantra_pressure_points_and_stance_hooks():
    state,p = battle()
    p.statuses.set('w_mental_fortress',4)
    p.statuses.set('w_rushdown',2)
    p.draw_pile = [create_card('card.defend_watcher') for _ in range(4)]
    flurry = create_card('card.flurry_of_blows')
    p.discard_pile = [flurry]
    change_stance(state,'wrath')
    assert p.block == 4 and len(p.hand) == 3 and p.hand[0] is flurry
    gain_mantra(state,12)
    assert p.stance == 'divinity' and p.statuses.get('mantra') == 2 and p.mantra_total == 12
    play(state,'pressure_points')
    assert state.enemies[0].hp == 992
    play(state,'pressure_points',target=1)
    assert [e.hp for e in state.enemies] == [984,992]


def test_potions_bark_holy_water_and_swivel():
    state,p = battle()
    p.relics = [create_relic('relic.sacred_bark')]
    p.potions = [create_potion('potion.bottled_miracle'),create_potion('potion.stance'),create_potion('potion.ambrosia')]
    use_potion(state,0)
    assert len(p.hand) == 4
    use_potion(state,0)
    choose_cards(state,[0])
    assert p.stance == 'calm'
    energy = p.cost
    use_potion(state,0)
    assert p.stance == 'divinity' and p.cost == energy+5
    play(state,'swivel')
    attack = create_card('card.strike_watcher')
    p.hand = [attack]
    assert get_card_current_cost(state,attack) == 0
    energy = p.cost
    play_card(state,0,0)
    assert p.cost == energy and p.statuses.get('w_swivel') == 0
    run = SimpleNamespace(relics=[create_relic('relic.pure_water')])
    holy = create_relic('relic.holy_water')
    run.relics.append(holy)
    holy.on_obtained(run)
    assert [r.relic_id for r in run.relics] == ['relic.holy_water']


def test_master_reality_upgrades_other_character_generation_not_rewards():
    from game.watcher import generate
    state,p = battle()
    play(state,'master_reality')
    generate(state,'smite')
    assert p.hand[-1].upgraded
    play(state,'blade_dance')
    shivs = [c for c in p.hand if c.card_id == 'card.shiv']
    assert len(shivs) == 3 and all(c.upgraded for c in shivs)
    assert not create_card('card.smite').upgraded


def test_melange_can_discard_entire_reshuffled_pile_then_continue_draw():
    state,p = battle()
    p.relics = [create_relic('relic.melange')]
    p.discard_pile = [create_card('card.strike_watcher')]
    p.draw_cards(1,state)
    choose_scry(state,[0])
    assert state.pending_choice.kind == 'scry' and not p.hand
    choose_scry(state,[])
    assert len(p.hand) == 1 and state.pending_choice is None


def test_enemy_multihit_pauses_for_damage_draw_shuffle_scry():
    from game.engine import process_enemy_action_payload
    state,p = battle()
    p.relics = [create_relic('relic.centennial_puzzle'),create_relic('relic.melange')]
    dispatch_event(state,'battle_start')
    p.discard_pile = [create_card('card.defend_watcher') for _ in range(5)]
    logs = []
    process_enemy_action_payload(state,state.enemies[0],{
        'op':'enemy_multi_action',
        'actions':[{'op':'enemy_attack','damage':4},{'op':'enemy_attack','damage':4}],
    },logs)
    assert p.hp == 96 and state.pending_choice.kind == 'scry'
    choose_scry(state,[])
    assert p.hp == 92 and len(p.hand) == 3


def test_golden_eye_nirvana_weave_and_no_draw():
    state,p = battle()
    p.relics = [create_relic('relic.golden_eye')]
    p.statuses.set('w_nirvana',3)
    p.statuses.set('no_draw',1)
    weave = create_card('card.weave')
    p.draw_pile = [create_card('card.defend_watcher') for _ in range(5)] + [weave]
    play(state,'cut_through_fate')
    assert len(state.pending_choice.options) == 4
    choose_scry(state,[0])
    assert len(p.hand) == 1 and p.hand[0] is weave
    assert p.block == 3


def test_wallop_overkill_and_talk_to_hand_blocked_hits():
    state,p = battle()
    state.enemies[0].hp = 2
    play(state,'wallop')
    assert p.block == 9
    play(state,'talk_to_the_hand',target=1)
    p.block = 0
    state.enemies[1].block = 100
    play(state,'flying_sleeves',target=1)
    assert p.block == 4


def test_artifact_blocks_mark_and_talk_to_hand():
    state,p = battle()
    enemy = state.enemies[0]
    enemy.statuses.set('artifact',2)
    play(state,'pressure_points')
    assert enemy.statuses.get('mark') == 0 and enemy.hp == 1000
    play(state,'talk_to_the_hand')
    assert enemy.statuses.get('talk_to_the_hand') == 0


def test_vault_and_meditate_end_at_correct_point():
    state,p = battle()
    p.draw_pile = [create_card('card.defend_watcher') for _ in range(12)]
    play(state,'vault')
    assert state.turn_count == 2 and p.hp == 100 and len(p.hand) == 5
    kept = create_card('card.strike_watcher')
    p.discard_pile = [kept]
    play(state,'meditate')
    assert state.turn_count == 2 and p.stance == 'none'
    choose_cards(state,[0])
    assert state.turn_count == 3 and p.stance == 'calm'
    assert any(c is kept for c in p.hand)


def test_blasphemy_buffer_and_normal_death():
    state,p = battle()
    play(state,'blasphemy')
    p.statuses.set('buffer',1)
    state.turn_count += 1
    p.start_turn(state)
    dispatch_event(state,'turn_start')
    assert p.hp == 100 and p.stance == 'none' and not p.statuses.get('buffer')
    play(state,'blasphemy')
    state.turn_count += 1
    p.start_turn(state)
    dispatch_event(state,'turn_start')
    assert p.hp == 0 and state.battle_over


def test_lesson_learned_permanent_upgrade_and_minion_exclusion():
    state,p = battle()
    state.run_state = SimpleNamespace(master_deck=[create_card('card.defend_watcher')])
    state.enemies[0].hp = 1
    state.enemies[0].is_minion = True
    play(state,'lesson_learned')
    assert not state.run_state.master_deck[0].upgraded
    state.enemies[1].hp = 1
    play(state,'lesson_learned',target=1)
    assert state.run_state.master_deck[0].upgraded


def test_direct_attack_damage_and_previews_use_stance_once():
    from game.damage import deal_damage
    from game.intent_preview import preview_enemy_attack_damage
    from game.card_preview import format_card_actual_preview
    state,p = battle()
    change_stance(state,'wrath')
    assert preview_enemy_attack_damage(state,state.enemies[0],4) == 8
    assert '12' in format_card_actual_preview(state,create_card('card.strike_watcher'))
    deal_damage(state,state.enemies[0],p,4,damage_kind='attack')
    assert p.hp == 92
    change_stance(state,'divinity')
    deal_damage(state,p,state.enemies[0],5,damage_kind='attack')
    assert state.enemies[0].hp == 985


def test_service_scry_commands_and_read_only_queries():
    from test_py_save.test_pending_toolbox_and_dance_regressions import make_service_battle
    service,state = make_service_battle()
    p = state.player
    p.hand = [create_card('card.just_lucky'),create_card('card.miracle')]
    p.draw_pile = [create_card('card.defend_watcher') for _ in range(4)]
    reply = service.handle_message(state.session_id,'tester','/card play 0 0')
    assert '预见' in reply and state.pending_choice.kind == 'scry'
    assert '抽牌堆' in service.handle_message(state.session_id,'tester','/card draw')
    assert '预见' in service.handle_message(state.session_id,'tester','/card end')
    service.handle_message(state.session_id,'tester','/card scry skip')
    assert state.pending_choice is None and p.block == 2


def test_omniscience_two_plays_trigger_attack_relic_twice():
    state,p = battle()
    p.relics = [create_relic('relic.duality')]
    p.draw_pile = [create_card('card.strike_watcher')]
    play(state,'omniscience')
    choose_cards(state,[0])
    assert state.enemies[0].hp == 988
    assert p.statuses.get('dexterity') == 2


def test_auto_play_chain_waits_for_scry_and_preserves_destination():
    from game.effects import apply_card_effect
    state,p = battle()
    cut = create_card('card.cut_through_fate')
    strike = create_card('card.strike_watcher')
    p.draw_pile = [strike,create_card('card.defend_watcher'),cut]
    source = create_card('card.omniscience')
    apply_card_effect(state,source,{'op':'play_draw_pile_top_count','times':2},0,{})
    assert state.pending_choice.kind == 'scry' and state.enemies[0].hp == 993
    assert not p.exhaust_pile and not p.discard_pile
    choose_scry(state,[])
    assert state.enemies[0].hp == 987
    assert any(c is cut for c in p.discard_pile) and any(c is strike for c in p.discard_pile)


def test_swivel_survives_turn_and_free_x_attack_keeps_effective_x():
    state,p = battle()
    play(state,'swivel')
    play(state,'swivel')
    end_turn(state)
    assert p.statuses.get('w_swivel') == 2
    p.cost = 3
    p.hand = [create_card('card.whirlwind'),create_card('card.strike_watcher')]
    before = [enemy.hp for enemy in state.enemies]
    play_card(state,0,0)
    assert p.cost == 3 and p.statuses.get('w_swivel') == 1
    assert [enemy.hp for enemy in state.enemies] == [hp-15 for hp in before]
    play_card(state,0,0)
    assert p.cost == 3 and p.statuses.get('w_swivel') == 0
