"""Watcher effects and hooks; all choices participate in ordered combat resolution."""
import random
from game.resolution import run_steps, resume
from game.stances import change_stance, gain_mantra, stance_of
from game.scry import request_scry
from game.pending_choice import PendingChoice, enqueue_pending_choice, clear_pending_choice, get_pending_choice


def remove_identity(pile, card):
    index = next((i for i,c in enumerate(pile) if c is card), None)
    if index is None:
        return False
    pile.pop(index)
    return True


def upgrade_generated(state, card):
    from data.card.upgrade_rules import upgrade_card
    if state.player.statuses.get('w_master_reality') and not card.upgraded and card.upgrade_patch:
        return upgrade_card(card)
    return card


def put_in_hand(state, card):
    pile = state.player.discard_pile if state.player.is_hand_full() else state.player.hand
    pile.append(card)
    return ['【{}】加入{}。'.format(card.name, '弃牌堆（手牌已满）' if pile is state.player.discard_pile else '手牌')]


def generate(state, key, count=1, pile='hand', upgraded=False, hits=None):
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card
    logs = []
    for _ in range(max(0,count)):
        card = create_card('card.'+key)
        if hits is not None:
            card.card_vars['amount'] = hits
        card = upgrade_card(card) if upgraded else upgrade_generated(state, card)
        card.temporary = card.created_in_battle = True
        if pile == 'hand':
            logs.extend(put_in_hand(state,card))
        else:
            state.player.draw_pile.insert(random.randrange(len(state.player.draw_pile)+1),card)
            logs.append('【{}】随机加入抽牌堆。'.format(card.name))
    return logs


def passive_block(state, amount):
    from game.block import gain_block_without_modifiers
    if amount <= 0:
        return []
    return gain_block_without_modifiers(state,state.player,state.player,amount)


def draw(state, amount):
    from game.effects import draw_cards_with_no_draw_check
    return draw_cards_with_no_draw_check(state, amount, draw_source='watcher')


def status(state, key, amount, target=None):
    from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
    return apply_status_with_player_relics(game_state=state,source=state.player,
        target=target or state.player,status_key=key,amount=amount)


def request_choice(state, source, mode, options, count=1, **payload):
    if not options:
        return ['没有可选择的牌。']
    count = min(count, len(options))
    prompt = '{}：选择 {} 项，使用 /card pick 编号（空格分隔）。\n'.format(source,count)
    prompt += '\n'.join('[{}] {}'.format(i,c.summary_text() if hasattr(c,'summary_text') else c)
                        for i,c in enumerate(options))
    enqueue_pending_choice(state, PendingChoice(kind='watcher_select',source=source,prompt=prompt,
        options=list(options),payload=dict(mode=mode,count=count,pause_resolution=True,**payload)))
    return [prompt]


def choose_cards(state, indices):
    choice = get_pending_choice(state)
    if choice is None or choice.kind != 'watcher_select':
        return '当前没有观者选择。'
    p = choice.payload
    if len(indices) != p['count'] or len(indices) != len(set(indices)) or any(i < 0 or i >= len(choice.options) for i in indices):
        return '请选择 {} 个不同的有效编号。\n{}'.format(p['count'],choice.prompt)
    selected = [choice.options[i] for i in indices]
    mode = p['mode']
    pile_name = {'meditate':'discard_pile','omniscience':'draw_pile'}.get(mode)
    if pile_name and any(not any(c is item for item in getattr(state.player,pile_name)) for c in selected):
        return '选项已变化，无法提交。'
    clear_pending_choice(state,'watcher_select')
    logs = []
    if mode == 'stance':
        logs.extend(change_stance(state, ['calm','wrath'][indices[0]]))
    elif mode == 'wish':
        card = p['card']
        if indices[0] == 2:
            run = getattr(state,'run_state',None)
            if run is not None:
                run.gold += card.card_vars['gold']
            else:
                state.player.gold = getattr(state.player,'gold',0) + card.card_vars['gold']
            logs.append('许愿获得 {} 金币。'.format(card.card_vars['gold']))
        else:
            key = ['plated_armor','strength'][indices[0]]
            logs.extend(status(state,key,card.card_vars[['armor','strength'][indices[0]]]))
    elif mode == 'foreign_influence':
        card = upgrade_generated(state,selected[0])
        card.temporary = card.created_in_battle = True
        if p['zero']:
            card.temporary_cost_override = 0
        logs.extend(put_in_hand(state,card))
    elif mode == 'meditate':
        for card in selected:
            remove_identity(state.player.discard_pile,card)
            card.temporary_retain_once = True
            logs.extend(put_in_hand(state,card))
    elif mode == 'omniscience':
        from game.effects import play_card_from_effect_and_exhaust
        card = selected[0]
        remove_identity(state.player.draw_pile,card)
        # New child continuations must run before the selecting card's parent.
        from collections import deque
        parents = getattr(state,'_resolution_steps',deque())
        state._resolution_steps = deque()
        from game.engine import move_card_to_exhaust_pile
        def auto_play():
            if state.battle_over or not state.player.is_alive() or not state.get_alive_enemies():
                return []
            return play_card_from_effect_and_exhaust(state,p['card'],card,reason='omniscience',
                source_label='通晓万物',defer_destination=True)
        logs.extend(run_steps(state,[auto_play,auto_play,
            lambda: move_card_to_exhaust_pile(state,card,reason='omniscience')]))
        state._resolution_steps.extend(parents)
    logs.extend(resume(state))
    return '\n'.join(logs)


