from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class UserSkillProfile(Base):
    __tablename__ = "user_skill_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    skills = Column(Text, nullable=False, default="[]")
    experience_level = Column(String(64), nullable=False)
    target_job_titles = Column(Text, nullable=False, default="[]")
    is_active = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 一个画像可以收藏多个岗位
    favorite_jobs = relationship(
        "FavoriteJob",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
