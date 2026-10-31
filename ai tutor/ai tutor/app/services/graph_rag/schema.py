"""
Graph Schema — Pydantic models for the Knowledge Graph.

Defines the data models matching the extraction output JSON format,
with built-in validation for dyslexia-friendly rules and referential integrity.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


ALLOWED_NODE_TYPES = {"concept", "definition", "question", "example"}


class Concept(BaseModel):
    """A knowledge concept extracted from the text."""
    concept_id: str = Field(..., description="Unique ID like K1, K2")
    name: str = Field(..., description="Short concept name")
    node_type: str = Field(default="concept", description="concept | definition | question | example")
    definition: str = Field(..., description="Dyslexia-friendly definition or full question text")
    examples: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    page_ref: Optional[int] = None
    source_section: Optional[str] = None
    source_text: str = Field(default="", description="The raw chunk text this concept was extracted from")

    @field_validator("node_type")
    @classmethod
    def validate_node_type(cls, v: str) -> str:
        v_lower = v.lower().strip()
        return v_lower if v_lower in ALLOWED_NODE_TYPES else "concept"

    @field_validator("definition")
    @classmethod
    def validate_definition(cls, v: str) -> str:
        """Ensure definition is non-empty."""
        if not v or not v.strip():
            return "No definition available."
        return v


class Section(BaseModel):
    """A document section containing concepts."""
    section_id: str = Field(..., description="Section ID like S1.1")
    title: str = Field(..., description="Section title")
    page_start: Optional[int] = None
    concepts: list[Concept] = Field(default_factory=list)


class Chapter(BaseModel):
    """A document chapter containing sections."""
    chapter_id: str = Field(..., description="Chapter ID like C1")
    title: str = Field(..., description="Chapter title")
    summary: str = Field(default="", description="One-sentence summary")
    sections: list[Section] = Field(default_factory=list)


class Relationship(BaseModel):
    """A relationship between two entities in the knowledge graph."""
    rel_id: str = Field(..., description="Relationship ID like R1")
    source: str = Field(..., description="Source entity ID")
    target: str = Field(..., description="Target entity ID")
    type: str = Field(..., description="Relationship type")
    reason: str = Field(default="", description="Why this relationship exists")
    confidence: str = Field(default="medium", description="high/medium/low")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {
            "part_of", "depends_on", "related_to", "example_of",
            "contrasts_with", "defined_in", "leads_to",
        }
        if v not in allowed:
            v_lower = v.lower().replace(" ", "_")
            if v_lower in allowed:
                return v_lower
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        v_lower = v.lower()
        return v_lower if v_lower in allowed else "medium"


class SkippedItem(BaseModel):
    """An item that could not be extracted."""
    item: str
    reason: str


class DocumentMetadata(BaseModel):
    """Metadata about the source document."""
    title: str = ""
    subject: str = ""
    processing_notes: str = ""


class KnowledgeGraph(BaseModel):
    """
    Top-level knowledge graph model.
    Represents the complete extracted knowledge from a document.
    """
    document_metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    chapters: list[Chapter] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    skipped_items: list[SkippedItem] = Field(default_factory=list)

    def get_all_concept_ids(self) -> set[str]:
        """Get all concept IDs in the graph."""
        ids = set()
        for chapter in self.chapters:
            ids.add(chapter.chapter_id)
            for section in chapter.sections:
                ids.add(section.section_id)
                for concept in section.concepts:
                    ids.add(concept.concept_id)
        return ids

    def get_all_concepts(self) -> list[Concept]:
        """Get a flat list of all concepts."""
        concepts = []
        for chapter in self.chapters:
            for section in chapter.sections:
                concepts.extend(section.concepts)
        return concepts

    def get_concept_by_id(self, concept_id: str) -> Optional[Concept]:
        """Look up a concept by its ID."""
        for chapter in self.chapters:
            for section in chapter.sections:
                for concept in section.concepts:
                    if concept.concept_id == concept_id:
                        return concept
        return None

    def validate_relationships(self) -> list[str]:
        """
        Check that all relationship sources and targets reference existing IDs.
        Returns list of error messages.
        """
        all_ids = self.get_all_concept_ids()
        errors = []
        for rel in self.relationships:
            if rel.source not in all_ids:
                errors.append(
                    f"Relationship {rel.rel_id}: source '{rel.source}' not found"
                )
            if rel.target not in all_ids:
                errors.append(
                    f"Relationship {rel.rel_id}: target '{rel.target}' not found"
                )
        return errors

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return self.model_dump()
