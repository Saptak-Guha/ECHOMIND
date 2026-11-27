"""
EchoMind Knowledge Graph Engine
Extracts entities and relationships to build a personal knowledge graph.
"""

import json
from typing import Any, Dict, List
from app.core.config import settings
from app.ai.llm import llm_client
from app.ai.text_utils import parse_llm_json


class KnowledgeGraphEngine:
    """
    Builds and maintains a personal knowledge graph.
    
    Nodes: People, Projects, Events, Interests, Goals, Experiences
    Relationships: Influenced by, worked on, attended, interested in, etc.
    """

    def __init__(self):
        self._llm = None

    async def initialize(self):
        llm_client.initialize()
        if llm_client.available:
            self._llm = llm_client

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities and relationships from text."""
        if self._llm:
            return await self._llm_extract(text)
        return self._heuristic_extract(text)

    # Capitalised words that are never entities: sentence-leading pronouns,
    # weekdays, months and the like would otherwise flood the graph.
    ENTITY_STOPWORDS = {
        "i", "i'm", "i've", "i'll", "i'd", "my", "me", "we", "you", "he", "she",
        "they", "it", "the", "a", "an", "this", "that", "these", "those",
        "but", "and", "or", "so", "then", "there", "here", "what", "when",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
        "january", "february", "march", "april", "may", "june", "july",
        "august", "september", "october", "november", "december",
        "today", "tomorrow", "yesterday", "however", "because", "if", "although",
    }

    def _heuristic_extract(self, text: str) -> Dict[str, Any]:
        """Basic entity extraction using heuristics."""
        words = text.split()

        # Simple proper noun detection (capitalized words not at sentence start)
        potential_entities = []
        for i, word in enumerate(words):
            clean = word.strip(".,!?;:'\"()")
            if not clean or not clean[0].isupper():
                continue
            if i == 0 or words[i - 1].endswith((".", "!", "?")):
                continue
            # Drop pronouns, connectives and calendar words, plus 1-2 letter
            # fragments that are almost always noise rather than entities.
            if clean.lower() in self.ENTITY_STOPWORDS or len(clean) < 3:
                continue
            potential_entities.append(clean)

        # Deduplicate
        entities = list(set(potential_entities))

        return {
            "nodes": [
                {"label": e, "type": "concept", "confidence": 0.3}
                for e in entities[:20]
            ],
            "relationships": [],
            "topics": [],
        }

    async def _llm_extract(self, text: str) -> Dict[str, Any]:
        """Use LLM for intelligent entity and relationship extraction."""
        prompt = f"""Extract entities and relationships from this text to build a personal knowledge graph.

TEXT:
{text[:4000]}

Return JSON:
{{
    "nodes": [
        {{
            "label": "entity name",
            "type": "person|project|event|interest|goal|experience|skill|organization|location|concept",
            "description": "brief description",
            "confidence": <float 0-1>
        }}
    ],
    "relationships": [
        {{
            "source": "entity name 1",
            "target": "entity name 2",
            "type": "knows|works_on|attended|interested_in|achieved|influenced_by|related_to|part_of|located_in",
            "description": "brief description of relationship",
            "weight": <float 0-1>
        }}
    ],
    "topics": ["main topics discussed"]
}}

Extract meaningful entities and relationships. Focus on personally significant items. Return ONLY JSON."""

        try:
            response = await self._llm.complete(
                prompt,
                max_tokens=1000,
                temperature=0.3,
            )
            return parse_llm_json(response, text_fields=("description", "label"))
        except Exception:
            return self._heuristic_extract(text)

    async def discover_insights(self, graph_data: Dict) -> List[Dict]:
        """Discover insights from the knowledge graph structure."""
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if not nodes:
            return [{"insight": "Add more data to discover insights", "type": "info"}]

        insights = []

        # Most connected nodes
        connection_counts = {}
        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            connection_counts[src] = connection_counts.get(src, 0) + 1
            connection_counts[tgt] = connection_counts.get(tgt, 0) + 1

        if connection_counts:
            most_connected = max(connection_counts, key=connection_counts.get)
            insights.append({
                "insight": f"'{most_connected}' is your most connected entity with {connection_counts[most_connected]} connections",
                "type": "hub",
                "entity": most_connected,
            })

        # Node type distribution
        type_counts = {}
        for node in nodes:
            ntype = node.get("type", "unknown")
            type_counts[ntype] = type_counts.get(ntype, 0) + 1

        dominant_type = max(type_counts, key=type_counts.get) if type_counts else "unknown"
        insights.append({
            "insight": f"Your knowledge graph is dominated by '{dominant_type}' entities ({type_counts.get(dominant_type, 0)} nodes)",
            "type": "distribution",
        })

        return insights


knowledge_graph_engine = KnowledgeGraphEngine()
