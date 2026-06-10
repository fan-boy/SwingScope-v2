import uuid
from datetime import datetime
from app.schemas.base import APIModel


class ExecutionLogRead(APIModel):
    id: uuid.UUID
    level: str
    event: str
    message: str
    entity_type: str | None
    entity_id: uuid.UUID | None
    meta: dict | None
    created_at: datetime
