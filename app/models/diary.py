from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.database import Base

class Diary(Base):
    __tablename__ = "diaries"

    diary_id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now, nullable=False)
    context = Column(JSON, nullable=True)  # コンテキスト情報（場所、気分など）
    summary = Column(String, nullable=False)  # 会話の要約