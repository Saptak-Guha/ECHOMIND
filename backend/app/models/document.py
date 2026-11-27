"""
EchoMind Document Model
Stores uploaded documents for personality and behavior extraction.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class DocumentType(str, enum.Enum):
    EMAIL = "email"
    NOTE = "note"
    JOURNAL = "journal"
    SOCIAL = "social"
    TRANSCRIPT = "transcript"
    CHAT = "chat"
    ARTICLE = "article"
    RESUME = "resume"
    OTHER = "other"


class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    doc_type = Column(Enum(DocumentType), default=DocumentType.OTHER)
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    embedding_ids = Column(ARRAY(String), default=list)
    chunks_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    extracted_entities = Column(JSON, default=dict)
    extracted_emotions = Column(JSON, default=dict)
    extracted_topics = Column(JSON, default=list)
    metadata_json = Column(JSON, default=dict)
    file_path = Column(Text, nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<Document {self.title}>"
