from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

class File(Base):
    __tablename__ = "files"

    id          = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name   = Column(String(255), nullable=False)
    minio_path  = Column(String(255), nullable=False)
    file_size   = Column(BigInteger)
    upload_time = Column(DateTime, default=datetime.now)
    status      = Column(String(20), default="active")