"""
EchoMind Ingestion Routes
Upload and process documents, conversations, and batch data.
"""

import os
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4
from fastapi import (
    APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.config import settings
from app.core.database import get_db, async_session_factory
from app.core.security import get_current_user_id
from app.models.document import Document, DocumentType, ProcessingStatus
from app.models.memory import Memory, MemoryType, SourceType
from app.schemas.schemas import DocumentUpload, DocumentResponse, BatchUpload, ProcessingStatus as ProcessingStatusSchema
from app.ai.embeddings import embedding_engine
from app.ai.personality_engine import personality_engine
from app.ai.behavior_engine import behavior_engine
from app.ai.memory_engine import memory_engine
from app.ai.emotional_engine import emotional_engine
from app.ai.knowledge_graph_engine import knowledge_graph_engine
from app.ai.profile_builder import build_from_text
from app.core.vector_store import vector_store

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])

async def _run_ai_pipeline(doc: Document, content: str, db: AsyncSession) -> None:
    """Run a document through the AI pipeline, mutating `doc` in place.

    Shared by the synchronous /document path and the background /batch worker so
    both produce identical results. Caller owns the transaction.
    """
    # 1. Embed and persist to the vector store
    embedding = await embedding_engine.generate_embedding(content[:8000])
    embedding_id = await vector_store.store_embedding(
        user_id=str(doc.user_id),
        content=content[:2000],
        embedding=embedding,
        metadata={"doc_id": str(doc.id), "doc_type": doc.doc_type, "title": doc.title},
        collection_name="documents",
    )
    doc.embedding_ids = [embedding_id]

    # 2. Classify into long-term memory
    classification = await memory_engine.classify_memory(content)
    db.add(
        Memory(
            user_id=doc.user_id,
            memory_type=classification.get("memory_type", "semantic"),
            content=content[:5000],
            summary=classification.get("summary", doc.title),
            embedding_id=embedding_id,
            importance_score=classification.get("importance_score", 0.5),
            emotional_valence=classification.get("emotional_valence", 0.0),
            source_type=SourceType.DOCUMENT,
            source_id=str(doc.id),
            tags=classification.get("tags", []),
        )
    )

    # 3. Entities, topics, emotions
    entities = await knowledge_graph_engine.extract_entities(content)
    doc.extracted_entities = entities
    doc.extracted_topics = entities.get("topics", [])
    doc.extracted_emotions = await emotional_engine.analyze_emotion(content)

    # 4. Grow the persisted twin: personality, behavior and knowledge graph.
    #    Reuse the entities already extracted above rather than re-running.
    await build_from_text(
        db,
        str(doc.user_id),
        content,
        source_label=doc.doc_type or "document",
        entities=entities,
    )

    doc.processing_status = ProcessingStatus.COMPLETED
    doc.processed_at = datetime.now(timezone.utc)
    doc.chunks_count = 1


async def process_document(doc_id: str) -> None:
    """Background worker: process one pending document.

    Runs after the request has returned, so it opens its own session rather than
    reusing the request-scoped one (which is already closed by then).
    """
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Document).where(Document.id == UUID(doc_id)))
            doc = result.scalar_one_or_none()
            if doc is None:
                # Silent returns here previously left rows stuck in PENDING with
                # no trace of why — always say something.
                print(f"  ⚠️ process_document: document {doc_id} not found; skipping")
                return

            doc.processing_status = ProcessingStatus.PROCESSING
            await db.flush()

            await _run_ai_pipeline(doc, doc.content, db)
            await db.commit()
        except Exception as e:
            await db.rollback()
            # Re-open cleanly to record the failure; the rolled-back session
            # cannot be reused to persist the error state.
            async with async_session_factory() as err_db:
                result = await err_db.execute(select(Document).where(Document.id == UUID(doc_id)))
                doc = result.scalar_one_or_none()
                if doc is not None:
                    doc.processing_status = ProcessingStatus.FAILED
                    doc.metadata_json = {**(doc.metadata_json or {}), "error": str(e)}
                    await err_db.commit()


