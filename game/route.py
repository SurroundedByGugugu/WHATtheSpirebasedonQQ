# -*- coding: utf-8 -*-
# 路线节点：普通敌人、精英、事件、商店、休息点、Boss

from dataclasses import dataclass, field
from data.route.encounters import get_encounter_display_name

@dataclass
class RouteNode:
    node_id: str
    node_type: str
    name: str
    encounter_id: str = ""
    next_node_ids: list = field(default_factory=list)

    # 固定 5 列地图用。旧路线不写时保持 -1，走旧逻辑。
    floor: int = -1
    col: int = -1

    def summary_text(self):
        return "{}：{}".format(self.name, self.node_type)


def build_route(route_template):
    nodes = []

    for item in route_template:
        nodes.append(RouteNode(
            node_id=item.get("node_id", ""),
            node_type=item.get("node_type", ""),
            name=item.get("name", ""),
            encounter_id=item.get("encounter_id", ""),
            next_node_ids=list(item.get("next_node_ids", [])),
            floor=int(item.get("floor", -1)),
            col=int(item.get("col", -1)),
        ))

    return nodes


def get_node_by_id(route_nodes, node_id):
    for node in route_nodes:
        if node.node_id == node_id:
            return node
    return None


def get_next_nodes(route_nodes, current_node):
    if current_node is None:
        return []

    result = []

    for node_id in current_node.next_node_ids:
        node = get_node_by_id(route_nodes, node_id)
        if node is not None:
            result.append(node)

    return result

MAP_WIDTH = 5


def is_grid_route(run_state):
    for node in getattr(run_state, "route_nodes", []):
        if getattr(node, "floor", -1) >= 0:
            return True
    return False


def get_floor_nodes(route_nodes, floor):
    nodes = [
        node for node in route_nodes
        if getattr(node, "floor", -1) == floor
    ]
    nodes.sort(key=lambda node: getattr(node, "col", -1))
    return nodes


def get_max_floor(route_nodes):
    floors = [
        getattr(node, "floor", -1)
        for node in route_nodes
        if getattr(node, "floor", -1) >= 0
    ]
    if not floors:
        return -1
    return max(floors)


def node_type_display_text(node, run_state=None):
    node_type = getattr(node, "node_type", "")

    if node_type == "boss":
        encounter_id = getattr(node, "encounter_id", "")

        if encounter_id:
            return "Boss：{}".format(get_encounter_display_name(encounter_id))

        boss_name = ""
        boss_encounter_id = ""
        if run_state is not None:
            boss_name = getattr(run_state, "boss_name", "")
            boss_encounter_id = getattr(run_state, "boss_encounter_id", "")

        if boss_name:
            return "Boss：{}".format(boss_name)

        if boss_encounter_id:
            return "Boss：{}".format(get_encounter_display_name(boss_encounter_id))

        return "Boss"

    mapping = {
        "ancient": "先古之民",
        "starting": "起始战斗",
        "normal_enemy": "普通",
        "elite": "精英",
        "event": "事件",
        "mystery": "？",
        "shop": "商店",
        "rest": "火堆",
        "treasure": "宝箱",
    }
    return mapping.get(node_type, node_type)


def format_floor_line(run_state, floor, reachable_node_ids=None, show_reachability=False):
    route_nodes = getattr(run_state, "route_nodes", [])
    nodes = get_floor_nodes(route_nodes, floor)

    if not nodes:
        return "第 {} 层：无".format(floor)

    reachable_node_ids = set(reachable_node_ids or [])
    parts = []

    for node in nodes:
        col = getattr(node, "col", -1)
        text = "[{}] {}".format(col, node_type_display_text(node, run_state))

        if show_reachability:
            if node.node_id in reachable_node_ids:
                text += "（可选）"
            else:
                text += "（不可达）"

        parts.append(text)

    return "第 {} 层：{}".format(floor, " / ".join(parts))


def find_next_node_by_column(run_state, current_node, column):
    """
    固定 5 列地图：
    /card next N 中的 N 表示下一层列号，而不是可选列表下标。
    """
    if current_node is None:
        return None

    if getattr(current_node, "floor", -1) < 0:
        return None

    next_nodes = get_next_nodes(run_state.route_nodes, current_node)

    for node in next_nodes:
        if getattr(node, "col", -1) == column:
            return node

    return None


