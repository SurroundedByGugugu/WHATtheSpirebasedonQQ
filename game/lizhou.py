"""李昼的资源、实体牌状态、可恢复选择与星座结算。

直觉与幸运在回合末状态伤害前选牌。
投刃/幻魔、锚定之眼、浮动衰减及锚定保留在清理手牌前依次结算。
"""
import copy
import random
from collections import deque

from data.card.character.lizhou_cards import ZODIACS, ELEMENTS
from game.resolution import resumable, resume
from game.pending_choice import PendingChoice, enqueue_pending_choice, clear_pending_choice, get_pending_choice

PREFIX = 'card.lizhou.'


def key(card):
    cid = getattr(card, 'card_id', '')
    return cid[len(PREFIX):] if cid.startswith(PREFIX) else ''


def powers(state, name=None):
    entries = getattr(state.player, 'lizhou_powers', [])
    return [p for p in entries if name is None or p['key'] == name]


def power_amount(state, name):
    return sum(p['card'].card_vars.get('amount', 1) for p in powers(state, name))


def remove(pile, card):
    for i, item in enumerate(pile):
        if item is card:
            pile.pop(i)
            return True
    return False


def all_cards(state):
    seen = set()
    for pile in (state.player.hand, state.player.draw_pile, state.player.discard_pile,
                 state.player.exhaust_pile, getattr(state, 'lizhou_resolving', []),
                 getattr(state, 'lizhou_moon_queue', [])):
        for card in list(pile):
            if id(card) not in seen:
                seen.add(id(card))
                yield card


def annihilation_progress(state, amount):
    for card in all_cards(state):
        if key(card) == 'tiny_annihilation':
            card.lizhou_discount = min(92, getattr(card, 'lizhou_discount', 0) +
                                      amount * card.card_vars['reduction'])


def status(state, name, amount, target=None):
    from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
    return apply_status_with_player_relics(game_state=state, source=state.player,
        target=target if target is not None else state.player, status_key=name, amount=amount)


def heal(state, amount):
    from game.relic_logic.combat_relic_utils import heal_player_in_combat
    return heal_player_in_combat(state, amount, source_name='李昼')


def block(state, amount, card=None):
    from game.effects import apply_card_effect
    return apply_card_effect(state, card, {'op': 'gain_block', 'target': 'self',
        'amount': {'base': amount, 'modifier_profile': 'block'}}, 0, {})


def passive_block(state, amount, card):
    from game.block import gain_block_without_modifiers
    return gain_block_without_modifiers(state, state.player, state.player, amount, card=card)


def energy_gained(state, amount):
    if state is None or amount <= 0:
        return []
    logs = []
    for power in powers(state, 'easy_battle'):
        n = power['card'].card_vars['amount']
        logs.extend(heal(state, n))
        logs.extend(passive_block(state, n, power['card']))
    return logs


def energy(state, amount):
    if amount <= 0:
        return []
    state.player.cost += amount
    return ['获得{}能量。'.format(amount)] + energy_gained(state, amount)


def order(state, amount, *, spend=False):
    previous = state.player.statuses.get('lizhou_order')
    state.player.statuses.set('lizhou_order', max(0, previous+amount))
    actual = state.player.statuses.get('lizhou_order')-previous
    if actual == 0:
        return []
    if actual > 0 or spend:
        annihilation_progress(state, abs(actual))
    logs = ['调序{}，当前{}。'.format('{:+}'.format(actual), previous+actual)]
    if actual > 0:
        for _ in powers(state, 'ever_changing'):
            logs.extend(energy(state, 1))
    return logs


@resumable()
def anchor(state, card, amount=1):
    foresights = powers(state, 'astronomic_foresight') if amount > 0 else []
    amount += len(foresights)
    card.lizhou_anchor = max(0, getattr(card, 'lizhou_anchor', 0)+amount)
    logs = ['【{}】锚定{}。'.format(card.name, card.lizhou_anchor)]
    if amount > 0:
        annihilation_progress(state, 1)
        if key(card) == 'focus':
            card.lizhou_order_discount = getattr(card, 'lizhou_order_discount', 0)+1
        if any(r.relic_id == 'relic.replica_camera' for r in state.player.relics):
            card.lizhou_anchor_count = getattr(card, 'lizhou_anchor_count', 0)+1
            if card.lizhou_anchor_count % 3 == 0:
                logs.extend(request(state, '复刻相机', 'replay', [c for c in state.player.hand if not getattr(c, 'lizhou_anchor', 0)]))
                yield logs
                logs = []
        for p in powers(state, 'anchor_definition'):
            logs.extend(passive_block(state, p['card'].card_vars['amount'], p['card']))
        for _ in powers(state, 'ever_changing'):
            logs.extend(energy(state, 1))
    for power in foresights:
        if power['card'].upgraded:
            logs.extend(order(state, 1))
    return logs


