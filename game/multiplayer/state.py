# -*- coding: utf-8 -*-

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


ROOM_STATUS_LOBBY = "lobby"
ROOM_STATUS_BATTLE = "battle"
ROOM_STATUS_REWARD = "reward"
ROOM_STATUS_COMPLETE = "complete"
ROOM_STATUS_DEFEAT = "defeat"


@dataclass
class MultiPlayerSlot:
    user_id: str
    character_id: str
    character_name: str
    max_hp: int
    hp: int
    max_cost: int
    gold: int = 0
    max_potion_slots: int = 3
    master_deck: List[Any] = field(default_factory=list)
    relics: List[Any] = field(default_factory=list)
    potions: List[Any] = field(default_factory=list)
    player_state: Any = None
    ended_turn: bool = False

    def label(self):
        return "{}({})".format(self.character_name, self.user_id)

    def is_alive(self):
        player = self.player_state
        if player is not None:
            return bool(player.is_alive())
        return int(self.hp) > 0


@dataclass
class MultiBattleState:
    session_id: str
    encounter_id: str
    enemies: List[Any]
    active_user_id: str = ""
    turn_count: int = 1
    battle_over: bool = False
    victory: bool = False

    def get_alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy.is_alive()]

    def is_all_enemies_dead(self):
        return len(self.get_alive_enemies()) == 0


@dataclass
class MultiRewardState:
    gold_amount: int
    potion_by_user_id: Dict[str, Any] = field(default_factory=dict)
    relic_options: List[Any] = field(default_factory=list)
    relic_choices: Dict[str, Optional[int]] = field(default_factory=dict)
    resolved: bool = False
    resolution_logs: List[str] = field(default_factory=list)


@dataclass
class MultiRoomState:
    session_id: str
    host_user_id: str
    seed: int
    status: str = ROOM_STATUS_LOBBY
    players: List[MultiPlayerSlot] = field(default_factory=list)
    battle: Any = None
    reward: Any = None

    def get_player(self, user_id):
        user_id = str(user_id)
        for slot in self.players:
            if str(slot.user_id) == user_id:
                return slot
        return None

    def living_players(self):
        return [slot for slot in self.players if slot.is_alive()]

    def player_count(self):
        return len(self.players)

