from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List

# モデル
from app.schemas.chat import SetContextRequest, MessageRequest, SummaryRequest
from app.models.user import User
from app.database import get_db
from app.core.security import get_current_user
# サービス
from app.services.chat import set_context, send_message, get_summary

router = APIRouter(prefix="/chat")

@router.get("/")
async def root():
    return RedirectResponse(url="/docs")

@router.post("/context")
async def set_chat_context(
    context: SetContextRequest,
    current_user: User = Depends(get_current_user)
):
    """会話のコンテキストを設定"""
    return await set_context(context)

@router.post("/message")
async def send_chat_message(
    request: MessageRequest,
    current_user: User = Depends(get_current_user)
):
    """メッセージを送信"""
    return await send_message(request.message)

@router.post("/summarize")
async def summarize(
    request: SummaryRequest,
    current_user: User = Depends(get_current_user)
):
    """会話を要約"""
    return await get_summary(request.conversation)