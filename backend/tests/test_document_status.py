import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from core.database import Base
from models.department import Department
from models.project import Project
from models.document import Document, DocumentStatus
from models.status_history import StatusHistory
from services.document_service import update_status


@pytest.mark.asyncio
async def test_document_status_transitions():
    # 1. Initialize an in-memory SQLite database
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 2. Insert dummy Department & Project
        dept = Department(id="dept-1", name="Engineering", code="ENG")
        session.add(dept)
        await session.flush()
        
        project = Project(id="proj-1", name="Assembly Line 1", department_id=dept.id)
        session.add(project)
        await session.flush()
        
        # 3. Create a Document
        doc = Document(
            id="doc-1",
            filename="sop.txt",
            filepath="/storage/sop.txt",
            project_id=project.id,
            department_id=dept.id,
            status=DocumentStatus.UPLOADED.value
        )
        session.add(doc)
        await session.commit()

    async with async_session() as session:
        # 4. Update status 3 times
        await update_status(session, "doc-1", DocumentStatus.EXTRACTING.value, "Extracting text...")
        await update_status(session, "doc-1", DocumentStatus.CHUNKING.value, "Chunking document...")
        await update_status(session, "doc-1", DocumentStatus.READY.value, "Ready to query.")
        await session.commit()

    async with async_session() as session:
        # 5. Query and assert
        res_doc = await session.execute(select(Document).where(Document.id == "doc-1"))
        doc_obj = res_doc.scalar_one()
        assert doc_obj.status == DocumentStatus.READY.value
        assert doc_obj.status_message == "Ready to query."

        res_history = await session.execute(
            select(StatusHistory)
            .where(StatusHistory.document_id == "doc-1")
            .order_by(StatusHistory.created_at.asc())
        )
        history_rows = res_history.scalars().all()
        
        assert len(history_rows) == 3
        
        assert history_rows[0].from_status == DocumentStatus.UPLOADED.value
        assert history_rows[0].to_status == DocumentStatus.EXTRACTING.value
        assert history_rows[0].message == "Extracting text..."

        assert history_rows[1].from_status == DocumentStatus.EXTRACTING.value
        assert history_rows[1].to_status == DocumentStatus.CHUNKING.value
        assert history_rows[1].message == "Chunking document..."

        assert history_rows[2].from_status == DocumentStatus.CHUNKING.value
        assert history_rows[2].to_status == DocumentStatus.READY.value
        assert history_rows[2].message == "Ready to query."

    await engine.dispose()
