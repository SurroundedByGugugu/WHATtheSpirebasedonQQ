"""Per-player FIFO orbs; values are resolved at trigger time."""
from dataclasses import dataclass, field
import random

NAMES = dict(lightning="闪电球", frost="冰霜球", dark="黑暗球", glass="玻璃球", plasma="等离子球")

@dataclass
class Orb:
    uid: int
    kind: str
    value: int = 0

@dataclass
class OrbRack:
    capacity: int = 0
    orbs: list = field(default_factory=list)
    next_uid: int = 1
    channeled: dict = field(default_factory=dict)
    first_channel_slot_available: bool = field(init=False)

    def __post_init__(self):
        # A character starting without slots can enter the orb system once per battle.
        self.first_channel_slot_available = self.capacity == 0

def rack(player):
    if not hasattr(player, "orb_rack"):
        player.orb_rack = OrbRack()
    return player.orb_rack

def zone_info(state):
    zone = getattr(state, "active_zone", None)
    return getattr(zone, "element", ""), bool(getattr(zone, "is_extreme", False))

def values(state, player, orb):
    focus = player.statuses.get("focus")
    element, extreme = zone_info(state)
    if orb.kind == "lightning":
        return max(0, 3 + focus), max(0, 8 + focus)
    if orb.kind == "frost":
        return max(0, 2 + focus), max(0, 5 + focus)
    if orb.kind == "dark":
        growth = max(0, 6 + focus)
        if element == "shade":
            growth = growth * 2 if extreme else growth * 3 // 2
        return growth, orb.value
    if orb.kind == "glass":
        passive = max(0, orb.value + focus)
        return passive, passive * 2
    return 1, 2

def finish_check(state, logs):
    from game.engine import check_battle_result
    if not state.battle_over:
        result = check_battle_result(state)
        if result:
            logs.append(result)
    return state.battle_over

def emit(state, player, name, orb):
    from game.battle_context import BattleContext
    from game.event_bus import dispatch_event
    return dispatch_event(state, name, BattleContext(
        game_state=state, player=player, source=player,
        extra={"orb": orb, "orb_uid": orb.uid, "orb_kind": orb.kind}))

def trigger(state, player, orb, evoke=False):
    """Execute one effect; removal is owned by evoke_orb."""
    if state.battle_over:
        return []
    from game.damage import deal_damage
    from game.block import gain_block_without_modifiers
    passive, burst = values(state, player, orb)
    amount = burst if evoke else passive
    element, extreme = zone_info(state)
    logs = ["【{}】{}：{}。".format(NAMES[orb.kind], "激发" if evoke else "被动", amount)]
    if orb.kind == "dark" and not evoke:
        orb.value += amount
    elif orb.kind == "plasma":
        player.cost += amount
    elif orb.kind == "frost":
        logs.extend(gain_block_without_modifiers(state, player, player, amount, block_source="orb"))
        if element == "water" and not finish_check(state, logs):
            regen = (3 if extreme else 2) if evoke else (2 if extreme else 1)
            player.gain_status("regeneration", regen)
            logs.append("水 Zone：获得 {} 层再生。".format(regen))
    else:
        targets = [e for e in state.enemies if e.is_alive() and not getattr(e, "_unselectable", False)]
        if targets and orb.kind == "dark":
            lowest = min(e.hp for e in targets)
            targets = [random.choice([e for e in targets if e.hp == lowest])]
        elif targets and orb.kind == "lightning" and element != "thunder" and player.statuses.get("electrodynamics") <= 0:
            targets = [random.choice(targets)]
        for target in targets:
            hit = amount * 3 // 2 if target.statuses.get("lock_on") > 0 else amount
            logs.extend(deal_damage(state, player, target, hit, damage_kind="orb"))
        if finish_check(state, logs):
            return logs
        if orb.kind == "glass" and not evoke:
            change = (1 if extreme else 0) if element == "crystal" else -1
            orb.value = max(0, orb.value + change)
    if not finish_check(state, logs):
        logs.extend(emit(state, player, "orb_evoked" if evoke else "orb_passive", orb))
        finish_check(state, logs)
    return logs

