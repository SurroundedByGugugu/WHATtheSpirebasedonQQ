"""图鉴故事接口：以注册表 ID 为键，正文支持换行，按纯文本展示。

示例（取消注释并替换正文即可）：
CARD_STORIES["card.strike"] = "第一段故事。\n\n第二段故事。"
RELIC_STORIES["relic.burning_blood"] = "这里填写遗物的小故事。"
遗物未填写时自动使用遗物模板自带的 story；修改后重新构建网页版。
"""

CARD_STORIES: dict[str, str] = {}
RELIC_STORIES: dict[str, str] = {}
