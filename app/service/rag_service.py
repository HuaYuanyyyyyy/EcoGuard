import asyncio
import json
import re
import time
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.hybrid_search import hybrid_search, hybrid_search_by_filename
from app.service.history_service import save_message
from app.prompts.parse import PARSE_PROMPT
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

# # 检测意图
# def detect_intent(user_input: str) -> str:
#     template = PromptTemplate.from_template(INTENT_PROMPT)
#     prompt = template.format(user_input=user_input)
#     response = llm.invoke([HumanMessage(content=prompt)])
#     return response.content.strip()

# # 解析污染数据
# def parse_pollution_data(user_input: str) -> list:
#     prompt = f"""从下面的文字中提取污染物数据，只输出JSON，不要输出其他任何内容，不要加代码块标记。
#                 注意：输出的JSON中，字符串值内部不能包含双引号，如需引用名称请用单引号或去掉引号。
#                 如果没有找到任何污染物数据，返回 {{"items": []}}

#                 输入文字：
#                 {user_input}

#                 输出格式：
#                 {{"items": [{{"name": "污染物名称", "measured_value": "实测值"}}]}}
#             """
#     response = llm.invoke([HumanMessage(content=prompt)])
#     print("LLM返回内容：", response.content)  # 加这行
#     result = json.loads(response.content)
#     return result.get("items", [])
def parse_input(user_input: str, history_text: str = "（无历史对话）") -> dict:
    template = PromptTemplate.from_template(PARSE_PROMPT)
    prompt = template.format(user_input=user_input, history=history_text)
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        try:
            retry_response = llm.invoke([HumanMessage(
                content=f"以下JSON格式有错误，请修复后重新输出，只输出JSON不要其他内容：\n{content}"
            )])
            result = json.loads(retry_response.content.strip())
        except (json.JSONDecodeError, Exception):
            result = {"intent": "chat", "items": []}
    return result

# 单个污染物检测（抽出来方便并发）
async def check_single_item(item: dict, chroma) -> dict:
    # docs = chroma.similarity_search(
    #     f"{item['name']}排放标准限值",
    #     k=3
    # )
    # 换成混合检索
    doc_contents = hybrid_search(f"{item['name']}排放标准限值", top_k=3)
    context = "\n".join(doc_contents)
    # source_files = list(set([
    #     doc.metadata.get("file_name", "未知文件")
    #     for doc in docs
    # ]))
    # source_files 混合检索暂时取不到 metadata，先用固定值
    source_files = ["标准文档"]

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
        try:
            retry_response = await llm.ainvoke([HumanMessage(
                content=f"以下JSON格式有错误，请修复后重新输出，只输出JSON不要其他内容，字符串内部不要用双引号：\n{content}"
            )])
            result = json.loads(retry_response.content.strip())
        except (json.JSONDecodeError, Exception):
            result = {
                "name": item["name"],
                "measured_value": item["measured_value"],
                "standard_value": "未知",
                "is_compliant": None,
                "reason": "LLM返回格式异常，无法解析结果",
            }

    result["source_files"] = source_files
    return result


# 检测合规性
async def check_compliance(user_input: str) -> dict:
    chroma = get_chroma()
    parsed = parse_input(user_input)          # 改这里
    items = parsed.get("items", [])

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



async def stream_check_compliance(user_input: str, items: list, session_id: str = None) -> AsyncGenerator[str, None]:
    chroma = get_chroma()
    results = []

    # 每个污染物检测完立刻发出，不等其他的
    t2 = time.time()
    tasks = [check_single_item(item, chroma) for item in items]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        # 立刻推给前端
        yield f"data: {json.dumps({'type': 'result_item', 'item': result}, ensure_ascii=False)}\n\n"
    print(f"[阶段2] 解析耗时: {time.time() - t2:.2f}s")
    # 所有检测完后流式输出总结
    t3 = time.time()
    template = PromptTemplate.from_template(SUMMARY_PROMPT)
    prompt = template.format(results=json.dumps(results, ensure_ascii=False))

    summary_text = ""
    async for chunk in llm.astream([HumanMessage(content=prompt)]):
        if chunk.content:
            summary_text += chunk.content
            yield f"data: {json.dumps({'type': 'summary_chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    print(f"[阶段3] 解析耗时: {time.time() - t3:.2f}s")

    # content 存压缩结论（给后续轮次当上下文），raw 存原始 JSON（给前端回显表格）
    save_message(
        session_id, "assistant", _compact_results(results, summary_text),
        raw=json.dumps({"results": results, "summary": summary_text}, ensure_ascii=False),
    )


