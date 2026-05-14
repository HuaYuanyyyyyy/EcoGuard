# 合规判断提示词

INTENT_PROMPT = """判断用户输入的意图，只返回以下三个值之一：
- compliance：用户输入了污染物数据，需要合规检测
- system：用户在询问系统相关问题，比如怎么使用、能做什么
- irrelevant：与环保合规无关的问题

用户输入：{user_input}

只返回 compliance、system、irrelevant 三个词之一，不要输出其他任何内容。
"""