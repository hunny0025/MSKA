"""
A2 — Ingestion pipeline runner.

Implements the full document lifecycle:
  uploaded → extracting → scanning_pii → chunking → embedding → indexing → ready | quarantined | failed

Public interface: run_ingestion_pipeline(document_id)
Called via BackgroundTasks from the upload endpoint (A3).

Design rules:
- Every stage catches its own exceptions and transitions status to `failed`.
- PII detection quarantines the document (status = quarantined); the
  chunks still exist in the DB for auditors but the FAISS index is NOT
  populated.
- The Chunk ORM records carry the vector as a JSON column so the DB is
  always the canonical source of truth; FAISS is a read-cache.
"""
from __future__ import annotations

import json
import os
import pathlib
import logging
import traceback
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import async_session_factory
from models.document import Document, DocumentStatus
from models.chunk import Chunk
from services.document_service import update_status
from pipeline.extractors.dispatch import extract_text_from_file
from pipeline.pii_scanner import scan as pii_scan
from pipeline.chunker import chunk_text
from pipeline.embedder import embed_texts
from adapters.vectorstore.faiss_adapter import vector_store

logger = logging.getLogger("pipeline.runner")


async def run_ingestion_pipeline(document_id: str) -> None:
    """
    Entry point for background ingestion.

    Creates its own DB session (runs outside the request scope).
    All status transitions are persisted as they happen so SSE can
    stream them in real time.
    """
    async with async_session_factory() as db:
        await _run(db, document_id)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

async def _run(db: AsyncSession, document_id: str) -> None:
    doc = await _fetch_document(db, document_id)
    if not doc:
        logger.error("Pipeline: document %s not found — aborting", document_id)
        return

    # ── Stage 1: extraction ────────────────────────────────────────────────
    raw_text = await _stage_extract(db, doc)
    if raw_text is None:
        return  # status already set to `failed`

    # ── Stage 2: PII scan ──────────────────────────────────────────────────
    pii_ok = await _stage_pii(db, doc, raw_text)
    if not pii_ok:
        return  # status already set to `quarantined`

    # ── Stage 3: chunking ──────────────────────────────────────────────────
    chunks_text = await _stage_chunk(db, doc, raw_text)
    if chunks_text is None:
        return  # status already set to `failed`

    # ── Stage 4: embedding ────────────────────────────────────────────────
    vectors = await _stage_embed(db, doc, chunks_text)
    if vectors is None:
        return  # status already set to `failed`

    # ── Stage 5: DB + FAISS indexing ──────────────────────────────────────
    await _stage_index(db, doc, chunks_text, vectors)


# ---------------------------------------------------------------------------

async def _fetch_document(db: AsyncSession, document_id: str) -> Document | None:
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def _stage_extract(db: AsyncSession, doc: Document) -> str | None:
    await update_status(db, doc.id, DocumentStatus.extracting)
    logger.info("Pipeline[%s]: extracting text from %s", doc.id, doc.filename)
    try:
        suffix = pathlib.Path(doc.filename).suffix.lower()
        raw_text = extract_text_from_file(doc.file_path, suffix)
        return raw_text
    except Exception as exc:
        logger.error("Pipeline[%s]: extraction failed: %s", doc.id, exc, exc_info=True)
        await update_status(db, doc.id, DocumentStatus.failed, error=str(exc))
        return None


async def _stage_pii(db: AsyncSession, doc: Document, text: str) -> bool:
    await update_status(db, doc.id, DocumentStatus.scanning_pii)
    logger.info("Pipeline[%s]: scanning for PII", doc.id)
    try:
        result = pii_scan(text)
        if result.has_pii:
            logger.warning(
                "Pipeline[%s]: PII detected (%s) — quarantining",
                doc.id, result.matched_types,
            )
            doc.pii_flagged = True
            await db.commit()
            await update_status(
                db, doc.id, DocumentStatus.quarantined,
                error=f"PII detected: {', '.join(result.matched_types)}",
            )
            return False
        return True
    except Exception as exc:
        logger.error("Pipeline[%s]: PII scan failed: %s", doc.id, exc, exc_info=True)
        await update_status(db, doc.id, DocumentStatus.failed, error=str(exc))
        return False


async def _stage_chunk(db: AsyncSession, doc: Document, text: str) -> list[str] | None:
    await update_status(db, doc.id, DocumentStatus.chunking)
    logger.info("Pipeline[%s]: chunking text", doc.id)
    try:
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Chunker produced 0 chunks — document may be empty")
        return chunks
    except Exception as exc:
        logger.error("Pipeline[%s]: chunking failed: %s", doc.id, exc, exc_info=True)
        await update_status(db, doc.id, DocumentStatus.failed, error=str(exc))
        return None


async def _stage_embed(db: AsyncSession, doc: Document, chunks: list[str]) -> list[list[float]] | None:
    await update_status(db, doc.id, DocumentStatus.embedding)
    logger.info("Pipeline[%s]: embedding %d chunks", doc.id, len(chunks))
    try:
        vectors = embed_texts(chunks)
        return vectors
    except Exception as exc:
        logger.error("Pipeline[%s]: embedding failed: %s", doc.id, exc, exc_info=True)
        await update_status(db, doc.id, DocumentStatus.failed, error=str(exc))
        return None


async def _stage_index(
    db: AsyncSession,
    doc: Document,
    chunks: list[str],
    vectors: list[list[float]],
) -> None:
    await update_status(db, doc.id, DocumentStatus.indexing)
    logger.info("Pipeline[%s]: indexing %d chunks into DB + FAISS", doc.id, len(chunks))
    try:
        chunk_records = []
        faiss_docs = []

        for i, (chunk_text_val, vector) in enumerate(zip(chunks, vectors)):
            chunk_id = str(uuid.uuid4())
            chunk_record = Chunk(
                id=chunk_id,
                document_id=doc.id,
                project_id=doc.project_id,
                chunk_index=i,
                text=chunk_text_val,
                embedding_json=json.dumps(vector),
            )
            chunk_records.append(chunk_record)
            faiss_docs.append({
                "id": chunk_id,
                "text": chunk_text_val,
                "embedding": vector,
                "metadata": {
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "classification": doc.classification,
                    "department_id": doc.department_id,
                    "chunk_index": i,
                },
            })

        # Persist to relational DB
        db.add_all(chunk_records)
        await db.flush()

        # Persist to FAISS (project-scoped namespace)
        vector_store.add_documents(doc.project_id, faiss_docs)

        # Mark document ready
        doc.chunk_count = len(chunk_records)
        await db.commit()
        await update_status(db, doc.id, DocumentStatus.ready)
        logger.info("Pipeline[%s]: READY — %d chunks indexed", doc.id, len(chunk_records))

    except Exception as exc:
        logger.error("Pipeline[%s]: indexing failed: %s", doc.id, exc, exc_info=True)
        await update_status(db, doc.id, DocumentStatus.failed, error=str(exc))
