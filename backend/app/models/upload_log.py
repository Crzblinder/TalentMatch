"""上传与操作日志模型。"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class UploadLog(Base):
    """文件上传与操作日志表。"""

    __tablename__ = "upload_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(Integer, nullable=True, index=True)
    file_name = Column(String(255), nullable=True, default="", index=True)
    file_size = Column(Integer, nullable=True, default=0)
    file_type = Column(String(64), nullable=True, default="")
    status = Column(String(32), nullable=False, index=True)
    message = Column(Text, nullable=True, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
