from data.relic.base_relic import RelicTemplate


class AnchoredEye(RelicTemplate):
    def __init__(self):
        super().__init__('relic.anchored_eye', '锚定之眼',
            '每回合结束时，手牌中拥有保留词条的牌各获得1锚定。', '', 'starting', 'character.lizhou')


class TwelveZodiacs(RelicTemplate):
    def __init__(self):
        super().__init__('relic.twelve_zodiacs', '十二星座卡牌',
            '获得重复星座牌时，可选其中1张随机转为星座牌，保留升级。升级状态不同不算重复；转换可连锁，也可能转回原种类。',
            '', 'starting', 'character.lizhou')


LIZHOU_RELIC_REGISTRY = {'relic.anchored_eye': AnchoredEye, 'relic.twelve_zodiacs': TwelveZodiacs}


class StarFireworks(RelicTemplate):
    def __init__(self):
        super().__init__('relic.star_fireworks', '星形烟花', '战斗开始时获得3调序。', '', 'common', 'character.lizhou')
    def on_event(self, event_name, context):
        if event_name == 'battle_start':
            from game.lizhou import order
            return order(context.game_state, 3)
        return []

class ReplicaCamera(RelicTemplate):
    def __init__(self):
        super().__init__('relic.replica_camera', '复刻相机', '每当任意卡牌被锚定3次，选择1张没有锚定的手牌获得重放1。', '', 'uncommon', 'character.lizhou')

class Telescope(RelicTemplate):
    def __init__(self):
        super().__init__('relic.telescope', '天文望远镜', '每回合开始时升级所有手牌。', '', 'rare', 'character.lizhou')
    def on_turn_start_hand_ready(self, game_state, player):
        from data.card.upgrade_rules import upgrade_card
        for card in player.hand:
            card.__dict__.update(upgrade_card(card).__dict__)
        return ['【天文望远镜】升级所有手牌。']

class Savior(RelicTemplate):
    def __init__(self):
        super().__init__('relic.savior', '救星', '每回合开始时获得1能量，抽1张牌，选择1张手牌获得锚定1和浮动1。', '', 'boss', 'character.lizhou')
    def on_turn_start_hand_ready(self, game_state, player):
        return savior_effect(game_state)

from game.resolution import resumable
@resumable()
def savior_effect(state):
    from game.lizhou import energy, draw, request
    yield energy(state, 1)
    yield draw(state, 1)
    yield request(state, '救星', 'savior', state.player.hand)

class Folder(RelicTemplate):
    def __init__(self):
        super().__init__('relic.folder', '文件夹', '手牌上限增加10。', '', 'uncommon', '')
    def on_event(self, event_name, context):
        if event_name == 'battle_start':
            context.player.max_hand_size += 10
        return []

LIZHOU_RELIC_REGISTRY.update({
    'relic.star_fireworks': StarFireworks, 'relic.replica_camera': ReplicaCamera,
    'relic.telescope': Telescope, 'relic.savior': Savior, 'relic.folder': Folder,
})
