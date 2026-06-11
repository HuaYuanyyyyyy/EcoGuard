from sqlalchemy import Column, String, Text, DateTime, Integer
from datetime import datetime
from app.model.file import Base

class Message(Base):
    __tablename__ = "messages"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), index=True, nullable=False)
    role       = Column(String(20), nullable=False)  # 'user' / 'assistant'
    content    = Column(Text, nullable=False)
    raw        = Column(Text, nullable=True)  # 合规结果原始 JSON，用于前端回显表格
    created_at = Column(DateTime, default=datetime.now)


class ChatSession(Base):
    __tablename__ = "sessions"

    id         = Column(String(36), primary_key=True)
    title      = Column(String(100), default="新会话")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
