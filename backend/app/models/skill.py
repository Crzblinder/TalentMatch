from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.models.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    aliases = Column(Text, nullable=False, default="[]")
    definition = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