@router.post("/document", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    data: DocumentUpload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Upload a document for personality/behavior extraction."""
    words = data.content.split()

    doc = Document(
        user_id=user_id,
        title=data.title,
        content=data.content,
        doc_type=data.doc_type,
        word_count=len(words),
        metadata_json=data.metadata or {},
        processing_status=ProcessingStatus.PROCESSING,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    try:
        await _run_ai_pipeline(doc, data.content, db)
    except Exception as e:
        doc.processing_status = ProcessingStatus.FAILED
        doc.metadata_json = {**(doc.metadata_json or {}), "error": str(e)}

    return doc


@router.post("/conversation")
async def submit_conversation(
    messages: List[dict],
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Submit conversation data for learning."""
    all_text = " ".join([m.get("content", "") for m in messages])

    # Grow the persisted twin from the conversation, same as a document would.
    build_result = await build_from_text(
        db, user_id, all_text, source_label="conversation"
    )
    personality_analysis = build_result.get("personality_analysis", {})

    # Create memories from conversation
    memory_classification = await memory_engine.classify_memory(all_text)
    memory = Memory(
        user_id=user_id,
        memory_type=memory_classification.get("memory_type", "episodic"),
        content=all_text[:5000],
        summary=memory_classification.get("summary", "Conversation"),
        importance_score=memory_classification.get("importance_score", 0.5),
        emotional_valence=memory_classification.get("emotional_valence", 0.0),
        source_type=SourceType.CHAT,
        tags=memory_classification.get("tags", []),
    )
    db.add(memory)

    # Generate embedding and store
    embedding = await embedding_engine.generate_embedding(all_text[:8000])
    await vector_store.store_embedding(
        user_id=user_id,
        content=all_text[:2000],
        embedding=embedding,
        metadata={"source": "conversation", "message_count": len(messages)},
    )

    return {
        "status": "processed",
        "memories_created": 1,
        "personality_analysis": personality_analysis,
        "personality_version": build_result.get("personality_version"),
        "behavior_version": build_result.get("behavior_version"),
        "nodes_created": build_result.get("nodes_created", 0),
    }


@router.post("/batch")
async def batch_upload(
    data: BatchUpload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Batch upload multiple documents; each is processed in the background."""
    results = []
    for doc_data in data.documents:
        doc = Document(
            user_id=user_id,
            title=doc_data.title,
            content=doc_data.content,
            doc_type=doc_data.doc_type,
            word_count=len(doc_data.content.split()),
            processing_status=ProcessingStatus.PENDING,
        )
        db.add(doc)
        await db.flush()
        results.append({"id": str(doc.id), "title": doc.title, "status": "pending"})

    # Commit before scheduling: the workers open their own sessions and would
    # not see these rows if the request transaction were still open.
    await db.commit()
    for r in results:
        background_tasks.add_task(process_document, r["id"])

    return {"uploaded": len(results), "documents": results}


@router.post("/file", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    doc_type: str = Form("other"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Upload a text-based file (.txt/.md/.json/.csv) for processing."""
    allowed = {".txt", ".md", ".markdown", ".json", ".csv", ".log"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Allowed: {', '.join(sorted(allowed))}",
        )

    raw = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit",
        )

    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")

    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty")

    # Keep the original on disk so the source can be re-processed later.
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid4().hex}{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as fh:
        fh.write(raw)

    doc = Document(
        user_id=user_id,
        title=file.filename or stored_name,
        content=content,
        doc_type=doc_type,
        word_count=len(content.split()),
        metadata_json={"original_filename": file.filename, "stored_path": stored_path},
        processing_status=ProcessingStatus.PROCESSING,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    try:
        await _run_ai_pipeline(doc, content, db)
    except Exception as e:
        doc.processing_status = ProcessingStatus.FAILED
        doc.metadata_json = {**(doc.metadata_json or {}), "error": str(e)}

    return doc


@router.get("/status/{doc_id}", response_model=ProcessingStatusSchema)
async def get_processing_status(
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Check document processing status."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return ProcessingStatusSchema(
        id=doc.id,
        status=doc.processing_status.value,
        progress=1.0 if doc.processing_status == ProcessingStatus.COMPLETED else 0.5,
        message=f"Document '{doc.title}' is {doc.processing_status.value}",
    )