def get_reachable_columns_text(run_state, current_node):
    next_nodes = get_next_nodes(run_state.route_nodes, current_node)
    cols = [
        getattr(node, "col", -1)
        for node in next_nodes
        if getattr(node, "col", -1) >= 0
    ]
    cols = sorted(cols)

    if not cols:
        return "无"

    return "，".join(str(col) for col in cols)


def format_grid_route_text(run_state):
    lines = []
    lines.append("=== 当前路线 ===")

    current_node = run_state.get_current_node()
    if current_node is None:
        lines.append("当前没有路线节点。")
        return "\n".join(lines)

    current_floor = getattr(current_node, "floor", -1)
    current_col = getattr(current_node, "col", -1)
    max_floor = get_max_floor(run_state.route_nodes)

    if current_floor == 0:
        lines.append("地图进度：第 0 / {} 层".format(max_floor))
        lines.append("当前位置：先古之民")
    else:
        lines.append("地图进度：第 {} / {} 层".format(current_floor, max_floor))
        lines.append("当前位置：列 {}，{}".format(
            current_col,
            node_type_display_text(current_node, run_state)
        ))

    boss_name = getattr(run_state, "boss_name", "")
    boss_encounter_id = getattr(run_state, "boss_encounter_id", "")
    if boss_name or boss_encounter_id:
        lines.append("本轮 Boss：{}".format(
            boss_name or get_encounter_display_name(boss_encounter_id)
        ))

    next_nodes = get_next_nodes(run_state.route_nodes, current_node)

    if not next_nodes:
        lines.append("")
        lines.append("没有可选下一节点。")
        return "\n".join(lines)

    next_floor = getattr(next_nodes[0], "floor", current_floor + 1)
    next_node_ids = [node.node_id for node in next_nodes]

    lines.append("")
    lines.append("下一层：")
    lines.append(format_floor_line(
        run_state,
        next_floor,
        reachable_node_ids=next_node_ids,
        show_reachability=True,
    ))

    preview_floor = next_floor + 1
    if preview_floor <= max_floor:
        preview_nodes = get_floor_nodes(run_state.route_nodes, preview_floor)
        if preview_nodes:
            lines.append("")
            lines.append("后续预告：")
            lines.append(format_floor_line(
                run_state,
                preview_floor,
                show_reachability=False,
            ))

    return "\n".join(lines)

def format_legacy_route_text(run_state):
    lines = []
    lines.append("=== 当前路线 ===")

    current_node = run_state.get_current_node()

    if current_node is None:
        lines.append("当前没有路线节点。")
        return "\n".join(lines)

    lines.append("当前节点：{} ({})".format(
        current_node.name,
        current_node.node_type
    ))

    boss_name = getattr(run_state, "boss_name", "")
    boss_encounter_id = getattr(run_state, "boss_encounter_id", "")
    if boss_name or boss_encounter_id:
        lines.append("本轮 Boss：{}".format(
            boss_name or get_encounter_display_name(boss_encounter_id)
        ))

    if run_state.completed_node_ids:
        lines.append("已完成节点：{}".format(", ".join(run_state.completed_node_ids)))
    else:
        lines.append("已完成节点：无")

    next_nodes = get_next_nodes(run_state.route_nodes, current_node)

    lines.append("")
    lines.append("可选下一节点：")

    if not next_nodes:
        lines.append("无。")
    else:
        for index, node in enumerate(next_nodes):
            node_type_text = node.node_type

            if node.node_type == "boss":
                encounter_id = getattr(node, "encounter_id", "")
                if encounter_id:
                    node_type_text = "boss：{}".format(
                        get_encounter_display_name(encounter_id)
                    )

            lines.append("[{}] {} ({})".format(
                index,
                node.name,
                node_type_text
            ))

    return "\n".join(lines)

def format_route_text(run_state):
    if is_grid_route(run_state):
        return format_grid_route_text(run_state)
    return format_legacy_route_text(run_state)