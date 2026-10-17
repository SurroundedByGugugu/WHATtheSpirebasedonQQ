"""Small shared formatter for progress shown on relic buttons."""

def relic_counter_text(relic, battle=None, run_state=None):
    relic_id = getattr(relic, "relic_id", "")
    if relic_id == "relic.doubao":
        return "+{}力量".format(int(getattr(relic, "completed_battles", 0)))
    if relic_id == "relic.ink_bottle":
        return "{}/10".format(int(getattr(relic, "card_count", 0) or 0) % 10)
    if relic_id in {"relic.shuriken", "relic.kunai", "relic.ornamental_fan"}:
        counts = getattr(battle, "player_card_type_played_counts_this_turn", {}) if battle else {}
        return "{}/3".format(int((counts or {}).get("attack", 0) or 0) % 3)
    if relic_id == "relic.letter_opener":
        counts = getattr(battle, "player_card_type_played_counts_this_turn", {}) if battle else {}
        return "{}/3".format(int((counts or {}).get("skill", 0) or 0) % 3)
    if relic_id in {"relic.pen_nib", "relic.nunchaku"}:
        return "{}/10".format(int(getattr(relic, "attack_count", 0) or 0) % 10)
    if relic_id == "relic.sundial":
        return "{}/3".format(int(getattr(relic, "shuffle_count", 0) or 0) % 3)
    if relic_id == "relic.keystone_of_the_tomb":
        return "{}/6".format(int(getattr(relic, "skill_play_count", 0) or 0) % 6)
    if relic_id == "relic.incense_burner":
        return "{}/6".format(int(getattr(relic, "turn_counter", 0) or 0) % 6)
    if relic_id == "relic.happy_flower":
        return "{}/3".format(int(getattr(relic, "turn_counter", 0) or 0) % 3)
    return ""
