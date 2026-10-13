"""Yoirine 的晶重放奖励与敌方行动后反射结算。"""
from game.resolution import resumable


def after_crystal_replay(state):
    player = state.player
    if getattr(state, 'crystal_replayed_turn', -1) == state.turn_count:
        return []
    state.crystal_replayed_turn = state.turn_count
    amount = player.statuses.get('crystal_dust')
    if amount <= 0 or not player.is_alive() or state.battle_over:
        return []
    from game.block import gain_block_without_modifiers
    return ['【结晶微尘】本回合首次晶重放，获得 {} 点格挡。'.format(amount)] + gain_block_without_modifiers(
        state, player, player, amount)


@resumable()
def after_enemy_actions(state):
    player = state.player
    armed = getattr(state, 'crystal_reflection_turn', -1) == state.turn_count
    state.crystal_reflection_turn = -1
    if not armed or getattr(state, 'player_attacked_turn', -1) != state.turn_count or not player.is_alive():
        return []
    remaining = max(0, player.block)
    player.block = 0
    enemies = [enemy for enemy in state.enemies if enemy.is_alive()]
    if not remaining or not enemies:
        return []
    amount = (remaining + len(enemies) - 1) // len(enemies)
    yield ['【晶面反射】失去 {} 点格挡，对每个敌人造成 {} 点无来源环境伤害。'.format(remaining, amount)]
    from game.damage import deal_damage
    for enemy in enemies:
        yield deal_damage(state, None, enemy, amount, damage_kind='environment', is_reaction_damage=True)
