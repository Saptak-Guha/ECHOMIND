"""
EchoMind Neo4j Connection
Neo4j driver for knowledge graph operations.
"""

from typing import Any, Dict, List, Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings


class Neo4jClient:
    """Async Neo4j client for knowledge graph operations."""

    def __init__(self):
        self.driver: Optional[AsyncDriver] = None

    async def connect(self):
        """Initialize Neo4j connection."""
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )

    async def disconnect(self):
        """Close Neo4j connection."""
        if self.driver:
            await self.driver.close()

    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def create_node(self, user_id: str, node_type: str, label: str, properties: Dict = None) -> Dict:
        """Create a knowledge graph node."""
        props = properties or {}
        props["user_id"] = user_id
        props["label"] = label
        query = f"""
        CREATE (n:{node_type} $props)
        SET n.created_at = datetime()
        RETURN n, elementId(n) as node_id
        """
        result = await self.execute_query(query, {"props": props})
        return result[0] if result else {}

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict = None,
    ) -> Dict:
        """Create a relationship between two nodes."""
        props = properties or {}
        query = f"""
        MATCH (a) WHERE elementId(a) = $source_id
        MATCH (b) WHERE elementId(b) = $target_id
        CREATE (a)-[r:{relationship_type} $props]->(b)
        SET r.created_at = datetime()
        RETURN type(r) as relationship, elementId(r) as rel_id
        """
        result = await self.execute_query(
            query, {"source_id": source_id, "target_id": target_id, "props": props}
        )
        return result[0] if result else {}

    async def get_user_graph(self, user_id: str, limit: int = 100) -> Dict:
        """Get the full knowledge graph for a user."""
        query = """
        MATCH (n {user_id: $user_id})
        OPTIONAL MATCH (n)-[r]-(m {user_id: $user_id})
        RETURN collect(DISTINCT {
            id: elementId(n),
            label: n.label,
            type: labels(n)[0],
            properties: properties(n)
        }) as nodes,
        collect(DISTINCT {
            id: elementId(r),
            source: elementId(startNode(r)),
            target: elementId(endNode(r)),
            type: type(r),
            properties: properties(r)
        }) as edges
        LIMIT $limit
        """
        result = await self.execute_query(query, {"user_id": user_id, "limit": limit})
        return result[0] if result else {"nodes": [], "edges": []}

    async def search_nodes(self, user_id: str, search_term: str, node_type: str = None) -> List[Dict]:
        """Search for nodes by label or properties."""
        type_filter = f"AND '{node_type}' IN labels(n)" if node_type else ""
        query = f"""
        MATCH (n {{user_id: $user_id}})
        WHERE toLower(n.label) CONTAINS toLower($search_term) {type_filter}
        RETURN elementId(n) as id, n.label as label, labels(n)[0] as type, properties(n) as properties
        ORDER BY n.label
        LIMIT 50
        """
        return await self.execute_query(query, {"user_id": user_id, "search_term": search_term})

    async def get_insights(self, user_id: str) -> List[Dict]:
        """Discover insights from the knowledge graph — most connected nodes, clusters, etc."""
        query = """
        MATCH (n {user_id: $user_id})-[r]-(m)
        WITH n, count(r) as connections
        ORDER BY connections DESC
        LIMIT 10
        RETURN elementId(n) as id, n.label as label, labels(n)[0] as type, connections
        """
        return await self.execute_query(query, {"user_id": user_id})

    async def init_constraints(self):
        """Create graph database constraints and indexes."""
        constraints = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Person) ON (n.user_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Project) ON (n.user_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Event) ON (n.user_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Interest) ON (n.user_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Goal) ON (n.user_id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Experience) ON (n.user_id)",
        ]
        for constraint in constraints:
            try:
                await self.execute_query(constraint)
            except Exception:
                pass  # Index may already exist


neo4j_client = Neo4jClient()
