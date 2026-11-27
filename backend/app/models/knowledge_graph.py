"""
EchoMind Knowledge Graph Models (PostgreSQL mirror)
These mirror the Neo4j graph structure for relational queries and backup.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
import enum


class NodeType(str, enum.Enum):
    PERSON = "person"
    PROJECT = "project"
    EVENT = "event"
    INTEREST = "interest"
    GOAL = "goal"
    EXPERIENCE = "experience"
    SKILL = "skill"
    ORGANIZATION = "organization"
    LOCATION = "location"
    CONCEPT = "concept"


class KnowledgeGraphNode(Base):
    __tablename__ = "knowledge_graph_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    neo4j_id = Column(String(255), nullable=True)  # Reference to Neo4j node
    node_type = Column(Enum(NodeType), nullable=False, index=True)
    label = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    properties = Column(JSON, default=dict)
    embedding_id = Column(String(255), nullable=True)
    importance_score = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<KGNode {self.node_type.value}: {self.label}>"


class KnowledgeGraphEdge(Base):
    __tablename__ = "knowledge_graph_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    neo4j_id = Column(String(255), nullable=True)
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_graph_nodes.id", ondelete="CASCADE"), nullable=False)
    relationship_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    properties = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<KGEdge {self.relationship_type}: {self.source_node_id} -> {self.target_node_id}>"