def floating(state, card, amount=1):
    card.lizhou_floating = max(0, getattr(card, 'lizhou_floating', 0)+amount)
    if amount > 0:
        annihilation_progress(state, 1)
    return ['【{}】浮动{}。'.format(card.name, card.lizhou_floating)]


def free(state, card):
    if getattr(card, 'lizhou_free_battle', False) or getattr(card, 'lizhou_free_turn', -1) == state.turn_count:
        return True
    return False


def order_cost(state, card):
    if getattr(card, 'lizhou_zero_order', False) or getattr(card, 'lizhou_zero_order_turn', -1) == state.turn_count:
        return 0
    return max(0, card.card_vars.get('order', 0)-getattr(card, 'lizhou_order_discount', 0))


def permission(state, card, reason):
    if reason != 'normal':
        return True, ''
    if getattr(card, 'lizhou_floating', 0) and not powers(state, 'floating_tide'):
        return False, '【{}】仍有浮动，不能手动打出。'.format(card.name)
    if getattr(card, 'lizhou_anchor', 0) < card.card_vars.get('anchor_gate', 0):
        return False, '【{}】锚定不足。'.format(card.name)
    if not free(state, card) and state.player.statuses.get('lizhou_order') < card.card_vars.get('order_gate', 0):
        return False, '【{}】调序不足。'.format(card.name)
    return True, ''


def prepare_play(state, card, context, paid=0, automatic=False):
    resolving = getattr(state, 'lizhou_resolving', None)
    if resolving is None:
        state.lizhou_resolving = resolving = []
    resolving.append(card)
    context['lizhou_free'] = bool(context.get('lizhou_free', False) or free(state, card))
    context['spent_cost'] = paid
    card.lizhou_play_anchor = getattr(card, 'lizhou_anchor', 0)
    context['lizhou_automatic'] = automatic
    context['lizhou_damage_difference'] = max(0, 92-paid)
    if getattr(state.player, 'lizhou_domain_turn', -1) == state.turn_count:
        card.lizhou_domain_used = state.turn_count
    if key(card) == 'star_flower' and 'retain' not in card.keywords:
        card.keywords.append('retain')
    logs = []
    if not automatic:
        gate = card.card_vars.get('anchor_gate', 0)
        if gate:
            logs.extend(anchor(state, card, -gate))
    return logs


def request(state, source, mode, options, count=1, minimum=None, **payload):
    if not options:
        return []
    count = min(count, len(options))
    minimum = count if minimum is None else min(minimum, count)
    prompt = '{}：选择{}～{}项，/card pick 编号（空格分隔）；可选0项时可 /card skip。\n'.format(source, minimum, count)
    prompt += '\n'.join('[{}] {}'.format(i, c.summary_text() if hasattr(c, 'summary_text') else c)
                        for i, c in enumerate(options))
    enqueue_pending_choice(state, PendingChoice(kind='lizhou_select', source=source, prompt=prompt,
        options=list(options), payload=dict(mode=mode, count=count, minimum=minimum, pause_resolution=True, **payload)))
    return [prompt]


def put_hand(state, card):
    pile = state.player.discard_pile if state.player.is_hand_full() else state.player.hand
    pile.append(card)
    return ['【{}】加入{}。'.format(card.name, '弃牌堆（手牌已满）' if pile is state.player.discard_pile else '手牌')]


def create_zodiac(state, *, exhaust=False, ethereal=False, free_battle=False, free_turn=False, zero=None, upgraded=False):
    from data.card.AAAregistry import create_card
    card = create_card(PREFIX+random.choice(ZODIACS))
    if upgraded:
        from data.card.upgrade_rules import upgrade_card
        card = upgrade_card(card)
    card.temporary = card.created_in_battle = True
    for enabled, keyword in ((exhaust, 'exhaust'), (ethereal, 'ethereal')):
        if enabled and keyword not in card.keywords:
            card.keywords.append(keyword)
    card.lizhou_free_battle = free_battle
    if free_turn:
        card.lizhou_free_turn = state.turn_count
    if zero == 'battle':
        card.lizhou_zero_order = True
    if zero == 'turn':
        card.lizhou_zero_order_turn = state.turn_count
    return put_hand(state, card)


