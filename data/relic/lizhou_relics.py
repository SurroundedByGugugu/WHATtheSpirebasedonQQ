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
