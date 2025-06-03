from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.schemas.diary import DiaryResponse
from app.models.diary import Diary
from app.database import get_db

router = APIRouter(prefix="/diary")

@router.get("/", response_model=List[DiaryResponse])
async def get_diaries(db: Session = Depends(get_db)):
    """日記の一覧を取得"""
    conversations = db.query(Diary).all()
    return conversations

@router.get("/{diary_id}", response_model=DiaryResponse)
async def get_diary(diary_id: int, db: Session = Depends(get_db)):
    """特定の日記を取得"""
    conversation = db.query(Diary).filter(Diary.id == diary_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="日記が見つかりません")
    return conversation

@router.delete("/{diary_id}")
async def delete_diary(diary_id: int, db: Session = Depends(get_db)):
    """日記を削除"""
    conversation = db.query(Diary).filter(Diary.id == diary_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="日記が見つかりません")
    
    db.delete(conversation)
    db.commit()
    return {"message": "日記を削除しました"} 