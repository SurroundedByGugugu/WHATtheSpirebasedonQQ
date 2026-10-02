# 充能球测试与规则

已实现单人战斗和测试房的球系统，并接入[故障机器人、蓝色卡池、专属遗物与药水](../defect_content.md)。合作/PVP的独立战斗引擎尚未接入。

## 快速试用

已有路线后执行（`/ctrl`、`.ctrl`、`。ctrl` 均可）：

```text
/ctrl testroom battle
/ctrl orb slots 5
/ctrl orb channel 闪电
/ctrl orb channel 冰霜
/ctrl orb channel 黑暗
/ctrl orb channel 玻璃
/ctrl orb channel 等离子
/ctrl orb focus 2
/ctrl orb show
/card end
```

手动控制：

```text
/ctrl orb passive 1
/ctrl orb passive all
/ctrl orb evoke 1 2
/ctrl orb value 1 18
/ctrl orb remove 1
/ctrl orb clear
/ctrl orb addslots 1
/ctrl orb help
```

位置从1开始。`evoke 1 2` 是同一颗球激发两次后移除；每次重新选敌。
`value` 只能修改黑暗计数或玻璃基础值。`focus` 设置集中；`addstate 集中 1 self` 增加集中。
`clear`、`remove` 和缩槽不激发。缩槽从最右侧丢弃超额球。控制台球槽、生成数量、激发次数上限100，防止误输入造成大量日志。
普通角色初始零球槽，故障机器人初始3个球槽；零槽生成失败。控制台修改只作用于当前战斗。

## 结算

手牌结束回合效果与清理 → 中毒 → 非等离子球被动 → 敌人行动。
等离子在回合开始的正常能量恢复后触发，支持冰淇淋。
计划妥当等留牌选择完成后才进入中毒/球阶段。
进入中毒阶段时记录球快照，该阶段新生成的球不参与本次自然被动。
最后一个非爪牙敌人死亡后停止后续球和敌人行动；一次球群攻先完成整个目标列表的伤害。
水Zone获得的再生沿用已有回合结束治疗时机，冰球自身不直接治疗。

集中 F：闪电 3+F / 8+F，冰霜 2+F / 5+F，黑暗初始6、每次增长max(0,6+F)、激发已有计数，玻璃基础G初始4、被动max(0,G+F)、激发为被动两倍，等离子1/2。
所有最终数值非负；玻璃基础最低0且不自动移除。
黑球选最低当前生命，平局随机。

雷Zone使闪电群体化，不增伤、不重放；可与电动力学共存但不重复触发。
水/极水使冰球被动额外获得1/2再生，激发2/3再生。
阴/极阴使黑球增长乘1.5/2，最后向下取整，不改变已有计数。
晶Zone让玻璃不衰减，极晶让其被动伤害结算后基础值+1；其他环境被动后基础值-1。
球不走攻击牌的力量、虚弱、易伤和通用Zone倍率；冰球不走敏捷、脆弱，但保留正常伤害/格挡事件。

## 卡牌与遗物接口

`game.orbs` 提供 `channel`、`trigger`、`trigger_passives`、`evoke_orb`、`set_slots`。
球主人显式传入；列表保存顺序，每颗球有独立编号和内部值，玩家状态可深拷贝。
生成/被动/激发提供 `orb_channeled`、`orb_passive`、`orb_evoked` 事件。
激发事件按效果次数触发，移除只执行一次。战斗结束时不再派发后续球事件。
