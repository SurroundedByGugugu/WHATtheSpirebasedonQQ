# -*- coding: utf-8 -*-

from data.card.base_card import CardTemplate


# starting

def create_earth_origin_dominion():
    return CardTemplate(
        card_id="card.earth_origin_dominion",
        name="地原统御",
        card_type="skill",
        cost=3,
        target="self",
        description="展开地 Zone。获得 10 点格挡。",
        quantity="starting",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "block": 10,
        },
        effects=[
            {
                "op": "set_zone",
                "element": "earth",
            },
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "地原统御+",
            "description": "费用减少 1。展开地 Zone。获得 10 点格挡。",
            "cost": 2,
        }
    )
def create_anatexis_action():
    return CardTemplate(
        card_id="card.anatexis_action",
        name="熔离作用",
        card_type="skill",
        cost=1,
        target="self",
        description="获得 4 点格挡和 3 层岩层。",
        quantity="starting",
        attack_element="earth",
        owner_character_id="character.suzuri",
        card_vars={
            "block": 4,
            "rock_layer": 3,
        },
        effects=[
            {
                "op": "gain_block",
                "target": "self",
                "amount": {
                    "var": "block",
                    "modifier_profile": "block",
                },
            },
            {
                "op": "gain_status",
                "target": "self",
                "status": "rock_layer",
                "amount": {
                    "var": "rock_layer",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "熔离作用+",
            "description": "获得 6 点格挡和 4 层岩层。",
            "card_vars": {
                "block": 6,
                "rock_layer": 4,
            },
        }
    )


# common
def create_anatexis():
    return CardTemplate(
        card_id="card.anatexis",
        name="深熔作用",
        card_type="skill",
        cost=2,
        target="self",
        description="获得 1 层岩浆层。有岩层时，消耗岩层并获得 1 点费用。",
        quantity="common",
        owner_character_id="character.suzuri",
        card_vars={
            "magma_layer": 1,
            "energy": 1,
        },
        effects=[
            {
                "op": "gain_status",
                "target": "self",
                "status": "magma_layer",
                "amount": {
                    "var": "magma_layer",
                },
            },
            {
                "op": "consume_status_gain_energy_if_present",
                "status": "rock_layer",
                "energy": {
                    "var": "energy",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "深熔作用+",
            "description": "获得 2 层岩浆层。有岩层时，消耗岩层并获得 1 点费用。",
            "card_vars": {
                "magma_layer": 2,
            }
        }
    )


# uncommon
def create_eruption_action():
    return CardTemplate(
        card_id="card.eruption_action",
        name="喷出作用",
        card_type="skill",
        cost=1,
        target="self",
        description="抽 2 张牌。在手牌中选择至多 1 张牌添加保留。",
        quantity="uncommon",
        owner_character_id="character.suzuri",
        card_vars={
            "draw": 2,
            "retain_count": 1,
        },
        effects=[
            {
                "op": "draw_cards",
                "amount": {
                    "var": "draw",
                },
            },
            {
                "op": "choose_hand_add_retain",
                "count": {
                    "var": "retain_count",
                },
            },
        ],
        upgraded=False,
        upgrade_patch={
            "name": "喷出作用+",
            "description": "抽 3 张牌。在手牌中选择至多 2 张牌添加保留。",
            "card_vars": {
                "draw": 3,
                "retain_count": 2,
            },
        }
    )