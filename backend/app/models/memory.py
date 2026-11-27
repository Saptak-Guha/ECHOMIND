"""
EchoMind Memory Model
Five memory types: semantic, episodic, behavioral, preference, emotional.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class MemoryType(str, enum.Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    BEHAVIORAL = "behavioral"
    PREFERENCE = "preference"
    EMOTIONAL = "emotional"


class SourceType(str, enum.Enum):
    CHAT = "chat"
    EMAIL = "email"
    DOCUMENT = "document"
    NOTE = "note"
    JOURNAL = "journal"
    SOCIAL = "social"
    TRANSCRIPT = "transcript"
    MANUAL = "manual"


class Memory(Base):
    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    memory_type = Column(Enum(MemoryType), nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    embedding_id = Column(String(255), nullable=True)
    importance_score = Column(Float, default=0.5)
    emotional_valence = Column(Float, default=0.0)  # -1.0 (negative) to 1.0 (positive)
    source_type = Column(Enum(SourceType), nullable=True)
    source_id = Column(String(255), nullable=True)
    tags = Column(ARRAY(String), default=list)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    accessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    access_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="memories")

    def __repr__(self):
        return f"<Memory {self.memory_type.value}: {self.summary or self.content[:50]}>"
