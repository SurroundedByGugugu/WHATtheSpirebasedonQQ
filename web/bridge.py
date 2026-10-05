"""Browser-only adapter. The original game and QQ entry point stay untouched."""
import json

from app.game_service import GameService, CHARACTER_CHOICES
from data.character.AAAregistry import create_character
from data.content_gate import private_content_session
from game.card_cost import get_card_current_cost
from game.card_preview import format_card_actual_preview
from game.display_names import format_card_display_name
from game.intent_preview import format_enemy_intent_text
from game.route import get_next_nodes
from game.run_engine import get_run_view
from game.status.status_display import get_status_display_text
from game.node.node_rest import get_rest_options, is_action_available, get_upgradable_cards
from game.node.node_shop import get_effective_remove_price, get_effective_random_remove_price
from game.relic_logic.run_relic_utils import has_run_relic
from data.card.upgrade_rules import upgrade_card
from game.engine import get_pending_player_choice_hint
from game.relic_logic.bottle_utils import get_bottle_candidates
from game.stances import stance_of, NAMES as STANCE_NAMES
from game.orbs import NAMES as ORB_NAMES, values as orb_values, format_orbs

service = GameService()
SESSION = "web:solo"
USER = "local-player"


def action(name, command=None, description="", **extra):
    return dict(name=name, command=command, description=description, **extra)


def card_actions(cards, command):
    return [action(format_card_display_name(card) if hasattr(card, "name") else str(card),
                   f"/card {command} {index}", card.summary_text() if hasattr(card, "summary_text") else "") for index, card in enumerate(cards)]


def pile_card_actions(options, command):
    """Keep the engine's combined-pile option indices and expose each source pile."""
    choices = []
    for index, item in enumerate(options):
        card = item["card"]
        choices.append(action(f"{item['pile_label']} · {format_card_display_name(card)}",
                              f"/card {command} {index}", card.summary_text()))
    return choices


def battle_selection(battle):
    """Use engine option order, which can differ from hand indices."""
    pending = battle.pending_choice
    commands = {"discard_to_draw_top": "top", "hand_to_draw_top": "handtop",
                "upgrade_hand": "upgrade_hand", "toolbox": "toolbox",
                "four_color_nectar": "dance", "element_plating": "plate",
                "abyss_index": "abyss_index"}
    if pending is not None:
        if pending.kind == "synchronization":
            effect = "共鸣和消耗" if pending.payload.get("add_exhaust", True) else "共鸣"
            return dict(title=f"{pending.source or '同调'}：选择一张牌",
                        hint=f"点击消耗堆以外的一张牌，添加{effect}。",
                        options=pile_card_actions(pending.options, "sync"))
        if pending.kind == "radiant_reflection":
            return dict(title=f"{pending.source or '辉晶映照'}：选择添加重放的牌",
                        hint="可选择手牌、抽牌堆或弃牌堆中的牌，每张添加重放 1。",
                        command="/card reflect", multiple=True, minimum=1,
                        maximum=int(pending.payload.get("max_count", 1) or 1),
                        options=pile_card_actions(pending.options, "reflect"))
        if pending.kind == "fossil_exhaust_hand":
            return dict(title=f"{pending.source or '化石'}：选择消耗的手牌",
                        hint="每消耗一张手牌获得一层岩层，也可以不选择直接继续。",
                        command="/card fossil", multiple=True, minimum=0,
                        maximum=len(pending.options), emptyValue="none",
                        options=[action(format_card_display_name(card), f"/card fossil {index}", card.summary_text())
                                 for index, card in pending.options])
        if pending.kind in {"scry", "defect_select", "watcher_select"}:
            scry = pending.kind == "scry"
            count = pending.payload.get("count", len(pending.options))
            command = "scry" if scry else "pick"
            return dict(title=(pending.source or "选牌") + ("：选择放入弃牌堆的牌" if scry else "：选择卡牌或效果"),
                        command=f"/card {command}", multiple=True, minimum=0 if scry else count,
                        maximum=len(pending.options) if scry else count, emptyValue="skip",
                        options=card_actions(pending.options, command))
        if pending.kind in {"retain_hand", "well_laid_plans"}:
            from game.constants import KEYWORD_RETAIN
            options = card_actions(battle.player.hand, "retain")
            if pending.kind == "retain_hand":
                options = [option for option, card in zip(options, battle.player.hand)
                           if KEYWORD_RETAIN not in card.keywords]
            return dict(title="选择保留的手牌", command="/card retain", multiple=True, minimum=0,
                        maximum=min(pending.payload.get("max_count", 1), len(options)),
                        emptyValue="skip", options=options)
        if pending.kind == "night_terror":
            return dict(title="夜魇：选择复制的手牌", options=card_actions(battle.player.hand, "nightmare"))
        command = commands.get(pending.kind)
        if command:
            return dict(title=(pending.source or "特殊效果") + "：选择一张牌",
                        hint=pending.prompt.split("/card")[0].rstrip("：。 ") or "点击卡牌完成选择。",
                        options=card_actions(pending.options, command))
        return dict(title="请处理特殊选择", hint=get_pending_player_choice_hint(battle), options=[])
    if battle.pending_discard_selection:
        return dict(title="选择要丢弃的手牌", command="/card drop", multiple=True,
                    minimum=battle.pending_discard_min_count,
                    maximum=battle.pending_discard_max_count,
                    options=card_actions(battle.player.hand, "drop"))
    for field, command, title in (
        ("discard_to_draw", "top", "选择弃牌放回抽牌堆顶"),
        ("exhaust_hand", "exhaust_hand", "选择消耗的手牌"),
        ("hand_to_draw_top", "handtop", "选择手牌放回抽牌堆顶"),
        ("upgrade_hand", "upgrade_hand", "选择升级的手牌"),
        ("duplicate_hand", "duplicate_hand", "选择复制的手牌"),
        ("exhume", "exhume", "选择从消耗堆取回的牌"),
        ("potion_card", "potion_pick", "药水：选择一张牌"),
        ("nilrys", "codex", "尼利的宝典：选择一张牌"),
    ):
        if getattr(battle, f"pending_{field}_selection", False):
            options = card_actions(getattr(battle, f"pending_{field}_options", []), command)
            if field == "nilrys":
                options.append(action("跳过选牌", "/card codex skip"))
            return dict(title=title, options=options)
    if battle.pending_elixir_selection:
        return dict(title="万灵药水：选择要消耗的手牌", command="/card elixir", multiple=True,
                    minimum=0, maximum=battle.pending_elixir_max_count or None,
                    options=[action(format_card_display_name(card), f"/card elixir {index}", card.description)
                             for index, card in battle.pending_elixir_options])
    return None


