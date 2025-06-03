from pydantic import BaseModel
from datetime import datetime

class ChatContext(BaseModel):
    date: datetime
    time_of_day: str
    location: str
    companion: str
    mood: str

class SetContextRequest(BaseModel):
    context: ChatContext

class MessageRequest(BaseModel):
    content: str

class SummaryRequest(BaseModel):
    conversation: str 