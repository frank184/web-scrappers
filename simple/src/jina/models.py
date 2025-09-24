from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ReadResult(BaseModel):
    url: str
    status: int
    fetched_at: datetime
    content: Optional[str] = None  # Jina Reader returns markdown-ish cleaned text
    meta: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
