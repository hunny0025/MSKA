"""Maruti Suzuki Knowledge Assistant — SQLAlchemy ORM models."""

from models.base import BaseModel
from models.user import User
from models.role import Role
from models.department import Department
from models.project import Project
from models.document import Document
from models.audit import AuditLog
from models.chat import ChatSession, ChatMessage, BookmarkedMessage
from models.notification import Notification
from models.feedback import Feedback
from models.chunk import Chunk
from models.status_history import StatusHistory

