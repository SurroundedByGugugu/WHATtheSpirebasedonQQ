# -*- coding: utf-8 -*-
# 输出格式整理：状态、手牌、牌堆、奖励列表等

def render_lines(lines):
    return "\n".join(lines)


def render_error(text):
    return "错误：{}".format(text)


def render_info(text):
    return text