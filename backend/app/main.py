"""
EchoMind — Human Digital Twin Intelligence Platform
FastAPI Application Entry Point
"""

import sys
from contextlib import asynccontextmanager

# Windows consoles default to cp1252, which cannot encode the emoji used in the
# startup banner below — without this the first print kills app startup.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db, close_db, seed_demo_user
from app.core.redis import redis_client
from app.core.neo4j import neo4j_client
from app.core.vector_store import vector_store
from app.ai.embeddings import embedding_engine
from app.ai.personality_engine import personality_engine
from app.ai.behavior_engine import behavior_engine
from app.ai.twin_engine import twin_engine
from app.ai.memory_engine import memory_engine
from app.ai.prediction_engine import prediction_engine
from app.ai.simulation_engine import simulation_engine
from app.ai.emotional_engine import emotional_engine
from app.ai.communication_engine import communication_engine
from app.ai.knowledge_graph_engine import knowledge_graph_engine

# Import routes
from app.routes.auth import router as auth_router
from app.routes.ingestion import router as ingestion_router
from app.routes.twin import router as twin_router
from app.routes.api_routes import (
    memory_router,
    personality_router,
    behavior_router,
    prediction_router,
    simulation_router,
    graph_router,
    analytics_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # ── Startup ──
    print("🧠 EchoMind — Initializing Human Digital Twin Intelligence Platform...")

    # Initialize database
    try:
        await init_db()
        created = await seed_demo_user()
        print(f"  ✅ PostgreSQL connected{' (demo user seeded)' if created else ''}")
    except Exception as e:
        print(f"  ⚠️ PostgreSQL: {e}")

    # Initialize Redis
    try:
        await redis_client.connect()
        print("  ✅ Redis connected")
    except Exception as e:
        print(f"  ⚠️ Redis: {e}")

    # Initialize Neo4j
    try:
        await neo4j_client.connect()
        await neo4j_client.init_constraints()
        print("  ✅ Neo4j connected")
    except Exception as e:
        print(f"  ⚠️ Neo4j: {e}")

    # Initialize Vector Store
    try:
        await vector_store.connect()
        print("  ✅ Vector Store (ChromaDB + FAISS) connected")
    except Exception as e:
        print(f"  ⚠️ Vector Store: {e}")

    # Initialize AI Engines
    try:
        await embedding_engine.initialize()
        await personality_engine.initialize()
        await behavior_engine.initialize()
        await twin_engine.initialize()
        await memory_engine.initialize()
        await prediction_engine.initialize()
        await simulation_engine.initialize()
        await emotional_engine.initialize()
        await communication_engine.initialize()
        await knowledge_graph_engine.initialize()
        print("  ✅ All 10 AI Engines initialized")
    except Exception as e:
        print(f"  ⚠️ AI Engines: {e}")

    print("🚀 EchoMind is ready!")
    print(f"   Version: {settings.APP_VERSION}")
    print(f"   API: http://{settings.HOST}:{settings.PORT}{settings.API_PREFIX}")

    yield

    # ── Shutdown ──
    print("🔄 EchoMind — Shutting down...")
    await close_db()
    await redis_client.disconnect()
    await neo4j_client.disconnect()
    vector_store.save_faiss_index()
    print("👋 EchoMind stopped.")


# ── Create Application ──
app = FastAPI(
    title="EchoMind",
    description="Human Digital Twin Intelligence Platform — Learn, Model, Simulate, and Predict human behavior.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routes ──
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(ingestion_router, prefix=settings.API_PREFIX)
app.include_router(twin_router, prefix=settings.API_PREFIX)
app.include_router(memory_router, prefix=settings.API_PREFIX)
app.include_router(personality_router, prefix=settings.API_PREFIX)
app.include_router(behavior_router, prefix=settings.API_PREFIX)
app.include_router(prediction_router, prefix=settings.API_PREFIX)
app.include_router(simulation_router, prefix=settings.API_PREFIX)
app.include_router(graph_router, prefix=settings.API_PREFIX)
app.include_router(analytics_router, prefix=settings.API_PREFIX)


# ── Root Endpoint ──
@app.get("/")
async def root():
    return {
        "name": "EchoMind",
        "tagline": "Human Digital Twin Intelligence Platform",
        "version": settings.APP_VERSION,
        "status": "operational",
        "modules": [
            "Personality Learning Engine",
            "Behavioral Modeling Engine",
            "Digital Twin Generator",
            "Long-Term Memory System",
            "Decision Prediction Engine",
            "Future Self Simulator",
            "Communication Cloning",
            "Emotional Intelligence Engine",
            "Knowledge Graph",
            "Digital Legacy System",
        ],
        "docs": f"{settings.API_PREFIX}/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "echomind"}
