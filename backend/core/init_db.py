"""
Database table creation utility.
"""

from core.database import Base


async def init_tables(engine):
    """Creates all database tables defined in the metadata."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