def run_selection(run):
    queue = run.pending_bottle_selections
    if queue:
        cards = [card for _, card in get_bottle_candidates(run, queue[0]["required_card_type"])]
        options = card_actions(cards, "bottle")
        options.append(action("跳过瓶装", "/card bottle -1"))
        return dict(title="瓶装：选择一张牌", options=options)
    for field, command, title, default in (
        ("pending_astrolabe_selections", "astrolabe", "星盘：选择变化并升级的牌", 3),
        ("pending_empty_cage_selections", "cage", "空鸟笼：选择移除的牌", 2),
    ):
        queue = getattr(run, field, [])
        if queue:
            count = queue[0].get("count", default)
            options = card_actions(run.master_deck, command)
            if command == "cage":
                options = [option for option, card in zip(options, run.master_deck)
                           if card.card_id != "card.curse.bell"]
            return dict(title=title, command=f"/card {command}", multiple=True,
                        minimum=count, maximum=count, options=options)
    if getattr(run, "pending_orrery_selection", False):
        groups = run.pending_orrery_groups
        index = run.pending_orrery_index
        cards = groups[index] if index < len(groups) else []
        return dict(title=f"星系仪：第 {index + 1} 组选牌", options=card_actions(cards, "orrery"))
    if getattr(run, "pending_dollys_mirror_selection", False):
        return dict(title="多利之镜：选择复制的牌", options=card_actions(run.master_deck, "mirror"))
    return None


