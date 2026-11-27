"""
EchoMind Profile Builder
Turns a single piece of ingested text into persisted twin state: an evolving
personality profile, an evolving behavior profile, and knowledge graph nodes.

Every ingestion path routes through `build_from_text` so documents, files,
conversations and batches all grow the twin identically.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.personality_engine import personality_engine
from app.ai.behavior_engine import behavior_engine
from app.ai.knowledge_graph_engine import knowledge_graph_engine
from app.models.personality import PersonalityProfile, BehaviorProfile
from app.models.knowledge_graph import KnowledgeGraphNode, KnowledgeGraphEdge, NodeType

# A profile is a running mean over every text ever ingested, so each new sample
# counts for 1/(n+1). Confidence saturates as samples accumulate.
CONFIDENCE_SATURATION = 12.0


def _blend(old: Optional[float], new: Optional[float], n: int) -> float:
    """Fold `new` into a running mean of `n` prior samples."""
    if new is None:
        return float(old or 0.0)
    if old is None or n <= 0:
        return round(float(new), 4)
    return round((float(old) * n + float(new)) / (n + 1), 4)


def _blend_dict(old: Optional[dict], new: Optional[dict], n: int) -> dict:
    """Running mean across every key in either dict."""
    old = old or {}
    new = new or {}
    keys = set(old) | set(new)
    merged = {}
    for k in keys:
        o, v = old.get(k), new.get(k)
        if isinstance(o, (int, float)) or isinstance(v, (int, float)):
            merged[k] = _blend(
                o if isinstance(o, (int, float)) else None,
                v if isinstance(v, (int, float)) else None,
                n,
            )
    return merged


def _merge_list(old: Optional[list], new: Optional[list], cap: int = 30) -> list:
    """Union of two string lists, order-preserving, capped."""
    seen, out = set(), []
    for item in list(old or []) + list(new or []):
        key = item.lower() if isinstance(item, str) else str(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out[:cap]


def _merge_counts(old: Optional[dict], new: Optional[dict], cap: int = 40) -> dict:
    """Sum two word-frequency maps, keeping the most frequent terms."""
    merged = dict(old or {})
    for word, count in (new or {}).items():
        if isinstance(count, (int, float)):
            merged[word] = merged.get(word, 0) + count
    return dict(sorted(merged.items(), key=lambda kv: kv[1], reverse=True)[:cap])


def _confidence(data_points: int) -> float:
    """Confidence grows with sample count and plateaus just under 1.0."""
    return round(min(data_points / CONFIDENCE_SATURATION, 1.0) * 0.95, 4)


async def _latest(db: AsyncSession, model, user_id: str):
    """Most recent version of a profile model, or None."""
    result = await db.execute(
        select(model)
        .where(model.user_id == user_id)
        .order_by(desc(model.version))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _build_personality(
    db: AsyncSession, user_id: str, analysis: Dict[str, Any]
) -> PersonalityProfile:
    """Append a new personality version blending this sample into the running mean."""
    prev = await _latest(db, PersonalityProfile, user_id)
    n = prev.data_points_count if prev else 0

    traits = analysis.get("personality_traits", {}) or {}
    style = analysis.get("writing_style", {}) or {}

    profile = PersonalityProfile(
        user_id=user_id,
        version=(prev.version + 1) if prev else 1,
        openness=_blend(prev.openness if prev else None, traits.get("openness"), n),
        conscientiousness=_blend(prev.conscientiousness if prev else None, traits.get("conscientiousness"), n),
        extraversion=_blend(prev.extraversion if prev else None, traits.get("extraversion"), n),
        agreeableness=_blend(prev.agreeableness if prev else None, traits.get("agreeableness"), n),
        neuroticism=_blend(prev.neuroticism if prev else None, traits.get("neuroticism"), n),
        avg_sentence_length=_blend(prev.avg_sentence_length if prev else None, style.get("avg_sentence_length"), n),
        vocabulary_richness=_blend(prev.vocabulary_richness if prev else None, style.get("vocabulary_richness"), n),
        formality_score=_blend(prev.formality_score if prev else None, style.get("formality_score"), n),
        complexity_score=_blend(prev.complexity_score if prev else None, style.get("complexity_score"), n),
        tone_profile=_blend_dict(prev.tone_profile if prev else None, analysis.get("tone_profile"), n),
        vocabulary_fingerprint=_merge_counts(
            prev.vocabulary_fingerprint if prev else None, style.get("vocabulary_fingerprint")
        ),
        beliefs=_merge_list(prev.beliefs if prev else None, analysis.get("beliefs")),
        interests=_merge_list(prev.interests if prev else None, analysis.get("interests")),
        values=_merge_list(prev.values if prev else None, analysis.get("values")),
        communication_patterns={
            **(prev.communication_patterns or {} if prev else {}),
            **(analysis.get("communication_patterns") or {}),
        },
        data_points_count=n + 1,
        confidence_score=_confidence(n + 1),
    )
    db.add(profile)
    return profile


async def _build_behavior(
    db: AsyncSession, user_id: str, analysis: Dict[str, Any]
) -> BehaviorProfile:
    """Append a new behavior version blending this sample into the running mean."""
    prev = await _latest(db, BehaviorProfile, user_id)
    n = prev.data_points_count if prev else 0

    profile = BehaviorProfile(
        user_id=user_id,
        version=(prev.version + 1) if prev else 1,
        risk_tolerance=_blend(prev.risk_tolerance if prev else None, analysis.get("risk_tolerance"), n),
        decisiveness=_blend(prev.decisiveness if prev else None, analysis.get("decisiveness"), n),
        adaptability=_blend(prev.adaptability if prev else None, analysis.get("adaptability"), n),
        persistence=_blend(prev.persistence if prev else None, analysis.get("persistence"), n),
        creativity=_blend(prev.creativity if prev else None, analysis.get("creativity"), n),
        # Categorical fields take the newest reading rather than a mean.
        decision_style=analysis.get("decision_style") or (prev.decision_style if prev else "analytical"),
        decision_speed=analysis.get("decision_speed") or (prev.decision_speed if prev else "moderate"),
        problem_solving_style=analysis.get("problem_solving_style") or (prev.problem_solving_style if prev else "systematic"),
        habits=_merge_list(prev.habits if prev else None, analysis.get("habits")),
        productivity_patterns={
            **(prev.productivity_patterns or {} if prev else {}),
            **(analysis.get("productivity_patterns") or {}),
        },
        work_preferences={
            **(prev.work_preferences or {} if prev else {}),
            **(analysis.get("work_preferences") or {}),
        },
        data_points_count=n + 1,
        confidence_score=_confidence(n + 1),
    )
    db.add(profile)
    return profile


def _coerce_node_type(raw: Optional[str]) -> NodeType:
    """Map an engine-supplied type string onto the NodeType enum, defaulting to CONCEPT."""
    try:
        return NodeType((raw or "concept").strip().lower())
    except ValueError:
        return NodeType.CONCEPT


async def _build_graph(
    db: AsyncSession, user_id: str, entities: Dict[str, Any], source_label: str
) -> int:
    """Persist extracted entities as graph nodes, de-duplicating by label.

    Nodes seen again gain importance rather than being inserted twice, so the
    graph reflects what the user actually keeps talking about.
    """
    raw_nodes: List[dict] = list(entities.get("nodes") or [])
    for topic in entities.get("topics") or []:
        if isinstance(topic, str):
            raw_nodes.append({"label": topic, "type": "interest", "confidence": 0.5})

    if not raw_nodes:
        return 0

    # Existing nodes for this user, keyed by lowercase label.
    existing_result = await db.execute(
        select(KnowledgeGraphNode).where(KnowledgeGraphNode.user_id == user_id)
    )
    by_label = {n.label.lower(): n for n in existing_result.scalars().all()}

    created: List[KnowledgeGraphNode] = []
    for raw in raw_nodes:
        label = str(raw.get("label") or "").strip()
        if not label or len(label) > 200:
            continue
        key = label.lower()
        if key in by_label:
            node = by_label[key]
            # Repetition is signal: nudge importance up, never past 1.0.
            node.importance_score = round(min((node.importance_score or 0.5) + 0.08, 1.0), 4)
            props = dict(node.properties or {})
            props["mentions"] = int(props.get("mentions", 1)) + 1
            node.properties = props
            continue
        node = KnowledgeGraphNode(
            user_id=user_id,
            node_type=_coerce_node_type(raw.get("type")),
            label=label,
            description=raw.get("description"),
            importance_score=round(float(raw.get("confidence") or 0.5), 4),
            properties={"mentions": 1, "source": source_label},
        )
        db.add(node)
        by_label[key] = node
        created.append(node)

    # Flush so new nodes have ids before edges reference them.
    if created:
        await db.flush()

    # Explicit relationships from the engine, plus co-occurrence links between
    # entities that showed up in the same text.
    for rel in entities.get("relationships") or []:
        src = by_label.get(str(rel.get("source", "")).lower())
        tgt = by_label.get(str(rel.get("target", "")).lower())
        if src is not None and tgt is not None and src.id != tgt.id:
            db.add(
                KnowledgeGraphEdge(
                    user_id=user_id,
                    source_node_id=src.id,
                    target_node_id=tgt.id,
                    relationship_type=str(rel.get("type") or "related_to")[:100],
                    weight=float(rel.get("weight") or 1.0),
                )
            )

    # ponytail: co-occurrence chain (not a full clique) keeps edges O(n) per
    # document. Switch to pairwise if the graph needs true density metrics.
    if len(created) > 1:
        for a, b in zip(created, created[1:]):
            db.add(
                KnowledgeGraphEdge(
                    user_id=user_id,
                    source_node_id=a.id,
                    target_node_id=b.id,
                    relationship_type="co_occurs_with",
                    weight=0.5,
                )
            )

    return len(created)


async def build_from_text(
    db: AsyncSession,
    user_id: str,
    text: str,
    source_label: str = "document",
    entities: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Grow every persisted twin profile from one text sample.

    Caller owns the transaction. `entities` may be passed in when the caller has
    already run entity extraction, to avoid doing it twice.
    """
    if not text or not text.strip():
        return {"personality_version": None, "behavior_version": None, "nodes_created": 0}

    sample = text[:8000]

    personality_analysis = await personality_engine.analyze_text(sample)
    behavior_analysis = await behavior_engine.analyze_behavior(sample)
    if entities is None:
        entities = await knowledge_graph_engine.extract_entities(sample)

    personality = await _build_personality(db, user_id, personality_analysis)
    behavior = await _build_behavior(db, user_id, behavior_analysis)
    nodes_created = await _build_graph(db, user_id, entities, source_label)

    return {
        "personality_version": personality.version,
        "behavior_version": behavior.version,
        "nodes_created": nodes_created,
        "personality_analysis": personality_analysis,
        "behavior_analysis": behavior_analysis,
    }
