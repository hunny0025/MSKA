"""
Audit Logging service layer.
"""

import json
from sqlalchemy.ext.asyncio import AsyncSession
from models.audit import AuditLog


async def log_activity(
    db: AsyncSession,
    user_id: str | None,
    action: str,
    target_type: str,
    target_id: str | None = None,
    details: dict | None = None
) -> AuditLog:
    """
    Creates an immutable audit log entry.
    """
    details_str = json.dumps(details) if details else None
    
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details_str
    )
    
    db.add(log_entry)
    await db.commit()
    return log_entry