def node_actions(run):
    reward = run.pending_reward
    if reward is not None:
        options = []
        active = reward.active_card_option_index
        if 0 <= active < len(reward.options) and not reward.options[active].claimed and not reward.options[active].skipped:
            current = reward.options[active]
            if current.option_type == "card":
                options.extend(card_actions(current.payload.get("cards", []), "pick"))
                if has_run_relic(run, "relic.singing_bowl"):
                    options.append(action("颂钵：最大生命 +2", "/card bowl"))
        else:
            for index, item in enumerate(reward.options):
                if item.claimed or item.skipped:
                    continue
                payload = item.payload or {}
                detail = getattr(payload.get("relic") or payload.get("potion"), "description", "")
                potion = payload.get("potion")
                if (item.option_type == "potion" and potion is not None
                        and len(run.potions) >= run.max_potion_slots
                        and potion.potion_id != "potion.fruit_juice"):
                    options.append(action(item.title + " · 替换药水", description=detail,
                        options=[action("替换 " + old.name, f"/card replace_potion {index} {slot}", old.description)
                                 for slot, old in enumerate(run.potions)]))
                else:
                    options.append(action(item.title, f"/card take {index}", detail))
        options.append(action("放弃剩余奖励", "/card skip"))
        return "选择奖励", options
    shop = run.pending_shop
    if shop is not None:
        options = []
        for index, item in enumerate(shop.items):
            payload = item.payload or {}
            value = payload.get(item.item_type)
            reason = "已售罄" if item.sold else "金币不足" if item.price > run.gold else ""
            options.append(action(f"{item.title} · {item.price} 金币", f"/card buy {index}",
                getattr(value, "description", ""), disabled=bool(reason), reason=reason,
                detailCommand=f"/card item {index}"))
        if not shop.remove_used:
            price = get_effective_remove_price(run)
            options.append(action(f"定向删牌 · {price} 金币", options=card_actions(run.master_deck, "remove"),
                                  disabled=run.gold < price, reason="金币不足" if run.gold < price else ""))
            price = get_effective_random_remove_price(run)
            options.append(action(f"随机删牌 · {price} 金币", "/card random_remove",
                                  disabled=run.gold < price, reason="金币不足" if run.gold < price else ""))
        options.append(action("离开商店", "/card leave"))
        return "商店", options
    if run.pending_rest is not None:
        options = []
        for index, (key, name) in enumerate(get_rest_options(run)):
            available = key == "leave" or is_action_available(run, key)
            item = action(name, f"/card rest {index}", disabled=not available,
                          reason="已使用或被遗物限制" if not available else "")
            if key == "smith":
                item["command"] = None
                item["options"] = [action(format_card_display_name(card), f"/card smith {i}",
                    f"当前：{card.summary_text()}\n升级：{upgrade_card(card).summary_text()}")
                    for i, (_, card) in enumerate(get_upgradable_cards(run))]
            elif key == "pipe":
                item["command"] = None
                item["options"] = card_actions(run.master_deck, "rest_remove")
            options.append(item)
        return "火堆", options
    treasure = run.pending_treasure
    if treasure is not None:
        options = ([action("打开宝箱", "/card open")] if not treasure.opened else
                   [action(item.title, f"/card take {index}") for index, item in enumerate(treasure.items)
                    if not item.claimed and not item.skipped])
        options.append(action("离开宝箱", "/card leave"))
        return "宝箱", options
    if run.pending_special_rest is not None:
        return "选择补给", [action("进入商店", "/card special_rest 0"), action("进入火堆", "/card special_rest 1")]
    for field, command in (("pending_ancient", "ancient"), ("pending_event", "event")):
        pending = getattr(run, field, None)
        if pending is not None:
            return pending.title, [action(choice.title, f"/card {command} {index}")
                                   for index, choice in enumerate(pending.choices)]
    return "选择路线", []


def character_choices():
    choices = []
    for choice in CHARACTER_CHOICES:
        character = create_character(choice["character_id"])
        choices.append({**choice, "maxHp": character.max_hp, "startingGold": character.starting_gold})
    return choices


def combat_status(battle):
    if battle is None:
        return None
    player = battle.player
    stance = stance_of(player)
    container = player.orb_rack
    summaries = format_orbs(player, battle).splitlines()[1:]
    orbs = []
    for index, orb in enumerate(container.orbs):
        passive, evoke = orb_values(battle, player, orb)
        orbs.append({"uid": orb.uid, "kind": orb.kind, "name": ORB_NAMES[orb.kind],
                     "passive": passive, "evoke": evoke, "value": orb.value,
                     "summary": summaries[index]})
    zone = battle.active_zone
    return {
        "stance": stance, "stanceName": STANCE_NAMES.get(stance, stance),
        "showStance": player.character_id == "character.watcher" or stance != "none",
        "orbCapacity": container.capacity, "orbs": orbs, "focus": player.statuses.get("focus"),
        "zone": {"element": zone.element, "name": zone.name, "extreme": bool(zone.is_extreme),
                 "duration": zone.duration, "description": zone.description} if zone else None,
    }


