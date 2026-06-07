# -*- coding: utf-8 -*-

from game.constants import DEBUG_SEED
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
    get_combat_view,
    discard_selected_hand_cards,
    get_status_detail,
    get_zone_field_view,
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
    skip_reward,
    replace_reward_potion,
    handle_shop_buy,
    handle_shop_buy_batch,
    handle_remove_card_view_or_choose,
    handle_random_remove_card,
    leave_shop,
    handle_rest_option,
    handle_smith_card,
    handle_event_option,
    handle_ancient_option,
    handle_shop_item_detail,
)
from game.route import format_route_text


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
        "character_id": "character.lumine",
        "name": "昼·里辛塔法"
    },
    {
        "index": 3,
        "character_id": "character.yoirine",
        "name": "Yoirine"
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

    def get_owner(self, session_id):
        return self.session_owners.get(session_id)

    def is_owned_by_other_user(self, session_id, user_id):
        owner_user_id = self.get_owner(session_id)

        if owner_user_id is None:
            return False

        return str(owner_user_id) != str(user_id)

    def append_run_progress_after_battle(self, session_id, run_state, battle_reply):
        """
        战斗命令执行后，检查当前战斗是否结束。
        如果结束，把结果交给 RunEngine 处理。
        """
        route_reply = finish_current_battle_if_needed(run_state)

        if not route_reply:
            return battle_reply

        full_reply = battle_reply + "\n\n" + route_reply

        if run_state.run_over:
            self.clear_run(session_id)

        return full_reply

    def handle_message(self, session_id, user_id, raw_message):
        """
        处理一条文本命令。
        不认识 QQ，不认识 LLOB。
        """
        text = raw_message.strip()
        if not (text.startswith("/card")  or text.startswith(".card") or text.startswith("。card")):
            return None
        parts = text.split()
        if len(parts) == 1:
            return self.help_text()
        command = parts[1].lower()

        if command in ("help", "帮助"):
            return self.help_text()

        if command in ("characters", "character", "chars", "角色", "角色选择", "查看角色"):
            return self.character_choices_text()

        if command == "new":
            if self.get_run(session_id) is not None and self.is_owned_by_other_user(session_id, user_id):
                return self.SAME_GROUP_SINGLE_GAME_MESSAGE
            character_id = self.resolve_character_id(parts)
            if character_id is None:
                return "角色编号无效。\n{}".format(self.character_choices_text())
            run_state, reply = start_run(
                session_id=session_id,
                character_id=character_id,
                seed=DEBUG_SEED
            )
            self.set_run(session_id, run_state, user_id)
            return reply

        run_state = self.get_run(session_id)

        if run_state is None:
            return "当前会话还没有路线。使用 /card new [角色序号] 开始。"

        # 只要 run 存在，就要检查 owner，不再依赖 current_battle
        if self.is_owned_by_other_user(session_id, user_id):
            return self.SAME_GROUP_SINGLE_GAME_MESSAGE

        # 这些命令是 Run 层命令，允许当前没有战斗
        if command in ("hand", "view", "查看", "手牌", "查看战斗状态", "查看手牌"):
            return get_run_view(run_state)

        if command in ("status", "状态", "查看状态", "查看buff", "buff", "debuff"):
            if run_state.current_battle is None:
                return "当前不在战斗中，没有可查看的全场状态。"
            return get_status_detail(run_state.current_battle)

        if command in ("state", "zone", "field", "场地", "查看场地", "查看zone", "查看field"):
            if run_state.current_battle is None:
                return "当前不在战斗中，没有可查看的 Zone / Field。"
            return get_zone_field_view(run_state.current_battle)

        if command in ("route", "map", "路线", "地图"):
            return format_route_text(run_state)
        
        if command in ("reward", "rewards", "奖励", "查看奖励"):
            return get_reward_view(run_state)

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

        if command in ("potions", "potion_list", "药水", "查看药水", "道具", "查看道具"):
            return self.get_run_potions(run_state)
        
        if command in ("deck", "master_deck", "牌库", "查看牌库", "卡组", "查看卡组"):
            return self.get_run_deck(run_state)
        
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
                return "用法：/card take 奖励编号，例如 /card take 0 或 /card take 0,1,2"
            option_indices = self.parse_index_list(parts[2])
            if option_indices is None:
                return "奖励编号必须是数字。多个编号用英文逗号或中文逗号分隔，例如 /card take 0,1,2。"
            if len(option_indices) == 1:
                reply = take_reward(run_state, option_indices[0])
            else:
                reply = take_rewards(run_state, option_indices)
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
        

        game_state = run_state.current_battle

        if game_state is None:
            return "当前不在战斗中。可以使用 /card route 查看路线，或 /card next 0 进入下一节点。"
        
        if command in ("drop", "drop_hand", "丢弃手牌", "选择丢弃"):
            game_state = run_state.current_battle
            if game_state is None:
                return "当前不在战斗中。"
            if not game_state.pending_discard_selection:
                return "当前没有需要处理的弃牌选择。"
            reply = self.handle_drop(game_state, parts)
            return self.append_run_progress_after_battle(session_id, run_state, reply)

        if game_state.pending_discard_selection:
            return "当前需要先处理丢弃选择。使用 /card drop 0 2 3，或 /card drop none。"
        
        if command in ("potion", "use_potion", "useitem", "item", "使用药水", "使用道具"):
            game_state = run_state.current_battle
            if game_state is None:
                # 一些画饼的占位符：
                # if 污浊药水： （战斗外使用效果不同
                # if 果汁： 战斗外允许使用
                # if 散装佛珠：（下一个？必定不是战斗）
                return "当前不在战斗中，不能使用药水。"
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

        return "未知命令：{}。\n{}".format(command, self.help_text())

    def get_run_relics(self, run_state):
        relics = getattr(run_state, "relics", [])
        if not relics:
            return "当前没有遗物。"
        lines = []
        lines.append("=== 当前遗物 ===")

        for index, relic in enumerate(relics):
            lines.append("[{}] 【{}】：{}".format(
                index,
                relic.name,
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
            lines.append("[{}] 【{}】：{}".format(
                index,
                relic.name,
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
            return "【{}】没有记录故事。".format(relic.name)
        return "\n".join([
            "=== 遗物故事 ===",
            "[{}] 【{}】".format(relic_index, relic.name),
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
            lines.append("[{}] 【{}】：{}".format(
                index,
                potion.name,
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

        return "\n".join(lines)

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

        target_index = 0

        if len(parts) >= 4:
            try:
                target_index = int(parts[3])
            except ValueError:
                return "敌人编号必须是数字。"

        if len(hand_indices) == 1:
            reply = play_card(game_state, hand_indices[0], target_index)
        else:
            reply = play_cards_by_original_indices(game_state, hand_indices, target_index)

        return "\n\n".join([
            reply,
            get_combat_view(game_state)
        ])
    
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

        target_index = 0

        if len(parts) >= 4:
            try:
                target_index = int(parts[3])
            except ValueError:
                return "敌人编号必须是数字。"

        return use_potion(game_state, potion_index, target_index)

    def handle_drop(self, game_state, parts):
        """
        /card drop 0 2 3
        /card drop none
        """
        if not game_state.pending_discard_selection:
            return "当前没有需要处理的弃牌选择。"

        if len(parts) < 3:
            return "用法：/card drop 0 2 3。若不丢弃，使用 /card drop none。"

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

    def help_text(self):
        return "\n".join([
            "卡牌测试命令（*命令中的“/”与 “。”和“.”等价）：",
            "当前版本：v26.06.07",
            "/card characters 查看可选角色",
            "/card new 0      选择 0 号测试角色并开始测试战斗",
            "/card view       查看战斗状态和手牌",
            "/card help       查看帮助",
            "*目前全部指令过多，请使用.help我超，塔 查看相关内容。"
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