@resumable()
def selected_effect(state, choice, selected):
    from game.engine import move_card_to_exhaust_pile
    mode = choice.payload['mode']
    for card in selected:
        if mode == 'anchor':
            yield anchor(state, card, choice.payload.get('amount', 1))
        elif mode == 'replay':
            card.replay_extra = getattr(card, 'replay_extra', 0)+1
        elif mode == 'savior':
            yield anchor(state, card)
            yield floating(state, card)
        elif mode == 'intuition':
            if remove(state.player.hand, card):
                if choice.payload.get('upgraded'):
                    state.player.lizhou_intuition_draw = getattr(state.player, 'lizhou_intuition_draw', 0)+1
                if card.card_type in ('status', 'curse'):
                    yield move_card_to_exhaust_pile(state, card, reason=choice.source)
                    if card.card_type == 'curse':
                        # This power explicitly exhausts even returning curses.
                        if remove(state.player.hand, card) or remove(state.player.discard_pile, card):
                            state.player.exhaust_pile.append(card)
                        run = getattr(state, 'run_state', None)
                        uid = getattr(card, '_master_deck_uid', None)
                        if run is not None and uid is not None:
                            for i, original in enumerate(run.master_deck):
                                if getattr(original, '_master_deck_uid', None) == uid:
                                    from game.deck_utils import apply_card_removed_or_transformed_side_effects
                                    run.master_deck.pop(i)
                                    run.hp, run.max_hp = state.player.hp, state.player.max_hp
                                    yield apply_card_removed_or_transformed_side_effects(run, original, 'intuition_luck')
                                    state.player.hp, state.player.max_hp = run.hp, run.max_hp
                                    break
                else:
                    from game.engine import resolve_discarded_card
                    yield resolve_discarded_card(state, card, reason=choice.source, trigger_clever=True)
        elif mode == 'floating':
            yield floating(state, card)
        elif mode == 'retain':
            if 'retain' not in card.keywords:
                card.keywords.append('retain')
        elif mode == 'paid_retain':
            if any(c is card for c in state.player.hand) and getattr(card, 'lizhou_anchor', 0) > 0:
                card.lizhou_anchor -= 1
                card.temporary_retain_once = True
                card.lizhou_paid_retain_turn = state.turn_count
        elif mode == 'discard_retained':
            if remove(state.player.hand, card):
                from game.engine import resolve_discarded_card
                yield resolve_discarded_card(state, card, reason=choice.source, trigger_clever=True)
        elif mode == 'exhaust':
            if remove(state.player.hand, card):
                yield move_card_to_exhaust_pile(state, card, reason=choice.source)
        elif mode in ('retrieve', 'key'):
            pile = state.player.exhaust_pile if mode == 'retrieve' else state.player.draw_pile
            if remove(pile, card):
                yield put_hand(state, card)
        elif mode == 'copy':
            for _ in range(choice.payload.get('copies', 1)):
                yield put_hand(state, copy.deepcopy(card))
        elif mode == 'constellation':
            yield trigger_constellation(state, key(card))


def choose_cards(state, indices):
    choice = get_pending_choice(state)
    if choice is None or choice.kind != 'lizhou_select':
        return '当前没有李昼选牌。'
    p = choice.payload
    if (len(set(indices)) != len(indices) or not p['minimum'] <= len(indices) <= p['count'] or
            any(i < 0 or i >= len(choice.options) for i in indices)):
        return '选择数量或编号无效。\n'+choice.prompt
    clear_pending_choice(state, 'lizhou_select')
    logs = selected_effect(state, choice, [choice.options[i] for i in indices])
    logs.extend(resume(state))
    return '\n'.join(logs)


def draw(state, count):
    from game.effects import draw_cards_with_no_draw_check
    return draw_cards_with_no_draw_check(state, count, draw_source='lizhou')


