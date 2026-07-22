from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class PromptVariant(Base):
    __tablename__ = "prompt_variants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    agent_type = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    template = Column(Text, nullable=False)
    technique = Column(String(64), nullable=True)  # CoT, Few-Shot, Zero-Shot, etc.
    variant_metadata = Column(JSON, default=dict)
    is_baseline = Column(Integer, default=0)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    dataset_size = Column(Integer, nullable=False)
    metrics = Column(JSON, default=dict)
    # Per-variant results
    variant_results = Column(JSON, default=dict)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
