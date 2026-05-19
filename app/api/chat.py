import time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.service.rag_service import parse_input, stream_check_compliance, stream_normal_chat

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
            stream_check_compliance(user_input, items),  # 直接把items传进去
            media_type="text/event-stream"
        )
    else:
        return StreamingResponse(
            stream_normal_chat(user_input),
            media_type="text/event-stream"
        )