@resumable()
def hit(state, card, amount, target_index, times=1, everyone=False, random_target=False, hp_loss=False):
    from game.effects import apply_card_effect, get_alive_enemies
    for _ in range(times):
        if not get_alive_enemies(state):
            break
        target = 'all_enemies' if everyone else ('random_enemy' if random_target else 'selected_enemy')
        if hp_loss:
            from game.damage import deal_damage
            for enemy in get_alive_enemies(state):
                yield deal_damage(state, state.player, enemy, amount, damage_kind='hp_loss', card=card, ignore_block=True)
        else:
            op = 'deal_damage_all_enemies' if everyone else 'deal_damage_random_enemies' if random_target else 'deal_damage'
            yield apply_card_effect(state, card, {'op': op, 'target': target,
                'amount': {'base': amount, 'modifier_profile': 'attack_damage'}}, target_index, {})


def debuff(state, name, amount, target_index, everyone=False):
    from game.effects import get_alive_enemies, get_target_enemy
    enemies = get_alive_enemies(state) if everyone else [get_target_enemy(state, target_index)]
    logs = []
    for enemy in enemies:
        if enemy is not None:
            logs.extend(status(state, name, amount, enemy))
    return logs


@resumable()
def auto_play(state, source, card, free_order=False):
    from game.effects import play_card_from_effect_and_exhaust
    from data.card.keyword_rules import can_play_card
    allowed, reason = can_play_card(state, card, play_reason='effect_auto_play')
    if not allowed:
        state.player.discard_pile.append(card)
        return ['【{}】未能自动打出，进入弃牌堆：{}'.format(card.name, reason)]
    yield play_card_from_effect_and_exhaust(state, source, card, reason='lizhou', force_exhaust=False,
        effect_context_extra={'lizhou_free': free_order}, source_label=source.name)


@resumable()
def drain_moon(state):
    if getattr(state, 'lizhou_draining_moon', False) or getattr(state, 'lizhou_resolving', []):
        return []
    state.lizhou_draining_moon = True
    queue = getattr(state, 'lizhou_moon_queue', deque())
    try:
        while queue and not state.battle_over and state.player.is_alive():
            card = queue.popleft()
            yield auto_play(state, card, card, free_order=True)
    finally:
        state.lizhou_draining_moon = False


def escaped_flower(state, card):
    if key(card) != 'star_flower':
        return []
    # Moving to discard while full suspends the escape until a later normal draw.
    if state.player.is_hand_full():
        for pile in (state.player.exhaust_pile, state.player.draw_pile):
            if remove(pile, card):
                state.player.discard_pile.append(card)
        return []
    for pile in (state.player.exhaust_pile, state.player.draw_pile, state.player.discard_pile):
        if remove(pile, card):
            return put_hand(state, card)
    return []


def destination_override(state, card):
    """Return None for ordinary routing; exhaust events still precede returning."""
    from game.engine import move_card_to_exhaust_pile
    p = state.player
    k = key(card)
    if k == 'key':
        p.draw_pile.insert(0, card)
        if 'exhaust' in card.keywords:
            remove(p.draw_pile, card)
            return move_card_to_exhaust_pile(state, card)
        return ['钥匙置于抽牌堆底部。']
    intrinsic = k in ('star_flower', 'spinning_stardust')
    if intrinsic or (card.card_type != 'power' and powers(state, 'infinity_void') and getattr(card, 'lizhou_anchor', 0) > 0):
        logs = []
        if not intrinsic:
            card.lizhou_anchor -= 1
        if 'exhaust' in card.keywords or getattr(card, 'force_exhaust_after_play', False) or (
                card.card_type == 'skill' and p.statuses.get('corruption')):
            logs.extend(move_card_to_exhaust_pile(state, card))
            if any(c is card for c in p.hand):
                return logs
            remove(p.exhaust_pile, card)
            remove(p.discard_pile, card)
        logs.extend(put_hand(state, card))
        return logs
    return None


@resumable()
def finish_play(state, card):
    remove(getattr(state, 'lizhou_resolving', []), card)
    yield drain_moon(state)


def reserve_echo(state):
    if not powers(state, 'stardust_cancer'):
        return False
    used = getattr(state.player, 'lizhou_echo_used', 0)
    state.player.lizhou_echo_used = used+1
    return used < len(powers(state, 'stardust_cancer'))


