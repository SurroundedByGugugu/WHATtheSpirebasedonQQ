# -*- coding: utf-8 -*-

import copy

def has_upgrade(card):
    """
    判断这张卡是否有可用升级。
    多次升级牌即使已经 upgraded=True，也仍然可以升级。
    """
    if getattr(card, "multi_upgrade", False):
        return True

    if getattr(card, "upgraded", False):
        return False

    patch = getattr(card, "upgrade_patch", None)
    return bool(patch)

def upgrade_card(card):
    """
    返回升级后的卡牌副本，不修改原卡。

    如果没有 upgrade_patch，则返回原效果副本，并标记 upgrade_unavailable=True。
    显示层可以据此显示“暂时没有可用的升级”。
    """
    upgraded_card = copy.deepcopy(card)

    if getattr(upgraded_card, "multi_upgrade", False):
        return upgrade_multi_upgrade_card(upgraded_card)

    if getattr(upgraded_card, "upgraded", False):
        return upgraded_card

    patch = getattr(upgraded_card, "upgrade_patch", None)

    if not patch:
        setattr(upgraded_card, "upgrade_unavailable", True)
        return upgraded_card

    apply_upgrade_patch(upgraded_card, patch)
    upgraded_card.upgraded = True

    return upgraded_card

def upgrade_multi_upgrade_card(card):
    """
    多次升级牌专用逻辑。

    当前用于灼热攻击：
    第 1 次升级：伤害 +4
    第 2 次升级：伤害 +5
    第 3 次升级：伤害 +6
    即每次增加 upgrade_count + 3。
    """
    patch = getattr(card, "upgrade_patch", {}) or {}

    old_upgrade_count = int(getattr(card, "upgrade_count", 0))
    new_upgrade_count = old_upgrade_count + 1

    damage_var = patch.get("damage_var", "damage")
    damage_bonus_offset = int(patch.get("damage_bonus_offset", 3))
    damage_bonus = new_upgrade_count + damage_bonus_offset

    if not hasattr(card, "card_vars") or card.card_vars is None:
        card.card_vars = {}

    old_damage = int(card.card_vars.get(damage_var, 0))
    new_damage = old_damage + damage_bonus
    card.card_vars[damage_var] = new_damage

    base_name = getattr(card, "base_name", None)
    if not base_name:
        base_name = card.name.split("+")[0]
        setattr(card, "base_name", base_name)

    if new_upgrade_count == 1:
        card.name = base_name + "+"
    else:
        card.name = "{}+{}".format(base_name, new_upgrade_count)

    description_template = patch.get(
        "description_template",
        "造成 {} 点伤害。能被多次升级。"
    )
    card.description = description_template.format(new_damage)

    card.upgraded = True
    card.upgrade_count = new_upgrade_count

    return card

def apply_upgrade_patch(card, patch):
    """
    应用卡牌自己的升级补丁。

    支持两类写法：

    一、常规顶层替换：
        {
            "name": "打击+",
            "cost": 0,
            "card_vars": {"damage": 9},
            "effects": [...]
        }

    二、嵌套路径补丁：
        {
            "patches": [
                {
                    "path": ["effects", 0, "amount", "base"],
                    "value": 9
                }
            ]
        }
    """
    if "name" in patch:
        card.name = patch["name"]
    else:
        card.name = card.name + "+"

    if "cost" in patch:
        card.cost = patch["cost"]

    if "target" in patch:
        card.target = patch["target"]

    if "description" in patch:
        card.description = patch["description"]

    if "card_type" in patch:
        card.card_type = patch["card_type"]

    if "quantity" in patch:
        card.quantity = patch["quantity"]

    if "owner_character_id" in patch:
        card.owner_character_id = patch["owner_character_id"]

    if "card_vars" in patch:
        if not hasattr(card, "card_vars") or card.card_vars is None:
            card.card_vars = {}

        for key, value in patch["card_vars"].items():
            card.card_vars[key] = copy.deepcopy(value)

    if "x_rules" in patch:
        card.x_rules = copy.deepcopy(patch["x_rules"])

    if "effects" in patch:
        card.effects = copy.deepcopy(patch["effects"])

    if "set_keywords" in patch:
        card.keywords = list(patch["set_keywords"])

    if "add_keywords" in patch:
        if not hasattr(card, "keywords") or card.keywords is None:
            card.keywords = []

        for keyword in patch["add_keywords"]:
            if keyword not in card.keywords:
                card.keywords.append(keyword)

    if "remove_keywords" in patch:
        if not hasattr(card, "keywords") or card.keywords is None:
            card.keywords = []

        for keyword in patch["remove_keywords"]:
            if keyword in card.keywords:
                card.keywords.remove(keyword)

    if "patches" in patch:
        apply_path_patches(card, patch["patches"])

    if "cost_rules" in patch:
        card.cost_rules = copy.deepcopy(patch["cost_rules"])

    if "multi_upgrade" in patch:
        card.multi_upgrade = bool(patch["multi_upgrade"])

    if "upgrade_count" in patch:
        card.upgrade_count = int(patch["upgrade_count"])

    return card

