"""Browser-only adapter. The original game and QQ entry point stay untouched."""
import json

from app.game_service import GameService, CHARACTER_CHOICES
from data.content_gate import private_content_session
from game.card_cost import get_card_current_cost
from game.card_preview import format_card_actual_preview
from game.display_names import format_card_display_name
from game.intent_preview import format_enemy_intent_text
from game.route import get_next_nodes
from game.run_engine import get_run_view
from game.status.status_display import get_status_display_text

service = GameService()
SESSION = "web:solo"
USER = "local-player"


def snapshot(reply=""):
    run = service.get_run(SESSION)
    result = {"reply": reply, "characters": CHARACTER_CHOICES, "run": None,
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
        "relics": [getattr(item, "name", "遗物") for item in player.relics],
        "potions": [getattr(item, "name", "药水") for item in player.potions],
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
    elif not run.pending_reward and not run.has_pending_node():
        for index, next_node in enumerate(get_next_nodes(run.route_nodes, node)):
            choice = next_node.col if node.floor >= 0 else index
            state["routes"].append({"name": next_node.name, "column": choice,
                                    "command": f"/card next {choice}"})
    # Use the engine's own choice titles; special follow-up selections remain in its text view.
    for field, command in (("pending_ancient", "ancient"), ("pending_event", "event")):
        pending = getattr(run, field, None)
        if pending is not None:
            for index, choice in enumerate(getattr(pending, "choices", [])):
                state["choices"].append({"name": choice.title,
                                         "command": f"/card {command} {index}"})
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
特殊选牌请按冒险记录中的提示操作。也可省略 /card 前缀输入命令。
本局在当前标签页中运行，刷新或关闭页面会丢失进度。"""
