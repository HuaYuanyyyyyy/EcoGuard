from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.service.rag_service import detect_intent, stream_check_compliance, stream_normal_chat

router = APIRouter(prefix="/chat", tags=["问答"])

class ChatRequest(BaseModel):
    message: str

@router.post("/query")
async def query(request: ChatRequest):
    user_input = request.message.strip()

    if not user_input:
        return {"type": "error", "content": "输入不能为空"}

    intent = detect_intent(user_input)

    if intent == "compliance":
        return StreamingResponse(
            stream_check_compliance(user_input),
            media_type="text/event-stream"
        )
    else:
        return StreamingResponse(
            stream_normal_chat(user_input),
            media_type="text/event-stream"
        )