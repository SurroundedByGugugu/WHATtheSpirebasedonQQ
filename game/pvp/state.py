# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Dict, List


PVP_STATUS_LOBBY = "lobby"
PVP_STATUS_BATTLE = "battle"
PVP_STATUS_COMPLETE = "complete"

PVP_BASE_MAX_COST = 4
PVP_MAX_CARDS_PER_TURN = 12
PVP_FORCED_TURN_BONUS = 1
PVP_OVERHEAT_THRESHOLD = 4


@dataclass
class PvpRuleConfig:
    base_cost: int = PVP_BASE_MAX_COST
    max_cards_per_turn: int = PVP_MAX_CARDS_PER_TURN
    forced_turn_bonus: int = PVP_FORCED_TURN_BONUS
    overheat_threshold: int = PVP_OVERHEAT_THRESHOLD


@dataclass
class PvpPlayerSlot:
    user_id: str
    character_id: str
    character_name: str
    side: str
    max_hp: int
    hp: int
    max_cost: int = PVP_BASE_MAX_COST
    master_deck: List[Any] = field(default_factory=list)
    relics: List[Any] = field(default_factory=list)
    potions: List[Any] = field(default_factory=list)
    player_state: Any = None
    overheated_cards: List[Any] = field(default_factory=list)

    def label(self):
        return "{}侧 {}({})".format(self.side, self.character_name, self.user_id)

    def is_alive(self):
        player = self.player_state
        if player is not None:
            return bool(player.is_alive())
        return int(self.hp) > 0


@dataclass
class PvpBattleState:
    active_user_id: str
    turn_count: int = 1
    cards_played_this_turn: int = 0
    card_play_counts_this_turn: Dict[str, int] = field(default_factory=dict)
    pending_attacks: List[Dict[str, Any]] = field(default_factory=list)
    battle_over: bool = False


@dataclass
class PvpRoomState:
    session_id: str
    host_user_id: str
    seed: int
    status: str = PVP_STATUS_LOBBY
    players: List[PvpPlayerSlot] = field(default_factory=list)
    battle: Any = None
    rules: PvpRuleConfig = field(default_factory=PvpRuleConfig)

    def get_player(self, user_id):
        user_id = str(user_id)
        for slot in self.players:
            if str(slot.user_id) == user_id:
                return slot
        return None

    def living_players(self):
        return [slot for slot in self.players if slot.is_alive()]

    def opponents_of(self, user_id):
        user_id = str(user_id)
        return [slot for slot in self.players if str(slot.user_id) != user_id]
