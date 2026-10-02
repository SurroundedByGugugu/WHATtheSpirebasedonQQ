"""Defect card effects and selections, reusing the combat damage/block pipeline."""
import random
from game.orbs import rack, channel, trigger_passives, evoke_orb, set_slots
from game.pending_choice import PendingChoice, enqueue_pending_choice, get_pending_choice, clear_pending_choice


def put_in_hand(state, card, logs):
    player = state.player
    if player.is_hand_full():
        player.discard_pile.append(card)
        logs.append('手牌已满，【{}】进入弃牌堆。'.format(card.name))
    else:
        player.hand.append(card)
        logs.append('【{}】加入手牌。'.format(card.name))


def random_blue(state, kind=None, rarity=None, zero=False):
    from data.card.character.defect_cards import SPECS, make_card
    choices = [key for key,s in SPECS.items() if s['rarity'] != 'starting' and key != 'self_repair'
               and (kind is None or s['kind'] == kind) and (rarity is None or s['rarity'] == rarity)]
    card = make_card(random.choice(choices))
    if zero:
        card.temporary_cost_override = 0
    logs = []
    put_in_hand(state, card, logs)
    return logs


def request_selection(state, card, mode, count):
    pile_name = {'seek':'draw_pile','hologram':'discard_pile','recycle':'hand'}[mode]
    options = list(getattr(state.player, pile_name))
    count = min(count, len(options))
    if not count:
        return ['没有可选择的牌。']
    prompt = '{}：选择 {} 张牌，使用 /card pick 编号（从0开始，可空格分隔）。\n'.format(card.name,count)
    prompt += '\n'.join('[{}] {}'.format(i,c.summary_text()) for i,c in enumerate(options))
    enqueue_pending_choice(state, PendingChoice(kind='defect_select', source=card.name, prompt=prompt,
        options=options, payload=dict(mode=mode, count=count, requested_count=count, pile=pile_name, source_card=card)))
    return [prompt]


def choose_cards(state, indices):
    choice = get_pending_choice(state)
    if choice is None or choice.kind != 'defect_select':
        return '当前没有蓝色牌选择。'
    count = choice.payload['count']
    if len(indices) != count or len(set(indices)) != count or any(i < 0 or i >= len(choice.options) for i in indices):
        return '请选择 {} 个不同的有效编号。\n{}'.format(count, choice.prompt)
    player = state.player
    pile = getattr(player, choice.payload['pile'])
    cards = [choice.options[i] for i in indices]
    if any(not any(c is item for item in pile) for c in cards):
        return '选项已变化，请重新查看当前选择。'
    logs = []
    # Remove by identity: two equal dataclass card instances are distinct cards.
    for card in cards:
        index = next(i for i,c in enumerate(pile) if c is card)
        pile.pop(index)
        if choice.payload['mode'] == 'recycle':
            from game.card_cost import get_card_current_cost
            from game.engine import move_card_to_exhaust_pile
            cost = get_card_current_cost(state, card)
            energy = player.cost if cost == 'X' else max(0, int(cost))
            logs.extend(move_card_to_exhaust_pile(state, card, reason='recycle'))
            player.cost += energy
            logs.append('回收获得 {} 能量。'.format(energy))
        else:
            put_in_hand(state, card, logs)
    clear_pending_choice(state, 'defect_select')
    while state.pending_choice is not None and state.pending_choice.kind == 'defect_select':
        next_choice = state.pending_choice
        source_card = next_choice.payload['source_card']
        next_choice.options = [c for c in getattr(player,next_choice.payload['pile']) if c is not source_card]
        next_choice.payload['count'] = min(next_choice.payload['requested_count'],len(next_choice.options))
        if next_choice.payload['count']:
            next_choice.prompt = '{}：选择 {} 张牌，使用 /card pick 编号（从0开始）。\n'.format(next_choice.source,next_choice.payload['count'])
            next_choice.prompt += '\n'.join('[{}] {}'.format(i,c.summary_text()) for i,c in enumerate(next_choice.options))
            break
        clear_pending_choice(state,'defect_select')
    if state.pending_choice is not None:
        logs.append(state.pending_choice.prompt)
    return '\n'.join(logs)