def apply_path_patches(root, patches):
    """
    应用嵌套路径补丁。

    patches 示例：

    1. 默认 set：
        {
            "path": ["effects", 0, "amount", "base"],
            "value": 9
        }

    2. merge_dict：
        {
            "mode": "merge_dict",
            "path": ["card_vars"],
            "value": {"damage": 9}
        }

    3. append：
        {
            "mode": "append",
            "path": ["keywords"],
            "value": "exhaust"
        }

    4. extend：
        {
            "mode": "extend",
            "path": ["effects"],
            "value": [...]
        }
    """
    for patch in patches:
        apply_path_patch(root, patch)

def apply_path_patch(root, patch):
    path = patch.get("path")
    mode = patch.get("mode", "set")

    if not path:
        raise ValueError("升级嵌套补丁缺少 path：{}".format(patch))

    parent, key = resolve_parent_and_key(root, path)

    if mode == "set":
        set_child(parent, key, copy.deepcopy(patch.get("value")))
        return

    if mode == "merge_dict":
        target = get_child(parent, key)
        value = patch.get("value", {})

        if not isinstance(target, dict):
            raise TypeError("merge_dict 目标不是 dict，path={}。".format(path))

        if not isinstance(value, dict):
            raise TypeError("merge_dict 的 value 不是 dict，path={}。".format(path))

        for k, v in value.items():
            target[k] = copy.deepcopy(v)

        return

    if mode == "append":
        target = get_child(parent, key)

        if not isinstance(target, list):
            raise TypeError("append 目标不是 list，path={}。".format(path))

        target.append(copy.deepcopy(patch.get("value")))
        return

    if mode == "extend":
        target = get_child(parent, key)
        value = patch.get("value", [])

        if not isinstance(target, list):
            raise TypeError("extend 目标不是 list，path={}。".format(path))

        if not isinstance(value, list):
            raise TypeError("extend 的 value 不是 list，path={}。".format(path))

        target.extend(copy.deepcopy(value))
        return

    raise ValueError("未知升级补丁 mode：{}，path={}。".format(mode, path))

def resolve_parent_and_key(root, path):
    """
    返回 path 指向位置的父容器和最后一个 key。

    例如：
        path = ["effects", 0, "effects", 0, "amount", "x_conditional_var", "x_gte"]

    返回：
        parent = card.effects[0]["effects"][0]["amount"]["x_conditional_var"]
        key = "x_gte"
    """
    current = root

    for key in path[:-1]:
        current = get_child(current, key)

    return current, path[-1]

def get_child(container, key):
    if isinstance(container, dict):
        return container[key]

    if isinstance(container, list):
        return container[int(key)]

    return getattr(container, key)

def set_child(container, key, value):
    if isinstance(container, dict):
        container[key] = value
        return

    if isinstance(container, list):
        container[int(key)] = value
        return

    setattr(container, key, value)