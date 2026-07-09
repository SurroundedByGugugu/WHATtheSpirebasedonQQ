# -*- coding: utf-8 -*-

from data.character.lumine_character import LumineCharacter
from data.character.yoirine_character import YoirineCharacter
from data.character.suzuri_character import SuzuriCharacter
from data.character.armored_warrior_character import ArmoredWarriorCharacter
from data.character.silent_huntress_character import SilentHuntressCharacter
from data.character.test_character import TestCharacter


CHARACTER_REGISTRY = {
    "character.test": TestCharacter,
    "character.armored_warrior" : ArmoredWarriorCharacter,
    "character.silent_huntress": SilentHuntressCharacter,
    "character.lumine": LumineCharacter,
    "character.yoirine":YoirineCharacter,
    "character.suzuri": SuzuriCharacter,
}


def create_character(character_id):
    character_class = CHARACTER_REGISTRY.get(character_id)

    if character_class is None:
        raise ValueError("未知角色 ID：{}".format(character_id))

    return character_class()