def effect(state, card, spec, target_index, context):
    from game.effects import apply_card_effect, is_enemy_intent_attack
    from data.card.AAAregistry import create_card
    from game.card_cost import get_card_current_cost
    from game.engine import resolve_discarded_card
    player = state.player
    key = spec['action']
    v = card.card_vars
    n = v.get('amount', 1)
    logs = []
    target = state.enemies[target_index] if 0 <= target_index < len(state.enemies) else None

    def standard(op, amount=0, target='self', profile=None, **extra):
        if state.battle_over:
            return
        local = dict(context, _defect_amount=amount)
        amount_spec = {'context_var':'_defect_amount'}
        if profile:
            amount_spec['modifier_profile'] = profile
        logs.extend(apply_card_effect(state, card, dict(op=op, target=target, amount=amount_spec, **extra), target_index, local))
    def status(key, amount, target='self'):
        standard('gain_status', amount, target, status=key)
    def draw(count):
        logs.extend(player.draw_cards(count, state, draw_source=key))
    def generate(kind, count=1):
        logs.extend(channel(state, player, kind, count))
    def block(amount):
        standard('gain_block', max(0, amount), profile='block')
    def damage(amount, times=1, all_enemies=False, random_enemy=False):
        op = 'deal_damage_random_enemies' if random_enemy else 'deal_damage_all_enemies' if all_enemies else 'deal_damage'
        standard(op, amount, 'all_enemies' if all_enemies else 'selected_enemy', 'attack_damage', times=times)

    if key == 'melter' and target:
        target.block = 0
    damage_amount = v.get('damage')
    if damage_amount is not None:
        times = len(rack(player).orbs) if key == 'barrage' else 2 if key == 'rip_and_tear' else 1
        if key == 'thunder_strike':
            times = rack(player).channeled.get('lightning', 0)
        if key == 'claw':
            damage_amount += getattr(card, '_defect_claw_bonus', 0)
        alive_before = target is not None and target.is_alive()
        if times:
            damage(damage_amount, times, card.target == 'all_enemies', card.target == 'random_enemy')
        if key == 'sunder' and alive_before and not target.is_alive():
            player.cost += 3
            logs.append('分离击杀：获得3能量。')
        if state.battle_over:
            return logs
    if 'block' in v and key not in ('auto_shields','reinforced_body'):
        block(max(0,v['block'] - getattr(card,'_defect_steam_uses',0)) if key == 'steam_barrier' else v['block'])
        if state.battle_over:
            return logs

    if key in ('zap','ball_lightning'):
        generate('lightning')
    elif key == 'dualcast':
        logs.extend(evoke_orb(state, player, times=2))
    elif key == 'beam_cell':
        status('vulnerable', n, 'selected_enemy')
    elif key == 'charge_battery':
        status('next_turn_energy', 1)
    elif key == 'claw':
        seen = set()
        for item in [card] + player.hand + player.draw_pile + player.discard_pile:
            if item.card_id == 'card.claw' and id(item) not in seen:
                seen.add(id(item))
                item._defect_claw_bonus = getattr(item,'_defect_claw_bonus',0) + 2
                refresh_description(item)
    elif key in ('cold_snap','coolheaded'):
        generate('frost')
        if key == 'coolheaded' and not state.battle_over:
            draw(n)
    elif key == 'compile_driver':
        draw(len({o.kind for o in rack(player).orbs}))
    elif key == 'go_for_the_eyes' and target and target.is_alive() and is_enemy_intent_attack(target.get_current_intent()):
        status('weak', n, 'selected_enemy')
    elif key in ('hologram','seek','recycle'):
        logs.extend(request_selection(state, card, key, n if key == 'seek' else 1))
    elif key == 'rebound':
        status('defect_rebound', 1)
    elif key == 'recursion' and rack(player).orbs:
        orb = rack(player).orbs[0]
        kind, value = orb.kind, orb.value
        logs.extend(evoke_orb(state, player))
        if not state.battle_over:
            generate(kind)
            if rack(player).orbs and rack(player).orbs[-1].kind == kind:
                rack(player).orbs[-1].value = value
    elif key == 'stack':
        block(len(player.discard_pile) + n)
    elif key == 'steam_barrier':
        card._defect_steam_uses = getattr(card,'_defect_steam_uses',0) + 1
    elif key == 'streamline':
        card.cost = max(0, card.cost - 1)
    elif key == 'sweeping_beam':
        draw(1)
    elif key in ('turbo','overclock'):
        if key == 'turbo':
            player.cost += n
        else:
            draw(n)
        player.discard_pile.append(create_card('card.status.void' if key == 'turbo' else 'card.status.burn_i'))
    elif key == 'aggregate':
        player.cost += len(player.draw_pile) // n
    elif key == 'auto_shields' and player.block == 0:
        block(v['block'])
    elif key == 'blizzard':
        damage(n * rack(player).channeled.get('frost',0), all_enemies=True)
    elif key == 'bullseye':
        status('lock_on', n, 'selected_enemy')
    elif key == 'capacitor':
        set_slots(player, rack(player).capacity + n)
    elif key == 'chaos':
        for _ in range(n):
            generate(random.choice(('lightning','frost','dark','plasma')))
            if state.battle_over:
                break
    elif key == 'chill':
        generate('frost', sum(e.is_alive() for e in state.enemies))
    elif key == 'consume':
        status('focus', n)
        set_slots(player, rack(player).capacity - 1)
    elif key == 'darkness':
        generate('dark')
        if card.upgraded:
            logs.extend(trigger_passives(state, player, snapshot=[o for o in rack(player).orbs if o.kind == 'dark']))
    elif key == 'defragment':
        status('focus', n)
    elif key == 'doom_and_gloom':
        generate('dark')
    elif key == 'double_energy':
        player.cost *= 2
    elif key == 'equilibrium':
        status('defect_equilibrium', 1)
    elif key == 'ftl' and context.get('defect_cards_before',0) < n:
        draw(1)
    elif key == 'fusion':
        generate('plasma')
    elif key == 'genetic_algorithm':
        v['block'] += n
        uid = getattr(card,'_master_deck_uid',None)
        run = getattr(state,'run_state',getattr(player,'run_state',None))
        if uid is not None and run is not None:
            for master in run.master_deck:
                if getattr(master,'_master_deck_uid',None) == uid:
                    master.card_vars['block'] = master.card_vars.get('block',1) + n
                    refresh_description(master)
        refresh_description(card)
    elif key == 'glacier':
        generate('frost', 2)
    elif key in ('heatsinks','loop','self_repair','static_discharge'):
        status(key, n)
    elif key in ('hello_world','storm','creative_ai','echo_form','machine_learning'):
        status(key, 1)
    elif key == 'reinforced_body':
        for _ in range(context.get('x',0)):
            block(v['block'])
    elif key == 'reprogram':
        status('focus', -n)
        status('strength', n)
        status('dexterity', n)
    elif key == 'scrape':
        drawn = []
        logs.extend(player.draw_cards(n,state,draw_source='scrape',drawn_cards=drawn))
        for item in drawn:
            if any(c is item for c in player.hand) and get_card_current_cost(state, item) != 0:
                index = next(i for i,c in enumerate(player.hand) if c is item)
                player.hand.pop(index)
                logs.extend(resolve_discarded_card(state, item, reason='刮削', trigger_clever=True))
    elif key == 'skim':
        draw(n)
    elif key == 'tempest':
        generate('lightning', context.get('x',0) + n)
    elif key == 'white_noise':
        logs.extend(random_blue(state,kind='power',zero=True))
    elif key == 'all_for_one':
        for item in list(player.discard_pile):
            if not player.is_hand_full() and get_card_current_cost(state,item) == 0:
                index = next(i for i,c in enumerate(player.discard_pile) if c is item)
                player.discard_pile.pop(index)
                put_in_hand(state,item,logs)
    elif key == 'amplify_defect':
        status('amplify',n)
    elif key == 'biased_cognition':
        status('focus',n)
        status('bias',1)
    elif key == 'buffer_defect':
        status('buffer',n)
    elif key == 'core_surge':
        status('artifact',1)
    elif key == 'electrodynamics':
        status('electrodynamics',1)
        generate('lightning',n)
    elif key == 'fission':
        removed = 0
        snapshot = list(rack(player).orbs)
        for orb in snapshot:
            index = next((i for i,o in enumerate(rack(player).orbs) if o.uid == orb.uid),None)
            if index is None:
                continue
            if card.upgraded:
                logs.extend(evoke_orb(state, player, index))
            else:
                rack(player).orbs.pop(index)
            if state.battle_over:
                break
            removed += 1
        if not state.battle_over:
            player.cost += removed
            draw(removed)
    elif key == 'hyperbeam':
        status('focus',-3)
    elif key == 'meteor_strike':
        generate('plasma',3)
    elif key == 'multi_cast':
        logs.extend(evoke_orb(state,player,times=context.get('x',0)+n))
    elif key == 'rainbow':
        for kind in ('lightning','frost','dark'):
            generate(kind)
    elif key == 'reboot':
        player.draw_pile.extend(player.hand)
        player.draw_pile.extend(player.discard_pile)
        player.hand.clear()
        player.discard_pile.clear()
        random.shuffle(player.draw_pile)
        for relic in player.relics:
            handler = getattr(relic,'on_shuffle',None)
            if handler:
                logs.extend(handler(state,player) or [])
        draw(n)
    if key == 'steam_barrier':
        refresh_description(card)
    return logs