@resumable()
def constellation_effect(state, card, target_index):
    k = key(card)
    up = card.upgraded
    p = state.player
    if k == 'aries':
        yield status(state, 'buffer', 2 if up else 1)
    elif k == 'taurus':
        yield status(state, 'lizhou_fortify', 5 if up else 3)
    elif k == 'gemini':
        yield debuff(state, 'enemy_anchor', 5 if up else 3, target_index)
        yield debuff(state, 'enemy_floating', 7 if up else 5, target_index)
    elif k == 'cancer':
        yield request(state, card.name, 'copy', [c for c in p.hand if key(c) in ZODIACS], copies=2 if up else 1)
    elif k == 'leo':
        yield status(state, 'intangible', 1)
    elif k == 'virgo':
        yield order(state, 9 if up else 6)
    elif k == 'libra':
        yield energy(state, 5 if up else 3)
    elif k == 'scorpio':
        yield status(state, 'vigor', 8 if up else 5)
    elif k == 'sagittarius':
        yield heal(state, 18 if up else 9)
    elif k == 'capricorn':
        for name in ('weak', 'vulnerable', 'frail'):
            yield debuff(state, name, 3, target_index, everyone=up)
    elif k == 'aquarius':
        yield draw(state, 4 if up else 3)
    elif k == 'pisces':
        yield create_zodiac(state, exhaust=True, zero='battle' if up else 'turn')


@resumable()
def trigger_constellation(state, zodiac_key):
    from data.card.character.lizhou_cards import create_lizhou_card
    from game.effects import get_auto_play_target_index
    card = create_lizhou_card(zodiac_key)
    echo = reserve_echo(state)
    target_index = get_auto_play_target_index(state, card)
    yield constellation_effect(state, card, target_index)
    if echo:
        yield constellation_effect(state, card, target_index)


