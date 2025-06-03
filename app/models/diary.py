from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Diary(Base):
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.now)
    context = Column(JSON)  # コンテキスト情報（場所、気分など）
    messages = Column(JSON)  # 会話メッセージの履歴
    summary = Column(String, nullable=True)  # 会話の要約
    
    # ユーザーとの関連
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="diaries") 