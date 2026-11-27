"""
EchoMind Analytics Model
Stores platform analytics and scoring metrics over time.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MetricType(str, enum.Enum):
    TWIN_ACCURACY = "twin_accuracy"
    PERSONALITY_CONSISTENCY = "personality_consistency"
    DECISION_PREDICTION_ACCURACY = "decision_prediction_accuracy"
    MEMORY_RECALL_ACCURACY = "memory_recall_accuracy"
    COMMUNICATION_SIMILARITY = "communication_similarity"
    BEHAVIOR_MATCH = "behavior_match"
    EMOTIONAL_TREND = "emotional_trend"
    KNOWLEDGE_GROWTH = "knowledge_growth"
    MEMORY_GROWTH = "memory_growth"


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metadata_json = Column(JSON, default=dict)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="analytics")

    def __repr__(self):
        return f"<Analytics {self.metric_type.value}: {self.metric_value}>"
