from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.sql import func

from app.models.base import Base


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(
        Integer, ForeignKey("user_skill_profiles.id"), nullable=False, index=True
    )
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    match_score = Column(Float, nullable=False)
    skill_score = Column(Float, nullable=True)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)
    matched_skills = Column(Text, nullable=False, default="[]")
    missing_skills = Column(Text, nullable=False, default="[]")
    transferable_skills = Column(Text, nullable=False, default="[]")
    analysis_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
