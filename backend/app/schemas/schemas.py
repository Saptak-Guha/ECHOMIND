"""
EchoMind Pydantic Schemas
Request/response schemas for all API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


# ─── Auth Schemas ───────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str]
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Document / Ingestion Schemas ───────────────────────────────────────

class DocumentUpload(BaseModel):
    title: str
    content: str
    doc_type: str = "other"
    metadata: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: UUID
    title: str
    doc_type: str
    processing_status: str
    word_count: int
    chunks_count: int
    extracted_topics: List[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True

class BatchUpload(BaseModel):
    documents: List[DocumentUpload]

class ProcessingStatus(BaseModel):
    id: UUID
    status: str
    progress: float = 0.0
    message: Optional[str] = None


# ─── Memory Schemas ─────────────────────────────────────────────────────

class MemoryResponse(BaseModel):
    id: UUID
    memory_type: str
    content: str
    summary: Optional[str]
    importance_score: float
    emotional_valence: float
    source_type: Optional[str]
    tags: List[str]
    created_at: datetime
    access_count: int

    class Config:
        from_attributes = True

class MemorySearch(BaseModel):
    query: str
    memory_types: Optional[List[str]] = None
    top_k: int = 10
    min_importance: float = 0.0

class MemoryStats(BaseModel):
    total_memories: int
    by_type: Dict[str, int]
    avg_importance: float
    total_access_count: int
    oldest_memory: Optional[datetime]
    newest_memory: Optional[datetime]


# ─── Twin Chat Schemas ──────────────────────────────────────────────────

class TwinMessage(BaseModel):
    message: str
    conversation_id: Optional[UUID] = None
    include_memory: bool = True
    include_personality: bool = True

class TwinResponse(BaseModel):
    response: str
    conversation_id: UUID
    twin_confidence_score: float
    personality_match_score: float
    behavior_similarity_score: float
    memories_used: List[str]
    personality_context: Dict[str, Any]

class TwinProfile(BaseModel):
    overall_accuracy: float
    personality_match: float
    behavior_similarity: float
    communication_similarity: float
    data_points: int
    last_updated: Optional[datetime]


# ─── Personality Schemas ────────────────────────────────────────────────

class PersonalityResponse(BaseModel):
    id: UUID
    version: int
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float
    formality_score: float
    complexity_score: float
    vocabulary_richness: float
    tone_profile: Dict[str, float]
    beliefs: List[str]
    interests: List[str]
    values: List[str]
    confidence_score: float
    data_points_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class PersonalityEvolution(BaseModel):
    timeline: List[Dict[str, Any]]
    significant_changes: List[Dict[str, Any]]


# ─── Behavior Schemas ───────────────────────────────────────────────────

class BehaviorResponse(BaseModel):
    id: UUID
    version: int
    risk_tolerance: float
    decisiveness: float
    adaptability: float
    persistence: float
    creativity: float
    decision_style: str
    problem_solving_style: str
    habits: List[Dict]
    confidence_score: float
    data_points_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Prediction Schemas ─────────────────────────────────────────────────

class PredictionRequest(BaseModel):
    scenario: str = Field(..., min_length=10, description="Describe the scenario for prediction")

class PredictionResponse(BaseModel):
    id: UUID
    scenario: str
    prediction_text: str
    confidence_pct: float
    reasoning: str
    personality_factors: Dict[str, Any]
    behavior_factors: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class PredictionValidation(BaseModel):
    prediction_id: UUID
    actual_outcome: str
    was_accurate: bool


# ─── Simulation Schemas ─────────────────────────────────────────────────

class SimulationRequest(BaseModel):
    simulation_type: str  # career, life, skill, startup
    title: str
    params: Dict[str, Any] = Field(default_factory=dict)

class SimulationResponse(BaseModel):
    id: UUID
    simulation_type: str
    title: str
    outcomes: List[Dict[str, Any]]
    risk_analysis: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Knowledge Graph Schemas ────────────────────────────────────────────

class GraphNodeResponse(BaseModel):
    id: str
    label: str
    node_type: str
    properties: Dict[str, Any]
    connections: int = 0

class GraphEdgeResponse(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    weight: float

class GraphVisualization(BaseModel):
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]

class GraphInsight(BaseModel):
    id: str
    label: str
    node_type: str
    connections: int
    insight: str


# ─── Analytics Schemas ──────────────────────────────────────────────────

class DashboardMetrics(BaseModel):
    twin_accuracy: float
    decision_accuracy: float
    personality_match: float
    behavior_similarity: float
    communication_similarity: float
    total_memories: int
    total_documents: int
    total_predictions: int
    total_simulations: int
    knowledge_nodes: int
    emotional_trend: List[Dict[str, Any]]
    knowledge_growth: List[Dict[str, Any]]
    memory_growth: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]

class EmotionalTrend(BaseModel):
    timeline: List[Dict[str, Any]]
    current_mood: Dict[str, float]
    mood_changes: List[Dict[str, Any]]

class LifeTimelineEvent(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    date: datetime
    importance: float
    connected_entities: List[str]
