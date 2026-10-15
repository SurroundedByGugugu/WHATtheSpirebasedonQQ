from data.zones.base_zone import ZoneTemplate
from data.zones.AAAregistry import register_zone
from game.resolution import resumable

@register_zone('zone.star')
class StarZone(ZoneTemplate):
    timed = True
    def __init__(self, extreme=False):
        super().__init__('zone.extreme_star' if extreme else 'zone.star', '极·星' if extreme else '星',
                         '每打出1张牌，随机触发1张' + ('升级后的' if extreme else '') + '星座牌效果。',
                         is_extreme=extreme, duration=3)
    def summary_text(self):
        return '{}（{}回合）：{}'.format(self.name, self.duration, self.description)
    def tick_turn_end(self):
        self.duration -= 1
    def is_expired(self):
        return self.duration <= 0
    def on_event(self, event_name, context):
        return self.resolve(context.game_state, event_name, context)
    @resumable(state_arg=1)
    def resolve(self, state, event_name, context):
        if event_name == 'card_play_after' and not self.is_expired():
            import random
            from data.card.character.lizhou_cards import ZODIACS, create_lizhou_card
            from game.lizhou import constellation_effect, draw, block
            from game.effects import get_auto_play_target_index
            c = create_lizhou_card(random.choice(ZODIACS), self.is_extreme)
            yield draw(context.game_state, 1)
            if c.card_id.endswith('.leo') and c.upgraded:
                yield block(context.game_state, 15, c)
            yield constellation_effect(context.game_state, c, get_auto_play_target_index(context.game_state, c))

@register_zone('zone.extreme_star')
class ExtremeStarZone(StarZone):
    def __init__(self):
        super().__init__(True)

def deploy_star(state, upgraded=False):
    current = state.active_zone
    if isinstance(current, StarZone) and current.is_extreme:
        current.duration += 2
    elif current is not None and current.is_extreme and not current.is_expired():
        return ['当前极 Zone 持续期间不可覆盖。']
    else:
        state.active_zone = StarZone(upgraded or isinstance(current, StarZone))
    return [state.active_zone.summary_text()]
