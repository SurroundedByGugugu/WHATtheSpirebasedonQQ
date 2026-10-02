"""Debug commands. Positions are one-based and validated before mutation."""
from game.orbs import NAMES, rack, channel, trigger, trigger_passives, evoke_orb, set_slots, format_orbs

HELP = """充能球控制（仅当前战斗，位置从1开始）：
/ctrl orb slots 3             设置球槽；缩槽移除最右多余球，不激发
/ctrl orb addslots 1          增减球槽
/ctrl orb channel 闪电 2      依次生成，可用闪电/冰霜/黑暗/玻璃/等离子或英文名
/ctrl orb passive all         所有当前球被动触发一次（包括等离子）
/ctrl orb passive 1           指定球被动触发一次
/ctrl orb evoke 1 2           第1颗球激发2次后移除
/ctrl orb remove 1            移除指定球，不激发
/ctrl orb clear               清空球，不激发
/ctrl orb focus -2            设置集中；增减也可用 /ctrl addstate 集中 1 self
/ctrl orb value 1 18          设置黑暗计数或玻璃基础值
/ctrl orb show                查看当前数值与Zone联动
/ctrl orb help"""

def handle_orb_ctrl(run_state, args):
    if args and args[0].lower() in ("help", "帮助"):
        return HELP
    state = getattr(run_state, "current_battle", None)
    if state is None or state.battle_over:
        return "当前不在进行中的战斗中。\n" + HELP
    player = state.player
    container = rack(player)
    command = args[0].lower() if args else "show"
    rest = args[1:]
    logs = []
    try:
        if command == "show" and not rest:
            pass
        elif command in ("slots", "addslots", "focus") and len(rest) == 1:
            number = int(rest[0])
            if command == "focus":
                player.statuses.set("focus", number)
            else:
                number += container.capacity if command == "addslots" else 0
                if not 0 <= number <= 100:
                    raise ValueError("球槽必须在0到100之间")
                set_slots(player, number)
        elif command == "channel" and 1 <= len(rest) <= 2:
            aliases = {name: kind for kind, name in NAMES.items()}
            aliases.update({name[:-1]: kind for kind, name in NAMES.items()})
            kind = aliases.get(rest[0], rest[0].lower())
            count = int(rest[1]) if len(rest) == 2 else 1
            if kind not in NAMES or not 1 <= count <= 100:
                raise ValueError("球种无效或数量不在1到100之间")
            logs.extend(channel(state, player, kind, count))
        elif command == "clear" and not rest:
            container.orbs.clear()
        elif command == "passive" and rest == ["all"]:
            logs.extend(trigger_passives(state, player))
        elif command in ("passive", "evoke", "remove", "value"):
            allowed = (1, 2) if command == "evoke" else (2,) if command == "value" else (1,)
            if len(rest) not in allowed:
                raise ValueError("参数数量错误")
            index = int(rest[0]) - 1
            if not 0 <= index < len(container.orbs):
                raise ValueError("球位置不存在，位置从1开始")
            orb = container.orbs[index]
            if command == "passive":
                logs.extend(trigger(state, player, orb))
            elif command == "remove":
                container.orbs.pop(index)
            elif command == "value":
                value = int(rest[1])
                if orb.kind not in ("dark", "glass") or value < 0:
                    raise ValueError("只能为黑暗或玻璃设置非负内部值")
                orb.value = value
            else:
                times = int(rest[1]) if len(rest) == 2 else 1
                if not 1 <= times <= 100:
                    raise ValueError("激发次数必须在1到100之间")
                logs.extend(evoke_orb(state, player, index, times))
        else:
            return HELP
    except (ValueError, TypeError) as exc:
        return "ctrl：参数错误：{}。\n{}".format(exc, HELP)
    if run_state is not None:
        run_state.hp = player.hp
    logs.append(format_orbs(player, state))
    return "ctrl：\n" + "\n".join(logs)
