"""
NetworkX Store — Graph storage and traversal using NetworkX.

Converts a KnowledgeGraph into a NetworkX DiGraph and provides
query methods for concept lookup, prerequisites, learning paths,
and keyword search.
"""

import json
import pickle
import logging
from pathlib import Path
from typing import Optional

import networkx as nx

from app.services.graph_rag.schema import KnowledgeGraph, Concept

logger = logging.getLogger(__name__)

# Node type colors for visualization
NODE_COLORS = {
    "chapter": "#4A90D9",     # Blue
    "section": "#50C878",     # Green
    "concept": "#FFD700",     # Gold
    "definition": "#FFA07A",  # Salmon
    "question": "#DA70D6",    # Orchid
    "example": "#87CEEB",     # Sky blue
}


class NetworkXStore:
    """
    Graph storage using NetworkX DiGraph.

    Provides methods for:
    - Building a graph from a KnowledgeGraph
    - Concept lookup and search (including raw source_text search)
    - Prerequisite chain traversal
    - Learning path computation
    - Graph serialization
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self._kg: Optional[KnowledgeGraph] = None
        self._concept_index: dict[str, dict] = {}  # concept_id -> details
        self._name_index: dict[str, str] = {}  # lowercase name -> concept_id

    def load_from_knowledge_graph(self, kg: KnowledgeGraph):
        """
        Build the NetworkX graph from a KnowledgeGraph.

        Creates nodes for chapters, sections, and concepts,
        and edges for all relationships.
        """
        self._kg = kg
        self.graph.clear()
        self._concept_index.clear()
        self._name_index.clear()

        # Add chapter nodes
        for chapter in kg.chapters:
            self.graph.add_node(
                chapter.chapter_id,
                type="chapter",
                title=chapter.title,
                summary=chapter.summary,
                color=NODE_COLORS["chapter"],
                label=chapter.title,
            )

            # Add section nodes
            for section in chapter.sections:
                self.graph.add_node(
                    section.section_id,
                    type="section",
                    title=section.title,
                    page_start=section.page_start,
                    color=NODE_COLORS["section"],
                    label=section.title,
                )

                # Add concept nodes
                for concept in section.concepts:
                    node_type = getattr(concept, "node_type", "concept") or "concept"
                    color = NODE_COLORS.get(node_type, NODE_COLORS["concept"])

                    node_data = {
                        "type": "concept",          # graph node type (always "concept" for traversal)
                        "node_type": node_type,     # semantic type: concept/question/definition/example
                        "name": concept.name,
                        "definition": concept.definition,
                        "examples": concept.examples,
                        "keywords": concept.keywords,
                        "page_ref": concept.page_ref,
                        "source_section": section.section_id,
                        "source_text": concept.source_text,
                        "color": color,
                        "label": concept.name,
                    }
                    self.graph.add_node(concept.concept_id, **node_data)

                    # Build indexes
                    self._concept_index[concept.concept_id] = node_data
                    self._name_index[concept.name.lower()] = concept.concept_id

        # Add relationship edges
        for rel in kg.relationships:
            if self.graph.has_node(rel.source) and self.graph.has_node(rel.target):
                self.graph.add_edge(
                    rel.source,
                    rel.target,
                    rel_id=rel.rel_id,
                    type=rel.type,
                    reason=rel.reason,
                    confidence=rel.confidence,
                    label=rel.type,
                )

        logger.info(
            f"NetworkX graph built: {self.graph.number_of_nodes()} nodes, "
            f"{self.graph.number_of_edges()} edges"
        )

    def get_concept(self, concept_id: str) -> Optional[dict]:
        """Get full concept details by ID."""
        if concept_id in self._concept_index:
            return self._concept_index[concept_id]

        # Try by name
        if concept_id.lower() in self._name_index:
            cid = self._name_index[concept_id.lower()]
            return self._concept_index.get(cid)

        return None

    def get_prerequisites(self, concept_id: str) -> list[dict]:
        """
        Get all prerequisite concepts (ancestors via depends_on edges).

        Returns concepts in dependency order (foundations first).
        """
        if not self.graph.has_node(concept_id):
            return []

        prereqs = []
        visited = set()

        def _traverse(node_id):
            if node_id in visited:
                return
            visited.add(node_id)

            for pred in self.graph.predecessors(node_id):
                edge_data = self.graph.get_edge_data(pred, node_id)
                if edge_data and edge_data.get("type") == "depends_on":
                    _traverse(pred)

            for succ in self.graph.successors(node_id):
                edge_data = self.graph.get_edge_data(node_id, succ)
                if edge_data and edge_data.get("type") == "depends_on":
                    _traverse(succ)
                    if succ in self._concept_index:
                        prereqs.append({"concept_id": succ, **self._concept_index[succ]})

        _traverse(concept_id)
        return prereqs

    def get_related(self, concept_id: str) -> list[dict]:
        """Get all directly related concepts (any relationship type)."""
        if not self.graph.has_node(concept_id):
            return []

        related = []
        for succ in self.graph.successors(concept_id):
            edge = self.graph.get_edge_data(concept_id, succ)
            node = self.graph.nodes.get(succ, {})
            if node.get("type") == "concept":
                related.append({
                    "concept_id": succ,
                    "relationship": edge.get("type", "related_to"),
                    "confidence": edge.get("confidence", "medium"),
                    **node,
                })

        for pred in self.graph.predecessors(concept_id):
            edge = self.graph.get_edge_data(pred, concept_id)
            node = self.graph.nodes.get(pred, {})
            if node.get("type") == "concept":
                related.append({
                    "concept_id": pred,
                    "relationship": edge.get("type", "related_to"),
                    "confidence": edge.get("confidence", "medium"),
                    **node,
                })

        return related

    def get_learning_path(self, from_id: str, to_id: str) -> list[dict]:
        """
        Compute the shortest learning path between two concepts.
        """
        if not self.graph.has_node(from_id):
            from_id = self._name_index.get(from_id.lower(), from_id)
        if not self.graph.has_node(to_id):
            to_id = self._name_index.get(to_id.lower(), to_id)

        if not self.graph.has_node(from_id) or not self.graph.has_node(to_id):
            return []

        try:
            undirected = self.graph.to_undirected()
            path = nx.shortest_path(undirected, from_id, to_id)

            result = []
            for node_id in path:
                node = self.graph.nodes.get(node_id, {})
                result.append({
                    "concept_id": node_id,
                    "type": node.get("type", "unknown"),
                    "name": node.get("name", node.get("title", node_id)),
                    "definition": node.get("definition", node.get("summary", "")),
                })
            return result
        except nx.NetworkXNoPath:
            return []

    def search(self, keyword: str, limit: int = 20) -> list[dict]:
        """
        Search for concepts by keyword match.

        Searches concept names, definitions, keywords, examples, and source_text.
        """
        keyword_lower = keyword.lower()
        results = []

        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") != "concept":
                continue

            score = 0
            name = data.get("name", "").lower()
            definition = data.get("definition", "").lower()
            keywords = [k.lower() for k in data.get("keywords", [])]
            examples = [e.lower() for e in data.get("examples", [])]
            source_text = data.get("source_text", "").lower()

            if keyword_lower == name:
                score = 100
            elif keyword_lower in name:
                score = 80
            elif keyword_lower in keywords:
                score = 60
            elif keyword_lower in definition:
                score = 40
            elif keyword_lower in source_text:
                score = 30
            elif any(keyword_lower in ex for ex in examples):
                score = 20

            if score > 0:
                results.append({"concept_id": node_id, "score": score, **data})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def search_raw(self, keyword: str, limit: int = 10) -> list[dict]:
        """
        Search source_text of concept nodes for keyword matches.
        Returns nodes whose raw source text contains the keyword.
        """
        keyword_lower = keyword.lower()
        results = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") != "concept":
                continue
            source_text = data.get("source_text", "").lower()
            if keyword_lower in source_text:
                results.append({"concept_id": node_id, **data})
        return results[:limit]

    def get_chapter_summary(self, chapter_id: str) -> Optional[dict]:
        """Get a chapter with all its concepts listed."""
        if not self.graph.has_node(chapter_id):
            return None

        node = self.graph.nodes[chapter_id]
        if node.get("type") != "chapter":
            return None

        concepts = []
        try:
            undirected = self.graph.to_undirected()
            connected = nx.node_connected_component(undirected, chapter_id)
            for nid in connected:
                ndata = self.graph.nodes.get(nid, {})
                if ndata.get("type") == "concept":
                    concepts.append({"concept_id": nid, **ndata})
        except Exception:
            ch_num = chapter_id.replace("C", "")
            for nid, ndata in self.graph.nodes(data=True):
                if ndata.get("type") == "concept":
                    src_sec = ndata.get("source_section", "")
                    if src_sec.startswith(f"S{ch_num}."):
                        concepts.append({"concept_id": nid, **ndata})

        return {
            "chapter_id": chapter_id,
            "title": node.get("title", ""),
            "summary": node.get("summary", ""),
            "concepts": concepts,
        }

    def get_graph_stats(self) -> dict:
        """Return statistics about the graph."""
        node_types: dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("node_type", data.get("type", "unknown"))
            node_types[t] = node_types.get(t, 0) + 1

        edge_types: dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            t = data.get("type", "unknown")
            edge_types[t] = edge_types.get(t, 0) + 1

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": node_types,
            "edge_types": edge_types,
            "is_dag": nx.is_directed_acyclic_graph(self.graph),
        }

    # --- Serialization ---

    def save_graphml(self, path: str | Path):
        """Save graph to GraphML format."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        G = self.graph.copy()
        for node_id in G.nodes():
            for key, val in list(G.nodes[node_id].items()):
                if isinstance(val, list):
                    G.nodes[node_id][key] = json.dumps(val)
                elif val is None:
                    G.nodes[node_id][key] = ""

        nx.write_graphml(G, str(path))
        logger.info(f"Graph saved to {path}")

    def save_pickle(self, path: str | Path):
        """Save graph as pickle for fast loading."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "graph": self.graph,
                "concept_index": self._concept_index,
                "name_index": self._name_index,
            }, f)
        logger.info(f"Graph saved to {path}")

    def load_pickle(self, path: str | Path):
        """Load graph from pickle."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.graph = data["graph"]
        self._concept_index = data["concept_index"]
        self._name_index = data["name_index"]
        logger.info(f"Graph loaded from {path}")

    def get_nodes_for_viz(self) -> tuple[list[dict], list[dict]]:
        """
        Get nodes and edges formatted for streamlit-agraph visualization.
        """
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("type", "concept")
            semantic_type = data.get("node_type", node_type)
            size_map = {"chapter": 30, "section": 22, "concept": 15}
            color = data.get("color", NODE_COLORS.get(semantic_type, NODE_COLORS.get(node_type, "#888")))

            nodes.append({
                "id": node_id,
                "label": data.get("label", data.get("name", node_id)),
                "size": size_map.get(node_type, 15),
                "color": color,
                "title": data.get("definition", data.get("summary", "")),
                "type": node_type,
                "node_type": semantic_type,   # semantic sub-type (question/definition/example/concept)
                "definition": data.get("definition", data.get("summary", "")),
            })

        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "label": data.get("type", ""),
                "color": "#888888",
            })

        return nodes, edges
