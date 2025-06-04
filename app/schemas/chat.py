from pydantic import BaseModel
from datetime import datetime

class ChatContext(BaseModel):
    date: datetime
    time_of_day: str
    location: str
    companion: str
    mood: str


class Message(BaseModel):
    content: str

class Summary(BaseModel):
    pass 