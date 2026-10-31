"""
Graph Builder — Merges per-chunk extraction results into a unified Knowledge Graph.

Handles deduplication, ID conflict resolution, and automatic
part_of relationship generation from the document hierarchy.
"""

import logging
from typing import Optional

from app.services.graph_rag.schema import (
    KnowledgeGraph, Chapter, Section, Concept,
    Relationship, SkippedItem, DocumentMetadata,
)

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Merges multiple per-chunk extraction results into a single
    unified KnowledgeGraph.

    Handles:
    - Deduplication of concepts with the same name
    - ID conflict resolution across chunks
    - Automatic part_of relationship generation
    - Final validation
    """

    def __init__(self):
        self._chapters: dict[str, Chapter] = {}
        self._sections: dict[str, Section] = {}
        self._concepts: dict[str, Concept] = {}
        self._relationships: list[Relationship] = []
        self._skipped: list[SkippedItem] = []
        self._metadata: DocumentMetadata = DocumentMetadata()
        self._concept_name_map: dict[str, str] = {}  # name -> concept_id
        self._id_remap: dict[str, str] = {}  # old_id -> new_id
        self._rel_counter = 0
        self._concept_counter = 0

    def _ensure_unique_concept_id(self, concept_id: str) -> str:
        """Generate a new unique concept ID if there's a conflict."""
        if concept_id not in self._concepts:
            return concept_id

        # Conflict! Generate new ID
        self._concept_counter += 1
        new_id = f"K{self._concept_counter}"
        while new_id in self._concepts:
            self._concept_counter += 1
            new_id = f"K{self._concept_counter}"

        self._id_remap[concept_id] = new_id
        return new_id

    def _remap_id(self, old_id: str) -> str:
        """Get the remapped ID if one exists."""
        return self._id_remap.get(old_id, old_id)

    def _merge_concept(self, concept: Concept, section_id: str) -> Optional[str]:
        """
        Add a concept, merging with existing if same name exists.

        Returns the final concept_id used.
        """
        name_lower = concept.name.lower().strip()

        # Check if we already have a concept with this name
        if name_lower in self._concept_name_map:
            existing_id = self._concept_name_map[name_lower]
            existing = self._concepts[existing_id]

            # Merge examples
            for ex in concept.examples:
                if ex not in existing.examples:
                    existing.examples.append(ex)

            # Merge keywords
            for kw in concept.keywords:
                if kw not in existing.keywords:
                    existing.keywords.append(kw)

            # Keep the longer/better definition
            if len(concept.definition) > len(existing.definition):
                existing.definition = concept.definition

            # Map this concept's ID to the existing one
            if concept.concept_id != existing_id:
                self._id_remap[concept.concept_id] = existing_id

            return existing_id

        # New concept
        final_id = self._ensure_unique_concept_id(concept.concept_id)
        concept.concept_id = final_id
        concept.source_section = section_id
        self._concepts[final_id] = concept
        self._concept_name_map[name_lower] = final_id

        # Track max concept number for future IDs
        try:
            num = int(final_id.replace("K", ""))
            self._concept_counter = max(self._concept_counter, num)
        except ValueError:
            pass

        return final_id

    def add_extraction_result(self, result: dict):
        """
        Add a single chunk's extraction result to the builder.

        Args:
            result: The parsed JSON dict from the LLM extraction.
        """
        if not result:
            return

        # Update metadata (keep the most informative one)
        meta = result.get("document_metadata", {})
        if meta.get("title") and not self._metadata.title:
            self._metadata.title = meta["title"]
        if meta.get("subject") and not self._metadata.subject:
            self._metadata.subject = meta["subject"]

        # Process chapters
        for ch_data in result.get("chapters", []):
            ch_id = ch_data.get("chapter_id", "")
            if not ch_id:
                continue

            if ch_id not in self._chapters:
                self._chapters[ch_id] = Chapter(
                    chapter_id=ch_id,
                    title=ch_data.get("title", ""),
                    summary=ch_data.get("summary", ""),
                    sections=[],
                )

            # Process sections within this chapter
            for sec_data in ch_data.get("sections", []):
                sec_id = sec_data.get("section_id", "")
                if not sec_id:
                    continue

                if sec_id not in self._sections:
                    self._sections[sec_id] = Section(
                        section_id=sec_id,
                        title=sec_data.get("title", ""),
                        page_start=sec_data.get("page_start"),
                        concepts=[],
                    )

                # Process concepts within this section
                for concept_data in sec_data.get("concepts", []):
                    try:
                        concept_data["source_text"] = result.get("chunk_text", "")
                        concept = Concept(**concept_data)
                        self._merge_concept(concept, sec_id)
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse concept: {concept_data.get('name', '?')}: {e}"
                        )

        # Process relationships (remap IDs)
        for rel_data in result.get("relationships", []):
            try:
                self._rel_counter += 1
                rel = Relationship(
                    rel_id=f"R{self._rel_counter}",
                    source=self._remap_id(rel_data.get("source", "")),
                    target=self._remap_id(rel_data.get("target", "")),
                    type=rel_data.get("type", "related_to"),
                    reason=rel_data.get("reason", ""),
                    confidence=rel_data.get("confidence", "medium"),
                )
                self._relationships.append(rel)
            except Exception as e:
                logger.warning(f"Failed to parse relationship: {e}")

        # Collect skipped items
        for skip in result.get("skipped_items", []):
            self._skipped.append(SkippedItem(
                item=skip.get("item", ""),
                reason=skip.get("reason", ""),
            ))

    def _generate_hierarchy_relationships(self):
        """
        Auto-generate part_of relationships from the chapter/section hierarchy.
        """
        for ch_id, chapter in self._chapters.items():
            for section in chapter.sections:
                # Section part_of Chapter
                self._rel_counter += 1
                self._relationships.append(Relationship(
                    rel_id=f"R{self._rel_counter}",
                    source=section.section_id,
                    target=ch_id,
                    type="part_of",
                    reason=f"{section.title} is a section within {chapter.title}",
                    confidence="high",
                ))

                # Concepts defined_in Section
                for concept in section.concepts:
                    self._rel_counter += 1
                    self._relationships.append(Relationship(
                        rel_id=f"R{self._rel_counter}",
                        source=concept.concept_id,
                        target=section.section_id,
                        type="defined_in",
                        reason=f"{concept.name} is defined in {section.title}",
                        confidence="high",
                    ))

    def _assign_concepts_to_sections(self):
        """Assign concepts to their respective sections in the chapter tree."""
        for sec_id, section in self._sections.items():
            section.concepts = [
                c for c in self._concepts.values()
                if c.source_section == sec_id
            ]

        # Assign sections to chapters
        for ch_id, chapter in self._chapters.items():
            ch_num = ch_id.replace("C", "")
            chapter.sections = [
                s for s_id, s in sorted(self._sections.items())
                if s_id.startswith(f"S{ch_num}.")
            ]

    def build(self) -> KnowledgeGraph:
        """
        Build the final unified KnowledgeGraph.

        Returns:
            Complete, validated KnowledgeGraph instance.
        """
        # Assign concepts to sections and sections to chapters
        self._assign_concepts_to_sections()

        # Generate hierarchy relationships
        self._generate_hierarchy_relationships()

        # Deduplicate relationships
        seen_rels = set()
        unique_rels = []
        for rel in self._relationships:
            key = (rel.source, rel.target, rel.type)
            if key not in seen_rels:
                seen_rels.add(key)
                unique_rels.append(rel)

        # Build the graph
        kg = KnowledgeGraph(
            document_metadata=self._metadata,
            chapters=sorted(self._chapters.values(), key=lambda c: c.chapter_id),
            relationships=unique_rels,
            skipped_items=self._skipped,
        )

        # Validate
        errors = kg.validate_relationships()
        if errors:
            logger.warning(f"Relationship validation: {len(errors)} issues found")
            for err in errors[:10]:
                logger.warning(f"  {err}")

            # Remove invalid relationships
            all_ids = kg.get_all_concept_ids()
            kg.relationships = [
                r for r in kg.relationships
                if r.source in all_ids and r.target in all_ids
            ]

        total_concepts = len(kg.get_all_concepts())
        logger.info(
            f"Knowledge graph built: "
            f"{len(kg.chapters)} chapters, "
            f"{sum(len(c.sections) for c in kg.chapters)} sections, "
            f"{total_concepts} concepts, "
            f"{len(kg.relationships)} relationships"
        )

        return kg


def build_knowledge_graph(extraction_results: list[dict]) -> KnowledgeGraph:
    """
    Convenience function to build a KnowledgeGraph from extraction results.

    Args:
        extraction_results: List of per-chunk JSON dicts from the extractor.

    Returns:
        Unified KnowledgeGraph.
    """
    builder = GraphBuilder()
    for result in extraction_results:
        builder.add_extraction_result(result)
    return builder.build()