def snapshot(reply=""):
    run = service.get_run(SESSION)
    result = {"reply": reply, "characters": character_choices(), "run": None,
              "confirmation": SESSION in service.pending_confirmations}
    if run is None:
        return result
    battle = run.current_battle
    player = battle.player if battle else run
    node = run.get_current_node()
    state = {
        "name": run.character_name, "hp": player.hp, "maxHp": player.max_hp,
        "gold": run.gold, "block": getattr(player, "block", 0),
        "energy": getattr(player, "cost", 0), "maxEnergy": player.max_cost,
        "node": node.name if node else "旅途起点", "floor": getattr(node, "floor", 0),
        "boss": run.boss_name, "battle": bool(battle),
        "turn": battle.turn_count if battle else 0,
        "view": get_run_view(run), "hand": [], "enemies": [], "routes": [],
        "choices": [], "deckCount": len(run.master_deck),
        "status": get_status_display_text(player.statuses) if battle else "",
        "combatStatus": combat_status(battle),
        "relics": [getattr(item, "name", "遗物") for item in player.relics],
        "relicDetails": [{
            "name": getattr(item, "name", "遗物"),
            "info": getattr(item, "description", "") or "暂无效果说明。",
            "story": getattr(item, "story", "") or "暂无故事。",
        } for item in player.relics],
        "potions": [getattr(item, "name", "药水") for item in player.potions],
        "potionDetails": [{"name": item.name, "description": item.description,
                           "target": item.target, "usable": bool(battle) or item.potion_id in {
                               "potion.saturated_calcium_carbonate_solution", "potion.fruit_juice", "potion.blood"}}
                          for item in player.potions],
        "selection": run_selection(run) or (battle_selection(battle) if battle else None),
    }
    if battle:
        for index, card in enumerate(player.hand):
            state["hand"].append({
                "index": index, "name": format_card_display_name(card),
                "cost": get_card_current_cost(battle, card), "type": card.card_type,
                "description": card.description, "summary": card.summary_text(),
                "preview": format_card_actual_preview(battle, card),
            })
        for index, enemy in enumerate(battle.enemies):
            if enemy.is_alive():
                state["enemies"].append({
                    "index": index, "name": enemy.name, "hp": enemy.hp,
                    "maxHp": enemy.max_hp, "block": enemy.block,
                    "intent": format_enemy_intent_text(battle, enemy),
                    "status": get_status_display_text(enemy.statuses),
                })
        state["piles"] = {"draw": len(player.draw_pile),
                          "discard": len(player.discard_pile), "exhaust": len(player.exhaust_pile)}
    elif not state["selection"] and not run.pending_reward and not run.has_pending_node():
        for index, next_node in enumerate(get_next_nodes(run.route_nodes, node)):
            choice = next_node.col if node.floor >= 0 else index
            state["routes"].append({"name": next_node.name, "column": choice,
                                    "command": f"/card next {choice}"})
    if not battle and not state["selection"]:
        state["actionTitle"], state["choices"] = node_actions(run)
    result["run"] = state
    return result


def dispatch(command=""):
    command = str(command).strip()
    parts = command.split()
    if parts and parts[0].lstrip("/.。").lower() == "card" and len(parts) > 1:
        if parts[1].lower() in {"multi", "mp", "多人", "联机", "pvp", "对战", "演绎"}:
            return json.dumps(snapshot("网页版目前仅支持单人游玩。"), ensure_ascii=False)
    if parts and parts[0].lstrip("/.。").lower() == "card" and (len(parts) == 1 or parts[1].lower() in {"help", "帮助"}):
        return json.dumps(snapshot(WEB_HELP), ensure_ascii=False)
    with private_content_session(SESSION):
        reply = service.handle_message(SESSION, USER, command) if command else ""
        return json.dumps(snapshot(reply or ("未识别命令，输入 /card help 查看帮助。" if command else "")),
                          ensure_ascii=False)

WEB_HELP = """单人冒险指令（编号从 0 开始）
/card new 0  选角色开局（0 铁甲战士 / 1 静默猎手 / 2 昼 / 3 Yoirine / 4 Suzuri）
/card view  当前状态；/card route  地图；/card deck  牌库
/card play 0 1  打出手牌 0，目标敌人 1；/card end  结束回合
/card next 0  选择下一层列号 0
/card ancient 0  开局选择；/card event 0  事件选择
/card reward  查看奖励；/card take 0  领取奖励；/card pick 0  选牌；/card skip  跳过
/card buy 0  商店购买；/card leave  离开商店或宝箱
/card rest 0  休息；/card rest 1  锻造；/card smith 0  选择升级卡牌
/card potions  药水；/card potion 0 1  使用药水 0，目标 1
/card relics  遗物；/card status  状态；/card state  场地
/card sl  回退节点；/card exit  结束本局（需要确认）
/card yes  确认；/card no  取消
常用操作可使用页面按钮；多张选牌先点选再确认。未覆盖的特殊选择可展开“高级操作”输入指令，也可省略 /card 前缀。
本局在当前标签页中运行，刷新或关闭页面会丢失进度。"""
