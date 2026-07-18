# 群内 PVP 演绎房说明

当前 PVP 是一个独立的演绎战斗房，和单人爬塔、多人测试房平行存在。它复用现有角色、卡牌、遗物、药水等内容，但底层房间和战斗节奏是单独搭建的第一版原型。

命令中的 `/card` 也可以按原项目习惯替换成 `.card` 或 `。card`。PVP 调度使用 `/card pvp ctrl ...`，普通 `/ctrl` 不再接入 PVP 房。

## 定位

PVP 演绎房不自动判断胜负。

系统只负责：

- 维护双方角色、HP、手牌、牌堆、遗物、费用。
- 处理出牌、待结算攻击、格挡、抽牌、状态附加等基础效果。
- 限制单回合运转上限。
- 允许任意参战者结束战斗。

胜负、剧情结果、是否认输、是否达成目标，都交由玩家自行结算。

## 开房与加入

```text
/card pvp new [角色编号]
/card pvp join [角色编号]
/card pvp start
/card pvp view
/card pvp close
```

- `new`：创建 PVP 演绎房，并让开房者加入 A 侧。开房者是房主。
- `join`：加入当前 PVP 房；开战前重复使用可换角色。
- `start`：开始 1v1 PVP，只有房主可以使用。
- `view`：查看当前 PVP 房或战斗状态。
- `close`：关闭当前 PVP 房，只有房主可以使用。

当前第一版 PVP 只支持 2 名玩家。开战后不能再加入或换角色。

## 角色编号

```text
0 铁甲战士
1 静默猎手
2 昼·里辛塔法
3 Yoirine
4 Suzuri
```

不填角色编号时，默认使用 `0 铁甲战士`。测试角色仅供内部测试房使用。

## PVP 专用控制台

PVP 有专用控制台，开战前后都可以使用：

```text
/card pvp ctrl
/card pvp ctrl rule
/card pvp ctrl addcard 打击 牌库
/card pvp ctrl addcard 杂技 牌库 2
/card pvp ctrl removecard 打击 牌库
/card pvp ctrl addrelic 墨水瓶
/card pvp ctrl removerelic 墨水瓶
/card pvp ctrl addhp 10
/card pvp ctrl addmaxhp 10
```

注意：

- 普通 `/ctrl` 不会修改 PVP 房；PVP 相关调度请使用 `/card pvp ctrl`。
- 不写玩家编号时，默认修改自己。
- 房主可以显式指定玩家编号、user_id 或 A/B 侧来修改他人资源。
- 非房主只能修改自己的资源。
- 当前 PVP 的 `addrelic` 只添加遗物本体，不完整执行所有单人爬塔中的获得时事件。

开战后可以修改战斗中的牌堆：

```text
/card pvp ctrl addcard 0 打击 手牌
/card pvp ctrl addcard 1 伤口 弃牌堆 2
/card pvp ctrl draw 0 3
/card pvp ctrl sethp 1 30
/card pvp ctrl setcost 0 6
/card pvp ctrl addblock 0 12
/card pvp ctrl addstate 1 易伤 2
```

## 规则调参

房主可以用 PVP 控制台修改房间规则，开战前后都可以改。

```text
/card pvp ctrl rule base_cost 4
/card pvp ctrl rule max_cards 12
/card pvp ctrl rule forced_bonus 1
/card pvp ctrl rule overheat 4
```

- `base_cost`：基础费用。修改后会同步所有玩家的费用上限，当前费用可用 `setcost` 单独改。
- `max_cards`：单回合最大出牌数。
- `forced_bonus`：因达到出牌上限强制换回合时，对方本回合获得的费用。
- `overheat`：单张具体卡牌的过热阈值。默认 `4` 表示第 1-4 次正常，第 5 次起过热。

房主也可以调度当前战斗：

```text
/card pvp ctrl active 1
/card pvp ctrl battle turn 3
/card pvp ctrl battle cards 11
```

