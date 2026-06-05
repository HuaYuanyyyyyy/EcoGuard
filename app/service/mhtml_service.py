import email
import json
import re
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.config import settings

llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.LLM_BASE_URL,
    model=settings.LLM_MODEL,
)

_EXTRACT_PROMPT = """从下面的排污许可表格文本中提取污染物记录。

只输出JSON数组，不要输出任何解释、分析或其他文字。

提取规则：
1. 每条记录需同时有：污染物名称、浓度限值（非"/"、非空）、标准文件名称（非"/"、非空）
2. 浓度限值为"/"或"/mg/Nm3"等无效值的行跳过
3. 输出格式（只输出这个，别的什么都不要）：
[{{"name":"污染物名称","measured_value":"浓度限值含单位","standard_file":"标准名称"}}]

表格内容：
{table_text}
"""

# 发给 LLM 的表格文本最大字符数，防止超 token
_MAX_TABLE_CHARS = 8000


def _get_html_with_most_cells(file_data: bytes) -> str:
    """Return the HTML part containing the most table cells (= data iframe)."""
    msg = email.message_from_bytes(file_data)
    best_html = ""
    best_count = -1
    for part in msg.walk():
        if part.get_content_type() != "text/html":
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        decoded = payload.decode("utf-8", errors="replace")
        soup = BeautifulSoup(decoded, "html.parser")
        count = len(soup.find_all(["td", "th"]))
        if count > best_count:
            best_count = count
            best_html = decoded
    return best_html


def _clean(text: str) -> str:
    """Collapse whitespace and remove control characters from a cell value."""
    return re.sub(r"\s+", " ", text).strip()


def _build_grid(table) -> list[list[str]]:
    """Build a 2D list respecting rowspan/colspan."""
    grid: dict[tuple, str] = {}
    ri = 0
    for tr in table.find_all("tr"):
        ci = 0
        for cell in tr.find_all(["td", "th"]):
            while (ri, ci) in grid:
                ci += 1
            text = _clean(cell.get_text(separator=" ", strip=True))
            rs = int(cell.get("rowspan", 1))
            cs = int(cell.get("colspan", 1))
            for r in range(rs):
                for c in range(cs):
                    grid[(ri + r, ci + c)] = text
            ci += cs
        ri += 1
    if not grid:
        return []
    max_row = max(r for r, c in grid) + 1
    max_col = max(c for r, c in grid) + 1
    return [[grid.get((r, c), "") for c in range(max_col)] for r in range(max_row)]


def _extract_table_text(file_data: bytes) -> str:
    """Extract readable table text, truncated to _MAX_TABLE_CHARS."""
    html = _get_html_with_most_cells(file_data)
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return ""
    main_table = max(tables, key=lambda t: len(t.find_all(["td", "th"])))
    grid = _build_grid(main_table)
    if not grid:
        return ""
    lines = []
    for row in grid:
        cells = [c for c in row if c.strip()]
        if cells:
            lines.append(" | ".join(cells))
    return "\n".join(lines)[:_MAX_TABLE_CHARS]


# 供 debug 端点引用
_get_main_html = _get_html_with_most_cells


def _extract_json_array(text: str) -> str:
    """Extract the first JSON array from text, ignoring surrounding prose."""
    # Find the first '[' and last ']'
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    # Fallback: strip markdown code fences
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("["):
                return part
    return text


async def parse_mhtml(file_data: bytes) -> list[dict]:
    """
    Use LLM to intelligently extract pollutant records from an MHTML file.
    Returns a list of {name, measured_value, standard_file}.
    """
    table_text = _extract_table_text(file_data)
    print(f"[MHTML] table_text 长度: {len(table_text)}")
    print(f"[MHTML] table_text 前500字:\n{table_text[:500]}")

    if not table_text:
        print("[MHTML] 表格文本为空，返回空列表")
        return []

    prompt = _EXTRACT_PROMPT.format(table_text=table_text)
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    print(f"[MHTML] LLM 返回:\n{content[:500]}")

    # 从响应中提取 JSON 数组（兼容 LLM 输出前置说明文字的情况）
    content = _extract_json_array(content)

    try:
        items = json.loads(content)
    except json.JSONDecodeError:
        print(f"[MHTML] JSON 解析失败，进行 retry")
        try:
            retry = await llm.ainvoke([HumanMessage(
                content=f"只输出JSON数组，不要其他任何内容：\n{content}"
            )])
            items = json.loads(_extract_json_array(retry.content.strip()))
        except Exception as e:
            print(f"[MHTML] retry 失败: {e}")
            return []

    if not isinstance(items, list):
        print(f"[MHTML] LLM 返回的不是列表: {type(items)}")
        return []

    result = []
    seen: set[tuple] = set()
    for item in items:
        name = str(item.get("name", "")).strip()
        value = str(item.get("measured_value", "")).strip()
        std = str(item.get("standard_file", "")).strip()
        if not name or not value or not std:
            continue
        if value in ("/", "") or value.startswith("/"):
            continue
        key = (name, value, std)
        if key in seen:
            continue
        seen.add(key)
        result.append({"name": name, "measured_value": value, "standard_file": std})

    print(f"[MHTML] 最终提取 {len(result)} 条")
    return result