@resumable()
def effect(state, card, effect_spec, target_index, context):
    k = key(card)
    p = state.player
    v = card.card_vars
    damage = v.get('damage', 0)
    if k in ZODIACS:
        echo = reserve_echo(state)
        yield draw(state, 1)
        if k == 'leo' and card.upgraded:
            yield block(state, 15, card)
        price = order_cost(state, card)
        qualifies = context.get('lizhou_free', False) or p.statuses.get('lizhou_order') >= price
        if qualifies:
            if not context.get('lizhou_free', False):
                yield order(state, -price, spend=True)
            yield constellation_effect(state, card, target_index)
        if echo:
            yield draw(state, 1)
            if k == 'leo' and card.upgraded:
                yield block(state, 15, card)
            if qualifies:
                yield constellation_effect(state, card, target_index)
            from game.battle_context import BattleContext
            from game.event_bus import dispatch_event
            from game.zone.zone_utils import record_player_card_played_this_turn
            record_player_card_played_this_turn(state, card, p)
            yield dispatch_event(state, 'card_play_after', BattleContext(game_state=state, player=p, source=p, card=card,
                extra={'lizhou_echo': True}))
        return []
    if card.card_type == 'power':
        gate = v.get('order_gate', 0)
        if gate and not context.get('lizhou_free', False):
            if p.statuses.get('lizhou_order') < gate:
                return ['调序不足，略过【{}】的调序效果。'.format(card.name)]
            yield order(state, -gate, spend=True)
        if k == 'time_master':
            p.lizhou_extra_turns = getattr(p, 'lizhou_extra_turns', 0)+v['count']
            state.force_end_turn_after_card = True
            state.force_end_turn_reason = card.name
        else:
            if not hasattr(p, 'lizhou_powers'):
                p.lizhou_powers = []
            if k not in ('moonlight', 'floating_tide', 'infinity_void', 'void_world', 'intuition_luck') or not powers(state, k):
                p.lizhou_powers.append({'key': k, 'card': card, 'counter': 0})
                p.statuses.add('lizhou_power_'+k, 1)
                yield ['【{}】能力生效。'.format(card.name)]
        return []
    if k in ('strike', 'meteor_fall', 'blunt_bullet', 'sharp_bullet'):
        yield hit(state, card, damage, target_index, times=2 if k == 'sharp_bullet' else 1)
        if k == 'meteor_fall' and card.upgraded:
            yield draw(state, 1)
    elif k in ('stellar_impact', 'dark_sky'):
        if k == 'dark_sky':
            yield status(state, 'lizhou_fortify', v['amount'])
        yield debuff(state, 'vulnerable', v['amount'], target_index)
        yield hit(state, card, damage, target_index)
    elif k == 'broken_hope':
        yield order(state, -p.statuses.get('lizhou_order'))
        yield hit(state, card, damage, target_index)
    elif k == 'star_warning':
        yield request(state, card.name, 'retain', list(reversed(p.draw_pile[-v['inspect']:])), v['count'], minimum=0)
        yield status(state, 'lizhou_counterbalance', 1)
        yield hit(state, card, damage, target_index)
    elif k == 'gliding_punishment':
        yield hit(state, card, damage, target_index, everyone=True)
        yield draw(state, v['count'])
    elif k == 'diamond_dust':
        for c in list(p.hand):
            yield floating(state, c, v['floating'])
            yield anchor(state, c, 2)
        yield hit(state, card, damage, target_index, everyone=True)
    elif k == 'wandering_star':
        for c in list(p.discard_pile):
            yield floating(state, c)
        yield hit(state, card, damage, target_index)
        for _ in range(2):
            if p.draw_pile:
                c = p.draw_pile.pop(random.randrange(len(p.draw_pile)))
                yield auto_play(state, card, c, free_order=True)
    elif k == 'rusted_thing':
        count = 0
        for c in list(p.hand):
            if 'retain' in c.keywords:
                count += 1
                c.keywords.remove('retain')
                if key(c) == 'star_flower':
                    c.keywords.append('retain')
            if getattr(c, 'lizhou_anchor', 0):
                count += 1
                c.lizhou_anchor = 0
        yield hit(state, card, damage, target_index, times=count*v['amount'], random_target=True)
    elif k == 'spinning_stardust':
        count = getattr(card, 'lizhou_spins', 0) if getattr(card, 'lizhou_spin_turn', -1) == state.turn_count else 0
        card.lizhou_spin_turn = state.turn_count
        card.lizhou_spins = count+1
        yield hit(state, card, damage, target_index, times=1+count//v['interval'])
    elif k == 'star_memory':
        yield hit(state, card, damage, target_index, everyone=True)
        yield request(state, card.name, 'retrieve', p.exhaust_pile)
    elif k in ('curtain_fall', 'self_destroying_sun'):
        yield order(state, -p.statuses.get('lizhou_order'))
        for c in all_cards(state):
            c.lizhou_anchor = c.lizhou_floating = 0
        yield hit(state, card, damage, target_index, everyone=True)
        if k == 'curtain_fall':
            yield request(state, card.name, 'exhaust', p.hand, 4, minimum=0)
        else:
            from game.damage import deal_damage
            from game.modifiers import apply_attack_damage_modifiers
            for ally in getattr(state, 'allied_players', []):
                if ally is not p and ally.is_alive():
                    amount = apply_attack_damage_modifiers(damage, state, p, ally, card=card)
                    yield deal_damage(state, p, ally, amount, card=card)
    elif k == 'dinosaur_buster':
        yield hit(state, card, damage, target_index)
        yield debuff(state, 'vulnerable', 3, target_index)
    elif k == 'star_breath':
        for enemy in state.enemies:
            enemy.block = 0
        yield hit(state, card, damage, target_index, everyone=True)
        yield order(state, -3)
    elif k == 'star_bloom':
        total = 0
        for c in all_cards(state):
            if key(c) == 'star_flower':
                total += getattr(c, 'lizhou_anchor', 0)
                c.lizhou_anchor = 0
        yield energy(state, (context.get('raw_x', 0)+(2 if card.upgraded else 0))*total)
        amount = p.cost
        p.cost = 0
        yield hit(state, card, 4*amount, target_index, everyone=True, hp_loss=True)
    elif k == 'tiny_annihilation':
        yield debuff(state, 'stun', 1, target_index, everyone=True)
        yield hit(state, card, context.get('lizhou_damage_difference', 0), target_index)
    elif k == 'defend':
        yield block(state, v['block'], card)
    elif k == 'star_flower':
        amount = getattr(card, 'lizhou_anchor', 0)
        card.lizhou_anchor = 0
        yield energy(state, amount)
        if not getattr(card, 'lizhou_flower_played', False):
            card.lizhou_flower_played = True
            if card.upgraded:
                yield anchor(state, card, 2)
    elif k in ('align_stars', 'star_order', 'stellar_rotation', 'colonize_orbit'):
        if k == 'star_order':
            yield draw(state, v['amount'])
        else:
            yield order(state, v['amount'])
        if 'block' in v:
            yield block(state, v['block'], card)
    elif k == 'anchoring':
        yield request(state, card.name, 'anchor', p.hand, amount=v['amount'])
    elif k == 'calculate_float':
        if len(p.hand) >= v['count']:
            yield request(state, card.name, 'floating', p.hand, v['count'])
        yield energy(state, 2)
    elif k == 'swallow_star':
        yield request(state, card.name, 'exhaust', p.hand, 2)
        yield block(state, v['block'], card)
    elif k in ('fingertip_cosmos', 'paint_sky', 'decorate_stars'):
        names = {'fingertip_cosmos': ('lizhou_fortify', 'lizhou_tenacity', 'lizhou_counterbalance'),
                 'paint_sky': ('lizhou_counterbalance',), 'decorate_stars': ('lizhou_fortify',)}[k]
        for name in names:
            yield status(state, name, v['amount'])
    elif k == 'meteor_shower':
        from game.engine import move_card_to_exhaust_pile
        cards = list(p.hand)
        for c in cards:
            if remove(p.hand, c):
                yield move_card_to_exhaust_pile(state, c)
        for _ in cards:
            yield create_zodiac(state, free_turn=True, upgraded=card.upgraded)
    elif k == 'collision':
        for name in ('weak', 'vulnerable'):
            yield debuff(state, name, 3, target_index, everyone=True)
    elif k == 'aye_captain':
        for _ in range(16):
            yield block(state, 1, card)
    elif k == 'domain':
        from data.zones.star_zone import deploy_star
        yield deploy_star(state, card.upgraded)
    elif k == 'focus':
        yield draw(state, v['count'])
    elif k == 'observe_stars':
        yield draw(state, 2)
    elif k in ('static_anchor', 'reverse_gravity'):
        yield debuff(state, 'enemy_anchor' if k == 'static_anchor' else 'enemy_floating', v['amount'], target_index)
    elif k == 'phantasm':
        if getattr(p, 'lizhou_phantasm_turn', -1) != state.turn_count:
            p.lizhou_phantasm_turn = state.turn_count
            if not hasattr(p, 'lizhou_powers'):
                p.lizhou_powers = []
            p.lizhou_powers.append({'key': k, 'card': card, 'turn': state.turn_count})
    elif k == 'key':
        yield request(state, card.name, 'key', p.draw_pile, 3)
        for pile in (p.discard_pile, p.exhaust_pile):
            p.draw_pile.extend(pile)
            pile.clear()
        random.shuffle(p.draw_pile)
    # Optional order clauses follow all base effects, including draws and choices.
    if k in ('blunt_bullet', 'sharp_bullet', 'dust_wave', 'twinkle', 'focus', 'observe_stars', 'freeze'):
        price = order_cost(state, card)
        if context.get('lizhou_free', False) or p.statuses.get('lizhou_order') >= price:
            if not context.get('lizhou_free', False):
                yield order(state, -price, spend=True)
            if k in ('focus', 'observe_stars'):
                yield draw(state, 3 if k == 'focus' else 2)
                if k == 'focus':
                    yield energy(state, 1)
            elif k == 'freeze':
                for c in list(p.hand):
                    yield anchor(state, c, v['amount'])
                yield debuff(state, 'enemy_anchor', v['amount'], target_index)
            elif k in ('blunt_bullet', 'sharp_bullet'):
                yield hit(state, card, damage, target_index, times=6 if k == 'sharp_bullet' else 1)
            elif k == 'dust_wave':
                from game.effects import get_alive_enemies
                for enemy in list(get_alive_enemies(state)):
                    yield hit(state, card, damage, state.enemies.index(enemy))
                    yield order(state, 1)
            else:
                yield block(state, v['block'], card)
                yield debuff(state, 'weak', v['amount'], target_index)


@resumable()
def before_cleanup(state):
    p = state.player
    for power in list(powers(state)):
        k, c = power['key'], power['card']
        if k == 'cast_blades':
            yield request(state, c.name, 'anchor', p.hand, c.card_vars['count'], minimum=0)
        elif k == 'phantasm' and power['turn'] == state.turn_count:
            yield request(state, c.name, 'exhaust', [h for h in p.hand if getattr(h, 'lizhou_anchor', 0)], len(p.hand), minimum=0)
    if any(getattr(r, 'relic_id', '') == 'relic.anchored_eye' for r in p.relics):
        for c in list(p.hand):
            if 'retain' in c.keywords:
                yield anchor(state, c)
    for c in p.hand:
        c.lizhou_floating = max(0, getattr(c, 'lizhou_floating', 0)-1)
        c.lizhou_anchored_before_cleanup = getattr(c, 'lizhou_anchor', 0) > 0
    candidates = [c for c in p.hand if getattr(c, 'lizhou_anchor', 0) > 0 and 'retain' not in c.keywords and 'ethereal' not in c.keywords]
    yield request(state, '锚定保留', 'paid_retain', candidates, len(candidates), minimum=0)



def after_cleanup(state):
    return []


@resumable()
def on_event(state, event, context):
    p = state.player
    if event == 'player_turn_end':
        for power in powers(state, 'intuition_luck'):
            yield request(state, '直觉与幸运', 'intuition', p.hand, len(p.hand), minimum=0, upgraded=power['card'].upgraded)
    elif event == 'damage_after' and context.extra.get('damage_kind') == 'attack':
        target, source = context.target, context.source
        if source is p and target is not p and target.is_alive() and target.statuses.get('enemy_anchor'):
            from game.damage import deal_damage
            yield deal_damage(state, p, target, target.statuses.get('enemy_anchor'), damage_kind='anchor')
        elif target is p and source is not None and source.statuses.get('enemy_floating') and context.extra.get('real_damage', 0) == 0:
            yield draw(state, 1)
            source.statuses.add('enemy_floating', -1)
    elif event == 'draw_card_after':
        c = context.card
        if key(c) == 'star_flower':
            yield draw(state, 1)
        if key(c) in ZODIACS and powers(state, 'moonlight') and remove(p.hand, c):
            if not hasattr(state, 'lizhou_moon_queue'):
                state.lizhou_moon_queue = deque()
            state.lizhou_moon_queue.append(c)
            yield drain_moon(state)
    elif event == 'card_play_after':
        c = context.card
        for power in powers(state, 'star_sea'):
            amount = getattr(c, 'lizhou_play_anchor', getattr(c, 'lizhou_anchor', 0))//3
            if amount:
                yield status(state, 'strength', amount)
                yield status(state, 'dexterity', amount)
        for power in list(powers(state, 'orderer')):
            if power['card'] is c:
                continue
            power['counter'] += 1
            if power['counter'] >= power['card'].card_vars['interval']:
                power['counter'] = 0
                yield order(state, 2)
        if key(c) in ZODIACS:
            for power in powers(state, 'fit_stars'):
                yield passive_block(state, power['card'].card_vars['amount'], power['card'])
    elif event == 'turn_start':
        p.lizhou_echo_used = 0
        count = getattr(p, 'lizhou_intuition_draw', 0)
        p.lizhou_intuition_draw = 0
        if count:
            yield draw(state, count)
        for power in list(powers(state)):
            k, c = power['key'], power['card']
            if k == 'human_dream':
                yield status(state, 'strength', 3 if c.upgraded else 2)
                yield status(state, 'dexterity', 3 if c.upgraded else 2)
            elif k in ELEMENTS:
                from data.card.character.lizhou_cards import create_lizhou_card
                yield request(state, c.name, 'constellation', [create_lizhou_card(z) for z in ELEMENTS[k]])
            elif k == 'star_sequence':
                yield create_zodiac(state, ethereal=True)
            elif k == 'anchor_kit':
                yield request(state, c.name, 'anchor', p.hand, len(p.hand), minimum=0)
            elif k == 'anchor_sail' and p.statuses.get('lizhou_order') < 6:
                yield order(state, 6)


@resumable()
def opening_flower_draws(state):
    # Innate/bottled opening cards bypass draw_cards; reserve the normal opening
    # draw count before this bonus so it is not swallowed by hand-size counting.
    flowers = [c for c in state.player.hand if key(c) == 'star_flower']
    for c in flowers:
        yield ['【{}】进入起始手牌，触发额外抽1张牌。'.format(c.name)]
        yield draw(state, 1)


def card_state_text(card):
    parts = []
    for attr, label in (('lizhou_anchor', '锚定'), ('lizhou_floating', '浮动')):
        n = getattr(card, attr, 0)
        if n:
            parts.append('{}{}'.format(label, n))
    return ' '.join(parts)
