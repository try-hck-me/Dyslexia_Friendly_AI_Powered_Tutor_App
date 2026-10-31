"""
Upload API — PDF upload and processing endpoint.

Processing pipeline:
  1. Extract text from PDF
  2. Section-aware chunking (respects chapter/section headings)
  3. Store raw chunks in ChromaDB (lossless fallback)
  4. LLM-based knowledge graph extraction (ALL chunks, no artificial limit)
  5. Build NetworkX graph and save to disk
  6. Index graph concept nodes into ChromaDB
  7. Reset global retriever so next query gets fresh data
"""

import logging
import time
import os
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.services.pdf_loader import extract_text_from_pdf
from app.services.chunker import chunk_by_sections
from app.services.vector_store import add_raw_chunks, get_collection, get_raw_chunks_collection, GRAPH_NODES_COLLECTION
from app.utils.formatter import build_response
from app.services.graph_rag.extractor import Extractor
from app.services.graph_rag.builder import build_knowledge_graph
from app.services.graph_rag.engine import index_graph_to_chromadb
from app.services.graph_service import get_store, save_global_store, reset_store
from app.services.embedding import get_model

logger = logging.getLogger(__name__)
router = APIRouter()

# Global dict to track upload progress per filename
PROGRESS_TRACKER: dict[str, dict] = {}


def update_progress(
    filename: str,
    progress: float,
    status: str,
    completed: bool = False,
    error: str | None = None,
):
    """Helper to update the global progress tracker."""
    PROGRESS_TRACKER[filename] = {
        "progress": progress,
        "status": status,
        "completed": completed,
        "error": error,
    }
    logger.info(f"Progress [{filename}]: {progress:.0f}% - {status}")


def process_pdf_background(file_bytes: bytes, filename: str):
    """
    Background task to:
      1. Extract text from PDF
      2. Section-aware chunk
      3. Store raw chunks (lossless)
      4. Extract knowledge graph from ALL chunks
      5. Build graph, save to disk
      6. Index graph nodes into ChromaDB
      7. Reset retriever singletons
    """
    try:
        # ── Step 1: Extract text ──────────────────────────────────────────
        update_progress(filename, 5, "Extracting text from PDF...")
        text = extract_text_from_pdf(file_bytes)
        if not text.strip():
            update_progress(filename, 100, "Failed: No text found in PDF", error="No text extracted")
            return

        char_count = len(text)
        update_progress(filename, 12, f"Text extracted ({char_count:,} chars). Splitting into sections...")

        # ── Step 2: Section-aware chunking ───────────────────────────────
        chunks = chunk_by_sections(
            text=text,
            source=filename,
            max_words_per_chunk=600,
            overlap_words=80,
        )

        if not chunks:
            update_progress(filename, 100, "Failed: Text too short to process", error="Text too short")
            return

        total_chunks = len(chunks)
        update_progress(filename, 18, f"Created {total_chunks} chunks. Storing raw content...")

        # ── Step 3: Store raw chunks (lossless fallback) ──────────────────
        raw_collection = get_raw_chunks_collection()
        # Clear old data for this source before inserting fresh data
        try:
            existing = raw_collection.get(where={"source": filename})
            if existing and existing["ids"]:
                raw_collection.delete(ids=existing["ids"])
                logger.info(f"Cleared {len(existing['ids'])} old raw chunks for '{filename}'")
        except Exception as e:
            logger.warning(f"Could not clear old raw chunks: {e}")

        num_raw = add_raw_chunks(chunks)
        update_progress(filename, 28, f"Stored {num_raw} raw chunks. Starting knowledge graph extraction...")

        # ── Step 4: LLM extraction from ALL chunks ────────────────────────
        extractor = Extractor()
        extraction_results = []

        for i, chunk in enumerate(chunks, 1):
            # Scale progress: 28% → 80%
            progress_pct = 28 + (i / total_chunks) * 52
            update_progress(
                filename,
                progress_pct,
                f"Extracting concepts (chunk {i}/{total_chunks})...",
            )
            res = extractor.extract_chunk(chunk, i, total_chunks)
            extraction_results.append(res)
            # Small delay to respect Groq rate limits
            time.sleep(0.8)

        update_progress(filename, 82, "Building knowledge graph structure...")

        # ── Step 5: Build Knowledge Graph ────────────────────────────────
        kg = build_knowledge_graph(extraction_results)
        total_concepts = len(kg.get_all_concepts())
        logger.info(f"Knowledge graph: {len(kg.chapters)} chapters, {total_concepts} concepts")

        # ── Step 6: Load into NetworkX and save ───────────────────────────
        store = get_store()
        store.load_from_knowledge_graph(kg)
        save_global_store()

        update_progress(filename, 88, f"Graph built ({total_concepts} concepts). Indexing into vector DB...")

        # ── Step 7: Index graph nodes into ChromaDB ───────────────────────
        graph_nodes_collection = get_collection(GRAPH_NODES_COLLECTION)
        embed_model = get_model()
        num_indexed = index_graph_to_chromadb(store, graph_nodes_collection, embed_model)

        # ── Step 8: Reset retriever so next query sees fresh data ──────────
        reset_store()

        update_progress(
            filename,
            100,
            f"Complete! {total_chunks} chunks stored, {num_indexed} concepts indexed.",
            completed=True,
        )
        logger.info(f"Upload complete for '{filename}': {total_chunks} chunks, {num_indexed} graph concepts.")

    except Exception as e:
        logger.error(f"Background upload failed for '{filename}': {e}", exc_info=True)
        update_progress(filename, 100, f"Error: {str(e)}", error=str(e))


