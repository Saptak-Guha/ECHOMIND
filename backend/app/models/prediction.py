"""
EchoMind Prediction & Simulation Models
Decision predictions and future-self simulations.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class SimulationType(str, enum.Enum):
    CAREER = "career"
    LIFE = "life"
    SKILL = "skill"
    STARTUP = "startup"
    RELATIONSHIP = "relationship"
    FINANCIAL = "financial"
    HEALTH = "health"


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario = Column(Text, nullable=False)
    prediction_text = Column(Text, nullable=False)
    confidence_pct = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)
    personality_factors = Column(JSON, default=dict)
    behavior_factors = Column(JSON, default=dict)
    supporting_memories = Column(JSON, default=list)
    actual_outcome = Column(Text, nullable=True)
    was_accurate = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    validated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction {self.confidence_pct}%: {self.scenario[:50]}>"


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    simulation_type = Column(Enum(SimulationType), nullable=False)
    title = Column(String(500), nullable=True)
    input_params = Column(JSON, default=dict)
    outcomes = Column(JSON, default=list)  # [{outcome, probability, risk_level, details}]
    risk_analysis = Column(JSON, default=dict)
    personality_influence = Column(JSON, default=dict)
    behavior_influence = Column(JSON, default=dict)
    timeline = Column(JSON, default=list)  # [{timepoint, event, probability}]
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="simulations")

    def __repr__(self):
        return f"<Simulation {self.simulation_type.value}: {self.title}>"