def effect(state, card, spec, target_index, context):
    from game.effects import apply_card_effect, is_enemy_intent_attack
    from data.card.AAAregistry import create_card, CARD_REGISTRY
    from data.content_gate import is_content_enabled
    p, v, key = state.player, card.card_vars, spec['action']
    n = v.get('amount',1)
    target = state.enemies[target_index] if 0 <= target_index < len(state.enemies) else None
    was_attacking = target is not None and is_enemy_intent_attack(target.get_current_intent())
    previous = context.get('watcher_previous_type','')
    steps = []
    def add(fn, *args, **kwargs):
        steps.append(lambda: fn(*args, **kwargs))
    def standard(op, amount, profile=None, **extra):
        def perform():
            if state.battle_over or not p.is_alive():
                return []
            amount_spec = {'context_var':'watcher_amount'}
            if profile:
                amount_spec['modifier_profile'] = profile
            return apply_card_effect(state,card,dict(op=op,amount=amount_spec,**extra),target_index,dict(context,watcher_amount=amount))
        steps.append(perform)
    def block(amount):
        standard('gain_block',amount,'block',target='self')
    def damage(amount, times=1):
        op = 'deal_damage_all_enemies' if card.target == 'all_enemies' else 'deal_damage_random_enemies' if card.target == 'random_enemy' else 'deal_damage'
        standard(op,amount,'attack_damage',target='selected_enemy',times=times)
    if key == 'just_lucky':
        add(request_scry,state,n,card.name)
    if key == 'prostrate':
        add(gain_mantra,state,n)
    if 'block' in v:
        block(v['block'] + getattr(card,'_retained_block',0))
    if 'damage' in v:
        amount = v['damage'] + getattr(card,'_retained_damage',0)
        if key == 'brilliance':
            amount += getattr(p,'mantra_total',0)
        times = n if key in ('tantrum','ragnarok','expunger') else 2 if key == 'flying_sleeves' else len(state.get_alive_enemies()) if key == 'bowling_bash' else 1
        damage(amount,times)
    stances = {'eruption':'wrath','crescendo':'wrath','tantrum':'wrath','vigilance':'calm','tranquility':'calm',
               'empty_body':'none','empty_fist':'none'}
    if key in stances:
        add(change_stance,state,stances[key])
    if key == 'cut_through_fate':
        add(request_scry,state,n,card.name)
        add(draw,state,1)
    elif key == 'third_eye':
        add(request_scry,state,n,card.name)
    elif key == 'halt' and stance_of(p) == 'wrath':
        block(n)
    elif key in ('crush_joints','sash_whip') and previous == ('skill' if key == 'crush_joints' else 'attack') and target:
        add(status,state,'vulnerable' if key == 'crush_joints' else 'weak',n,target)
    elif key == 'follow_up' and previous == 'attack':
        standard('gain_energy',1)
    elif key == 'fear_no_evil' and was_attacking:
        add(change_stance,state,'calm')
    elif key in ('evaluate','reach_heaven','alpha','beta'):
        add(generate,state,{'evaluate':'insight','reach_heaven':'through_violence','alpha':'beta','beta':'omega'}[key],pile='draw_pile')
    elif key in ('carve_reality','deceive_reality'):
        add(generate,state,'smite' if key == 'carve_reality' else 'safety')
    elif key in ('miracle','insight'):
        if key == 'miracle':
            standard('gain_energy',n)
        else:
            add(draw,state,n)
    elif key == 'wheel_kick' or key == 'sanctity' and previous == 'skill':
        add(draw,state,2)
    elif key == 'empty_mind':
        add(draw,state,n)
        add(change_stance,state,'none')
    elif key == 'inner_peace':
        add(draw,state,n) if stance_of(p) == 'calm' else add(change_stance,state,'calm')
    elif key == 'indignation':
        if stance_of(p) == 'wrath':
            for enemy in state.get_alive_enemies():
                add(status,state,'vulnerable',n,enemy)
        else:
            add(change_stance,state,'wrath')
    elif key in ('pray','worship'):
        add(gain_mantra,state,n)
        if key == 'pray':
            add(generate,state,'insight',pile='draw_pile')
    elif key == 'pressure_points':
        add(status,state,'mark',n,target)
        def marks():
            from game.damage import deal_damage
            logs = []
            for enemy in state.get_alive_enemies():
                logs.extend(deal_damage(state,p,enemy,enemy.statuses.get('mark'),damage_kind='hp_loss',ignore_block=True,card=card))
            return logs
        add(marks)
    elif key == 'talk_to_the_hand':
        add(status,state,'talk_to_the_hand',n,target)
    elif key == 'wreath_of_flame':
        add(status,state,'vigor',n)
    elif key == 'wave_of_the_hand':
        add(status,state,'w_wave',n)
    elif key == 'swivel':
        add(status,state,'w_swivel',1)
    elif key == 'scrawl':
        add(lambda: draw(state,max(0,p.max_hand_size-len(p.hand))))
    elif key == 'spirit_shield':
        block(n * len(p.hand))
    elif key == 'blasphemy':
        add(change_stance,state,'divinity')
        add(lambda: setattr(p,'blasphemy_due',state.turn_count+1))
    elif key == 'collect':
        add(lambda: p.statuses.add('w_collect',context.get('x',0)+n))
    elif key == 'conjure_blade':
        add(generate,state,'expunger',pile='draw_pile',hits=context.get('x',0)+n)
    elif key == 'simmering_fury':
        add(status,state,'w_simmer',n)
    elif key == 'judgment':
        def judge():
            from game.event_bus import dispatch_event
            from game.battle_context import BattleContext
            if target is not None and 0 < target.hp <= n:
                target.hp = 0
                return ['审判：{} 的生命变为0。'.format(target.name)] + dispatch_event(state,'enemy_death',
                    BattleContext(game_state=state,player=p,source=p,target=target,card=card,extra={'damage_kind':'judgment'}))
            return ['审判未达到生命阈值。']
        add(judge)
    elif key in ('meditate','omniscience'):
        add(lambda: request_choice(state,card.name,key,
            p.discard_pile if key == 'meditate' else p.draw_pile,n if key == 'meditate' else 1,card=card))
        if key == 'meditate':
            add(change_stance,state,'calm')
    elif key == 'wish':
        add(request_choice,state,card.name,'wish',['多层护甲','力量','金币'],card=card)
    elif key == 'foreign_influence':
        def foreign():
            candidates = [cid for cid in CARD_REGISTRY if is_content_enabled('card',cid)
                and (lambda c: c.card_type == 'attack' and c.quantity in ('common','uncommon','rare')
                     and cid != 'card.lesson_learned')(create_card(cid))]
            options = [create_card(cid) for cid in random.sample(candidates,min(3,len(candidates)))]
            return request_choice(state,card.name,key,options,zero=card.upgraded)
        add(foreign)
    elif card.card_type == 'power':
        if key == 'fasting':
            add(status,state,'strength',n)
            add(status,state,'dexterity',n)
            add(status,state,'w_fasting',1)
        elif key == 'deva_form':
            add(status,state,'deva_form',1)
        else:
            add(status,state,'w_'+key,n)
    if key in ('conclude','meditate','vault'):
        def end():
            state.force_end_turn_after_card = True
            state.force_end_turn_reason = card.name
            if key == 'vault':
                state.watcher_skip_enemy_actions = True
            return []
        add(end)
    return run_steps(state,steps)


