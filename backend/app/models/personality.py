"""
EchoMind Personality & Behavior Models
Stores evolving personality profiles and behavioral patterns.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base


class PersonalityProfile(Base):
    __tablename__ = "personality_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1)

    # Big Five Personality Traits (0.0 - 1.0)
    openness = Column(Float, default=0.5)
    conscientiousness = Column(Float, default=0.5)
    extraversion = Column(Float, default=0.5)
    agreeableness = Column(Float, default=0.5)
    neuroticism = Column(Float, default=0.5)

    # Writing Style Metrics
    avg_sentence_length = Column(Float, default=0.0)
    vocabulary_richness = Column(Float, default=0.0)  # Type-token ratio
    formality_score = Column(Float, default=0.5)  # 0=informal, 1=formal
    complexity_score = Column(Float, default=0.5)  # Flesch-Kincaid readability

    # Style Vectors (stored as JSON arrays)
    writing_style_vector = Column(JSON, default=list)
    tone_profile = Column(JSON, default=dict)  # {professional: 0.3, casual: 0.5, humorous: 0.2}
    vocabulary_fingerprint = Column(JSON, default=dict)  # Top words and frequencies

    # Extracted Traits
    beliefs = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    values = Column(JSON, default=list)
    communication_patterns = Column(JSON, default=dict)

    # Confidence & Meta
    confidence_score = Column(Float, default=0.0)
    data_points_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="personality_profiles")

    def __repr__(self):
        return f"<PersonalityProfile v{self.version} for {self.user_id}>"


class BehaviorProfile(Base):
    __tablename__ = "behavior_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1)

    # Core Behavioral Traits
    risk_tolerance = Column(Float, default=0.5)  # 0=risk-averse, 1=risk-seeking
    decisiveness = Column(Float, default=0.5)
    adaptability = Column(Float, default=0.5)
    persistence = Column(Float, default=0.5)
    creativity = Column(Float, default=0.5)

    # Decision Patterns
    decision_patterns = Column(JSON, default=dict)
    decision_speed = Column(String(50), default="moderate")  # fast, moderate, deliberate
    decision_style = Column(String(50), default="analytical")  # analytical, intuitive, collaborative

    # Work & Productivity
    problem_solving_style = Column(String(50), default="systematic")
    productivity_patterns = Column(JSON, default=dict)
    work_preferences = Column(JSON, default=dict)
    peak_hours = Column(JSON, default=list)

    # Habits & Patterns
    habits = Column(JSON, default=list)
    recurring_behaviors = Column(JSON, default=list)

    # Behavioral Embeddings
    behavioral_embeddings = Column(JSON, default=list)

    # Meta
    confidence_score = Column(Float, default=0.0)
    data_points_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="behavior_profiles")

    def __repr__(self):
        return f"<BehaviorProfile v{self.version} for {self.user_id}>"
