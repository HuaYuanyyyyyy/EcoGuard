from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.model.file import Base
from app.model.message import Message, ChatSession  # noqa: F401  注册到 Base.metadata，init_db 建表用
from app.config import settings

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    # messages 表早于 raw 字段上线，老库自动补列
    insp = inspect(engine)
    if "messages" in insp.get_table_names():
        cols = [c["name"] for c in insp.get_columns("messages")]
        if "raw" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE messages ADD COLUMN raw TEXT"))
