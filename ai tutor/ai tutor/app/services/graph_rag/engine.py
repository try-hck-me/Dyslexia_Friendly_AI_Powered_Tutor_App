"""
Query Engine — Abstraction layer over graph storage for knowledge queries.

Provides high-level query types:
- Concept lookup
- Prerequisites chain
- Learning path
- Explore neighbors
- Chapter summary
- Keyword search
- Hybrid semantic + graph retrieval (HybridRetriever)

The HybridRetriever uses DUAL collections:
  Path A — Graph nodes collection → graph hop expansion → rich structured context
  Path B — Raw chunks collection  → lossless exact text fallback

Both paths are merged and deduplicated before returning context to the LLM.
"""

import logging
from typing import Optional

import networkx as nx

from app.services.graph_rag.store import NetworkXStore
from app.services.graph_rag.schema import KnowledgeGraph


class HybridRetrieverNotReadyError(Exception):
    pass


logger = logging.getLogger(__name__)


class QueryResult:
    """Structured query result."""

    def __init__(
        self,
        query_type: str,
        query: str,
        results: list[dict] | dict,
        message: str = "",
        success: bool = True,
    ):
        self.query_type = query_type
        self.query = query
        self.results = results
        self.message = message
        self.success = success

    def to_dict(self) -> dict:
        return {
            "query_type": self.query_type,
            "query": self.query,
            "results": self.results,
            "message": self.message,
            "success": self.success,
        }


class QueryEngine:
    """
    High-level query interface over the knowledge graph.

    Wraps NetworkXStore with user-friendly query methods.
    """

    def __init__(self, store: Optional[NetworkXStore] = None):
        self.store = store or NetworkXStore()

    def load_graph(self, kg: KnowledgeGraph):
        """Load a knowledge graph into the store."""
        self.store.load_from_knowledge_graph(kg)

    def load_from_pickle(self, path: str):
        """Load graph from a pickle file."""
        self.store.load_pickle(path)

    def concept_lookup(self, name_or_id: str) -> QueryResult:
        """Look up a concept by name or ID."""
        concept = self.store.get_concept(name_or_id)
        if concept:
            related = self.store.get_related(
                name_or_id if name_or_id.startswith("K") else
                self.store._name_index.get(name_or_id.lower(), name_or_id)
            )
            concept["related_concepts"] = [
                {"name": r.get("name", ""), "relationship": r.get("relationship", "")}
                for r in related[:5]
            ]
            return QueryResult(
                query_type="concept_lookup",
                query=name_or_id,
                results=concept,
                message=f"Found concept: {concept.get('name', name_or_id)}",
            )

        search_results = self.store.search(name_or_id, limit=5)
        if search_results:
            return QueryResult(
                query_type="concept_lookup",
                query=name_or_id,
                results=search_results,
                message="No exact match. Did you mean one of these?",
            )

        return QueryResult(
            query_type="concept_lookup",
            query=name_or_id,
            results={},
            message=f"Concept '{name_or_id}' not found.",
            success=False,
        )

    def prerequisites(self, concept_name_or_id: str) -> QueryResult:
        """Get prerequisite concepts."""
        concept_id = concept_name_or_id
        if not concept_name_or_id.startswith("K"):
            concept_id = self.store._name_index.get(
                concept_name_or_id.lower(), concept_name_or_id
            )

        prereqs = self.store.get_prerequisites(concept_id)
        if prereqs:
            return QueryResult(
                query_type="prerequisites",
                query=concept_name_or_id,
                results=prereqs,
                message=f"Found {len(prereqs)} prerequisite(s) for '{concept_name_or_id}'",
            )

        return QueryResult(
            query_type="prerequisites",
            query=concept_name_or_id,
            results=[],
            message=f"No prerequisites found for '{concept_name_or_id}'.",
        )

    def learning_path(self, from_concept: str, to_concept: str) -> QueryResult:
        """Compute a learning path between two concepts."""
        from_id = from_concept
        to_id = to_concept
        if not from_concept.startswith(("K", "C", "S")):
            from_id = self.store._name_index.get(from_concept.lower(), from_concept)
        if not to_concept.startswith(("K", "C", "S")):
            to_id = self.store._name_index.get(to_concept.lower(), to_concept)

        path = self.store.get_learning_path(from_id, to_id)
        if path:
            return QueryResult(
                query_type="learning_path",
                query=f"{from_concept} → {to_concept}",
                results=path,
                message=f"Learning path: {len(path)} steps from '{from_concept}' to '{to_concept}'",
            )

        return QueryResult(
            query_type="learning_path",
            query=f"{from_concept} → {to_concept}",
            results=[],
            message=f"No path found between '{from_concept}' and '{to_concept}'.",
            success=False,
        )

    def explore(self, concept_name_or_id: str) -> QueryResult:
        """Explore the neighborhood of a concept."""
        concept_id = concept_name_or_id
        if not concept_name_or_id.startswith("K"):
            concept_id = self.store._name_index.get(
                concept_name_or_id.lower(), concept_name_or_id
            )

        related = self.store.get_related(concept_id)
        if related:
            return QueryResult(
                query_type="explore",
                query=concept_name_or_id,
                results=related,
                message=f"Found {len(related)} related concept(s)",
            )

        return QueryResult(
            query_type="explore",
            query=concept_name_or_id,
            results=[],
            message=f"No related concepts found for '{concept_name_or_id}'.",
        )

    def chapter_summary(self, chapter_id: str) -> QueryResult:
        """Get a summary of a chapter with all its concepts."""
        summary = self.store.get_chapter_summary(chapter_id)
        if summary:
            return QueryResult(
                query_type="chapter_summary",
                query=chapter_id,
                results=summary,
                message=f"Chapter: {summary['title']} ({len(summary['concepts'])} concepts)",
            )

        return QueryResult(
            query_type="chapter_summary",
            query=chapter_id,
            results={},
            message=f"Chapter '{chapter_id}' not found.",
            success=False,
        )

    def search(self, keyword: str) -> QueryResult:
        """Search for concepts by keyword."""
        results = self.store.search(keyword)
        return QueryResult(
            query_type="search",
            query=keyword,
            results=results,
            message=f"Found {len(results)} result(s) for '{keyword}'",
            success=len(results) > 0,
        )

    def get_all_chapters(self) -> list[dict]:
        """Get a list of all chapters for navigation."""
        chapters = []
        for node_id, data in self.store.graph.nodes(data=True):
            if data.get("type") == "chapter":
                chapters.append({
                    "chapter_id": node_id,
                    "title": data.get("title", ""),
                    "summary": data.get("summary", ""),
                })
        return sorted(chapters, key=lambda c: c["chapter_id"])

    def get_stats(self) -> dict:
        """Get graph statistics."""
        return self.store.get_graph_stats()


