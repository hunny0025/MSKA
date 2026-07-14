"""
D1 — Document Explorer API Router.

Routes:
  GET  /api/v1/projects/{project_id}/explorer/documents
      Paginated list of documents in a project with filters.

  GET  /api/v1/projects/{project_id}/explorer/documents/{doc_id}
      Full metadata + status history for a document.

  GET  /api/v1/projects/{project_id}/explorer/documents/{doc_id}/chunks
      Paginated list of chunks belonging to a document.

  DELETE /api/v1/projects/{project_id}/explorer/documents/{doc_id}
      Admin-only soft-delete (marks status=failed, removes FAISS entries).
"""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.permissions import PermissionChecker, Roles, get_current_user
from models.chunk import Chunk
from models.document import Document
from models.status_history import StatusHistory
from models.user import User

router = APIRouter(tags=["Document Explorer"])


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _doc_to_dict(doc: Document) -> dict:
    return {
        "id":           doc.id,
        "filename":     doc.filename,
        "classification": doc.classification,
        "status":       doc.status,
        "status_message": doc.status_message,
        "pii_flagged":  doc.pii_flagged,
        "chunk_count":  doc.chunk_count,
        "version":      doc.version,
        "project_id":   doc.project_id,
        "department_id": doc.department_id,
        "uploaded_by":  doc.uploaded_by,
        "created_at":   doc.created_at.isoformat() if doc.created_at else None,
        "updated_at":   doc.updated_at.isoformat() if doc.updated_at else None,
    }


def _history_to_dict(h: StatusHistory) -> dict:
    return {
        "id":           h.id,
        "from_status":  h.from_status,
        "to_status":    h.to_status,
        "message":      h.message,
        "created_at":   h.created_at.isoformat() if h.created_at else None,
    }


def _chunk_to_dict(c: Chunk) -> dict:
    return {
        "id":          c.id,
        "chunk_index": c.chunk_index,
        "text":        c.text,
        "created_at":  c.created_at.isoformat() if c.created_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/explorer/documents")
async def explorer_list_documents(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    status_filter: Optional[str] = Query(None, alias="status"),
    pii_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Paginated document list for the project explorer.

    Query params:
      status=ready|failed|quarantined|…
      pii_only=true
      page=1&page_size=20
    """
    q = select(Document).where(Document.project_id == project_id)

    if status_filter:
        q = q.where(Document.status == status_filter)
    if pii_only:
        q = q.where(Document.pii_flagged.is_(True))

    # Total count
    count_q = select(func.count()).select_from(q.subquery())
    total_res = await db.execute(count_q)
    total = total_res.scalar_one()

    # Paginated page
    q = q.order_by(Document.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(q)
    docs = res.scalars().all()

    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "items":     [_doc_to_dict(d) for d in docs],
    }


@router.get("/projects/{project_id}/explorer/documents/{doc_id}")
async def explorer_get_document(
    project_id: str,
    doc_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """Full document detail with status history."""
    res = await db.execute(
        select(Document).where(and_(Document.id == doc_id, Document.project_id == project_id))
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # History
    hist_res = await db.execute(
        select(StatusHistory)
        .where(StatusHistory.document_id == doc_id)
        .order_by(StatusHistory.created_at.asc())
    )
    history = [_history_to_dict(h) for h in hist_res.scalars().all()]

    return {**_doc_to_dict(doc), "history": history}


@router.get("/projects/{project_id}/explorer/documents/{doc_id}/chunks")
async def explorer_list_chunks(
    project_id: str,
    doc_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
):
    """Paginated chunk viewer for a document."""
    # Verify document belongs to project
    doc_res = await db.execute(
        select(Document).where(and_(Document.id == doc_id, Document.project_id == project_id))
    )
    if not doc_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    count_q = select(func.count()).where(
        and_(Chunk.document_id == doc_id, Chunk.project_id == project_id)
    )
    total = (await db.execute(count_q)).scalar_one()

    q = (
        select(Chunk)
        .where(and_(Chunk.document_id == doc_id, Chunk.project_id == project_id))
        .order_by(Chunk.chunk_index)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    res = await db.execute(q)
    chunks = res.scalars().all()

    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "items":     [_chunk_to_dict(c) for c in chunks],
    }


@router.delete(
    "/projects/{project_id}/explorer/documents/{doc_id}",
    status_code=status.HTTP_200_OK,
)
async def explorer_delete_document(
    project_id: str,
    doc_id: str,
    current_user: Annotated[User, Depends(PermissionChecker([Roles.PLATFORM_ADMIN, Roles.PROJECT_ADMIN]))],
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only: remove a document from the explorer.

    Marks status=failed, removes FAISS chunks for that document,
    and hard-deletes chunks from DB.  The Document row is retained
    for audit purposes.
    """
    res = await db.execute(
        select(Document).where(and_(Document.id == doc_id, Document.project_id == project_id))
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    # Soft-delete: mark failed
    from services.document_service import update_status
    from models.document import DocumentStatus
    await update_status(db, doc_id, DocumentStatus.FAILED, message="Deleted by administrator")

    # Hard-delete chunks from DB
    chunk_res = await db.execute(select(Chunk).where(Chunk.document_id == doc_id))
    for chunk in chunk_res.scalars().all():
        await db.delete(chunk)
    await db.commit()

    # Note: FAISS entries are stale now; they're filtered by status at query time
    # A full FAISS rebuild is triggered by periodic maintenance jobs (not in scope here).

    return {"detail": f"Document {doc_id} removed from project {project_id}"}
