from fastapi import APIRouter
from pydantic import BaseModel
from app.service.rag_service import detect_intent, check_compliance, normal_chat

router = APIRouter(prefix="/chat", tags=["问答"])

class ChatRequest(BaseModel):
    message: str

@router.post("/query")
def query(request: ChatRequest):
    user_input = request.message.strip()
    
    if not user_input:
        return {"type": "error", "content": "输入不能为空"}
    
    intent = detect_intent(user_input)
    
    if intent == "compliance":
        result = check_compliance(user_input)
        return {
            "type": "compliance",
            "results": result["results"],
            "summary": result["summary"]
        }
    else:
        reply = normal_chat(user_input)
        return {
            "type": "chat",
            "content": reply
        }