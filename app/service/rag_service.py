import asyncio
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
from typing import AsyncGenerator

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

# 单个污染物检测（抽出来方便并发）
async def check_single_item(item: dict, chroma) -> dict:
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

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        retry_response = await llm.ainvoke([HumanMessage(
            content=f"以下JSON格式有错误，请修复后重新输出，只输出JSON不要其他内容，字符串内部不要用双引号：\n{content}"
        )])
        result = json.loads(retry_response.content.strip())

    result["source_files"] = source_files
    return result


# 检测合规性
async def check_compliance(user_input: str) -> dict:
    chroma = get_chroma()
    items = parse_pollution_data(user_input)

    # 并发调用，所有污染物同时检测
    results = await asyncio.gather(*[
        check_single_item(item, chroma) for item in items
    ])
    results = list(results)

    # 自然语言总结
    template = PromptTemplate.from_template(SUMMARY_PROMPT)
    prompt = template.format(
        results=json.dumps(results, ensure_ascii=False)
    )
    summary_response = await llm.ainvoke([HumanMessage(content=prompt)])

    return {
        "results": results,
        "summary": summary_response.content
    }
# 正常聊天
def normal_chat(user_input: str) -> str:
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ])
    return response.content



async def stream_check_compliance(user_input: str) -> AsyncGenerator[str, None]:
    chroma = get_chroma()
    items = parse_pollution_data(user_input)

    results = []

    # 每个污染物检测完立刻发出，不等其他的
    tasks = [check_single_item(item, chroma) for item in items]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        # 立刻推给前端
        yield f"data: {json.dumps({'type': 'result_item', 'item': result}, ensure_ascii=False)}\n\n"

    # 所有检测完后流式输出总结
    template = PromptTemplate.from_template(SUMMARY_PROMPT)
    prompt = template.format(results=json.dumps(results, ensure_ascii=False))

    async for chunk in llm.astream([HumanMessage(content=prompt)]):
        if chunk.content:
            yield f"data: {json.dumps({'type': 'summary_chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

async def stream_normal_chat(user_input: str) -> AsyncGenerator[str, None]:
    async for chunk in llm.astream([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input)
    ]):
        if chunk.content:
            yield f"data: {json.dumps({'type': 'chat_chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"    