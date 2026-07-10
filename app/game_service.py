# -*- coding: utf-8 -*-

from game.constants import DEBUG_SEED
from game.command_help import command_tip
from game.engine import (
    play_card,
    play_cards_by_original_indices,
    end_turn,
    get_relics,
    use_potion,
    get_potions,
    get_draw_pile,
    get_discard_pile,
    get_exhaust_pile,
    discard_selected_hand_cards,
    choose_pending_discard_to_draw_top,
    choose_pending_exhaust_hand,
    choose_pending_hand_to_draw_top,
    get_status_detail,
    get_zone_field_view,
    choose_pending_upgrade_hand_card,
    choose_pending_duplicate_hand_card,
    choose_pending_element_plating,
    choose_pending_retain_hand_cards,
    format_pending_retain_hand_selection,
    choose_pending_fossil_exhaust_hand_cards,
    choose_pending_radiant_reflection_cards,
    choose_pending_synchronization_card,
    choose_pending_exhume_card,
    choose_pending_potion_card,
    choose_pending_elixir_cards,
    choose_pending_nilrys_card,
    choose_pending_toolbox_card,
    get_pending_player_choice_hint,
)

from game.relic_logic.bottle_utils import choose_pending_bottle_card, format_pending_bottle, has_pending_bottle_selection
from game.relic_logic.run_relic_utils import (
    format_pending_astrolabe, has_pending_astrolabe_selection,
    format_pending_empty_cage, has_pending_empty_cage_selection,
    format_pending_orrery, has_pending_orrery_selection, choose_pending_orrery_card,
    format_pending_dollys_mirror, has_pending_dollys_mirror_selection, choose_pending_dollys_mirror_card,
)

from game.run_engine import (
    start_run,
    get_run_view,
    choose_next_node,
    finish_current_battle_if_needed,
    get_reward_view,
    take_reward,
    take_rewards,
    choose_reward_card,
    choose_singing_bowl_reward,
    skip_reward,
    replace_reward_potion,
    handle_shop_buy,
    handle_shop_buy_batch,
    handle_remove_card_view_or_choose,
    handle_random_remove_card,
    leave_shop,
    handle_rest_option,
    handle_smith_card,
    handle_rest_remove_card,
    handle_event_option,
    handle_ancient_option,
    handle_shop_item_detail,
    reset_current_node_from_snapshot,
    handle_treasure_open,
    handle_treasure_take,
    leave_treasure,
    choose_astrolabe_cards,
    choose_empty_cage_cards,
    
)
from game.route import format_route_text
from game.reward import format_card_reward_choice
from game.display_names import format_potion_display_name, format_relic_display_name
from game.pending_choice import pending_choice_is
from app.debug_console import handle_debug_console, resolve_status_key, resolve_zone_spec
from app.command_parser import matches_root_command
from game.test_room import enter_test_room, get_test_room_usage
from data.content_gate import (
    get_private_content_status_text,
    set_private_content_enabled,
)
from game.multiplayer.service import MultiRoomService


CHARACTER_CHOICES = [
    {
        "index": 0,
        "character_id": "character.test",
        "name": "测试角色"
    },
    {
        "index": 1,
        "character_id": "character.armored_warrior",
        "name": "铁甲战士"
    },
    {
        "index": 2,
        "character_id": "character.silent_huntress",
        "name": "静默猎手"
    },
    {
        "index": 3,
        "character_id": "character.lumine",
        "name": "昼·里辛塔法"
    },
    {
        "index": 4,
        "character_id": "character.yoirine",
        "name": "Yoirine"
    },
    {
        "index": 5,
        "character_id": "character.suzuri",
        "name": "Suzuri"
    }
]

