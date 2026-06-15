from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=300)

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=300)

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}
