# -*- coding: utf-8 -*-

from data.character.armored_warrior_character_test import ArmoredWarriorTestCharacter
from data.character.armored_warrior_character import ArmoredWarriorCharacter
from data.character.test_character import TestCharacter


CHARACTER_REGISTRY = {
    "character.test": TestCharacter,
    "character.armored_warrior" : ArmoredWarriorCharacter,
    "character.armored_warrior_test" : ArmoredWarriorTestCharacter,
}


def create_character(character_id):
    character_class = CHARACTER_REGISTRY.get(character_id)

    if character_class is None:
        raise ValueError("未知角色 ID：{}".format(character_id))

    return character_class()