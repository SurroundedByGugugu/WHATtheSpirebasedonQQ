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
            next_node_ids=list(item.get("next_node_ids", []))
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


def format_route_text(run_state):
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