def refresh_description(card):
    from data.card.character.defect_cards import SPECS
    key = card.card_id.removeprefix('card.')
    if key in SPECS and isinstance(SPECS[key]['text'],str):
        variables = dict(card.card_vars)
        if key == 'claw':
            variables['damage'] += getattr(card,'_defect_claw_bonus',0)
        if key == 'steam_barrier':
            variables['block'] = max(0, variables['block'] - getattr(card,'_defect_steam_uses',0))
        card.description = SPECS[key]['text'].format(**variables)


def initialize_battle(state):
    from data.character.AAAregistry import create_character
    from game.orbs import OrbRack
    player = state.player
    template = create_character(player.character_id)
    slots = getattr(template,'starting_orb_slots',0)
    if any(r.relic_id == 'relic.runic_capacitor' for r in player.relics):
        slots += 3
    player.orb_rack = OrbRack(capacity=slots)


def before_card(state, card, context, logs):
    """Once per played card, before effects; reserve rebound and echo charges."""
    if getattr(card,'card_type',None) not in ('attack','skill','power','status','curse'):
        return
    player = state.player
    turn = state.turn_count
    if getattr(state,'defect_play_turn',None) != turn:
        state.defect_play_turn = turn
        state.defect_plays = 0
        state.defect_echo_used = 0
    card._defect_rebound = player.statuses.get('defect_rebound') > 0
    if card._defect_rebound:
        player.statuses.add('defect_rebound',-1)
    echo = player.statuses.get('echo_form')
    # Echo gained midturn starts copying subsequent cards on that same turn.
    if echo > getattr(state,'defect_echo_used',0):
        state.defect_echo_used = getattr(state,'defect_echo_used',0) + 1
        context['replay_extra'] = context.get('replay_extra',0) + 1
        logs.append('回响形态：本张牌额外结算一次。')


