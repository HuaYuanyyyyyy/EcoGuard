PARSE_PROMPT = """分析用户输入，完成两件事：
1. 判断意图
2. 如果是合规检测，提取污染物数据

只输出JSON，不要输出其他任何内容，不要加代码块标记，字符串值内部不能包含双引号。

用户输入：{user_input}

输出格式：
{{
  "intent": "compliance或chat或irrelevant",
  "items": [
    {{"name": "污染物名称", "measured_value": "实测值"}}
  ]
}}

intent说明：
- compliance：用户输入了污染物数据，需要合规检测
- chat：用户在询问问题，比如怎么使用、环保知识等
- irrelevant：与环保合规完全无关

注意：
- 如果intent不是compliance，items返回空数组[]
- 只提取明确给出实测值的污染物，没有数值的不提取
"""