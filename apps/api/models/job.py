import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base

class JournalProcessingJob(Base):
    __tablename__ = "journal_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    journal_id = Column(UUID(as_uuid=True), ForeignKey("journals.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False) # pending, processing, completed, failed
    step = Column(String, nullable=True) # chunking, embedding, extracting
    error = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
