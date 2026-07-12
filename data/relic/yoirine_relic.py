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
    

class UnsealedAbyssRelic(RelicTemplate):
    def __init__(self):
        RelicTemplate.__init__(
            self,
            relic_id="relic.unsealed_abyss",
            name="解封的深渊",
            story="饱和的裂隙终于不再承认边界。自裂隙深处溢出的辉光，像是某种沉默的注视。",
            description="由【饱和裂隙】变化而来。拾起时，若牌组中有【辉晶领域】，为其中一张添加固有、保留和消耗；若没有，则加入一张拥有固有、保留和消耗的【辉晶领域】。展开 Zone 时自动升为极 Zone。极 Zone 持续时间变为无限，但每回合开始时失去 1 点生命。",
            quantity="myth",
            owner_character_id="character.yoirine",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from data.card.AAAregistry import create_card
        from game.constants import KEYWORD_INNATE, KEYWORD_RETAIN, KEYWORD_EXHAUST
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics

        logs = []

        keywords_to_add = [
            KEYWORD_INNATE,
            KEYWORD_RETAIN,
            KEYWORD_EXHAUST,
        ]

        def empower_crystal_zone(card):
            if not hasattr(card, "keywords") or card.keywords is None:
                card.keywords = []

            added = []
            for keyword in keywords_to_add:
                if keyword not in card.keywords:
                    card.keywords.append(keyword)
                    added.append(keyword)

            return added

        target_card = None
        for card in getattr(run_state, "master_deck", []) or []:
            if getattr(card, "card_id", "") == "card.crystal_zone":
                target_card = card
                break

        if target_card is not None:
            empower_crystal_zone(target_card)
            logs.append("【{}】触发：牌组中的【{}】获得固有、保留和消耗。".format(
                self.name,
                getattr(target_card, "name", "辉晶领域")
            ))
            return logs

        new_card = create_card("card.crystal_zone")
        empower_crystal_zone(new_card)

        logs.append("【{}】触发：牌组中没有【辉晶领域】，获得一张拥有固有、保留和消耗的【辉晶领域】。".format(
            self.name
        ))
        logs.extend(add_card_to_master_deck_with_relics(
            run_state,
            new_card,
            source=self.name,
            apply_gain_preview=False
        ))

        return logs

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
                "make_extreme_infinite": True,
                "logs": [
                    "【{}】触发：同属性极 Zone 再展开时，额外延长 2 回合；极 Zone 持续时间固定为无限。".format(self.name)
                ]
            }

        return {
            "force_extreme": True,
            "make_extreme_infinite": True,
            "logs": [
                "【{}】触发：展开 Zone 时自动再次展开，升级为极 Zone，且持续时间变为无限。".format(self.name)
            ]
        }

    def on_event(self, event_name, context):
        from game.constants import EVENT_TURN_START

        if event_name != EVENT_TURN_START:
            return []

        game_state = context.game_state
        player = getattr(game_state, "player", None)

        if player is None or not player.is_alive():
            return []

        zone = getattr(game_state, "active_zone", None)
        if zone is None:
            return []

        if not getattr(zone, "is_extreme", False):
            return []

        if not bool(getattr(zone, "unsealed_abyss_infinite", False)):
            return []

        logs = []
        logs.append("【{}】触发：无限极 Zone 的代价使 {} 失去 1 点生命。".format(
            self.name,
            player.name
        ))

        from game.damage import deal_damage
        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=player,
            amount=1,
            damage_kind="relic_hp_loss",
            card=None,
            is_reaction_damage=False,
            ignore_block=True,
            count_as_player_self_action_hp_loss=True
        ))

        return logs
    
class WhirlwallSparrowDownRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.whirlwall_sparrow_down",
            name="旋壁雀的绒羽",
            description="拾起时，在牌组中添加一张额外拥有保留的【磐愿+】。",
            story="重要的，不应该被忘记的人的羽毛。为什么会被丢在这里？……为什么会被“拿走”？",
            quantity="uncommon",
            owner_character_id="character.yoirine",
            allow_duplicate=False
        )

    def on_obtained(self, run_state):
        from data.card.AAAregistry import create_card
        from data.card.upgrade_rules import upgrade_card
        from game.constants import KEYWORD_RETAIN
        from game.relic_logic.run_relic_utils import add_card_to_master_deck_with_relics

        card = create_card("card.rockbound_wish")
        card = upgrade_card(card)

        if KEYWORD_RETAIN not in getattr(card, "keywords", []):
            card.keywords.append(KEYWORD_RETAIN)

        logs = ["【{}】触发：获得一张拥有保留的【{}】。".format(
            self.name,
            card.name
        )]

        logs.extend(add_card_to_master_deck_with_relics(
            run_state,
            card,
            source=self.name,
            apply_gain_preview=False
        ))

        return logs
    
class AbyssalWhisperRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.abyssal_whisper",
            name="深渊的诱语",
            description="阴 Zone 下，阴属性能力牌费用 -1，最低 -1。打出这类牌时失去 1 点生命。",
            story="脑海中的低语。无法理解的引诱之声。",
            quantity="rare",
            owner_character_id="character.yoirine",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_CARD_PLAY_AFTER

        if event_name != EVENT_CARD_PLAY_AFTER:
            return []

        game_state = context.game_state
        player = getattr(game_state, "player", None)
        card = getattr(context, "card", None)

        if player is None or card is None:
            return []

        if getattr(card, "card_type", "") != "power":
            return []

        if str(getattr(card, "attack_element", "") or "").strip().lower() != "shade":
            return []

        zone = getattr(game_state, "active_zone", None)
        if zone is None:
            return []

        try:
            if zone.is_expired():
                return []
        except Exception:
            pass

        if str(getattr(zone, "element", "") or "").strip().lower() != "shade":
            return []

        logs = []
        logs.append("【{}】触发：打出阴属性能力牌【{}】，失去 1 点生命。".format(
            self.name,
            card.name
        ))

        from game.damage import deal_damage
        logs.extend(deal_damage(
            game_state=game_state,
            source=player,
            target=player,
            amount=1,
            damage_kind="relic_hp_loss",
            card=card,
            is_reaction_damage=False,
            ignore_block=True,
            count_as_player_self_action_hp_loss=True
        ))

        return logs
    
class HomewardDeepLongingRelic(RelicTemplate):
    def __init__(self):
        super().__init__(
            relic_id="relic.homeward_deep_longing",
            name="“归乡深念”",
            description="每回合第一次由你造成的攻击伤害增加已失去生命比例。",
            story="某人温柔的声音。为什么如此重要的人的记忆会变得模糊？",
            quantity="uncommon",
            owner_character_id="character.yoirine",
            allow_duplicate=False
        )

    def on_event(self, event_name, context):
        from game.constants import EVENT_DAMAGE_BEFORE

        if event_name != EVENT_DAMAGE_BEFORE:
            return []

        game_state = context.game_state
        player = getattr(game_state, "player", None)

        if player is None:
            return []

        if getattr(context, "source", None) is not player:
            return []

        target = getattr(context, "target", None)
        if target is None or not hasattr(target, "enemy_id"):
            return []

        if context.extra.get("damage_kind", "") != "attack":
            return []

        current_turn = int(getattr(game_state, "turn_count", 0) or 0)
        used_turn = int(getattr(game_state, "homeward_deep_longing_used_turn", -1) or -1)

        if used_turn == current_turn:
            return []

        max_hp = int(getattr(player, "max_hp", 0) or 0)
        hp = int(getattr(player, "hp", 0) or 0)

        if max_hp <= 0:
            return []

        lost_hp = max(0, max_hp - hp)
        if lost_hp <= 0:
            game_state.homeward_deep_longing_used_turn = current_turn
            return []

        old_amount = int(context.extra.get("amount", 0) or 0)
        multiplier = 1.0 + float(lost_hp) / float(max_hp)
        new_amount = int(old_amount * multiplier)

        context.extra["amount"] = new_amount
        game_state.homeward_deep_longing_used_turn = current_turn

        return ["【{}】触发：已失去生命 {}/{}，本次攻击伤害 {} -> {}。".format(
            self.name,
            lost_hp,
            max_hp,
            old_amount,
            new_amount
        )]