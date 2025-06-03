from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, List
from app.schemas.user import UserResponse

class DiaryResponse(BaseModel):
    id: int
    date: datetime
    context: Dict
    messages: List[Dict]
    summary: Optional[str] = None
    user: UserResponse

    class Config:
        from_attributes = True 

class DiaryRequest(BaseModel):
    date: datetime
    context: Dict
    messages: List[Dict]
    summary: Optional[str] = None

    class Config:
        from_attributes = True 