# ============================================================
# Hybrid Graph RAG Retriever (REDESIGNED)
# ============================================================


class HybridRetriever:
    """
    Dual-path hybrid retriever combining:
      Path A — Graph node embeddings → graph hop expansion → structured context
      Path B — Raw chunk embeddings  → exact text passages (lossless fallback)

    Flow:
      1. Encode question with sentence-transformer.
      2a. Query graph_nodes ChromaDB → get seed concept IDs.
           → BFS expand seed nodes in NetworkX for `hops` hops.
           → For each collected node, assemble: name + definition + source_text.
      2b. Query raw_chunks ChromaDB → get top-k raw text passages.
      3. Merge both paths: graph context first, then append unique raw passages.
      4. Deduplicate by text fingerprint.
      5. Return merged context string + entity names.
    """

    def __init__(
        self,
        store: NetworkXStore,
        graph_nodes_collection,       # ChromaDB collection: graph_concept_nodes
        raw_chunks_collection,        # ChromaDB collection: raw_study_chunks
        embed_model,
    ):
        self.store = store
        self.graph_collection = graph_nodes_collection
        self.raw_collection = raw_chunks_collection
        self.embed_model = embed_model

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        hops: int = 3,
    ) -> tuple[str, list[str]]:
        """
        Retrieve rich context for a question using dual-path retrieval.

        Args:
            question: The student's natural-language question.
            top_k: Number of seed nodes / raw chunks to retrieve.
            hops: Graph traversal hops from each seed node.

        Returns:
            Tuple of (context_string, entity_names_list).

        Raises:
            HybridRetrieverNotReadyError: If both collections are empty.
        """
        graph_empty = self.graph_collection.count() == 0
        raw_empty = self.raw_collection.count() == 0

        if graph_empty and raw_empty:
            raise HybridRetrieverNotReadyError(
                "No study material found. Please upload a PDF first."
            )

        query_embedding = self.embed_model.encode(question).tolist()

        context_parts: list[str] = []
        entity_names: list[str] = []
        seen_fingerprints: set[str] = set()

        # ── Path A: Graph Nodes ──
        graph_context_parts: list[str] = []

        if not graph_empty:
            try:
                graph_results = self.graph_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, self.graph_collection.count()),
                )
                seed_ids: list[str] = graph_results["ids"][0] if graph_results["ids"] else []

                # Expand seeds via BFS in graph
                collected_node_ids: set[str] = set()
                for seed_id in seed_ids:
                    if not self.store.graph.has_node(seed_id):
                        resolved = self.store._name_index.get(seed_id.lower())
                        if resolved and self.store.graph.has_node(resolved):
                            seed_id = resolved
                        else:
                            continue
                    collected_node_ids.add(seed_id)
                    self._bfs_collect(seed_id, hops, collected_node_ids)

                # Prioritize: seed nodes first (serve their source_text),
                # then neighbors (serve their definition)
                ordered_ids = list(seed_ids) + [
                    nid for nid in collected_node_ids if nid not in seed_ids
                ]

                for node_id in ordered_ids:
                    node_data = self.store.graph.nodes.get(node_id, {})
                    if node_data.get("type") != "concept":
                        continue

                    name = node_data.get("name", "")
                    definition = node_data.get("definition", "")
                    examples = node_data.get("examples", [])
                    source_text = node_data.get("source_text", "")
                    node_type = node_data.get("node_type", "concept")

                    parts = []
                    if name:
                        label = f"[{node_type.upper()}] {name}" if node_type != "concept" else f"**{name}**"
                        parts.append(label)

                    # For seed nodes: use the full raw source text
                    if node_id in seed_ids and source_text:
                        parts.append(source_text)
                    else:
                        # For neighbors: definition is sufficient to save tokens
                        if definition:
                            parts.append(definition)
                        if examples:
                            parts.append("Examples: " + "; ".join(examples))

                    text_block = "\n".join(parts)
                    fingerprint = text_block[:200]
                    if text_block and fingerprint not in seen_fingerprints:
                        seen_fingerprints.add(fingerprint)
                        graph_context_parts.append(text_block)
                        if name:
                            entity_names.append(name)

            except Exception as e:
                logger.warning(f"Graph path retrieval error (will use raw fallback): {e}")

        # ── Path B: Raw Chunks ──
        raw_context_parts: list[str] = []

        if not raw_empty:
            try:
                raw_results = self.raw_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=min(top_k, self.raw_collection.count()),
                    include=["documents", "metadatas"],
                )
                raw_docs = raw_results["documents"][0] if raw_results["documents"] else []
                raw_metas = raw_results["metadatas"][0] if raw_results["metadatas"] else []

                for i, doc in enumerate(raw_docs):
                    if not doc or not doc.strip():
                        continue
                    heading = ""
                    if i < len(raw_metas) and raw_metas[i]:
                        heading = raw_metas[i].get("heading", "")

                    label = f"[{heading}]\n" if heading else ""
                    text_block = label + doc.strip()
                    fingerprint = text_block[:200]
                    if fingerprint not in seen_fingerprints:
                        seen_fingerprints.add(fingerprint)
                        raw_context_parts.append(text_block)

            except Exception as e:
                logger.warning(f"Raw chunk retrieval error: {e}")

        # ── Merge ──
        # If graph path found content, use it first; then append unique raw chunks
        # If graph path found nothing, use raw chunks only
        if graph_context_parts:
            context_parts = graph_context_parts + raw_context_parts
        else:
            context_parts = raw_context_parts
            logger.info("Graph context empty — using raw chunk fallback only.")

        if not context_parts:
            return "", []

        context_string = "\n\n---\n\n".join(context_parts)
        return context_string, entity_names

    def _bfs_collect(
        self, start_id: str, max_hops: int, collected: set[str]
    ) -> None:
        """BFS traversal from start_id, collecting node IDs up to max_hops."""
        frontier = {start_id}
        for _ in range(max_hops):
            next_frontier: set[str] = set()
            for node_id in frontier:
                for neighbor in self.store.graph.successors(node_id):
                    if neighbor not in collected:
                        collected.add(neighbor)
                        next_frontier.add(neighbor)
                for neighbor in self.store.graph.predecessors(node_id):
                    if neighbor not in collected:
                        collected.add(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier
            if not frontier:
                break


def index_graph_to_chromadb(
    store: NetworkXStore,
    chroma_collection,
    embed_model,
) -> int:
    """
    Index all concept nodes from a NetworkX graph into the graph_nodes ChromaDB collection.

    For each concept node, creates an embedding of:
      "[node_type] [name]: [definition] Keywords: [keywords] Source: [source_text snippet]"

    This richer embedding improves semantic search quality.

    Args:
        store: A loaded NetworkXStore with the knowledge graph.
        chroma_collection: ChromaDB collection for graph nodes.
        embed_model: SentenceTransformer model for encoding.

    Returns:
        Number of concepts indexed.
    """
    ids: list[str] = []
    documents: list[str] = []

    for node_id, data in store.graph.nodes(data=True):
        if data.get("type") != "concept":
            continue

        name = data.get("name", "")
        definition = data.get("definition", "")
        keywords = data.get("keywords", [])
        source_text = data.get("source_text", "")
        node_type = data.get("node_type", "concept")

        text_parts = []
        if node_type and node_type != "concept":
            text_parts.append(f"[{node_type}]")
        if name:
            text_parts.append(f"Concept: {name}")
        if definition:
            text_parts.append(f"Definition: {definition}")
        if keywords:
            text_parts.append("Keywords: " + ", ".join(keywords))
        # Include only first 300 chars of source_text to keep embedding focused
        if source_text:
            text_parts.append(f"Source: {source_text[:300]}")

        doc_text = "\n".join(text_parts) if text_parts else node_id

        ids.append(node_id)
        documents.append(doc_text)

    if not ids:
        logger.warning("No concept nodes found to index.")
        return 0

    logger.info(f"Encoding {len(ids)} concepts for ChromaDB indexing...")
    raw_embeddings = embed_model.encode(documents, show_progress_bar=False)
    embeddings = [emb.tolist() for emb in raw_embeddings]

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end = min(i + batch_size, len(ids))
        chroma_collection.upsert(
            ids=ids[i:end],
            documents=documents[i:end],
            embeddings=embeddings[i:end],
        )

    logger.info(f"Indexed {len(ids)} concepts into graph nodes ChromaDB collection.")
    return len(ids)
