import json
from unittest.mock import patch

import pytest

from data.card.AAAregistry import create_card
from data.enemy.AAAregistry import create_enemy
from data.relic.AAAregistry import create_relic
from game.engine import end_turn, play_card, start_battle_with_player, process_enemy_action
from game.node.node_shop import ShopItem, ShopState, apply_shop_price_modifiers, buy_shop_item
from game.reward import RewardOption, RewardState, get_available_relic_ids, get_available_potion_ids_by_quantity
from test_py_save.test_abyss_combat_regressions import make_battle, strike
from web import bridge
from app.game_service import GameService


def new_run(character=0):
    bridge.service = GameService()
    bridge.dispatch(f'/card new {character}')
    return bridge.service.get_run(bridge.SESSION)


@pytest.mark.parametrize('player_poison', [False, True])
def test_flying_does_not_block_poison_or_lose_flight(player_poison):
    game = make_battle()
    game.enemies = [create_enemy('enemy.byrd')]
    owner = game.player if player_poison else game.enemies[0]
    owner.statuses.set('flying', 3)
    owner.statuses.set('poison', 6)
    owner.block = 100
    old_hp = owner.hp
    # Isolate pre-action poison from the Byrd's subsequent attack.
    from game.event_bus import dispatch_event
    from game.constants import EVENT_BEFORE_ENEMY_ACTIONS
    dispatch_event(game, EVENT_BEFORE_ENEMY_ACTIONS)
    assert owner.hp == old_hp - 6
    assert owner.block == 100
    assert owner.statuses.get('poison') == 5
    assert owner.statuses.get('flying') == 3


def test_ninja_scroll_adds_three_shivs_without_replacing_draws():
    game = make_battle()
    game.player.relics = [create_relic('relic.ninja_scroll')]
    game.player.draw_pile = [create_card('card.strike_yoirine') for _ in range(10)]
    game, _ = start_battle_with_player('scroll', game.character_id, game.player, ['enemy.byrd'])
    assert len(game.player.hand) == 8
    assert sum(c.card_id == 'card.shiv' for c in game.player.hand) == 3
    assert len(game.player.draw_pile) == 5


@pytest.mark.parametrize('initial, expected_damage, expected_count, ended',
                         [(0, 30, 3, False), (10, 20, 0, True), (11, 10, 0, True)])
def test_time_warp_counts_each_replay_and_cancels_remainder(initial, expected_damage, expected_count, ended):
    game = make_battle()
    game.enemies[0].statuses.set('time_warp', 12)
    game.time_warp_card_count = initial
    card = strike('')
    card.replay_extra = 2
    game.player.hand = [card]
    play_card(game, 0, 0)
    assert game.enemies[0].hp == 1000 - expected_damage
    assert game.time_warp_card_count == expected_count
    assert game.turn_count == (2 if ended else 1)
    assert game.enemies[0].statuses.get('strength') == (2 if ended else 0)


def test_repulsor_shuffles_added_dazed_with_existing_draw_pile():
    game = make_battle()
    enemy = create_enemy('enemy.repulsor')
    enemy._last_action_key = 'a'
    game.enemies = [enemy]
    game.player.draw_pile = [strike('') for _ in range(5)]
    with patch('game.engine.random.shuffle') as shuffle:
        process_enemy_action(game, enemy)
    shuffle.assert_called_once_with(game.player.draw_pile)
    assert len(game.player.draw_pile) == 7
    assert sum(c.card_id == 'card.status.dazed' for c in game.player.draw_pile) == 2


def test_membership_immediately_discounts_and_never_compounds():
    run = new_run()
    run.relics = []
    run.gold = 1000
    run.pending_shop = ShopState(items=[
        ShopItem('relic', '会员卡', 200, {'relic': create_relic('relic.membership_card')}),
        ShopItem('card', '卡牌', 101, {'card': strike('')}),
    ])
    buy_shop_item(run, 0)
    assert run.gold == 800
    assert run.pending_shop.items[1].price == 50
    for _ in range(3):
        apply_shop_price_modifiers(run, run.pending_shop.items)
    assert run.pending_shop.items[1].price == 50
    buy_shop_item(run, 1)
    assert run.gold == 750


@pytest.mark.parametrize('kind, payload', [
    ('card', lambda: strike('')),
    ('relic', lambda: create_relic('relic.anchor')),
    ('potion', lambda: __import__('data.potion.AAAregistry', fromlist=['create_potion']).create_potion('potion.block')),
])
def test_courier_restocks_distinct_objects_and_stacks_discounts(kind, payload):
    run = new_run()
    run.relics = [create_relic('relic.membership_card'), create_relic('relic.the_courier')]
    run.gold = 1000
    item = ShopItem(kind, '商品', 100, {kind: payload()})
    run.pending_shop = ShopState(items=[item])
    buy_shop_item(run, 0)
    assert run.gold == 960
    replacement = run.pending_shop.items[0]
    assert replacement is not item and not replacement.sold
    assert replacement.payload[kind] is not item.payload[kind]
    assert replacement.price == max(1, int(replacement.base_price * .4))
    if kind == 'relic':
        assert replacement.payload[kind].relic_id != item.payload[kind].relic_id


def test_ownership_filters_and_shared_turnip():
    run = new_run()
    run.relics = []
    for rid in ('ninja_scroll', 'snake_skull', 'paper_crane', 'the_specimen', 'tingsha', 'tough_bandages', 'twisted_funnel', 'hovering_kite', 'wrist_blade'):
        assert create_relic('relic.' + rid).owner_character_id == 'character.silent_huntress'
    assert create_relic('relic.turnip').owner_character_id == ''
    assert 'relic.stalactite' not in get_available_relic_ids(run)
    assert 'potion.saturated_calcium_carbonate_solution' not in get_available_potion_ids_by_quantity(run)['rare']
    run.character_id = 'character.suzuri'
    assert 'relic.stalactite' in get_available_relic_ids(run)
    assert 'potion.saturated_calcium_carbonate_solution' in get_available_potion_ids_by_quantity(run)['rare']


def test_reward_back_preserves_options_and_acquisition_is_transient():
    run = new_run()
    run.pending_ancient = None
    cards = [strike('') for _ in range(3)]
    option = RewardOption('card', '三选一', {'cards': cards})
    run.pending_reward = RewardState(options=[option], active_card_option_index=0)
    result = json.loads(bridge.dispatch('/card reward back'))
    assert run.pending_reward.active_card_option_index == -1
    assert not option.claimed and not option.skipped
    assert any(c['command'] == '/card take 0' for c in result['run']['choices'])
    bridge.dispatch('/card take 0')
    result = json.loads(bridge.dispatch('/card pick 0'))
    assert any(item['name'] == cards[0].name for item in result['acquired'])
    assert not json.loads(bridge.dispatch('/card view'))['acquired']


def test_special_rockbound_retain_and_stolen_card_are_visible():
    run = new_run(3)
    create_relic('relic.whirlwall_sparrow_down').on_obtained(run)
    card = run.master_deck[-1]
    assert '保留' in bridge.card_metadata(card)['keywords']
    assert bridge.card_actions([card], 'pick')[0]['rarity'] == card.quantity
    game = make_battle()
    game.player.hand = [card]
    game.enemies[0]._captured_card = card
    run.current_battle = game
    result = bridge.snapshot()['run']
    assert '保留' in result['hand'][0]['keywords']
    assert card.name in result['enemies'][0]['capturedCard']
