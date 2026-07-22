"""用户岗位收藏模型。"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class FavoriteJob(Base):
    """用户画像收藏的岗位，用于记录人才对目标岗位的关注。"""

    __tablename__ = "favorite_jobs"
    __table_args__ = (
        # 同一画像对同一岗位只能收藏一次
        UniqueConstraint("profile_id", "job_id", name="uq_profile_job_favorite"),
    )

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(
        Integer,
        ForeignKey("user_skill_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联的用户画像 ID",
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="收藏的岗位 ID",
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="收藏时间",
    )

    profile = relationship("UserSkillProfile", back_populates="favorite_jobs")
    job = relationship("Job", back_populates="favorite_jobs")