class GameService(object):
    """
    管理不同会话的 RunState

    main.py 只需要：
        reply = game_service.handle_message(session_id, user_id, raw_message)
        if reply:
            send_reply(reply)

    当前策略：
    - 一个 session 暂时只允许一个 owner 操作。
    - 群聊 session 通常是 group:{group_id}，因此同一群内暂时无法多开。
    - 后续如果要做多人内容，可以把 owners 从单个 user_id 扩展为参与者集合，
      或者把 session_id 改成 group:{group_id}:battle:{battle_id}。
    """

    SAME_GROUP_SINGLE_GAME_MESSAGE = "同一群内暂时无法多开"

    def __init__(self):
        self.sessions = {}
        self.session_owners = {}
        self.pending_confirmations = {}
        self.multiplayer_service = MultiRoomService()

    def get_run(self, session_id):
        return self.sessions.get(session_id)

    def set_run(self, session_id, run_state, owner_user_id):
        self.sessions[session_id] = run_state
        self.session_owners[session_id] = str(owner_user_id)

    def clear_run(self, session_id):
        if session_id in self.sessions:
            del self.sessions[session_id]

        if session_id in self.session_owners:
            del self.session_owners[session_id]

        if session_id in self.pending_confirmations:
            del self.pending_confirmations[session_id]

    def get_owner(self, session_id):
        return self.session_owners.get(session_id)

    def is_owned_by_other_user(self, session_id, user_id):
        owner_user_id = self.get_owner(session_id)

        if owner_user_id is None:
            return False

        return str(owner_user_id) != str(user_id)

    def append_run_progress_after_battle(self, session_id, run_state, battle_reply):
        """
        战斗命令执行后刷新当前 Run 信息。
        如果战斗结束，把结果交给 RunEngine 处理。
        """
        route_reply = finish_current_battle_if_needed(run_state)

        if route_reply:
            full_reply = battle_reply + "\n\n" + route_reply

            if run_state.run_over:
                self.clear_run(session_id)

            return full_reply

        if run_state.current_battle is not None and not run_state.current_battle.battle_over:
            return battle_reply + "\n\n" + get_run_view(run_state)

        return battle_reply

    def has_active_runs(self):
        return bool(self.sessions)

    def handle_private_content_command(self, session_id, parts):
        if len(parts) <= 2 or parts[2].lower() in ("status", "状态", "查看"):
            return "当前会话 private 内容开关：{}。".format(
                get_private_content_status_text(session_id=session_id)
            )

        action = parts[2].lower()

        if action in ("on", "open", "enable", "enabled", "开", "开启"):
            enabled = True
        elif action in ("off", "close", "disable", "disabled", "关", "关闭"):
            enabled = False
        else:
            return "用法：/card private on 或 /card private off。当前会话：{}。".format(
                get_private_content_status_text(session_id=session_id)
            )

        current_run = self.get_run(session_id)
        if current_run is not None and not getattr(current_run, "run_over", False):
            return "当前会话已有进行中的 Run，不能在 Run 过程中修改 private 内容开关。当前：{}。".format(
                get_private_content_status_text(session_id=session_id)
            )

        set_private_content_enabled(enabled, session_id=session_id)
        return "当前会话 private 内容开关：已{}。".format(
            get_private_content_status_text(session_id=session_id)
        )

    def is_known_card_command(self, command):
        return command in {
            "help", "帮助",
            "plate", "plating", "镀层", "选择镀层",
            "characters", "character", "chars", "角色", "角色选择", "查看角色",
            "info", "说明", "查看说明", "buffinfo", "状态说明",
            "private", "私货",
            "new",
            "yes", "y", "确认", "是",
            "no", "cancel", "取消", "否",
            "exit", "退出", "下一把",
            "sl", "读档", "回档", "回退","slyes",
            "hand", "view", "查看", "手牌", "查看战斗状态", "查看手牌", "run", "角色状态", "当前状态",
            "status", "状态", "查看状态", "查看buff", "buff", "debuff",
            "state", "zone", "field", "场地", "查看场地", "查看zone", "查看field",
            "route", "map", "路线", "地图",
            "reward", "rewards", "奖励", "查看奖励",
            "chest", "treasure", "宝箱", "查看宝箱",
            "open", "open_chest", "打开", "开宝箱", "打开宝箱",
            "relics", "relic", "遗物", "查看已有遗物", "查看遗物",
            "relic_story", "relicstory", "lore", "遗物故事", "查看遗物故事",
            "potions", "potion_list", "药水", "查看药水",
            "deck", "master_deck", "牌库", "查看牌库", "卡组", "查看卡组",
            "bottle", "bottled", "瓶装", "选择瓶装",
            "astrolabe", "星盘",
            "cage", "empty_cage", "鸟笼", "空鸟笼",
            "orrery", "星系仪",
            "mirror", "dolly", "dollys_mirror", "镜子", "多利之镜",
            "pick", "choose", "选择奖励", "选牌",
            "take", "claim", "领取", "拿取",
            "replace_potion", "replacepotion", "换药水", "替换药水",
            "bowl", "singing_bowl", "颂钵", "唱歌碗",
            "skip", "skip_reward", "跳过", "跳过奖励",
            "shop", "商店",
            "item", "goods", "商品", "查看商品", "shop_item", "detail", "详情",
            "buy", "购买",
            "remove", "remove_card", "删牌", "删除牌",
            "random_remove", "randomremove", "随机删牌",
            "leave", "离开",
            "rest", "火堆", "休息",
            "smith", "upgrade", "锻造", "升级",
            "rest_remove", "pipe", "peace_pipe", "烟斗", "宁静烟斗",
            "event", "事件",
            "testroom", "test_room", "测试房间",
            "ancient", "先古", "先古之民",
            "next", "go", "选择路线", "前进",
            "toolbox", "工具箱",
            "drop", "drop_hand", "丢弃手牌", "选择丢弃",
            "top", "headbutt", "置顶", "选择弃牌置顶",
            "exhaust_hand", "burn", "consume", "选择消耗", "消耗手牌",
            "handtop", "hand_top", "warcry", "置顶手牌", "手牌置顶",
            "upgrade_hand", "upgradehand", "armaments", "选择升级", "升级手牌",
            "duplicate_hand", "dual_wield", "复制手牌", "双持",
            "exhume", "发掘", "选择发掘",
            "retain", "retain_hand", "选择保留", "保留",
            "fossil", "化石",
            "potion_pick", "potion_card", "药水选牌", "选择药水牌",
            "elixir", "万灵", "万灵药水",
            "codex", "nilry", "nilrys", "宝典", "尼利",
            "potion", "use_potion", "useitem", "使用药水", "使用道具",
            "draw", "drawpile", "draw_pile", "抽牌堆", "查看抽牌堆",
            "discard", "discardpile", "discard_pile", "弃牌堆", "查看弃牌堆",
            "exhaust", "exhaustpile", "exhaust_pile", "消耗牌堆", "消耗堆", "查看消耗牌堆", "查看消耗堆",
            "reflect", "reflection", "映照", "辉晶映照",
            "sync", "synchronize", "同调",
            "play",
            "end",
        }

    def handle_message(self, session_id, user_id, raw_message):
        """
        处理一条文本命令。
        不认识 QQ，不认识 LLOB。
        """
        text = raw_message.strip()
        is_card_command = matches_root_command(text, "card")
        is_ctrl_command = matches_root_command(text, "ctrl")
        if not (is_card_command or is_ctrl_command):
            return None
        parts = text.split()
        if len(parts) == 1:
            if is_ctrl_command:
                return handle_debug_console(None, parts)
            return self.help_text()
        command = parts[1].lower()

        if is_ctrl_command:
            if command in ("help", "帮助"):
                return handle_debug_console(None, parts)

            run_state = self.get_run(session_id)
            if run_state is None:
                return "当前会话还没有路线。使用 /card new [角色序号] 开始。"
            if self.is_owned_by_other_user(session_id, user_id):
                return self.SAME_GROUP_SINGLE_GAME_MESSAGE
            reply = handle_debug_console(run_state, parts)
            route_reply = finish_current_battle_if_needed(run_state)
            if route_reply:
                full_reply = reply + "\n\n" + route_reply
                if run_state.run_over:
                    self.clear_run(session_id)
                return full_reply
            return reply

        if command in ("help", "帮助"):
            return self.opening_help_text()

        if command in ("characters", "character", "chars", "角色", "角色选择", "查看角色"):
            return self.character_choices_text()

        if command in ("info", "说明", "查看说明", "buffinfo", "状态说明"):
            return self.get_general_info(parts)

        if command in ("private", "私货"):
            return self.handle_private_content_command(session_id, parts)

        if command in ("multi", "mp", "多人", "联机"):
            return self.multiplayer_service.handle_message(session_id, user_id, parts)

        if command == "new":
            character_id = self.resolve_character_id(parts)
            if character_id is None:
                return "角色编号无效。\n{}".format(self.character_choices_text())

            current_run = self.get_run(session_id)

            # 没有 Run，或旧 Run 已结束但尚未清理：直接开新 Run。
            if current_run is None or getattr(current_run, "run_over", False):
                run_state, reply = start_run(
                    session_id=session_id,
                    character_id=character_id,
                    seed=DEBUG_SEED
                )
                self.set_run(session_id, run_state, user_id)
                self.pending_confirmations.pop(session_id, None)
                return reply

            # 已有正在进行的 Run 时，仍然保持同群单人操作限制。
            if self.is_owned_by_other_user(session_id, user_id):
                return self.SAME_GROUP_SINGLE_GAME_MESSAGE

            # 当前 owner 主动 new：进入二次确认。
            return self.request_new_run(session_id, character_id, user_id)

        run_state = self.get_run(session_id)

        if run_state is None:
            if not self.is_known_card_command(command):
                return "无效的指令：{}".format(command)
            return "当前会话还没有路线。使用 /card new [角色序号] 开始。"

        # 只要 run 存在，就要检查 owner，不再依赖 current_battle
        if self.is_owned_by_other_user(session_id, user_id):
            return self.SAME_GROUP_SINGLE_GAME_MESSAGE

        if command in ("yes", "y", "确认", "是"):
            return self.handle_yes(session_id, run_state)

        if command in ("no", "cancel", "取消", "否"):
            if session_id in self.pending_confirmations:
                del self.pending_confirmations[session_id]
                return "已取消确认操作。"
            return "当前没有需要取消的确认操作。"

        if command in ("exit", "退出", "下一把"):
            return self.request_exit_run(session_id, run_state)

        if command in ("sl", "读档", "回档", "回退"):
            return self.request_sl(session_id, run_state)
        if command == "slyes":
            return self.execute_sl(session_id, run_state)
        # 这些命令是 Run 层命令，允许当前没有战斗
        if command in ("hand", "view", "查看", "手牌", "查看战斗状态", "查看手牌", "run", "info", "角色", "角色状态", "当前状态"):
            return get_run_view(run_state)

        if command in ("status", "状态", "查看状态", "查看buff", "buff", "debuff"):
            if run_state.current_battle is None:
                return get_run_view(run_state)
            return get_status_detail(run_state.current_battle)

        if command in ("state", "zone", "field", "场地", "查看场地", "查看zone", "查看field"):
            if run_state.current_battle is None:
                return "当前不在战斗中，没有可查看的 Zone / Field。"
            return get_zone_field_view(run_state.current_battle)

        if command in ("route", "map", "路线", "地图"):
            return format_route_text(run_state)
        
        if command in ("reward", "rewards", "奖励", "查看奖励"):
            return get_reward_view(run_state)

        if command in ("chest", "treasure", "宝箱", "查看宝箱"):
            if getattr(run_state, "pending_treasure", None) is None:
                return "当前不在宝箱房间。"
            return get_reward_view(run_state)

        if command in ("open", "open_chest", "打开", "开宝箱", "打开宝箱"):
            if getattr(run_state, "pending_treasure", None) is None:
                return "当前没有可打开的宝箱。"
            return handle_treasure_open(run_state)

        if command in ("relics", "relic", "遗物", "查看已有遗物", "查看遗物"):
            return self.get_run_relics(run_state)
        
        if command in ("relic_story", "relicstory", "lore", "遗物故事", "查看遗物故事"):
            if len(parts) < 3:
                return "用法：/card relic_story 遗物编号，例如 /card relic_story 0"
            try:
                relic_index = int(parts[2])
            except ValueError:
                return "遗物编号必须是数字。"
            return self.get_run_relic_story(run_state, relic_index)

        if command in ("potions", "potion_list", "药水", "查看药水"):
            return self.get_run_potions(run_state)
        
        if command in ("deck", "master_deck", "牌库", "查看牌库", "卡组", "查看卡组"):
            if len(parts) >= 3:
                try:
                    card_index = int(parts[2])
                except ValueError:
                    return "牌库编号必须是数字。"
                return self.get_run_deck_detail(run_state, card_index)
            return self.get_run_deck(run_state)
        
        if command in ("bottle", "bottled", "瓶装", "选择瓶装"):
            if len(parts) < 3:
                return format_pending_bottle(run_state)
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "瓶装选择编号必须是数字。"
            return choose_pending_bottle_card(run_state, choice_index)

        if has_pending_bottle_selection(run_state):
            return "\n".join([
                "当前需要先处理瓶装选择。",
                "",
                format_pending_bottle(run_state)
            ])

        if command in ("astrolabe", "星盘"):
            if len(parts) < 3:
                return format_pending_astrolabe(run_state)
            indices = self.parse_index_list(parts[2])
            if indices is None:
                return "卡牌编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card astrolabe 0,1,2。"
            return choose_astrolabe_cards(run_state, indices)

        if has_pending_astrolabe_selection(run_state):
            return "\n".join([
                "当前需要先处理【星盘】选择。",
                "",
                format_pending_astrolabe(run_state)
            ])

        if command in ("cage", "empty_cage", "鸟笼", "空鸟笼"):
            if len(parts) < 3:
                return format_pending_empty_cage(run_state)
            indices = self.parse_index_list(parts[2])
            if indices is None:
                return "卡牌编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card cage 0,1。"
            return choose_empty_cage_cards(run_state, indices)

        if has_pending_empty_cage_selection(run_state):
            return "\n".join([
                "当前需要先处理【空鸟笼】选择。",
                "",
                format_pending_empty_cage(run_state)
            ])

        if command in ("orrery", "星系仪"):
            if len(parts) < 3:
                return format_pending_orrery(run_state)
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "星系仪选择编号必须是数字。"
            return choose_pending_orrery_card(run_state, choice_index)

        if has_pending_orrery_selection(run_state):
            return "\n".join([
                "当前需要先处理【星系仪】选择。",
                "",
                format_pending_orrery(run_state)
            ])

        if command in ("mirror", "dolly", "dollys_mirror", "镜子", "多利之镜"):
            if len(parts) < 3:
                return format_pending_dollys_mirror(run_state)
            try:
                card_index = int(parts[2])
            except ValueError:
                return "多利之镜牌组编号必须是数字。"
            return choose_pending_dollys_mirror_card(run_state, card_index)

        if has_pending_dollys_mirror_selection(run_state):
            return "\n".join([
                "当前需要先处理【多利之镜】选择。",
                "",
                format_pending_dollys_mirror(run_state)
            ])
        
        if command in ("pick", "choose", "选择奖励", "选牌"):
            if len(parts) < 3:
                return "用法：/card pick 卡牌编号，例如 /card pick 0"
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "卡牌编号必须是数字。"
            reply = choose_reward_card(run_state, choice_index)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply
        
        if command in ("take", "claim", "领取", "拿取"):
            if len(parts) < 3:
                if getattr(run_state, "pending_treasure", None) is not None:
                    return "用法：/card take 宝箱内容编号，例如 /card take 0"
                return "用法：/card take 奖励编号，例如 /card take 0 或 /card take 0,1,2"
            option_indices = self.parse_index_list(parts[2])
            if option_indices is None:
                return "编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card take 0,1,2。"
            if run_state.pending_reward is not None:
                if len(option_indices) == 1:
                    reply = take_reward(run_state, option_indices[0])
                else:
                    reply = take_rewards(run_state, option_indices)
            elif getattr(run_state, "pending_treasure", None) is not None:
                if len(option_indices) != 1:
                    return "宝箱内容暂不支持批量拿取，请使用 /card take 0。"
                reply = handle_treasure_take(run_state, option_indices[0])
            else:
                return "当前没有待领取奖励或宝箱内容。"
            if run_state.run_over:
                self.clear_run(session_id)
            return reply
        
        if command in ("replace_potion", "replacepotion", "换药水", "替换药水"):
            if len(parts) < 4:
                return "用法：/card replace_potion 奖励编号 已有药水编号，例如 /card replace_potion 2 0"
            try:
                option_index = int(parts[2])
            except ValueError:
                return "奖励编号必须是数字。"
            try:
                potion_index = int(parts[3])
            except ValueError:
                return "已有药水编号必须是数字。"
            reply = replace_reward_potion(run_state, option_index, potion_index)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply
                

        if command in ("bowl", "singing_bowl", "颂钵", "唱歌碗"):
            reply = choose_singing_bowl_reward(run_state)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply
        
        if command in ("skip", "skip_reward", "跳过", "跳过奖励"):
            reply = skip_reward(run_state)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply
        
        # 商店命令
        if command in ("shop", "商店"):
            if run_state.pending_shop is None:
                return "当前不在商店。"
            return get_run_view(run_state)
        
        if command in ("item", "goods", "商品", "查看商品", "shop_item", "detail", "详情"):
            if len(parts) < 3:
                return "用法：/card item 商品编号，例如 /card item 0"
            try:
                item_index = int(parts[2])
            except ValueError:
                return "商品编号必须是数字。"
            return handle_shop_item_detail(run_state, item_index)

        if command in ("buy", "购买"):
            if len(parts) < 3:
                return "用法：/card buy 商品编号，例如 /card buy 0 或 /card buy 0,1,2"
            item_indices = self.parse_index_list(parts[2])
            if item_indices is None:
                return "商品编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card buy 0,1,2。"
            if len(item_indices) == 1:
                return handle_shop_buy(run_state, item_indices[0])
            return handle_shop_buy_batch(run_state, item_indices)


        if command in ("remove", "remove_card", "删牌", "删除牌"):
            if len(parts) < 3:
                return handle_remove_card_view_or_choose(run_state)
            try:
                card_index = int(parts[2])
            except ValueError:
                return "卡牌编号必须是数字。"
            return handle_remove_card_view_or_choose(run_state, card_index)


        if command in ("random_remove", "randomremove", "随机删牌"):
            return handle_random_remove_card(run_state, seed=DEBUG_SEED)

        if command in ("leave", "离开"):
            if getattr(run_state, "pending_treasure", None) is not None:
                reply = leave_treasure(run_state)
                if run_state.run_over:
                    self.clear_run(session_id)
                return reply
            if run_state.pending_rest is not None:
                # 微型帐篷火堆专用离开；普通火堆若还没使用选项，会在 run_engine 里正常完成当前节点。
                from game.node.node_rest import has_miniature_tent
                if has_miniature_tent(run_state):
                    # 找到 leave 选项编号并调用统一处理。
                    from game.node.node_rest import get_rest_options
                    options = get_rest_options(run_state)
                    for idx, item in enumerate(options):
                        if item[0] == "leave":
                            reply = handle_rest_option(run_state, idx)
                            if run_state.run_over:
                                self.clear_run(session_id)
                            return reply
                return "当前在火堆。请选择火堆选项；拥有【微型帐篷】时可使用 leave 离开。"
            reply = leave_shop(run_state)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply

        # 火堆命令
        if command in ("rest", "火堆", "休息"):
            if len(parts) < 3:
                return get_run_view(run_state)
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "火堆选项编号必须是数字。"
            reply = handle_rest_option(run_state, choice_index)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply


        if command in ("smith", "upgrade", "锻造", "升级"):
            if len(parts) < 3:
                return "用法：/card smith 0"
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "锻造编号必须是数字。"
            reply = handle_smith_card(run_state, choice_index)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply

        if command in ("rest_remove", "pipe", "peace_pipe", "烟斗", "宁静烟斗"):
            if len(parts) < 3:
                return "用法：/card rest_remove 0"
            try:
                card_index = int(parts[2])
            except ValueError:
                return "卡牌编号必须是数字。"
            reply = handle_rest_remove_card(run_state, card_index)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply

        # 事件命令
        if command in ("event", "事件"):
            if len(parts) < 3:
                return get_run_view(run_state)
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "事件选项编号必须是数字。"
            reply = handle_event_option(run_state, choice_index, seed=DEBUG_SEED)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply

        if command in ("testroom", "test_room", "测试房间"):
            if len(parts) < 3:
                return get_test_room_usage()
            return enter_test_room(run_state, parts[2], seed=DEBUG_SEED)

        # 先古之民命令
        if command in ("ancient", "先古", "先古之民"):
            if len(parts) < 3:
                return get_run_view(run_state)
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "先古之民选项编号必须是数字。"
            reply = handle_ancient_option(run_state, choice_index, seed=DEBUG_SEED)
            if run_state.run_over:
                self.clear_run(session_id)
            return reply
        
        if run_state.pending_reward is not None:
            return "当前需要先处理战斗奖励。使用 /card reward 查看奖励，/card pick 0 选择卡牌，或 /card skip 跳过。"

        if command in ("next", "go", "选择路线", "前进"):
            if len(parts) < 3:
                return "用法：/card next 节点编号，例如 /card next 0"

            try:
                choice_index = int(parts[2])
            except ValueError:
                return "节点编号必须是数字。"

            reply = choose_next_node(run_state, choice_index, seed=DEBUG_SEED)

            if run_state.run_over:
                self.clear_run(session_id)

            return reply
        
        if not self.is_known_card_command(command):
            return "无效的指令：{}".format(command)

        game_state = run_state.current_battle

        if command in ("potion", "use_potion", "useitem", "item", "使用药水", "使用道具"):
            if game_state is None:
                return self.handle_use_potion_outside_battle(run_state, parts)
            reply = self.handle_use_potion(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)

        if game_state is None:
            return "当前不在战斗中。可以使用 /card route 查看路线，或 /card next 0 进入下一节点。"
        if command in ("plate", "plating", "镀层", "选择镀层"):
            if not pending_choice_is(game_state, "element_plating"):
                return "当前没有需要处理的镀层选择。"
            if len(parts) < 3:
                return "用法：/card plate 0"
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "镀层选择编号必须是数字。"
            reply = choose_pending_element_plating(game_state, choice_index)
            return self.append_run_progress_after_battle(session_id, run_state, reply)

        if pending_choice_is(game_state, "element_plating"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("toolbox", "工具箱"):
            if not getattr(game_state, "pending_toolbox_selection", False):
                return "当前没有需要处理的【工具箱】选择。"
            if len(parts) < 3:
                return "用法：/card toolbox 0"
            try:
                choice_index = int(parts[2])
            except ValueError:
                return "工具箱选择编号必须是数字。"
            reply = choose_pending_toolbox_card(game_state, choice_index)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if getattr(game_state, "pending_toolbox_selection", False):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("drop", "drop_hand", "丢弃手牌", "选择丢弃"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not game_state.pending_discard_selection:
                return "当前没有需要处理的弃牌选择。"
            reply = self.handle_drop(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_discard_selection:
            return get_pending_player_choice_hint(game_state)

        if command in ("top", "headbutt", "置顶", "选择弃牌置顶"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not (
                game_state.pending_discard_to_draw_selection
                or pending_choice_is(game_state, "discard_to_draw_top")
            ):
                return "当前没有需要处理的弃牌堆置顶选择。"
            reply = self.handle_discard_to_draw_top(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_discard_to_draw_selection or pending_choice_is(game_state, "discard_to_draw_top"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("exhaust_hand", "burn", "consume", "选择消耗", "消耗手牌") or (
            command == "exhaust" and game_state.pending_exhaust_hand_selection
        ):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not game_state.pending_exhaust_hand_selection:
                return "当前没有需要处理的手牌消耗选择。"
            reply = self.handle_exhaust_hand(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_exhaust_hand_selection:
            return get_pending_player_choice_hint(game_state)

        if command in ("handtop", "hand_top", "warcry", "置顶手牌", "手牌置顶"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not (
                game_state.pending_hand_to_draw_top_selection
                or pending_choice_is(game_state, "hand_to_draw_top")
            ):
                return "当前没有需要处理的手牌置顶选择。"
            reply = self.handle_hand_to_draw_top(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_hand_to_draw_top_selection or pending_choice_is(game_state, "hand_to_draw_top"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("upgrade_hand", "upgradehand", "armaments", "选择升级", "升级手牌"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not (
                game_state.pending_upgrade_hand_selection
                or pending_choice_is(game_state, "upgrade_hand")
            ):
                return "当前没有需要处理的手牌升级选择。"
            reply = self.handle_upgrade_hand(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_upgrade_hand_selection or pending_choice_is(game_state, "upgrade_hand"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("duplicate_hand", "dual_wield", "复制手牌", "双持"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not game_state.pending_duplicate_hand_selection:
                return "当前没有需要处理的复制手牌选择。"
            reply = self.handle_duplicate_hand(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_duplicate_hand_selection:
            return get_pending_player_choice_hint(game_state)

        if command in ("exhume", "发掘", "选择发掘"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not game_state.pending_exhume_selection:
                return "当前没有需要处理的发掘选择。"
            reply = self.handle_exhume(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if game_state.pending_exhume_selection:
            return get_pending_player_choice_hint(game_state)
        
        if command in ("retain", "retain_hand", "选择保留", "保留"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not pending_choice_is(game_state, "retain_hand"):
                return "当前没有需要处理的保留选择。"
            reply = self.handle_retain_hand(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if pending_choice_is(game_state, "retain_hand"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("fossil", "化石"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not pending_choice_is(game_state, "fossil_exhaust_hand"):
                return "当前没有需要处理的化石选择。"
            reply = self.handle_fossil(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if pending_choice_is(game_state, "fossil_exhaust_hand"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("reflect", "reflection", "映照", "辉晶映照"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not pending_choice_is(game_state, "radiant_reflection"):
                return "当前没有需要处理的辉晶映照选择。"
            reply = self.handle_radiant_reflection(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if pending_choice_is(game_state, "radiant_reflection"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("sync", "synchronize", "同调"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not pending_choice_is(game_state, "synchronization"):
                return "当前没有需要处理的同调选择。"
            reply = self.handle_synchronization(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if pending_choice_is(game_state, "synchronization"):
            return get_pending_player_choice_hint(game_state)
        
        if command in ("potion_pick", "potion_card", "药水选牌", "选择药水牌"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not getattr(game_state, "pending_potion_card_selection", False):
                return "当前没有需要处理的药水选牌。"
            reply = self.handle_potion_pick(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if getattr(game_state, "pending_potion_card_selection", False):
            return get_pending_player_choice_hint(game_state)

        if command in ("elixir", "万灵", "万灵药水"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not getattr(game_state, "pending_elixir_selection", False):
                return "当前没有需要处理的万灵药水选择。"
            reply = self.handle_elixir(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if getattr(game_state, "pending_elixir_selection", False):
            return get_pending_player_choice_hint(game_state)

        if command in ("codex", "nilry", "nilrys", "宝典", "尼利"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not getattr(game_state, "pending_nilrys_selection", False):
                return "当前没有需要处理的尼利的宝典选择。"
            reply = self.handle_codex(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        if getattr(game_state, "pending_nilrys_selection", False):
            return get_pending_player_choice_hint(game_state)

        if command in ("potion", "use_potion", "useitem", "item", "使用药水", "使用道具"):
            game_state = run_state.current_battle
            if game_state is None:
                return self.handle_use_potion_outside_battle(run_state, parts)
            reply = self.handle_use_potion(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)

        if command in ("draw", "drawpile", "draw_pile", "抽牌堆", "查看抽牌堆"):
            return get_draw_pile(game_state)

        if command in ("discard", "discardpile", "discard_pile", "弃牌堆", "查看弃牌堆"):
            return get_discard_pile(game_state)

        if command in ("exhaust", "exhaustpile", "exhaust_pile", "消耗牌堆", "消耗堆", "查看消耗牌堆", "查看消耗堆"):
            return get_exhaust_pile(game_state)

        if command == "play":
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。可以使用 /card route 查看路线，或 /card next 0 进入下一节点。"
            reply = self.handle_play(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)
        
        if command == "end":
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。可以使用 /card route 查看路线，或 /card next 0 进入下一节点。"
            reply = end_turn(game_state)
            return self.append_run_progress_after_battle(session_id, run_state, reply)

        return "无效的指令：{}".format(command)

    def request_exit_run(self, session_id, run_state):
        """
        /card exit / 下一把：
        任意时机结束当前 Run。
        - 战斗中：走战斗失败结算。
        - 战斗外：直接结束并清理当前 Run。
        """
        if getattr(run_state, "run_over", False):
            self.clear_run(session_id)
            return "当前 Run 已结束。可以使用 /card new [角色序号] 开始下一把。"

        self.pending_confirmations[session_id] = {"action": "exit_run"}

        game_state = run_state.current_battle
        if game_state is not None and not game_state.battle_over:
            title = "确认退出当前战斗并按战斗失败处理？"
        else:
            title = "确认结束当前 Run 并按失败处理？"

        return "\n".join([
            title,
            command_tip("yes", "使用 /card yes 确认。"),
            command_tip("no", "使用 /card no 取消。"),
        ])

    def request_sl(self, session_id, run_state):
        if getattr(run_state, "node_entry_snapshot", None) is None:
            return "当前节点没有可读取的节点入口快照。"

        self.pending_confirmations[session_id] = {"action": "sl"}

        return "\n".join([
            "确认读取存档并回到进入当前节点时？",
            command_tip("yes", "使用 /card yes 确认。"),
            command_tip("no", "使用 /card no 取消。"),
        ])
    def execute_sl(self, session_id, run_state):
        if getattr(run_state, "node_entry_snapshot", None) is None:
            return "当前节点没有可读取的节点入口快照。"

        self.pending_confirmations.pop(session_id, None)
        new_run_state, reply = reset_current_node_from_snapshot(run_state, seed=DEBUG_SEED)
        self.sessions[session_id] = new_run_state
        if new_run_state.run_over:
            self.clear_run(session_id)
        return reply
    def request_new_run(self, session_id, character_id, user_id):
        self.pending_confirmations[session_id] = {
            "action": "new_run",
            "character_id": character_id,
            "owner_user_id": str(user_id),
        }

        character_name = self.get_character_display_name(character_id)

        return "\n".join([
            "当前已有正在进行的 Run。确认放弃当前 Run 并开始新 Run？",
            "新 Run 角色：{}。".format(character_name),
            command_tip("yes", "使用 /card yes 确认。"),
            command_tip("no", "使用 /card no 取消。"),
        ])

    def handle_yes(self, session_id, run_state):
        pending = self.pending_confirmations.pop(session_id, None)
        if pending is None:
            return "当前没有需要确认的操作。"

        action = pending.get("action")

        if action in ("exit_battle", "exit_run"):
            game_state = run_state.current_battle

            # 战斗中：沿用战斗失败流程，让 finish_current_battle_if_needed 统一收尾。
            if game_state is not None and not game_state.battle_over:
                game_state.battle_over = True
                game_state.victory = False
                reply = "已退出当前战斗，按战斗失败处理。"
                return self.append_run_progress_after_battle(session_id, run_state, reply)

            # 战斗外：直接结束当前 Run。
            run_state.run_over = True
            run_state.victory = False
            self.clear_run(session_id)
            return "已结束当前 Run，按失败处理。\n可以使用 /card new [角色序号] 开始下一把。"
        
        if action == "sl":
            return self.execute_sl(session_id, run_state)

        if action == "new_run":
            character_id = pending.get("character_id")
            if character_id is None:
                return "新 Run 确认信息缺少角色。请重新使用 /card new [角色序号]。"

            owner_user_id = pending.get("owner_user_id") or self.get_owner(session_id)

            run_state, reply = start_run(
                session_id=session_id,
                character_id=character_id,
                seed=DEBUG_SEED
            )
            self.set_run(session_id, run_state, owner_user_id)

            return "已确认放弃当前 Run，并开始新 Run。\n\n" + reply

        return "未知确认操作：{}。".format(action)

    def get_general_info(self, parts):
        if len(parts) < 3:
            return "用法：/card info weak。也可查询：虚弱、易伤、脆弱、力量、仪式、火Zone、极晶Zone 等。"
        raw_key = " ".join(parts[2:]).strip().lower()
        return self.format_status_or_zone_info(raw_key)

    def format_status_or_zone_info(self, raw_key):
        status_key = resolve_status_key(raw_key)
        if status_key:
            return self.format_status_info(status_key)

        element, is_extreme = resolve_zone_spec(raw_key)
        if element:
            return self.format_zone_info(element, is_extreme=is_extreme)

        return "没有找到【{}】的说明。可用示例：/card info weak，/card info 虚弱，/card info 火Zone。".format(raw_key)

    def format_status_info(self, status_key):
        from game.status.status_defs import get_status_def, get_status_name

        detail_overrides = {
            "weak": "造成的攻击伤害减少 25%。",
            "vulnerable": "受到的攻击伤害增加 50%。",
            "frail": "获得的格挡减少 25%。",
            "strength": "攻击伤害按层数增加。层数可以为负。",
            "dexterity": "技能牌获得格挡按层数增加。层数可以为负。",
            "ritual": "玩家：回合开始时获得等同于层数的力量；敌人：敌方回合结束时获得等同于层数的力量，刚获得的同一回合不触发。",
            "artifact": "抵消下一次负面状态。",
            "stun": "跳过行动。",
        }
        status_def = get_status_def(status_key)
        if status_def is None:
            return "没有找到状态【{}】。".format(status_key)
        description = detail_overrides.get(status_key, getattr(status_def, "description", ""))
        if not description:
            description = "暂无详细说明。"
        lines = []
        lines.append("=== 状态说明 ===")
        lines.append("名称：{}（{}）".format(get_status_name(status_key), status_key))
        lines.append("类型：{}".format(getattr(status_def, "category", "neutral")))
        lines.append("显示：{}".format(getattr(status_def, "display_mode", "value")))
        lines.append("衰减：{} / {}".format(
            getattr(status_def, "decay_timing", "none"),
            getattr(status_def, "decay_amount", 0)
        ))
        lines.append("效果：{}".format(description))
        return "\n".join(lines)

    def format_zone_info(self, element, is_extreme=False):
        from data.zones.element_zones import get_element_display_name, get_zone_ability_text
        lines = []
        lines.append("=== Zone 说明 ===")
        lines.append("名称：{}{}Zone".format("极" if is_extreme else "", get_element_display_name(element)))
        lines.append("属性：{}（{}）".format(get_element_display_name(element), element))
        lines.append("效果：{}".format(get_zone_ability_text(element, is_extreme=is_extreme)))
        return "\n".join(lines)

    def get_run_relics(self, run_state):
        relics = getattr(run_state, "relics", [])
        if not relics:
            return "当前没有遗物。"
        lines = []
        lines.append("=== 当前遗物 ===")

        for index, relic in enumerate(relics):
            lines.append("[{}] {}：{}".format(
                index,
                format_relic_display_name(relic),
                relic.description
            ))
        lines.append("")
        lines.append("使用 /card relic_story 0 查看对应遗物故事。")
        return "\n".join(lines)
    
    def get_run_relics(self, run_state):
        relics = getattr(run_state, "relics", [])
        if not relics:
            return "当前没有遗物。"
        lines = []
        lines.append("=== 当前遗物 ===")
        for index, relic in enumerate(relics):
            lines.append("[{}] {}：{}".format(
                index,
                format_relic_display_name(relic),
                relic.description
            ))
        lines.append("")
        lines.append("使用 /card relic_story 0 查看对应遗物的小故事。")
        return "\n".join(lines)
    
    def get_run_relic_story(self, run_state, relic_index):
        relics = getattr(run_state, "relics", [])
        if not relics:
            return "当前没有遗物。"
        if relic_index < 0 or relic_index >= len(relics):
            return "遗物编号无效。"
        relic = relics[relic_index]
        story = getattr(relic, "story", "")
        if not story:
            return "{}没有记录故事。".format(format_relic_display_name(relic))
        return "\n".join([
            "=== 遗物故事 ===",
            "[{}] {}".format(relic_index, format_relic_display_name(relic)),
            # "",
            story
        ])

    def get_run_potions(self, run_state):
        potions = getattr(run_state, "potions", [])

        if not potions:
            return "当前没有药水。"

        lines = []
        lines.append("=== 当前药水 ===")

        for index, potion in enumerate(potions):
            lines.append("[{}] {}：{}".format(
                index,
                format_potion_display_name(potion),
                potion.description
            ))

        max_slots = getattr(run_state, "max_potion_slots", 3)
        lines.append("")
        lines.append("药水栏：{}/{}".format(len(potions), max_slots))

        return "\n".join(lines)

    def get_run_deck(self, run_state):
        deck = getattr(run_state, "master_deck", [])

        lines = []
        lines.append("=== 当前牌库 ===")
        lines.append("数量：{}".format(len(deck)))

        if not deck:
            lines.append("当前牌库为空。")
            return "\n".join(lines)

        for index, card in enumerate(deck):
            lines.append("[{}] {}".format(
                index,
                card.summary_text()
            ))

        lines.append("")
        lines.append("使用 /card deck 0 查看某张牌的完整说明。")

        return "\n".join(lines)

    def get_run_deck_detail(self, run_state, card_index):
        deck = getattr(run_state, "master_deck", [])
        if not deck:
            return "当前牌库为空。"
        if card_index < 0 or card_index >= len(deck):
            return "牌库编号无效。"
        card = deck[card_index]
        return "=== 牌库卡牌详情 ===\n[{}] {}".format(
            card_index,
            format_card_reward_choice(card)
        )

    def resolve_character_id(self, parts):
        """
        /card new [角色编号或角色ID]

        当前只有：
        0 -> character.test
        """
        if len(parts) < 3:
            return CHARACTER_CHOICES[0]["character_id"]

        raw_value = parts[2].strip()

        try:
            index = int(raw_value)
        except ValueError:
            index = None

        if index is not None:
            for item in CHARACTER_CHOICES:
                if item["index"] == index:
                    return item["character_id"]
            return None

        for item in CHARACTER_CHOICES:
            if raw_value == item["character_id"]:
                return item["character_id"]

        return None
    
    def get_character_display_name(self, character_id):
        for item in CHARACTER_CHOICES:
            if item["character_id"] == character_id:
                return "{} ({})".format(item["name"], item["character_id"])
        return character_id
    
    def character_choices_text(self):
        lines = []
        lines.append("=== 可选角色 ===")

        for item in CHARACTER_CHOICES:
            lines.append("[{}] {} ({})".format(
                item["index"],
                item["name"],
                item["character_id"]
            ))

        lines.append("")
        lines.append("开始战斗：/card new 0")
        return "\n".join(lines)

    def handle_play(self, game_state, parts):
        """
        /card play 手牌编号 [敌人编号]
        /card play 0,1,2,3 [敌人编号]
        /card play 0，1，2，3 [敌人编号]
        """
        if len(parts) < 3:
            return "用法：/card play 手牌编号 [敌人编号]，例如 /card play 0 或 /card play 0,1,2"

        hand_indices = self.parse_hand_index_list(parts[2])

        if hand_indices is None:
            return "手牌编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card play 0,1,2。"

        target_index = None

        if len(parts) >= 4:
            try:
                target_index = int(parts[3])
            except ValueError:
                return "敌人编号必须是数字。"

        if len(hand_indices) == 1:
            reply = play_card(game_state, hand_indices[0], target_index)
        else:
            reply = play_cards_by_original_indices(game_state, hand_indices, target_index)

        return reply
    
    def parse_index_list(self, raw_value):
        """
        解析编号列表。
        支持：
        0
        0,1,2
        0，1，2
        0、1、2
        返回 list[int]。
        解析失败返回 None。
        """
        text = raw_value.strip()
        text = text.replace("，", ",")
        text = text.replace("、", ",")
        if not text:
            return None
        parts = text.split(",")
        result = []
        for item in parts:
            item = item.strip()
            if not item:
                continue
            try:
                result.append(int(item))
            except ValueError:
                return None
        if not result:
            return None
        return result
    def parse_hand_index_list(self, raw_value):
        """
        兼容旧的手牌批量出牌解析。
        """
        return self.parse_index_list(raw_value)

    def handle_use_potion(self, game_state, parts):
        """
        /card potion 药水编号 [敌人编号]
        """
        if len(parts) < 3:
            return "用法：/card potion 药水编号 [敌人编号]"

        try:
            potion_index = int(parts[2])
        except ValueError:
            return "药水编号必须是数字。"

        target_index = None

        if len(parts) >= 4:
            try:
                target_index = int(parts[3])
            except ValueError:
                return "敌人编号必须是数字。"

        return use_potion(game_state, potion_index, target_index)



    def handle_use_potion_outside_battle(self, run_state, parts):
        if len(parts) < 3:
            return "用法：/card potion 药水编号。"

        try:
            potion_index = int(parts[2])
        except ValueError:
            return "药水编号必须是数字。"

        potions = getattr(run_state, "potions", []) or []

        if potion_index < 0 or potion_index >= len(potions):
            return "药水编号无效。"

        potion = potions[potion_index]
        potion_id = getattr(potion, "potion_id", "")

        outside_usable_potion_ids = {
            "potion.saturated_calcium_carbonate_solution",
            "potion.fruit_juice",
            "potion.blood",
        }

        if potion_id not in outside_usable_potion_ids:
            return "当前不在战斗中，不能使用【{}】。".format(getattr(potion, "name", "药水"))

        potions.pop(potion_index)

        logs = ["战斗外使用【{}】。".format(potion.name)]

        has_sacred_bark = any(
            getattr(relic, "relic_id", "") == "relic.sacred_bark"
            for relic in getattr(run_state, "relics", []) or []
        )

        if potion_id == "potion.fruit_juice":
            from game.relic_logic.run_relic_utils import increase_max_hp

            amount = int(getattr(potion, "effect_vars", {}).get("max_hp", 5) or 5)

            if has_sacred_bark:
                amount *= 2
                logs.append("【神圣树皮】触发：【{}】的数值翻倍。".format(potion.name))

            logs.extend(increase_max_hp(run_state, amount, potion.name))
            return "\n".join(logs)

        if potion_id == "potion.blood":
            from game.relic_logic.run_relic_utils import heal_run_hp_with_relics

            percent = 0.20
            if has_sacred_bark:
                percent *= 2
                logs.append("【神圣树皮】触发：【{}】的数值翻倍。".format(potion.name))

            amount = int(int(getattr(run_state, "max_hp", 0) or 0) * percent)
            logs.extend(heal_run_hp_with_relics(run_state, amount, source=potion.name))
            return "\n".join(logs)

        relic = None
        for owned_relic in getattr(run_state, "relics", []) or []:
            if getattr(owned_relic, "relic_id", "") == "relic.stalactite":
                relic = owned_relic
                break

        if relic is None:
            from data.relic.AAAregistry import create_relic

            relic = create_relic("relic.stalactite")
            run_state.relics.append(relic)
            logs.append("获得遗物：【{}】。".format(relic.name))

            if has_sacred_bark:
                increase = getattr(relic, "increase_start_rock_layer", None)
                if increase is not None:
                    increase(1)
                else:
                    relic.extra_rock_layer = int(getattr(relic, "extra_rock_layer", 0) or 0) + 1
                logs.append("【神圣树皮】触发：新获得的【钟乳石】战斗开始获得的岩层数 +1。当前额外值：{}。".format(
                    int(getattr(relic, "extra_rock_layer", 0) or 0)
                ))
        else:
            increase = getattr(relic, "increase_start_rock_layer", None)
            if increase is not None:
                increase(1)
            else:
                relic.extra_rock_layer = int(getattr(relic, "extra_rock_layer", 0) or 0) + 1

            logs.append("已有【钟乳石】，其战斗开始获得的岩层数 +1。当前额外值：{}。".format(
                int(getattr(relic, "extra_rock_layer", 0) or 0)
            ))

        return "\n".join(logs)


    def handle_drop(self, game_state, parts):
        """
        /card drop 0 2 3
        /card drop none
        """
        if not game_state.pending_discard_selection:
            return "当前没有需要处理的弃牌选择。"

        if len(parts) < 3:
            return "用法：/card drop 0 2 3。若不丢弃，使用 /card drop none。\ndrop 等效 drop_hand，丢弃手牌，选择丢弃。"

        raw_values = []

        for part in parts[2:]:
            for item in part.split(","):
                item = item.strip()
                if item:
                    raw_values.append(item)

        if len(raw_values) == 1 and raw_values[0].lower() in ("none", "no", "skip", "0张", "不丢", "不丢弃"):
            return discard_selected_hand_cards(game_state, [])

        hand_indices = []

        for raw_value in raw_values:
            try:
                hand_indices.append(int(raw_value))
            except ValueError:
                return "手牌编号必须是数字，或使用 none 表示不丢弃。"

        return discard_selected_hand_cards(game_state, hand_indices)
    
    def handle_discard_to_draw_top(self, game_state, parts):
        """
        /card top 0
        用于头槌：选择弃牌堆中的一张牌放到抽牌堆顶。
        """
        if not (
            game_state.pending_discard_to_draw_selection
            or pending_choice_is(game_state, "discard_to_draw_top")
        ):
            return "当前没有需要处理的弃牌堆置顶选择。"

        if len(parts) < 3:
            return "用法：/card top 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_discard_to_draw_top(game_state, choice_index)

    def handle_exhaust_hand(self, game_state, parts):
        """
        /card exhaust_hand 0
        /card exhaust 0
        用于坚毅+：选择一张手牌消耗。
        """
        if not game_state.pending_exhaust_hand_selection:
            return "当前没有需要处理的手牌消耗选择。"

        if len(parts) < 3:
            return "用法：/card exhaust_hand 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_exhaust_hand(game_state, choice_index)

    def handle_hand_to_draw_top(self, game_state, parts):
        """
        /card handtop 0
        用于战吼：选择一张手牌放到抽牌堆顶。
        """
        if not (
            game_state.pending_hand_to_draw_top_selection
            or pending_choice_is(game_state, "hand_to_draw_top")
        ):
            return "当前没有需要处理的手牌置顶选择。"

        if len(parts) < 3:
            return "用法：/card handtop 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_hand_to_draw_top(game_state, choice_index)

    def handle_upgrade_hand(self, game_state, parts):
        """
        /card upgrade_hand 0
        用于武装：选择一张手牌临时升级。
        """
        if not (
            game_state.pending_upgrade_hand_selection
            or pending_choice_is(game_state, "upgrade_hand")
        ):
            return "当前没有需要处理的手牌升级选择。"

        if len(parts) < 3:
            return "用法：/card upgrade_hand 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_upgrade_hand_card(game_state, choice_index)
    
    def handle_duplicate_hand(self, game_state, parts):
        """
        /card duplicate_hand 0
        用于双持：选择一张攻击或能力牌复制到手牌。
        """
        if not game_state.pending_duplicate_hand_selection:
            return "当前没有需要处理的复制手牌选择。"

        if len(parts) < 3:
            return "用法：/card duplicate_hand 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_duplicate_hand_card(game_state, choice_index)
    
    def handle_exhume(self, game_state, parts):
        """
        /card exhume 0
        用于发掘：选择一张消耗堆中的牌加入手牌。
        """
        if not game_state.pending_exhume_selection:
            return "当前没有需要处理的发掘选择。"

        if len(parts) < 3:
            return "用法：/card exhume 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_exhume_card(game_state, choice_index)
    def handle_retain_hand(self, game_state, parts):
        """
        /card retain 0
        /card retain 0,1
        /card retain skip
        """
        if not pending_choice_is(game_state, "retain_hand"):
            return "当前没有需要处理的保留选择。"

        if len(parts) < 3:
            return format_pending_retain_hand_selection(game_state)

        raw = " ".join(parts[2:]).strip().lower()

        if raw in ("skip", "none", "no", "不选", "跳过"):
            return choose_pending_retain_hand_cards(game_state, [], skip=True)

        choice_indices = self.parse_index_list(parts[2])

        if choice_indices is None:
            return "手牌编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card retain 0,1。"

        return choose_pending_retain_hand_cards(game_state, choice_indices, skip=False)
    


    def handle_fossil(self, game_state, parts):
        """
        /card fossil 0,1,2
        /card fossil none
        """
        if not pending_choice_is(game_state, "fossil_exhaust_hand"):
            return "当前没有需要处理的化石选择。"

        if len(parts) < 3:
            return get_pending_player_choice_hint(game_state)

        raw = " ".join(parts[2:]).strip().lower()

        if raw in ("none", "skip", "no", "不选", "跳过"):
            return choose_pending_fossil_exhaust_hand_cards(game_state, [], skip=True)

        choice_indices = self.parse_index_list(parts[2])

        if choice_indices is None:
            return "手牌编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card fossil 0,1。"

        return choose_pending_fossil_exhaust_hand_cards(game_state, choice_indices, skip=False)


    def handle_radiant_reflection(self, game_state, parts):
        """
        /card reflect 0
        /card reflect 0,1
        """
        if not pending_choice_is(game_state, "radiant_reflection"):
            return "当前没有需要处理的辉晶映照选择。"

        if len(parts) < 3:
            return "用法：/card reflect 0 或 /card reflect 0,1。"

        choice_indices = self.parse_index_list(parts[2])

        if choice_indices is None:
            return "编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card reflect 0,1。"

        return choose_pending_radiant_reflection_cards(game_state, choice_indices)
    
    def handle_synchronization(self, game_state, parts):
        """
        /card sync 0
        """
        if not pending_choice_is(game_state, "synchronization"):
            return "当前没有需要处理的同调选择。"

        if len(parts) < 3:
            return "用法：/card sync 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "编号必须是数字。"

        return choose_pending_synchronization_card(game_state, choice_index)
    
    def handle_potion_pick(self, game_state, parts):
        """
        /card potion_pick 0
        用于攻击/技能/能力药水与液态记忆。
        """
        if not getattr(game_state, "pending_potion_card_selection", False):
            return "当前没有需要处理的药水选牌。"

        if len(parts) < 3:
            return "用法：/card potion_pick 0。"

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字。"

        return choose_pending_potion_card(game_state, choice_index)

    def handle_elixir(self, game_state, parts):
        """
        /card elixir 0,1,2
        /card elixir none
        用于万灵药水：选择任意张手牌消耗。
        """
        if not getattr(game_state, "pending_elixir_selection", False):
            return "当前没有需要处理的万灵药水选择。"

        if len(parts) < 3:
            return "用法：/card elixir 0,1,2；不消耗则 /card elixir none。"

        raw = parts[2].strip().lower()
        if raw in ("none", "no", "skip", "不消耗", "无"):
            return choose_pending_elixir_cards(game_state, [])

        indices = self.parse_index_list(parts[2])
        if indices is None:
            return "手牌编号必须是数字列表，或使用 none 表示不消耗。"

        return choose_pending_elixir_cards(game_state, indices)

    def handle_codex(self, game_state, parts):
        """
        /card codex 0
        /card codex skip
        用于尼利的宝典：选择 1 张牌随机洗入抽牌堆。
        """
        if not getattr(game_state, "pending_nilrys_selection", False):
            return "当前没有需要处理的尼利的宝典选择。"

        if len(parts) < 3:
            return "用法：/card codex 0；跳过则 /card codex skip。"

        raw = parts[2].strip().lower()
        if raw in ("skip", "none", "no", "跳过", "不选"):
            return choose_pending_nilrys_card(game_state, skip=True)

        try:
            choice_index = int(parts[2])
        except ValueError:
            return "选择编号必须是数字，或使用 skip 跳过。"

        return choose_pending_nilrys_card(game_state, choice_index=choice_index)

    def help_text(self):
        return "\n".join([
            "/card view       查看战斗状态和手牌",
            "/card run        查看角色 hp/金币/药水/遗物 总览",
            "*目前全部指令过多，请使用(.help我超，塔)查看相关内容。",
            "**可使用(.help塔指令等效)查看指令的其他等效写法，部分支持中文。",
        ])

    def opening_help_text(self):
        return "\n".join([
            "卡牌测试命令（*命令中的“/”与 “。”和“.”等价）：",
            "当前版本：v26.7.10",
            "- 打防私有化",
            "- 画饼多人模式",
            "",
            "/card characters 查看可选角色",
            "/card private on/off      控制当前会话是否启用私货内容，默认开启",
            "/card new 0      选择 0 号测试角色并开始测试战斗",
            "/card view       查看战斗状态和手牌",
            "/card run        查看角色 hp/金币/药水/遗物 总览",
            "/card help       查看帮助",
            "*目前全部指令过多，请使用(.help我超，塔)查看相关内容。",
            "**可使用(.help塔指令等效)查看指令的其他等效写法，部分支持中文。",
            "***目前该项目已扩展至制作人看不见的地方运行，首先感谢我们的数值策划推广；",
            "然后制作人叠甲这玩意真的是为了进行自建扩展而搭建的框架，所以私货内容真的很多，原作内容更像是为了【可玩性填充】而进行的。"
        ])
            # "",
            # "兼容旧命令：/card status 和 /card hand 现在都会显示战斗状态 + 手牌。"
            # "/card relics     查看已有遗物",
            # "/card relic_story 0    查看遗物的小故事（*可能有严重的私货夹带",
            # "/card potions    查看药水",
            # "/card potion 0   使用第 0 个药水",
            # "/card potion 0 1 使用第 0 个药水，目标为第 1 个敌人",
            # "/card draw       查看抽牌堆",
            # "/card discard    查看弃牌堆",
            # "/card exhaust    查看消耗牌堆",
            # "/card deck       查看当前永久牌库",
            # "/card play 0     打出第 0 张手牌，默认攻击第 0 个敌人",
            # "/card play 0 1   打出第 0 张手牌，攻击第 1 个敌人",
            # "/card play 0,1,2 依次打出第 0、1、2 张原始手牌，默认攻击第 0 个敌人",
            # "/card play 0,1,2 1 依次打出第 0、1、2 张原始手牌，攻击第 1 个敌人",
            # "/card replace_potion 2 0 药水栏满时，用奖励 2 替换已有药水 0",
            # "/card end        结束当前回合",
            # "/card help       查看帮助",
            # "/card route     查看当前路线",        
            # "/card next 0    选择下一个节点",
            # "/card ancient 0 选择先古之民选项",
            # "/card event 0   选择事件选项",
            # "/card shop      查看商店",
            # "/card buy 0     购买商店商品",
            # "/card remove    查看可删除牌",
            # "/card remove 0  定向删除第 0 张牌",
            # "/card random_remove 随机删除一张牌",
            # "/card leave     离开商店",
            # "/card rest 0    火堆休息",
            # "/card rest 1    查看可锻造牌",
            # "/card smith 0   锻造升级一张牌",
