"""
Admin console compliance controls and feedback processing logic.
"""

import os
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from models.document import Document
from models.audit import AuditLog
from models.feedback import Feedback
from rag.chunker import chunker
from adapters.ai.embeddings import embedding_generator
from adapters.vectorstore.faiss_adapter import vector_store
from services.audit_service import log_activity


async def get_quarantined_documents(db: AsyncSession) -> list[Document]:
    """
    Retrieves all files flagged by the PII scanner during ingestion.
    """
    query = select(Document).where(Document.status == "quarantined")
    res = await db.execute(query)
    return list(res.scalars().all())


async def approve_quarantined_document(db: AsyncSession, doc_id: str, acting_user_id: str) -> Document:
    """
    Changes a quarantined document's status to approved and indexes it in the vector DB.
    """
    query = select(Document).where(Document.id == doc_id)
    res = await db.execute(query)
    doc = res.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status != "quarantined":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document is not quarantined")

    doc.status = "approved"
    await db.flush()

    # Trigger chunking and vector embedding indexing
    if doc.extracted_text:
        chunks = chunker.split_text(doc.extracted_text)
        if chunks:
            documents_to_index = []
            for idx, text_chunk in enumerate(chunks):
                chunk_id = f"{doc.id}_c{idx}"
                embedding = embedding_generator.get_embedding(text_chunk)
                documents_to_index.append({
                    "id": chunk_id,
                    "text": text_chunk,
                    "embedding": embedding,
                    "metadata": {
                        "document_id": doc.id,
                        "filename": doc.filename,
                        "classification": doc.classification,
                        "department_id": doc.department_id
                    }
                })
            vector_store.add_documents(doc.project_id, documents_to_index)

    await db.commit()

    await log_activity(
        db,
        user_id=acting_user_id,
        action="APPROVE_QUARANTINED_DOCUMENT",
        target_type="document",
        target_id=doc.id,
        details={"filename": doc.filename}
    )
    return doc


async def reject_quarantined_document(db: AsyncSession, doc_id: str, acting_user_id: str) -> None:
    """
    Permanently deletes a rejected quarantined file and its metadata row.
    """
    query = select(Document).where(Document.id == doc_id)
    res = await db.execute(query)
    doc = res.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    # Delete storage file from disk
    if os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception:
            pass # Keep database delete going

    await db.delete(doc)
    await db.commit()

    await log_activity(
        db,
        user_id=acting_user_id,
        action="REJECT_QUARANTINED_DOCUMENT",
        target_type="document",
        target_id=doc_id,
        details={"filename": doc.filename}
    )


async def get_all_audit_logs(db: AsyncSession) -> list[AuditLog]:
    """
    Lists global append-only log trails. Immutable read access.
    """
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    res = await db.execute(query)
    return list(res.scalars().all())


async def submit_feedback(db: AsyncSession, user_id: str, message_id: str, thumbs_up: bool, comment: str | None) -> Feedback:
    """
    Registers a user rating review on a generated message answer.
    """
    fb = Feedback(user_id=user_id, message_id=message_id, thumbs_up=thumbs_up, comment=comment)
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return fb


async def get_all_feedback_records(db: AsyncSession) -> list[Feedback]:
    """
    Lists user feedback ratings for compliance audits.
    """
    query = select(Feedback).order_by(Feedback.created_at.desc())
    res = await db.execute(query)
    return list(res.scalars().all())
