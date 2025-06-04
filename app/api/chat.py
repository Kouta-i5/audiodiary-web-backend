from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any

# モデル
from app.schemas.chat import ChatContext, Message, Summary
# サービス
from app.services.chat import set_context, send_message, get_summary

router = APIRouter(prefix="/chat")

@router.get("/")
async def root():
    return RedirectResponse(url="/docs")

@router.post("/context", response_model=Dict[str, Any])
async def set_chat_context(
    context: ChatContext,
):
    """会話のコンテキストを設定"""
    try:
        return await set_context(context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message")
async def send_chat_message(
    request: Message,
):
    """メッセージを送信"""
    try:
        response = await send_message(request.content)
        if not response:
            raise HTTPException(status_code=500, detail="AIからの応答が空です")
        return {"content": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summarize", response_model=Dict[str, str])
async def summarize():
    """会話を要約"""
    try:
        summary = await get_summary()
        return {"summary": summary}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))