@router.post("/upload")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload a PDF file for processing (Asynchronous).

    - Validates file and reads bytes
    - Immediately returns accepted status
    - Extracts, chunks, embeds, and builds knowledge graph in background
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported. Please upload a .pdf file.",
        )

    try:
        file_bytes = await file.read()

        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Save the physical PDF file to the uploads directory for serving to the frontend
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        PROGRESS_TRACKER[file.filename] = {"progress": 0, "status": "Initiating...", "completed": False}
        background_tasks.add_task(process_pdf_background, file_bytes, file.filename)

        return build_response(
            success=True,
            message=f"PDF '{file.filename}' upload started. Processing all pages.",
            data={
                "filename": file.filename,
                "status": "processing",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload initialization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate PDF upload: {str(e)}")


@router.get("/upload/status/{filename}")
async def get_upload_status(filename: str):
    """Get the current progress of a background processing task."""
    if filename not in PROGRESS_TRACKER:
        return build_response(
            success=False,
            message="No task found for this filename.",
            data={"progress": 0, "status": "Not found", "completed": False},
        )
    return build_response(success=True, data=PROGRESS_TRACKER[filename])


@router.get("/documents")
async def list_documents():
    """
    Return the list of source document filenames that have been indexed
    into ChromaDB (raw_study_chunks collection).

    This is the ground-truth list of what the AI can actually answer
    questions about — independent of browser localStorage state.
    """
    try:
        from app.services.vector_store import get_raw_chunks_collection

        collection = get_raw_chunks_collection()
        count = collection.count()

        if count == 0:
            return build_response(
                success=True,
                data={"documents": [], "total_chunks": 0},
            )

        # Retrieve all metadata to extract unique source filenames
        # We fetch in batches to avoid memory issues with large collections
        batch_size = 500
        all_sources: set[str] = set()

        for offset in range(0, count, batch_size):
            result = collection.get(
                limit=batch_size,
                offset=offset,
                include=["metadatas"],
            )
            for meta in (result.get("metadatas") or []):
                if meta and meta.get("source"):
                    all_sources.add(meta["source"])

        documents = sorted(all_sources)
        return build_response(
            success=True,
            data={
                "documents": documents,
                "total_chunks": count,
            },
        )

    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        return build_response(
            success=False,
            error=str(e),
            data={"documents": [], "total_chunks": 0},
        )


@router.get("/documents/{filename}/content")
async def get_document_content(filename: str):
    """
    Get the full reconstructed text content of a specific document 
    by retrieving all its raw chunks from ChromaDB and sorting them.
    """
    try:
        from app.services.vector_store import get_raw_chunks_collection
        collection = get_raw_chunks_collection()
        
        # Get all chunks for this source
        result = collection.get(
            where={"source": filename},
            include=["documents", "metadatas"]
        )
        
        if not result or not result["documents"]:
            return build_response(
                success=False,
                message=f"No content found for document '{filename}'",
                data={"text": "", "chunks": 0}
            )
            
        # Reconstruct chunks with their metadata so we can sort them
        chunks_data = []
        for i, doc in enumerate(result["documents"]):
            meta = result["metadatas"][i] if result["metadatas"] else {}
            chunks_data.append({
                "text": doc,
                "chunk_index": meta.get("chunk_index", 0)
            })
            
        # Sort by chunk_index to ensure correct reading order
        chunks_data.sort(key=lambda x: x["chunk_index"])
        
        # Combine text
        full_text = "\n\n".join(c["text"] for c in chunks_data)
        
        return build_response(
            success=True,
            data={
                "text": full_text,
                "chunks": len(chunks_data)
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching document content: {e}", exc_info=True)
        return build_response(
            success=False,
            error=str(e),
            data={"text": "", "chunks": 0}
        )

@router.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Delete a document and all its associated chunks from ChromaDB.
    Also clears the global store so the next query will be fresh.
    """
    try:
        from app.services.vector_store import get_raw_chunks_collection
        from app.services.graph_service import reset_store
        
        raw_collection = get_raw_chunks_collection()
        existing = raw_collection.get(where={"source": filename})
        
        if not existing or not existing["ids"]:
            return build_response(
                success=False,
                message=f"Document '{filename}' not found.",
            )
            
        # Delete chunks
        raw_collection.delete(ids=existing["ids"])
        logger.info(f"Deleted {len(existing['ids'])} chunks for '{filename}'")
        
        # Reset the global retriever to pick up changes
        reset_store()
        
        # Delete the physical file if it exists
        upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "uploads")
        file_path = os.path.join(upload_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Deleted physical file '{filename}'")
        
        return build_response(
            success=True,
            message=f"Document '{filename}' successfully deleted."
        )
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
        return build_response(
            success=False,
            error=str(e)
        )

