"""简历数据模型。"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class Resume(Base):
    """用户简历主表，存储解析后的完整简历数据。"""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, index=True)
    phone = Column(String(32), nullable=True, default="", index=True)
    email = Column(String(128), nullable=True, default="", index=True)
    file_name = Column(String(255), nullable=True, default="")
    file_size = Column(Integer, nullable=True, default=0)

    # 简历核心字段（JSON 序列化存储）
    basic_info = Column(Text, nullable=False, default="{}")
    education = Column(Text, nullable=False, default="[]")
    work_experience = Column(Text, nullable=False, default="[]")
    project_experience = Column(Text, nullable=False, default="[]")
    competition_experience = Column(Text, nullable=False, default="[]")
    awards = Column(Text, nullable=False, default="[]")
    certifications = Column(Text, nullable=False, default="[]")
    language_skills = Column(Text, nullable=False, default="[]")
    self_evaluation = Column(Text, nullable=True, default="")
    job_intention = Column(Text, nullable=False, default="{}")
    publications = Column(Text, nullable=False, default="[]")
    portfolio = Column(Text, nullable=False, default="[]")
    skills = Column(Text, nullable=False, default="[]")

    raw_text = Column(Text, nullable=True, default="")
    experience_level = Column(String(64), nullable=True, default="")
    education_level = Column(String(32), nullable=True, default="")
    fuzzy = Column(Boolean, default=False, nullable=False)
    obstacles = Column(Text, nullable=True, default="")

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