def before_resolution(state, card, context):
    if getattr(card,'card_type',None) not in ('attack','skill','power','status','curse'):
        return []
    if getattr(state,'defect_play_turn',None) != state.turn_count:
        state.defect_play_turn = state.turn_count
        state.defect_plays = 0
    context['defect_cards_before'] = getattr(state,'defect_plays',0)
    state.defect_plays = context['defect_cards_before'] + 1
    logs = []
    player = state.player
    if card.card_type == 'power':
        state.defect_powers_played = getattr(state,'defect_powers_played',0) + 1
        logs.extend(player.draw_cards(player.statuses.get('heatsinks'), state, draw_source='heatsinks'))
        logs.extend(channel(state, player, 'lightning', player.statuses.get('storm')))
    return logs


def on_event(state, event, context):
    player = state.player
    logs = []
    if event == 'turn_start' and not state.battle_over:
        bias = player.statuses.get('bias')
        if bias:
            from game.status.status_gain import format_status_gain_log
            result = player.gain_status_with_result('focus',-bias)
            logs.append('偏差认知：' + format_status_gain_log(player,'focus',-bias,result))
        if rack(player).orbs:
            from game.orbs import trigger
            orb = rack(player).orbs[0]
            for _ in range(player.statuses.get('loop')):
                if not any(o.uid == orb.uid for o in rack(player).orbs) or state.battle_over:
                    break
                logs.extend(trigger(state,player,orb))
        for key,kind,rarity in [('hello_world',None,'common'),('creative_ai','power',None)]:
            for _ in range(player.statuses.get(key)):
                if not state.battle_over:
                    logs.extend(random_blue(state,kind=kind,rarity=rarity))
    elif event == 'damage_after' and context.target is player and context.extra.get('real_damage',0) > 0:
        if context.extra.get('damage_kind') == 'attack' and player.is_alive():
            logs.extend(channel(state,player,'lightning',player.statuses.get('static_discharge')))
    elif event == 'turn_end':
        player.statuses.remove('defect_equilibrium')
        player.statuses.remove('defect_rebound')
    elif event == 'battle_end' and context.extra.get('victory'):
        from game.relic_logic.combat_relic_utils import heal_player_in_combat
        amount = player.statuses.get('self_repair')
        if amount:
            logs.extend(heal_player_in_combat(state,amount,'自我修复'))
            player.statuses.remove('self_repair')
    return logs


