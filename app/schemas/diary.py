from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
from app.schemas.chat import ChatContext

class DiaryResponse(BaseModel):
    diary_id: int
    date: datetime
    context: List[ChatContext]
    summary: Optional[str] = None

    class Config:
        from_attributes = True 

class DiaryRequest(BaseModel):
    date: datetime
    context: List[ChatContext]
    summary: Optional[str] = None

    class Config:
        from_attributes = True 