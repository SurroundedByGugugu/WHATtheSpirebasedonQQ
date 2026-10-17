"""Act-three Defect event and its pickup workflows."""
import random


def build_software_shop_event(run_state, rng=None, seed=None, source_node_type='event'):
    from data.relic.software_relics import SPECS
    from game.node.node_event_0 import EventState, EventChoice
    rng = rng or random.Random(seed)
    owned = {r.relic_id for r in run_state.relics}
    keys = [key for key in SPECS if 'relic.' + key not in owned]
    offered = rng.sample(keys, min(3, len(keys)))
    return EventState(title='软件商店', event_id='event.software_shop',
                      description='终端上陈列着几款智能软件。选择一款安装。',
                      choices=[EventChoice('【{}】{}'.format(SPECS[key][0], SPECS[key][1]),
                                           'software_install', payload={'key': key}) for key in offered]
                      or [EventChoice('离开。', 'leave')])


def obtain_software(run_state, key):
    from data.card.AAAregistry import create_card
    from data.card.upgrade_rules import upgrade_card
    from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics
    from game.node.node_ancient import (AncientState, _build_deck_selection,
                                       create_ancient_state, format_ancient, _start_card_reward)
    from game.deck_utils import can_remove_card
    rng = random.Random("{}:{}:{}".format(run_state.run_seed, run_state.current_node_id, key))
    logs = []
    if key in ('doubao', 'gpt'):
        cards = ([create_card('card.curse.enthralled'), create_card('card.curse.clumsy')]
                 if key == 'doubao' else [upgrade_card(create_card('card.creative_ai'))])
        for card in cards:
            logs.extend(add_card_to_master_deck_with_relics(run_state, card, source='软件商店'))
    elif key == 'claude':
        state = AncientState(title='Claude：移除卡牌', data={'software_after_remove': True})
        count = min(3, sum(can_remove_card(card) for card in run_state.master_deck))
        if count and _build_deck_selection(state, run_state, 'remove', count):
            run_state.pending_ancient = state
            logs.append(format_ancient(run_state))
        else:
            logs.extend(add_card_to_master_deck_with_relics(run_state, create_card('card.curse.region_lock'), source='Claude'))
    elif key == 'gemini':
        from game.reward import roll_rare_card_rewards
        cards = roll_rare_card_rewards(3, rng, 0.0, run_state=run_state)
        cards = [create_card(card.card_id) for card in cards]
        logs.extend(_start_card_reward(run_state, cards, 'Gemini：稀有牌三选一（可跳过）'))
    elif key == 'deepseek':
        run_state.pending_ancient = create_ancient_state(run_state, seed=rng.randrange(2**31), software_blessing=True)
        logs.append(format_ancient(run_state))
    return logs