def before_resolution(state, card, context):
    if getattr(card,'card_type','') in ('attack','skill','power','status','curse'):
        context['watcher_previous_type'] = getattr(state,'watcher_last_card_type','')
        state.watcher_last_card_type = card.card_type


def on_retain(state, card):
    key = card.card_id
    if key == 'card.perseverance':
        card._retained_block = getattr(card,'_retained_block',0) + card.card_vars['amount']
    if key == 'card.windmill_strike':
        card._retained_damage = getattr(card,'_retained_damage',0) + card.card_vars['amount']
    reduction = state.player.statuses.get('w_establishment') + (key == 'card.sands_of_time')
    if isinstance(card.cost,int) and card.cost >= 0:
        card.cost = max(0,card.cost-reduction)
    return []


def on_event(state, event, context):
    p = state.player
    s = p.statuses.get
    steps = []
    def add(fn,*args,**kwargs):
        steps.append(lambda: fn(*args,**kwargs))
    if event == 'stance_changed':
        add(passive_block,state,s('w_mental_fortress'))
        for card in list(p.discard_pile):
            if card.card_id == 'card.flurry_of_blows':
                def restore(card=card):
                    if p.is_hand_full() or not remove_identity(p.discard_pile,card):
                        return []
                    return put_in_hand(state,card)
                add(restore)
        if context.extra['new_stance'] == 'wrath':
            add(draw,state,s('w_rushdown'))
    elif event == 'scry_finished':
        add(passive_block,state,s('w_nirvana'))
        for card in list(p.discard_pile):
            if card.card_id == 'card.weave':
                def restore(card=card):
                    if p.is_hand_full() or not remove_identity(p.discard_pile,card):
                        return []
                    return put_in_hand(state,card)
                add(restore)
    elif event == 'turn_start':
        if getattr(p,'blasphemy_due',None) is not None and state.turn_count >= p.blasphemy_due:
            from game.damage import deal_damage
            p.blasphemy_due = None
            add(deal_damage,state,p,p,99999,damage_kind='effect',ignore_block=True)
        if s('w_fasting'):
            p.cost = max(0,p.cost-s('w_fasting'))
        if s('w_devotion'):
            add(gain_mantra,state,s('w_devotion'))
        if s('w_simmer'):
            amount = s('w_simmer')
            p.statuses.remove('w_simmer')
            add(change_stance,state,'wrath')
            add(draw,state,amount)
        add(generate,state,'smite',s('w_battle_hymn'))
        if s('w_collect'):
            p.statuses.add('w_collect',-1)
            add(generate,state,'miracle',upgraded=True)
        if s('w_foresight'):
            add(request_scry,state,s('w_foresight'),'先见之明')
    elif event == 'player_turn_end':
        if stance_of(p) == 'calm':
            add(passive_block,state,s('w_like_water'))
        add(generate,state,'insight',s('w_study'),pile='draw_pile')
        if s('w_omega'):
            from game.damage import deal_damage
            for enemy in state.get_alive_enemies():
                add(deal_damage,state,p,enemy,s('w_omega'),damage_kind='effect')
    elif event == 'turn_end':
        p.statuses.remove('w_wave')
    elif event == 'gain_block_after' and context.target is p and s('w_wave'):
        for enemy in state.get_alive_enemies():
            add(status,state,'weak',s('w_wave'),enemy)
    elif event == 'draw_card_after' and getattr(context.card,'card_id','') == 'card.deus_ex_machina':
        card = context.card
        if remove_identity(p.hand,card):
            from game.engine import move_card_to_exhaust_pile
            add(generate,state,'miracle',card.card_vars['amount'])
            add(move_card_to_exhaust_pile,state,card,reason='deus_ex_machina')
    elif event == 'damage_after' and context.source is p and context.extra.get('damage_kind') == 'attack':
        target = context.target
        add(passive_block,state,target.statuses.get('talk_to_the_hand'))
        if getattr(context.card,'card_id','') == 'card.wallop':
            add(passive_block,state,context.extra.get('unblocked_damage',context.extra.get('real_damage',0)))
    elif event == 'enemy_death' and getattr(context.card,'card_id','') == 'card.lesson_learned':
        if not getattr(context.target, 'is_minion', False) and not getattr(context.target, '_suppress_non_minion_kill_reward_once', False):
            run = getattr(state,'run_state',None)
            if run is not None:
                from data.card.upgrade_rules import upgrade_card, has_upgrade
                options = [(i,c) for i,c in enumerate(run.master_deck) if has_upgrade(c)]
                if options:
                    i,c = random.choice(options)
                    run.master_deck[i] = upgrade_card(c)
                    return ['勤学精进：永久升级【{}】。'.format(c.name)]
    return run_steps(state,steps)


def preview(state, card, context):
    from game.card_preview import _preview_effect
    v = card.card_vars
    key = card.card_id.removeprefix('card.')
    parts = []
    for field,op,profile in [('damage','deal_damage','attack_damage'),('block','gain_block','block')]:
        if field not in v:
            continue
        amount = v[field] + getattr(card,'_retained_'+field,0)
        if key == 'brilliance':
            amount += getattr(state.player,'mantra_total',0)
        if field == 'damage' and card.target == 'all_enemies':
            op = 'deal_damage_all_enemies'
        parts.append(_preview_effect(state,card,{'op':op,'target':'selected_enemy',
            'amount':{'context_var':'watcher_amount','modifier_profile':profile}},dict(context,watcher_amount=amount)))
    return '；'.join(p for p in parts if p)
