import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.chroma import get_chroma
from app.config import settings
from app.prompts.intent import INTENT_PROMPT
from app.prompts.compliance import COMPLIANCE_PROMPT
from app.prompts.summary import SUMMARY_PROMPT
from app.prompts.system import SYSTEM_PROMPT

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.LLM_BASE_URL,
    model=settings.LLM_MODEL
)

# 检测意图
def detect_intent(user_input: str) -> str:
    template = PromptTemplate.from_template(INTENT_PROMPT)
    prompt = template.format(user_input=user_input)
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content.strip()

# 解析污染数据
def parse_pollution_data(user_input: str) -> list:
    prompt = f"""从下面的文字中提取污染物数据，只输出JSON，不要输出其他任何内容，不要加代码块标记。
                注意：输出的JSON中，字符串值内部不能包含双引号，如需引用名称请用单引号或去掉引号。
                如果没有找到任何污染物数据，返回 {{"items": []}}

                输入文字：
                {user_input}

                输出格式：
                {{"items": [{{"name": "污染物名称", "measured_value": "实测值"}}]}}
            """
    response = llm.invoke([HumanMessage(content=prompt)])
    print("LLM返回内容：", response.content)  # 加这行
    result = json.loads(response.content)
    return result.get("items", [])

# 检测合规性
def check_compliance(user_input: str) -> dict:
    chroma = get_chroma()
    items = parse_pollution_data(user_input)
    results = []

    for item in items:
        docs = chroma.similarity_search(
            f"{item['name']}排放标准限值",
            k=3
        )
        context = "\n".join([doc.page_content for doc in docs])
        source_files = list(set([
            doc.metadata.get("file_name", "未知文件")
            for doc in docs
        ]))

        template = PromptTemplate.from_template(COMPLIANCE_PROMPT)
        prompt = template.format(
            context=context,
            name=item["name"],
            measured_value=item["measured_value"]
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        print("LLM111返回内容：", response.content)  # 加这行
        result = json.loads(response.content)
        result["source_files"] = source_files
        results.append(result)

    # 自然语言总结
    template = PromptTemplate.from_template(SUMMARY_PROMPT)
    prompt = template.format(
        results=json.dumps(results, ensure_ascii=False)
    )
    summary = llm.invoke([HumanMessage(content=prompt)]).content

    return {
        "results": results,
        "summary": summary
    }

# 正常聊天
def normal_chat(user_input: str) -> str:
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ])
    return response.content