def preview(state, card, context):
    """Read-only dynamic attack/block values using the standard preview rules."""
    from game.card_preview import _preview_effect
    key = card.card_id.removeprefix('card.')
    player = state.player
    damage = card.card_vars.get('damage')
    block = card.card_vars.get('block')
    times = 1
    if key == 'claw':
        damage += getattr(card,'_defect_claw_bonus',0)
    elif key == 'blizzard':
        damage = card.card_vars['amount'] * rack(player).channeled.get('frost',0)
    elif key == 'barrage':
        times = len(rack(player).orbs)
    elif key == 'thunder_strike':
        times = rack(player).channeled.get('lightning',0)
    elif key == 'rip_and_tear':
        times = 2
    elif key == 'stack':
        block = len(player.discard_pile) + card.card_vars['amount']
    elif key == 'steam_barrier':
        block = max(0,block-getattr(card,'_defect_steam_uses',0))
    elif key == 'auto_shields' and player.block:
        return '已有格挡，不获得额外格挡'
    parts = []
    if damage is not None:
        local = dict(context,defect_preview=damage)
        op = 'deal_damage_all_enemies' if card.target == 'all_enemies' else 'deal_damage_random_enemies' if card.target == 'random_enemy' else 'deal_damage'
        text = _preview_effect(state,card,{'op':op,'target':'selected_enemy','amount':{'context_var':'defect_preview','modifier_profile':'attack_damage'}},local)
        if times != 1:
            text += ' ×{}'.format(times)
        parts.append(text)
    if block is not None:
        local = dict(context,defect_preview=block)
        text = _preview_effect(state,card,{'op':'gain_block','amount':{'context_var':'defect_preview','modifier_profile':'block'}},local)
        if key == 'reinforced_body':
            text += ' ×{}'.format(context.get('x',0))
        parts.append(text)
    if key in ('multi_cast','tempest'):
        parts.append('{} {} 次'.format('激发' if key == 'multi_cast' else '生成闪电球',context.get('x',0)+card.card_vars['amount']))
    return '；'.join(part for part in parts if part)