def _compact_results(results: list, summary_text: str) -> str:
    lines = []
    for r in results:
        if r.get("is_compliant") is True:
            status = "合规"
        elif r.get("is_compliant") is False:
            status = "超标"
        else:
            status = "未知"
        lines.append(f"{r.get('name')} 实测{r.get('measured_value')}，标准值{r.get('standard_value')}，{status}")
    record = "；".join(lines)
    if summary_text:
        record += f"\n总结：{summary_text}"
    return record


async def stream_normal_chat(user_input: str, history: list = None, session_id: str = None) -> AsyncGenerator[str, None]:
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for m in history or []:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))
    messages.append(HumanMessage(content=user_input))

    reply = ""
    async for chunk in llm.astream(messages):
        if chunk.content:
            reply += chunk.content
            yield f"data: {json.dumps({'type': 'chat_chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    save_message(session_id, "assistant", reply)


# ── MHTML 合规检测 ─────────────────────────────────────────────────────────────

def _find_matching_file(standard_name: str, db):
    """Fuzzy-match a standard name from MHTML to an uploaded PDF file."""
    from app.model.file import File

    files = db.query(File).filter(File.status == "active").all()
    if not files:
        return None

    def normalize(s: str) -> str:
        return re.sub(r"[\s\-\.]", "", s).upper()

    std_norm = normalize(standard_name)
    # Extract GB standard code, e.g. "GB31573" from "GB 31573-2015"
    gb_codes = set(re.findall(r"GB\d+", std_norm))

    best_file = None
    best_score = 0.0

    for f in files:
        fn_norm = normalize(f.file_name)
        fn_no_ext = re.sub(r"\.PDF$", "", fn_norm)

        # GB code match is highest-confidence
        file_gb = set(re.findall(r"GB\d+", fn_norm))
        if gb_codes and file_gb and gb_codes & file_gb:
            score = 1.0
        elif std_norm in fn_no_ext or fn_no_ext in std_norm:
            score = min(len(std_norm), len(fn_no_ext)) / max(len(std_norm), len(fn_no_ext), 1)
        else:
            continue

        if score > best_score:
            best_score = score
            best_file = f

    return best_file


async def _check_mhtml_item(item: dict, db, chroma) -> dict:
    """Compliance check for one MHTML row using its referenced standard file."""
    standard_name = item.get("standard_file", "")
    matched_file = _find_matching_file(standard_name, db)

    if matched_file:
        doc_contents = hybrid_search_by_filename(
            f"{item['name']}排放标准限值",
            matched_file.file_name,
            top_k=3,
        )
        source_files = [matched_file.file_name]
    else:
        doc_contents = hybrid_search(f"{item['name']}排放标准限值", top_k=3)
        source_files = [standard_name or "标准文档"]

    context = "\n".join(doc_contents)
    template = PromptTemplate.from_template(COMPLIANCE_PROMPT)
    prompt = template.format(
        context=context,
        name=item["name"],
        measured_value=item["measured_value"],
    )

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        try:
            retry = await llm.ainvoke([HumanMessage(
                content=f"以下JSON格式有错误，请修复后重新输出，只输出JSON不要其他内容：\n{content}"
            )])
            result = json.loads(retry.content.strip())
        except (json.JSONDecodeError, Exception):
            result = {
                "name": item["name"],
                "measured_value": item["measured_value"],
                "standard_value": "未知",
                "is_compliant": None,
                "reason": "LLM返回格式异常，无法解析结果",
            }

    result["source_files"] = source_files
    return result


async def stream_check_mhtml(items: list, db) -> AsyncGenerator[str, None]:
    """Stream compliance results for a list of items parsed from an MHTML file."""
    chroma = get_chroma()
    results = []

    tasks = [_check_mhtml_item(item, db, chroma) for item in items]
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        yield f"data: {json.dumps({'type': 'result_item', 'item': result}, ensure_ascii=False)}\n\n"

    template = PromptTemplate.from_template(SUMMARY_PROMPT)
    prompt = template.format(results=json.dumps(results, ensure_ascii=False))

    async for chunk in llm.astream([HumanMessage(content=prompt)]):
        if chunk.content:
            yield f"data: {json.dumps({'type': 'summary_chunk', 'content': chunk.content}, ensure_ascii=False)}\n\n"

    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"