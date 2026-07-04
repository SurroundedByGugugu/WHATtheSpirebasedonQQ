# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import List, Dict, Any
from game.status.status_container import StatusContainer
from game.status.status_display import get_status_display_text
from data.zones.element_zones import get_element_display_name
ATTACK_TYPE_NAME_MAP = {
        "slash": "斩击",
        "piercing": "突刺",
        "blunt": "打击",
        "magic": "魔法",
    }

def get_attack_type_display_name(attack_type):
    return ATTACK_TYPE_NAME_MAP.get(attack_type, attack_type)

@dataclass
class EnemyIntent:
    kind: str
    value: int = 0
    status: str = ""
    target: str = "player"
    attack_type: str = ""
    attack_element: str = ""
    repeat: int = 1
    card_id: str = ""
    count: int = 1
    message: str = ""
    actions: List[Any] = field(default_factory=list)
    heal_unblocked: bool = False

    def to_text(self):
        if self.kind == "multi":
            parts = []
            for child in self.actions:
                if hasattr(child, "to_text"):
                    parts.append(child.to_text())
            if parts:
                return "；".join(parts)
            return "复合行动"

        if self.kind == "attack":
            tag_parts = []
            if self.attack_element:
                tag_parts.append(get_element_display_name(self.attack_element))
            if self.attack_type:
                tag_parts.append(get_attack_type_display_name(self.attack_type))

            if tag_parts:
                prefix = "{} 攻击".format("/".join(tag_parts))
            else:
                prefix = "攻击"

            if int(self.repeat) > 1:
                text = "{} {} ×{}".format(prefix, self.value, int(self.repeat))
            else:
                text = "{} {}".format(prefix, self.value)

            if getattr(self, "heal_unblocked", False):
                text += "，回复未被格挡伤害等量生命"

            return text

        if self.kind == "block":
            return "获得 {} 点格挡".format(self.value)
        if self.kind == "heal_all_allies":
            return "己方全员回复 {} 点生命".format(int(self.value))

        if self.kind == "status_all_allies":
            status_name_map = {
                "strength": "力量",
                "dexterity": "敏捷",
                "artifact": "人工制品",
                "ritual": "仪式",
                "metallicize": "金属化",
            }
            status_name = status_name_map.get(self.status, self.status)
            return "己方全员获得 {} 点{}".format(int(self.value), status_name)

        if self.kind == "block_mystic_or_self":
            return "给予神秘术士 {} 点格挡；若神秘术士不存在则自身获得 {} 点格挡".format(
                int(self.value),
                int(self.value)
            )
        if self.kind == "summon_gremlins":
            return "召唤 {} 只随机地精".format(int(self.count))

        if self.kind == "gremlin_leader_rally":
            return "所有敌人获得 {} 点力量，所有爪牙获得 {} 点格挡".format(
                int(self.value),
                int(self.count)
            )
        if self.kind == "summon_fixed_enemies":
            if self.message:
                return self.message
            return "召唤 {} 个敌人".format(int(self.count))

        if self.kind == "champ_burst":
            return "移除所有负面效果，获得 6 点力量"

        if self.kind == "bronze_orb_capture_card":
            return "将你抽牌堆中稀有度最高的牌之一移出战斗"

        if self.kind == "block_bronze_automaton":
            return "给予铜制机械人偶 {} 点格挡".format(int(self.value))

        if self.kind == "collector_buff":
            return "自身和所有火炬头获得 3 点力量，自身获得 15 点格挡"

        if self.kind == "collector_summon_torch_heads":
            return "召唤火炬头，将火炬头数量补至 2"
        if self.kind == "smart_ally_block_or_attack":
            return "给予随机队友 {} 点格挡；若无队友则攻击 {}".format(
                self.value,
                self.count
            )
        if self.kind == "split":
            return "分裂"
        
        if self.kind in ("add_card_to_discard", "add_card_to_draw", "add_card_to_hand"):
            card_name_map = {
                "card.status.slime_i": "黏液I",
                "card.status.dazed": "眩晕",
                "card.status.wound": "伤口",
                "card.status.burn_i": "灼伤I",
                "card.status.burn_ii": "灼伤II",
                "card.curse.parasite": "寄生",
                "card.status.void": "虚空",
            }

            card_name = card_name_map.get(self.card_id, self.card_id)

            if self.kind == "add_card_to_draw":
                pile_name = "抽牌堆"
            elif self.kind == "add_card_to_hand":
                return "向你的手牌加入 {} 张【{}】；若手牌已满则进入弃牌堆".format(
                    int(self.count),
                    card_name
                )
            else:
                pile_name = "弃牌堆"

            return "向你的{}加入 {} 张【{}】".format(
                pile_name,
                int(self.count),
                card_name
            )
        if self.kind == "add_curse_to_master_deck":
            card_name_map = {
                "card.curse.parasite": "寄生",
            }
            card_name = card_name_map.get(self.card_id, self.card_id)
            return "将 {} 张【{}】加入你的牌组".format(int(self.count), card_name)
        
        if self.kind == "status":
            status_name_map = {
                "vulnerable": "易伤",
                "weak": "虚弱",
                "frail": "脆弱",
                "thorns": "荆棘",
                "strength": "力量",
                "dexterity": "敏捷",
                "poison": "中毒",
                "poison_thorns": "毒荆棘",
                "artifact": "人工制品",
                "pain_stab": "疼痛戳刺",
                "stun": "眩晕",
                "ritual": "仪式",
                "barricade": "壁垒",
                "hex": "邪咒",
                "malleable": "柔韧",
                "curl_up": "蜷缩",
                "spore_cloud": "孢子云",
                "entangled": "缠身",
                "confusion": "混乱",
                "enrage": "激怒",
                "metallicize": "金属化",
                "burn": "烧伤",
                "shape_shift": "形态转换",
                "sharp_hide": "锋利外甲",
                "plated_armor": "多层护甲",
                "flying": "飞行",
                "life_link": "生命链接",
                "fading": "消逝",
                "shifting": "变幻",
                "writhing": "扭动",
                "self_destruct": "自爆",
                "constricted": "缠绕",
                "slow": "缓慢",
                "curious": "好奇",
                "time_warp": "时间扭曲",
                "draw_reduction": "抽牌减少",
            }
            status_name = status_name_map.get(self.status, self.status)

            value = int(self.value)
            if value < 0:
                if self.target == "self":
                    return "自身失去 {} 点{}".format(abs(value), status_name)
                return "使玩家失去 {} 点{}".format(abs(value), status_name)

            if self.target == "self":
                return "自身获得 {} 点{}".format(value, status_name)
            return "给予玩家 {} 点{}".format(value, status_name)
        
        if self.kind == "steal_gold":
            return "偷取 {} 金币".format(int(self.value))

        if self.kind == "escape":
            return "逃离战斗"
        
        if self.kind == "wait":
            if self.message:
                return self.message
            return "蓄力"
        
        return "未知意图"
    
