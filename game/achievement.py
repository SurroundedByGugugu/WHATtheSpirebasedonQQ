# -*- coding: utf-8 -*-


def check_run_end_achievements(run_state):
    """
    Run 结束时检查成就。

    当前只做占位。
    """
    run_state.init_reward_stats_if_needed()

    unlocked = {}

    if (
        run_state.reward_stats.get("gold_offered", 0) > 0
        and run_state.reward_stats.get("gold_taken", 0) == 0
    ):
        unlocked["谁要这个？"] = "一局游戏中没有拾起任何金币。"

    for achievement_name in unlocked:
        if achievement_name not in run_state.achievements:
            run_state.achievements.append(achievement_name)

    return unlocked


def format_unlocked_achievements(unlocked):
    if not unlocked:
        return ""

    lines = []
    lines.append("=== 解锁成就 ===")

    for key,value in unlocked.items():
        lines.append("【{}】:{}".format(key,value))

    return "\n".join(lines)