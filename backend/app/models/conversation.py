"""
EchoMind Conversation Model
Stores twin chat conversations with personality context and confidence scores.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    messages = Column(JSON, default=list)  # [{role, content, timestamp, confidence}]
    personality_context = Column(JSON, default=dict)
    twin_confidence_score = Column(Float, default=0.0)
    personality_match_score = Column(Float, default=0.0)
    behavior_similarity_score = Column(Float, default=0.0)
    memory_ids_used = Column(JSON, default=list)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation {self.title or self.id}>"