def evoke_orb(state, player, index=0, times=1):
    container = rack(player)
    if state.battle_over or times <= 0 or not 0 <= index < len(container.orbs):
        return []
    orb = container.orbs[index]
    logs = []
    for _ in range(times):
        logs.extend(trigger(state, player, orb, evoke=True))
        if state.battle_over:
            break
    container.orbs[:] = [item for item in container.orbs if item.uid != orb.uid]
    return logs

def channel(state, player, kind, count=1):
    if kind not in NAMES:
        raise ValueError("未知充能球")
    container = rack(player)
    logs = []
    for _ in range(max(0, count)):
        if state.battle_over:
            break
        if container.capacity <= 0 and container.first_channel_slot_available:
            container.capacity = 1
            container.first_channel_slot_available = False
            logs.append("首次生成充能球，获得 1 个球槽。")
        if container.capacity <= 0:
            logs.append("没有充能球栏位，无法生成。")
            break
        while len(container.orbs) >= container.capacity:
            logs.extend(evoke_orb(state, player))
            if state.battle_over:
                return logs
            if container.capacity <= 0:
                logs.append("没有充能球栏位，无法生成。")
                return logs
        orb = Orb(container.next_uid, kind, 6 if kind == "dark" else 4 if kind == "glass" else 0)
        container.next_uid += 1
        container.orbs.append(orb)
        container.channeled[kind] = container.channeled.get(kind, 0) + 1
        logs.append("生成【{}】。".format(NAMES[kind]))
        logs.extend(emit(state, player, "orb_channeled", orb))
        finish_check(state, logs)
    return logs

def trigger_passives(state, player, timing=None, snapshot=None):
    container = rack(player)
    snapshot = list(container.orbs) if snapshot is None else snapshot
    logs = []
    front = container.orbs[0] if container.orbs else None
    cables = any(getattr(r, "relic_id", "") == "relic.gold_plated_cables" for r in player.relics)
    for orb in snapshot:
        if state.battle_over:
            break
        if not any(item.uid == orb.uid for item in container.orbs):
            continue
        if timing == "start" and orb.kind != "plasma":
            continue
        if timing == "end" and orb.kind == "plasma":
            continue
        logs.extend(trigger(state, player, orb))
        if cables and orb is front and not state.battle_over and any(o.uid == orb.uid for o in container.orbs):
            logs.extend(trigger(state, player, orb))
    return logs

def set_slots(player, count):
    """Shrinking drops newest excess orbs without evoking them."""
    container = rack(player)
    container.capacity = max(0, int(count))
    if container.capacity > 0:
        container.first_channel_slot_available = False
    del container.orbs[container.capacity:]

def format_orbs(player, state=None):
    container = rack(player)
    lines = ["集中 {:+d}｜球槽 {}/{}｜最左优先激发".format(player.statuses.get("focus"), len(container.orbs), container.capacity)]
    element, extreme = zone_info(state)
    for index, orb in enumerate(container.orbs, 1):
        passive, burst = values(state, player, orb)
        extra = "积蓄{}／增长{}".format(orb.value, passive) if orb.kind == "dark" else "被动{}／激发{}".format(passive, burst)
        if orb.kind == "lightning" and (element == "thunder" or player.statuses.get("electrodynamics") > 0):
            extra += "／全体"
        if orb.kind == "glass":
            extra += "／基础{}／{}".format(orb.value, ("增长1" if extreme else "不衰减") if element == "crystal" else "衰减1")
        if orb.kind == "frost" and element == "water":
            extra += "／再生{}/{}".format(2 if extreme else 1, 3 if extreme else 2)
        lines.append("{}．{}〔{}〕".format(index, NAMES[orb.kind], extra))
    return "\n".join(lines)