@dataclass
class EnemyActionResult:
    action: Dict[str, Any]
    logs: List[str]


class Enemy(object):
    """
    敌人父类。

    约定：
    1. 敌人只管理自己的 hp、block、intent。
    2. 敌人 attack 时不直接扣玩家血，只返回 action。
    3. 具体伤害结算交给 engine.py。
    """

    def __init__(self, enemy_id, name, max_hp):
        self.enemy_id = enemy_id
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.block = 0
        self.statuses = StatusContainer()
        # 狂宴等效果使用。普通敌人默认不是爪牙。
        self.is_minion = False

    def is_alive(self):
        return self.hp > 0
    
    def clear_block(self):
        old_block = int(getattr(self, "block", 0))

        # 敌人也可能拥有壁垒，例如圆球守护者。
        if self.get_status_value("barricade") > 0:
            return 0

        self.block = 0
        return old_block

    def get_current_intent(self):
        raise NotImplementedError

    def get_intent_text(self, game_state=None):
        if not self.is_alive():
            return "已经走了有一会了"
        if game_state is not None:
            from game.intent_preview import format_enemy_intent_text
            return format_enemy_intent_text(game_state, self)

        return self.get_current_intent().to_text()

    def act(self):
        raise NotImplementedError

    def take_damage(self, damage):
        if damage <= 0:
            return "{} 没有受到伤害。".format(self.name)

        blocked = min(self.block, damage)
        self.block -= blocked

        real_damage = damage - blocked
        self.hp -= real_damage

        if self.hp < 0:
            self.hp = 0

        return "{} 受到 {} 点伤害，剩余 HP：{}/{}，格挡：{}。".format(
            self.name,
            real_damage,
            self.hp,
            self.max_hp,
            self.block
        )

    def status_text(self, game_state=None):
        intent_text = self.get_intent_text(game_state)
        if game_state is not None:
            player = getattr(game_state, "player", None)
            if any(getattr(relic, "relic_id", "") == "relic.runic_dome" for relic in getattr(player, "relics", []) or []):
                intent_text = "？？？" if self.is_alive() else self.get_intent_text(game_state)
        return "{} HP：{}/{}；格挡：{}；意图：{}；状态：{}".format(
            self.name,
            self.hp,
            self.max_hp,
            self.block,
            intent_text,
            get_status_display_text(self.statuses)
        )
    
    def get_status_value(self, key):
        return self.statuses.get(key)

    def gain_status(self, key, amount):
        from game.status.status_gain import add_status_with_artifact
        result = add_status_with_artifact(self, key, amount)
        return result["current"]

    def gain_status_with_result(self, key, amount):
        from game.status.status_gain import add_status_with_artifact
        return add_status_with_artifact(self, key, amount)
    
