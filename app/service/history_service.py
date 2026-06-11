# 对话历史读写。流式响应结束后才回写助手消息，
# 此时请求级 db 会话可能已关闭，所以这里统一用独立的 SessionLocal。
from datetime import datetime
from app.database import SessionLocal
from app.model.message import Message, ChatSession

# 取最近 8 条消息（约 4 轮对话）作为上下文窗口
HISTORY_LIMIT = 8
# 单条消息入库上限，防止超长总结把后续轮次的 prompt 撑爆
MAX_SAVED_CHARS = 2000
# 会话标题取首条用户消息的前 N 字
TITLE_CHARS = 20


def get_history(session_id: str, limit: int = HISTORY_LIMIT) -> list:
    if not session_id:
        return []
    db = SessionLocal()
    try:
        rows = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.id.desc())
            .limit(limit)
            .all()
        )
        return [{"role": r.role, "content": r.content} for r in reversed(rows)]
    finally:
        db.close()


def save_message(session_id: str, role: str, content: str, raw: str = None):
    if not session_id or not content:
        return
    db = SessionLocal()
    try:
        sess = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not sess:
            title = content[:TITLE_CHARS] if role == "user" else "新会话"
            db.add(ChatSession(id=session_id, title=title))
        else:
            sess.updated_at = datetime.now()
        db.add(Message(
            session_id=session_id,
            role=role,
            content=content[:MAX_SAVED_CHARS],
            raw=raw,
        ))
        db.commit()
    finally:
        db.close()


def list_sessions() -> list:
    db = SessionLocal()
    try:
        rows = (
            db.query(ChatSession)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )
        return [
            {
                "session_id": r.id,
                "title": r.title,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    finally:
        db.close()


def get_session_messages(session_id: str) -> list:
    db = SessionLocal()
    try:
        rows = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.id)
            .all()
        )
        return [{"role": r.role, "content": r.content, "raw": r.raw} for r in rows]
    finally:
        db.close()


def format_history(history: list) -> str:
    if not history:
        return "（无历史对话）"
    lines = []
    for m in history:
        prefix = "用户" if m["role"] == "user" else "助手"
        lines.append(f"{prefix}：{m['content']}")
    return "\n".join(lines)
