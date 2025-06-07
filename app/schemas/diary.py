from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.chat import ChatContext  # 既存

class DiaryRequest(BaseModel):
    summary: str
    context: Optional[ChatContext] = None

class DiaryResponse(BaseModel):
    diary_id: int
    date: datetime
    summary: str
    context: Optional[List[ChatContext]] = None

    class Config:
        from_attributes = True