## 战斗命令

```text
/card pvp play 手牌编号 [目标玩家编号]
/card pvp end
/card pvp finish
```

- `play`：打出指定手牌。
- 如果牌需要敌方目标，可以追加目标玩家编号。
- `end`：主动结束当前行动者回合。
- `finish`：任意参战者结束本场 PVP 战斗。系统不会宣布胜负。

目标玩家编号以 `view` 中显示的玩家列表为准。例如 `[1]` 是对方，就可以使用：

```text
/card pvp play 0 1
```

## 默认环境规则

当前 PVP 第一版默认使用以下规则：

- 双方基础费用为 4。
- 每名玩家每回合最多打出 12 张牌。
- 第 12 张牌会完整结算，然后强制进入对方回合。
- 因第 12 张牌强制换回合时，对方本回合获得 +1 费用。
- 主动使用 `/card pvp end` 结束回合时，不会给对方 +1 费用。
- 胜负由玩家自行判定。
- 任意参战者可以随时使用 `/card pvp finish` 结束战斗。

## 单卡过热

PVP 的过热不是按同名牌统计，而是按每一张具体卡牌统计。

```text
同一张具体卡牌：
第 1-4 次打出：正常进入弃牌堆，或按原本关键词进入消耗堆。
第 5 次及之后打出：完整结算后过热，暂时进入消耗堆。
下个自己的回合开始时：过热牌回到弃牌堆。
```

这意味着两张同名牌会分别计算过热次数。例如牌库里有两张【杂技】，它们不是共享 4 次额度，而是各算各的。

## 伤害与防御

当前攻击牌不会立刻扣血，而是先生成待结算攻击。当前行动者结束回合时，自己的待结算攻击会统一命中目标。

这会让防御变成有意义的预判：

- 你在自己的回合起的格挡，可以用于抵挡对方之后的攻击。
- 对方本回合到底打多少输出，只有等对方行动后才知道。
- 强制换回合会先结算攻击，再轮到对方行动。

当前第一版已处理常见效果，例如：

- 造成伤害。
- 获得格挡。
- 抽牌。
- 获得费用。
- 施加状态。

复杂卡牌、复杂遗物、复杂药水、Zone / Field、部分特殊状态还没有完整接入 PVP；未实现效果会显示“PVP 暂未处理卡牌效果”。

## 信息隐藏

设计目标上，PVP 环境默认类似“符文圆顶”：不直接展示对方完整意图。

当前第一版的实现是：

- 状态视图不会列出对方手牌详情。
- 待结算攻击只在视图中显示段数，不完整展示全部明细。
- 查看房间时，会显示自己的手牌。

但要注意：如果机器人回复仍发送在群聊里，那么“你的手牌”这段文本也会被群里看到。真正的私密手牌需要后续接入私聊或定向发送能力。

## 推荐流程

```text
/card pvp new 1
/card pvp join 2

/card pvp ctrl addcard 燃烧契约 牌库 2
/card pvp ctrl addcard 打击 牌库
/card pvp ctrl addrelic 墨水瓶
/card pvp ctrl rule max_cards 12

/card pvp start
/card pvp view
/card pvp play 0 1
/card pvp end
/card pvp ctrl addstate 1 易伤 2
/card pvp finish
```

建议先由双方在开战前约定剧情目标、牌库限制、遗物限制和结束条件，再由房主开始 PVP。

## 当前限制

- 第一版只支持 1v1。
- 不自动判断胜负。
- 普通 `/ctrl` 不接入 PVP；PVP 专用控制台 `/card pvp ctrl` 开战后仍可用。
- PVP 没有路线、奖励、怪物回合和爬塔流程。
- 药水使用尚未作为 PVP 命令接入。
- 遗物 hook 只部分自然生效，不能保证所有遗物都符合 PVP 语境。
- 状态回合末完整事件还在后续扩展中，当前主要优先保证出牌节奏、待结算攻击和过热规则。
