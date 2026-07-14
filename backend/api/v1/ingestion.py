"""
A3 — Document upload endpoint + SSE progress stream.

Routes:
  POST /api/v1/projects/{project_id}/documents
      Saves the file, creates the Document row (status=uploaded),
      schedules run_ingestion_pipeline via BackgroundTasks, and returns 202.

  GET  /api/v1/documents/{document_id}/progress
      SSE stream: polls status_history for new rows every 0.8 s and emits
      one JSON event per new transition until status is terminal
      (ready | quarantined | failed).
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import uuid
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from core.config import get_settings
from core.database import get_db, async_session_factory
from core.permissions import PermissionChecker, Roles, get_current_user
from models.document import Document, DocumentStatus
from models.status_history import StatusHistory
from models.user import User
from schemas.document import DocumentOut
from services.document_service import get_documents_by_project, get_document_by_id

router = APIRouter(tags=["Documents v2"])

settings = get_settings()

# Terminal statuses — SSE closes when one of these is reached
_TERMINAL = {DocumentStatus.READY.value, DocumentStatus.QUARANTINED.value, DocumentStatus.FAILED.value}


# ─────────────────────────────────────────────────────────────────────────────
# Upload
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/projects/{project_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def api_upload_document(
    project_id: str,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.PROJECT_ADMIN, Roles.DEPARTMENT_LEAD]))],
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document and schedule background ingestion.

    Returns 202 immediately with status=uploaded so the client can start
    polling the SSE progress endpoint.
    """
    from pipeline.runner import run_ingestion_pipeline
    from pipeline.extractors.dispatch import SUPPORTED_SUFFIXES

    filename = file.filename or "upload"
    suffix = pathlib.Path(filename).suffix.lower()

    if suffix not in SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{suffix}' is not supported. Accepted: {SUPPORTED_SUFFIXES}",
        )

    # Read bytes and persist to disk
    content = await file.read()
    os.makedirs(settings.file_storage_path, exist_ok=True)

    doc_id = str(uuid.uuid4())
    storage_filename = f"{project_id}_{doc_id}{suffix}"
    filepath = os.path.join(settings.file_storage_path, storage_filename)

    try:
        with open(filepath, "wb") as fh:
            fh.write(content)
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not write file to storage: {exc}",
        )

    # Determine version
    version_q = (
        select(Document)
        .where(and_(Document.filename == filename, Document.project_id == project_id))
        .order_by(Document.version.desc())
    )
    res = await db.execute(version_q)
    prev = res.scalars().first()
    version = (prev.version + 1) if prev else 1

    # Create DB record
    doc = Document(
        id=doc_id,
        filename=filename,
        filepath=filepath,
        classification="internal",
        pii_flagged=False,
        status=DocumentStatus.UPLOADED.value,
        version=version,
        project_id=project_id,
        department_id=current_user.department_id if hasattr(current_user, "department_id") and current_user.department_id else project_id,
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Schedule background ingestion (A2 runner)
    background_tasks.add_task(run_ingestion_pipeline, doc_id)

    return doc


# ─────────────────────────────────────────────────────────────────────────────
# SSE Progress
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/documents/{document_id}/progress")
async def api_document_progress(
    document_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    SSE stream delivering document ingestion progress events.

    Each event:
        data: {"status": "chunking", "message": null, "ts": "2024-..."}

    Closes automatically when status reaches ready | quarantined | failed.
    Client must reconnect on 404 (document not yet created).
    """
    return StreamingResponse(
        _progress_generator(document_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


async def _progress_generator(document_id: str) -> AsyncGenerator[str, None]:
    """Polls StatusHistory for new rows and yields SSE-formatted events."""
    last_seen_id: str | None = None
    timeout_seconds = 300  # 5 min safety cap
    elapsed = 0.0
    interval = 0.8  # poll interval

    while elapsed < timeout_seconds:
        async with async_session_factory() as db:
            # Check document exists
            doc_res = await db.execute(select(Document).where(Document.id == document_id))
            doc = doc_res.scalar_one_or_none()

            if not doc:
                yield _sse_event({"status": "pending", "message": "Waiting for document creation..."})
                await asyncio.sleep(interval)
                elapsed += interval
                continue

            # Fetch history rows newer than last_seen
            hist_q = (
                select(StatusHistory)
                .where(StatusHistory.document_id == document_id)
                .order_by(StatusHistory.created_at.asc())
            )
            if last_seen_id:
                hist_q = hist_q.where(StatusHistory.id > last_seen_id)

            hist_res = await db.execute(hist_q)
            rows = hist_res.scalars().all()

            for row in rows:
                last_seen_id = row.id
                event_data = {
                    "status": row.to_status,
                    "message": row.message,
                    "ts": row.created_at.isoformat() if row.created_at else None,
                }
                yield _sse_event(event_data)

            # Heartbeat when nothing new
            if not rows:
                yield _sse_event({"status": doc.status, "message": None, "ts": None}, event="heartbeat")

            # Check terminal
            if doc.status in _TERMINAL:
                yield _sse_event({"status": doc.status, "message": doc.status_message, "done": True})
                return

        await asyncio.sleep(interval)
        elapsed += interval

    yield _sse_event({"status": "timeout", "message": "Progress stream timed out", "done": True})


def _sse_event(data: dict, event: str = "progress") -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
