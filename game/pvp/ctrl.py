# -*- coding: utf-8 -*-

import copy

from data.relic.AAAregistry import create_relic
from game.display_names import format_relic_display_name
from game.pvp.state import PVP_STATUS_BATTLE
from game.status.status_defs import get_status_name


RULE_ALIASES = {
    "base_cost": "base_cost",
    "base": "base_cost",
    "cost": "base_cost",
    "fee": "base_cost",
    "基础费用": "base_cost",
    "费用": "base_cost",

    "max_cards": "max_cards_per_turn",
    "max_cards_per_turn": "max_cards_per_turn",
    "cards": "max_cards_per_turn",
    "maxplay": "max_cards_per_turn",
    "出牌上限": "max_cards_per_turn",
    "单回合最大出牌数": "max_cards_per_turn",

    "forced_bonus": "forced_turn_bonus",
    "forced_turn_bonus": "forced_turn_bonus",
    "bonus": "forced_turn_bonus",
    "强制奖励": "forced_turn_bonus",
    "切换奖励": "forced_turn_bonus",

    "overheat": "overheat_threshold",
    "overheat_threshold": "overheat_threshold",
    "过热": "overheat_threshold",
    "过热阈值": "overheat_threshold",
}


class PvpCtrlConsole(object):
    """Dedicated control console for PVP narrative rooms."""

    def handle(self, room, user_id, parts):
        if room is None:
            return "当前会话还没有 PVP 房。使用 /card pvp new [角色编号] 创建。"

        if len(parts) < 4:
            return self.help_text(room)

        command = parts[3].lower()
        args = parts[4:]

        if command in ("help", "帮助"):
            return self.help_text(room)
        if command in ("rule", "rules", "规则"):
            return self.handle_rule(room, user_id, args)
        if command in ("players", "player", "玩家"):
            return self.format_players(room)
        if command == "addcard":
            return self.handle_add_card(room, user_id, args)
        if command == "removecard":
            return self.handle_remove_card(room, user_id, args)
        if command == "addrelic":
            return self.handle_add_relic(room, user_id, args)
        if command == "removerelic":
            return self.handle_remove_relic(room, user_id, args)
        if command == "addhp":
            return self.handle_add_hp(room, user_id, args)
        if command == "sethp":
            return self.handle_set_hp(room, user_id, args)
        if command == "addmaxhp":
            return self.handle_add_max_hp(room, user_id, args)
        if command == "setmaxhp":
            return self.handle_set_max_hp(room, user_id, args)
        if command == "addcost":
            return self.handle_add_cost(room, user_id, args)
        if command == "setcost":
            return self.handle_set_cost(room, user_id, args)
        if command == "addblock":
            return self.handle_add_block(room, user_id, args)
        if command == "setblock":
            return self.handle_set_block(room, user_id, args)
        if command == "addstate":
            return self.handle_add_state(room, user_id, args)
        if command == "removestate":
            return self.handle_remove_state(room, user_id, args)
        if command == "draw":
            return self.handle_draw(room, user_id, args)
        if command in ("active", "turnplayer", "行动者"):
            return self.handle_active(room, user_id, args)
        if command in ("battle", "setbattle", "战斗"):
            return self.handle_battle_value(room, user_id, args)

        return "未知 PVP ctrl 指令：{}。\n{}".format(command, self.help_text(room))

    def help_text(self, room=None):
        lines = [
            "PVP 专用控制台：",
            "/card pvp ctrl rule                 查看规则",
            "/card pvp ctrl rule base_cost 4",
            "/card pvp ctrl rule max_cards 12",
            "/card pvp ctrl rule forced_bonus 1",
            "/card pvp ctrl rule overheat 4",
            "/card pvp ctrl addcard [玩家] 打击 牌库 [数量]",
            "/card pvp ctrl addcard [玩家] 打击 手牌 [数量]",
            "/card pvp ctrl removecard [玩家] 打击 弃牌堆 [数量]",
            "/card pvp ctrl addrelic [玩家] 墨水瓶 [数量]",
            "/card pvp ctrl addhp [玩家] 10",
            "/card pvp ctrl sethp [玩家] 30",
            "/card pvp ctrl setcost [玩家] 6",
            "/card pvp ctrl addstate [玩家] 力量 3",
            "/card pvp ctrl removestate [玩家] 易伤",
            "/card pvp ctrl active 玩家编号",
            "/card pvp ctrl battle turn 3",
        ]
        if room is not None:
            lines.append("")
            lines.append(self.format_rules(room))
        return "\n".join(lines)

    def is_host(self, room, user_id):
        return str(room.host_user_id) == str(user_id)

    def _resolve_player_ref(self, room, raw, current_user_id=None):
        text = str(raw or "").strip()
        if not text:
            return None
        lowered = text.lower()
        if lowered in ("self", "me", "自己", "我"):
            return room.get_player(current_user_id)
        for index, slot in enumerate(room.players):
            if lowered == str(index):
                return slot
            if lowered == str(slot.user_id).lower():
                return slot
            if lowered == str(slot.side).lower():
                return slot
        return None

    def _target_from_args(self, room, user_id, args):
        if args:
            explicit = self._resolve_player_ref(room, args[0], current_user_id=user_id)
            if explicit is not None:
                return explicit, args[1:], True
        return room.get_player(user_id), args, False

    def _target_or_error(self, room, user_id, args):
        slot, remaining, explicit = self._target_from_args(room, user_id, args)
        if slot is None:
            return None, remaining, "你不是当前 PVP 房的参战者；请显式指定玩家编号。"
        if explicit and str(slot.user_id) != str(user_id) and not self.is_host(room, user_id):
            return None, remaining, "只有房主可以修改其他玩家。"
        return slot, remaining, ""

    def _host_only(self, room, user_id):
        if not self.is_host(room, user_id):
            return "只有房主可以修改 PVP 房规则或战斗调度。"
        return ""

    def format_rules(self, room):
        rules = room.rules
        return "当前规则：base_cost={}；max_cards={}；forced_bonus={}；overheat={}。".format(
            int(rules.base_cost),
            int(rules.max_cards_per_turn),
            int(rules.forced_turn_bonus),
            int(rules.overheat_threshold),
        )

    def handle_rule(self, room, user_id, args):
        if not args:
            return self.format_rules(room)
        error = self._host_only(room, user_id)
        if error:
            return error
        if len(args) < 2:
            return "用法：/card pvp ctrl rule max_cards 12。\n{}".format(self.format_rules(room))

        key = RULE_ALIASES.get(str(args[0]).strip().lower())
        if key is None:
            return "未知规则：{}。\n{}".format(args[0], self.format_rules(room))

        from app.debug_console import parse_amount
        value = parse_amount(args[1])
        if value is None:
            return "规则数值必须是整数。"

        min_value = 1 if key == "max_cards_per_turn" else 0
        if value < min_value:
            return "{} 不能小于 {}。".format(key, min_value)

        old_value = int(getattr(room.rules, key))
        setattr(room.rules, key, int(value))
        if key == "base_cost":
            self._sync_base_cost(room, int(value))
        return "PVP 规则 {}：{} -> {}。\n{}".format(
            key,
            old_value,
            int(value),
            self.format_rules(room),
        )

    def _sync_base_cost(self, room, value):
        for slot in room.players:
            slot.max_cost = int(value)
            player = slot.player_state
            if player is not None:
                player.max_cost = int(value)

    def format_players(self, room):
        lines = ["PVP 玩家："]
        for index, slot in enumerate(room.players):
            lines.append("[{}] {} user_id={} side={}".format(
                index,
                slot.character_name,
                slot.user_id,
                slot.side,
            ))
        return "\n".join(lines)

    def _get_pile(self, slot, pile_name):
        if pile_name == "master_deck":
            return slot.master_deck, "牌库"
        player = slot.player_state
        if player is None:
            return None, ""
        title_by_pile = {
            "hand": "手牌",
            "draw_pile": "抽牌堆",
            "discard_pile": "弃牌堆",
            "exhaust_pile": "消耗牌堆",
        }
        return getattr(player, pile_name, None), title_by_pile.get(pile_name, pile_name)

    def _sync_slot_from_player(self, slot):
        player = slot.player_state
        if player is None:
            return
        slot.hp = int(getattr(player, "hp", slot.hp) or 0)
        slot.max_hp = int(getattr(player, "max_hp", slot.max_hp) or 0)
        slot.relics = getattr(player, "relics", []) or []
        slot.potions = getattr(player, "potions", []) or []

    def handle_add_card(self, room, user_id, args):
        from app.debug_console import create_console_card, parse_optional_count_and_pile, resolve_pile_name
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return error
        if len(args) < 2:
            return "用法：/card pvp ctrl addcard [玩家] 卡牌名 牌堆 [数量]。"
        card_name = args[0]
        count, raw_pile = parse_optional_count_and_pile(args[1:])
        if count is None:
            return "数量必须是正整数。"
        pile_name = resolve_pile_name(raw_pile)
        if pile_name is None:
            return "未知牌堆：{}。".format(raw_pile)
        pile, pile_title = self._get_pile(slot, pile_name)
        if pile is None:
            return "当前没有可修改的{}。".format(raw_pile)
        sample = create_console_card(card_name)
        if sample is None:
            return "未知卡牌：{}。".format(card_name)
        for _ in range(count):
            card = copy.deepcopy(sample)
            if room.status == PVP_STATUS_BATTLE:
                from game.pvp.engine import _ensure_card_uid
                _ensure_card_uid(card)
            pile.append(card)
        return "PVP ctrl：已向 {} 的{}加入 {} 张【{}】。".format(
            slot.label(),
            pile_title,
            count,
            getattr(sample, "name", card_name),
        )

    def handle_remove_card(self, room, user_id, args):
        from app.debug_console import card_matches, parse_optional_count_and_pile, resolve_pile_name
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return error
        if len(args) < 2:
            return "用法：/card pvp ctrl removecard [玩家] 卡牌名 牌堆 [数量]。"
        card_name = args[0]
        count, raw_pile = parse_optional_count_and_pile(args[1:])
        if count is None:
            return "数量必须是正整数。"
        pile_name = resolve_pile_name(raw_pile)
        if pile_name is None:
            return "未知牌堆：{}。".format(raw_pile)
        pile, pile_title = self._get_pile(slot, pile_name)
        if pile is None:
            return "当前没有可修改的{}。".format(raw_pile)
        removed = []
        kept = []
        remaining = count
        for card in pile:
            if remaining > 0 and card_matches(card, card_name):
                removed.append(card)
                remaining -= 1
            else:
                kept.append(card)
        pile[:] = kept
        if not removed:
            return "PVP ctrl：{} 的{}中没有找到【{}】。".format(slot.label(), pile_title, card_name)
        return "PVP ctrl：已从 {} 的{}移除 {} 张【{}】。".format(
            slot.label(),
            pile_title,
            len(removed),
            getattr(removed[0], "name", card_name),
        )

    def handle_add_relic(self, room, user_id, args):
        from app.debug_console import parse_positive_int, resolve_relic_id
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return error
        if not args:
            return "用法：/card pvp ctrl addrelic [玩家] 遗物名 [数量]。"
        relic_name = args[0]
        count = parse_positive_int(args[1], default=1) if len(args) >= 2 else 1
        if count is None:
            return "数量必须是正整数。"
        relic_id = resolve_relic_id(relic_name)
        if relic_id is None:
            return "未知遗物：{}。".format(relic_name)
        first_relic = None
        for _ in range(count):
            relic = create_relic(relic_id)
            if first_relic is None:
                first_relic = relic
            slot.relics.append(relic)
        if slot.player_state is not None:
            slot.player_state.relics = slot.relics
        return "PVP ctrl：{} 获得 {} 个{}。".format(
            slot.label(),
            count,
            format_relic_display_name(first_relic),
        )

    def handle_remove_relic(self, room, user_id, args):
        from app.debug_console import parse_positive_int, relic_matches
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return error
        if not args:
            return "用法：/card pvp ctrl removerelic [玩家] 遗物名 [数量]。"
        relic_name = args[0]
        count = parse_positive_int(args[1], default=1) if len(args) >= 2 else 1
        if count is None:
            return "数量必须是正整数。"
        removed = []
        kept = []
        remaining = count
        for relic in slot.relics:
            if remaining > 0 and relic_matches(relic, relic_name):
                removed.append(relic)
                remaining -= 1
            else:
                kept.append(relic)
        slot.relics[:] = kept
        if slot.player_state is not None:
            slot.player_state.relics = slot.relics
        if not removed:
            return "PVP ctrl：{} 没有找到遗物【{}】。".format(slot.label(), relic_name)
        return "PVP ctrl：已从 {} 移除 {} 个{}。".format(
            slot.label(),
            len(removed),
            format_relic_display_name(removed[0]),
        )

    def _entity_for_slot(self, slot):
        return slot.player_state if slot.player_state is not None else slot

    def _parse_target_amount(self, room, user_id, args, usage):
        from app.debug_console import parse_amount
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return None, None, error
        if not args:
            return None, None, usage
        amount = parse_amount(args[0])
        if amount is None:
            return None, None, "数值必须是整数。"
        return slot, amount, ""

    def handle_add_hp(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl addhp [玩家] 数量。")
        if error:
            return error
        owner = self._entity_for_slot(slot)
        old_hp = int(getattr(owner, "hp", 0))
        max_hp = int(getattr(owner, "max_hp", old_hp))
        owner.hp = max(0, min(max_hp, old_hp + amount))
        self._sync_slot_from_player(slot)
        return "PVP ctrl：{} HP {} -> {} / {}。".format(slot.label(), old_hp, owner.hp, max_hp)

    def handle_set_hp(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl sethp [玩家] 数量。")
        if error:
            return error
        owner = self._entity_for_slot(slot)
        old_hp = int(getattr(owner, "hp", 0))
        max_hp = int(getattr(owner, "max_hp", old_hp))
        owner.hp = max(0, min(max_hp, amount))
        self._sync_slot_from_player(slot)
        return "PVP ctrl：{} HP {} -> {} / {}。".format(slot.label(), old_hp, owner.hp, max_hp)

    def handle_add_max_hp(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl addmaxhp [玩家] 数量。")
        if error:
            return error
        owner = self._entity_for_slot(slot)
        old_max = int(getattr(owner, "max_hp", 0))
        old_hp = int(getattr(owner, "hp", 0))
        owner.max_hp = max(1, old_max + amount)
        owner.hp = max(0, min(owner.max_hp, old_hp + amount))
        self._sync_slot_from_player(slot)
        return "PVP ctrl：{} 最大 HP {} -> {}，HP {} -> {}。".format(
            slot.label(), old_max, owner.max_hp, old_hp, owner.hp
        )

    def handle_set_max_hp(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl setmaxhp [玩家] 数量。")
        if error:
            return error
        owner = self._entity_for_slot(slot)
        old_max = int(getattr(owner, "max_hp", 0))
        old_hp = int(getattr(owner, "hp", 0))
        owner.max_hp = max(1, amount)
        owner.hp = max(0, min(owner.max_hp, old_hp))
        self._sync_slot_from_player(slot)
        return "PVP ctrl：{} 最大 HP {} -> {}，HP {} -> {}。".format(
            slot.label(), old_max, owner.max_hp, old_hp, owner.hp
        )

    def _battle_player_or_error(self, slot):
        if slot.player_state is None:
            return None, "该玩家还没有进入 PVP 战斗。"
        return slot.player_state, ""

    def handle_add_cost(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl addcost [玩家] 数量。")
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        old = int(player.cost)
        player.cost = max(0, old + amount)
        return "PVP ctrl：{} 费用 {} -> {} / {}。".format(slot.label(), old, player.cost, player.max_cost)

    def handle_set_cost(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl setcost [玩家] 数量。")
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        old = int(player.cost)
        player.cost = max(0, amount)
        return "PVP ctrl：{} 费用 {} -> {} / {}。".format(slot.label(), old, player.cost, player.max_cost)

    def handle_add_block(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl addblock [玩家] 数量。")
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        old = int(player.block)
        player.block = max(0, old + amount)
        return "PVP ctrl：{} 格挡 {} -> {}。".format(slot.label(), old, player.block)

    def handle_set_block(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl setblock [玩家] 数量。")
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        old = int(player.block)
        player.block = max(0, amount)
        return "PVP ctrl：{} 格挡 {} -> {}。".format(slot.label(), old, player.block)

    def handle_add_state(self, room, user_id, args):
        from app.debug_console import parse_amount, resolve_status_key
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        if not args:
            return "用法：/card pvp ctrl addstate [玩家] 状态 [数量]。"
        status_key = resolve_status_key(args[0])
        if status_key is None:
            return "未知状态：{}。".format(args[0])
        amount = 1
        if len(args) >= 2:
            parsed = parse_amount(args[1])
            if parsed is None:
                return "状态数量必须是整数。"
            amount = parsed
        old = player.statuses.get(status_key)
        new = player.statuses.add(status_key, amount)
        return "PVP ctrl：{} 的{} {} -> {}。".format(
            slot.label(), get_status_name(status_key), old, new
        )

    def handle_remove_state(self, room, user_id, args):
        from app.debug_console import parse_amount, resolve_status_key
        slot, args, error = self._target_or_error(room, user_id, args)
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        if not args:
            return "用法：/card pvp ctrl removestate [玩家] 状态 [数量]。不写数量会清空。"
        status_key = resolve_status_key(args[0])
        if status_key is None:
            return "未知状态：{}。".format(args[0])
        old = player.statuses.get(status_key)
        if len(args) >= 2:
            amount = parse_amount(args[1])
            if amount is None:
                return "状态数量必须是整数。"
            new = player.statuses.add(status_key, -abs(amount))
        else:
            player.statuses.remove(status_key)
            new = 0
        return "PVP ctrl：{} 的{} {} -> {}。".format(
            slot.label(), get_status_name(status_key), old, new
        )

    def handle_draw(self, room, user_id, args):
        slot, amount, error = self._parse_target_amount(room, user_id, args, "用法：/card pvp ctrl draw [玩家] 数量。")
        if error:
            return error
        player, error = self._battle_player_or_error(slot)
        if error:
            return error
        logs = ["PVP ctrl：{} 抽 {} 张牌。".format(slot.label(), amount)]
        logs.extend(player.draw_cards(max(0, amount), game_state=None, draw_source="pvp_ctrl"))
        return "\n".join(logs)

    def handle_active(self, room, user_id, args):
        error = self._host_only(room, user_id)
        if error:
            return error
        if room.battle is None:
            return "当前 PVP 还没有开战。"
        if not args:
            return "用法：/card pvp ctrl active 玩家编号。"
        slot = self._resolve_player_ref(room, args[0], current_user_id=user_id)
        if slot is None:
            return "玩家编号无效：{}。".format(args[0])
        old = room.battle.active_user_id
        room.battle.active_user_id = slot.user_id
        return "PVP ctrl：当前行动者 {} -> {}。".format(old, slot.user_id)

    def handle_battle_value(self, room, user_id, args):
        from app.debug_console import parse_amount
        error = self._host_only(room, user_id)
        if error:
            return error
        if room.battle is None:
            return "当前 PVP 还没有开战。"
        if len(args) < 2:
            return "用法：/card pvp ctrl battle turn 3 或 /card pvp ctrl battle cards 11。"
        key = str(args[0]).strip().lower()
        value = parse_amount(args[1])
        if value is None:
            return "战斗数值必须是整数。"
        if key in ("turn", "turn_count", "回合", "行动序号"):
            old = int(room.battle.turn_count)
            room.battle.turn_count = max(1, int(value))
            return "PVP ctrl：行动序号 {} -> {}。".format(old, room.battle.turn_count)
        if key in ("cards", "cards_played", "出牌", "本回合出牌"):
            old = int(room.battle.cards_played_this_turn)
            room.battle.cards_played_this_turn = max(0, int(value))
            return "PVP ctrl：本回合出牌数 {} -> {}。".format(old, room.battle.cards_played_this_turn)
        return "未知战斗数值：{}。".format(args[0])

