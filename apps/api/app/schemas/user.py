import uuid
from datetime import datetime
from pydantic import EmailStr
from app.schemas.base import APIModel


class UserCreate(APIModel):
    email: EmailStr
    name: str | None = None


class UserRead(APIModel):
    id: uuid.UUID
    email: str
    name: str | None
    is_active: bool
    created_at: datetime
