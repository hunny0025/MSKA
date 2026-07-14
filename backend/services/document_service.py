"""
Document business logic service.
"""

import os
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import get_settings
from documentpipeline.parsers.registry import parser_registry
from documentpipeline.pii_scanner import pii_scanner
from documentpipeline.classifier import classifier
from rag.chunker import chunker
from adapters.ai.embeddings import embedding_generator
from adapters.vectorstore.faiss_adapter import vector_store
from models.document import Document
from services.audit_service import log_activity

settings = get_settings()


async def ingest_document(
    db: AsyncSession,
    upload_file: UploadFile,
    project_id: str,
    department_id: str,
    user_provided_classification: str,
    user_id: str
) -> Document:
    """
    Ingests and processes a uploaded document.
    Steps:
    1. Parse file extension and load registry parser.
    2. Extract raw text.
    3. Run PII scanner (regex) -> Flag quarantine.
    4. Validate and verify classification metadata.
    5. Check versioning: if file exists, increment version.
    6. Save file locally on disk.
    7. Save metadata database entity.
    8. Index in vector store (if approved).
    """
    filename = upload_file.filename
    _, ext = os.path.splitext(filename)
    
    try:
        parser = parser_registry.get_parser(ext)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Read binary bytes
    content_bytes = await upload_file.read()
    
    # 1. Parse text
    try:
        extracted_text = parser.extract_text(content_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail=f"Failed to parse text: {str(e)}"
        )

    # 2. Check PII
    pii_results = pii_scanner.scan(extracted_text)
    is_pii_flagged = pii_results["flagged"]
    doc_status = "quarantined" if is_pii_flagged else "approved"

    # 3. Classify
    final_classification = classifier.infer_classification(extracted_text, user_provided_classification)

    # 4. Check Versioning
    version = 1
    version_query = (
        select(Document)
        .where(Document.filename == filename)
        .where(Document.project_id == project_id)
        .order_by(Document.version.desc())
    )
    result = await db.execute(version_query)
    existing_doc = result.scalars().first()
    if existing_doc:
        version = existing_doc.version + 1

    # 5. Save file to storage disk
    os.makedirs(settings.file_storage_path, exist_ok=True)
    # Generate unique storage filename with version
    storage_filename = f"{project_id}_{version}_{filename}"
    filepath = os.path.join(settings.file_storage_path, storage_filename)
    
    try:
        with open(filepath, "wb") as f:
            f.write(content_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save document to storage: {str(e)}"
        )

    # 6. Save DB metadata
    doc = Document(
        filename=filename,
        filepath=filepath,
        extracted_text=extracted_text,
        classification=final_classification,
        pii_flagged=is_pii_flagged,
        status=doc_status,
        version=version,
        project_id=project_id,
        department_id=department_id
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # 7. Index chunks in vector database if approved (clean of PII details)
    if doc_status == "approved" and extracted_text:
        chunks = chunker.split_text(extracted_text)
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
            vector_store.add_documents(project_id, documents_to_index)

    # 8. Trigger user notifications for processing completions / warnings
    from services.notification_service import create_notification
    if doc_status == "quarantined":
        await create_notification(
            db, 
            user_id=user_id, 
            message=f"Document '{filename}' quarantined: PII details detected.", 
            severity_type="danger"
        )
    else:
        await create_notification(
            db, 
            user_id=user_id, 
            message=f"Document '{filename}' parsed and index loaded.", 
            severity_type="success"
        )

    # 9. Audit log write
    await log_activity(
        db,
        user_id=user_id,
        action="INGEST_DOCUMENT",
        target_type="document",
        target_id=doc.id,
        details={
            "filename": filename, 
            "version": version, 
            "classification": final_classification, 
            "pii_flagged": is_pii_flagged,
            "status": doc_status
        }
    )

    return doc




async def get_documents_by_project(db: AsyncSession, project_id: str) -> list[Document]:
    """
    Lists documents within a project boundary.
    """
    query = select(Document).where(Document.project_id == project_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_document_by_id(db: AsyncSession, doc_id: str) -> Document:
    """
    Retrieves specific document or raises 404.
    """
    query = select(Document).where(Document.id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


async def update_status(
    db: AsyncSession,
    document_id: str,
    new_status,  # accepts DocumentStatus enum or plain str
    message: str | None = None,
    error: str | None = None,       # alias used by pipeline runner
) -> Document:
    """
    Updates the status and message of a Document, and records the transition
    in StatusHistory atomically.

    Accepts either a DocumentStatus enum value or a plain string for
    new_status so callers in the pipeline runner and legacy code are both
    handled without changes.
    """
    from models.status_history import StatusHistory
    from models.document import DocumentStatus

    # Normalise enum → string value
    if isinstance(new_status, DocumentStatus):
        new_status_value = new_status.value
    else:
        new_status_value = str(new_status)

    # `error` is an alias for `message` used by the pipeline runner
    final_message = message or error

    # 1. Fetch document
    query = select(Document).where(Document.id == document_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    if not doc:
        raise ValueError(f"Document with id {document_id} not found")

    old_status = doc.status

    # 2. Update document
    doc.status = new_status_value
    if final_message is not None:
        doc.status_message = final_message

    # 3. Insert status history record
    history = StatusHistory(
        document_id=document_id,
        from_status=old_status,
        to_status=new_status_value,
        message=final_message,
    )
    db.add(history)
    await db.flush()
    await db.commit()   # commit so SSE readers see status immediately

    return doc

