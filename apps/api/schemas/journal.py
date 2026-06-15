from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class JournalBase(BaseModel):
    title: Optional[str] = None
    mood: Optional[str] = None
    entry_type: str = "daily"

class JournalCreate(JournalBase):
    content: str

class JournalUpdate(JournalBase):
    content: Optional[str] = None

class JournalResponse(JournalBase):
    id: UUID
    user_id: UUID
    content: str  # Decrypted content
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
