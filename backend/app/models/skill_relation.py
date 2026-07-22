from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.models.base import Base


class SkillRelation(Base):
    __tablename__ = "skill_relations"

    id = Column(Integer, primary_key=True, index=True)
    source_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    target_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    # relation types: dependency / similarity / co_occurrence
    relation_type = Column(String(32), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
