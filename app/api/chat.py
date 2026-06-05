import time
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.service.rag_service import parse_input, stream_check_compliance, stream_normal_chat, stream_check_mhtml
from app.service.mhtml_service import parse_mhtml
from app.database import get_db

router = APIRouter(prefix="/chat", tags=["问答"])

class ChatRequest(BaseModel):
    message: str

@router.post("/query")
async def query(request: ChatRequest):
    user_input = request.message.strip()

    if not user_input:
        return {"type": "error", "content": "输入不能为空"}

    t1 = time.time()
    parsed = parse_input(user_input)
    print(f"[阶段1] 解析耗时: {time.time() - t1:.2f}s")

    intent = parsed.get("intent")
    items = parsed.get("items", [])

    if intent == "compliance" and items:
        return StreamingResponse(
            stream_check_compliance(user_input, items),
            media_type="text/event-stream"
        )
    else:
        return StreamingResponse(
            stream_normal_chat(user_input),
            media_type="text/event-stream"
        )


@router.post("/debug-mhtml")
async def debug_mhtml(file: UploadFile = File(...)):
    """临时调试端点：直接返回 MHTML 解析结果，不走 RAG。"""
    import email
    from bs4 import BeautifulSoup
    from langchain_core.messages import HumanMessage
    from app.service.mhtml_service import (
        _get_main_html, _build_grid, _extract_table_text,
        llm, _EXTRACT_PROMPT
    )

    file_data = await file.read()

    msg = email.message_from_bytes(file_data)
    parts_info = [
        {"content_type": p.get_content_type(),
         "size": len(p.get_payload(decode=True) or b"")}
        for p in msg.walk()
    ]

    html = _get_main_html(file_data)
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    table_info = [{"cells": len(t.find_all(["td", "th"])), "rows": len(t.find_all("tr"))} for t in tables]

    grid_preview = []
    if tables:
        main_table = max(tables, key=lambda t: len(t.find_all(["td", "th"])))
        grid = _build_grid(main_table)
        grid_preview = grid[:5]

    table_text = _extract_table_text(file_data)

    # 调用 LLM 并返回原始输出
    llm_raw = ""
    if table_text:
        resp = await llm.ainvoke([HumanMessage(content=_EXTRACT_PROMPT.format(table_text=table_text))])
        llm_raw = resp.content.strip()

    items = await parse_mhtml(file_data)

    return {
        "file_size": len(file_data),
        "mime_parts": parts_info,
        "html_length": len(html),
        "tables_found": table_info,
        "grid_preview": grid_preview,
        "table_text_preview": table_text[:800],
        "llm_raw_output": llm_raw[:1000],
        "items_count": len(items),
        "items": items,
    }


@router.post("/check-mhtml")
async def check_mhtml(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".mhtml"):
        return {"type": "error", "content": "请上传 .mhtml 格式的文件"}

    file_data = await file.read()
    items = await parse_mhtml(file_data)

    if not items:
        return {"type": "error", "content": "未能从文件中提取到有效的污染物数据，请确认文件格式"}

    return StreamingResponse(
        stream_check_mhtml(items, db),
        media_type="text/event-stream"
    )