# -*- coding: utf-8 -*-

from data.relic.base_relic import RelicTemplate


class SaturatedFissureRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.saturated_fissure",
            name="饱和裂隙",
            story="上溢的深渊。无法再容纳的容器。",
            description="展开 Zone 时自动升为极 Zone；同属性极 Zone 期间再次展开时，额外延长 2 回合。",
            quantity="starting",
            owner_character_id="character.yoirine"
        )

    def modify_zone_deploy(self, context):
        game_state = context.game_state
        element = str(context.extra.get("element", "")).strip().lower()
        current_zone = getattr(game_state, "active_zone", None)

        same_extreme_zone = (
            current_zone is not None
            and getattr(current_zone, "is_extreme", False)
            and not current_zone.is_expired()
            and str(getattr(current_zone, "element", "")).strip().lower() == element
        )

        if same_extreme_zone:
            return {
                "extreme_extend_bonus": 2,
                "logs": [
                    "【{}】触发：同属性极 Zone 再展开时，额外延长 2 回合。".format(self.name)
                ]
            }

        return {
            "force_extreme": True,
            "logs": [
                "【{}】触发：展开 Zone 时自动再次展开，升级为极 Zone。".format(self.name)
            ]
        }
    
class MatteFalseEyeRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.matte_false_eye",
            name="灰暗的假眼",
            description="每次添加深渊凝视时，层数额外 +2。",
            story="被打磨成义眼片形状的哑光质地结晶。",
            quantity="common",
            owner_character_id="character.yoirine",
            allow_duplicate=False
        )

class FlowerInAbyssRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.flower_in_abyss",
            name="渊中花",
            description="有深渊凝视状态的敌人死亡时，将凝视层数均分至场上其他敌人。",
            story="被污秽淤染，仿佛氧化血液色彩的花朵。",
            quantity="rare",
            owner_character_id="character.yoirine",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_DAMAGE_AFTER
        if event_name != EVENT_DAMAGE_AFTER:
            return []

        dead = getattr(context, "target", None)
        if dead is None or not hasattr(dead, "enemy_id"):
            return []

        if not context.extra.get("target_was_alive", False) or not context.extra.get("target_is_dead_after", False):
            return []

        if getattr(dead, "_flower_in_abyss_triggered", False):
            return []

        if not hasattr(dead, "get_status_value"):
            return []

        gaze = int(dead.get_status_value("abyss_gaze"))
        if gaze <= 0:
            return []

        alive = [
            enemy
            for enemy in getattr(context.game_state, "enemies", []) or []
            if enemy is not dead and enemy.is_alive()
        ]

        if not alive:
            return []

        import random
        random.shuffle(alive)

        base, remainder = divmod(gaze, len(alive))
        if base <= 0 and remainder <= 0:
            return []

        setattr(dead, "_flower_in_abyss_triggered", True)

        logs = []
        logs.append("【{}】触发：将【{}】身上的 {} 层深渊凝视均分给其他敌人。".format(
            self.name,
            dead.name,
            gaze
        ))

        from game.relic_logic.combat_relic_utils import apply_status_with_player_relics
        player = getattr(context.game_state, "player", None)

        for index, enemy in enumerate(alive):
            amount = base + (1 if index < remainder else 0)
            if amount <= 0:
                continue

            logs.extend(apply_status_with_player_relics(
                game_state=context.game_state,
                source=player,
                target=enemy,
                status_key="abyss_gaze",
                amount=amount
            ))

        return logs