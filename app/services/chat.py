# app/services/chat.py
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
from dotenv import load_dotenv
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.diary import Diary
from app.schemas.chat import ChatContext

# ==== 環境変数 & OpenAI 初期化 ======================================
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")  # 必ず .env に設定

# ==== グローバル・シングルトン ======================================
class _Memory(BaseChatMessageHistory):
    def __init__(self) -> None:
        self.messages: List[AIMessage | HumanMessage] = []

    def add_message(self, message):
        self.messages.append(message)

    def clear(self):
        self.messages = []


current_context: ChatContext | None = None  # 直近セッションのコンテキスト
current_summary: str | None = None          # 要約のキャッシュ（未保存用）
memory = _Memory()                          # 会話メモリ

# ==== ユーティリティ =================================================
def get_default_context() -> ChatContext:
    """コンテキスト未設定時に使うデフォルト値"""
    now = datetime.now()
    return ChatContext(
        date=now,
        time_of_day="不明",
        location="不明",
        companion="不明",
        mood="不明",
    )


def format_context_info(ctx: ChatContext) -> str:
    return (
        f"日付: {ctx.date:%Y-%m-%d}\n"
        f"時間帯: {ctx.time_of_day}\n"
        f"場所: {ctx.location}\n"
        f"一緒にいる人: {ctx.companion}\n"
        f"気分: {ctx.mood}"
    )


def format_messages(msgs: List[AIMessage | HumanMessage]) -> str:
    if not msgs:
        return "まだ会話は始まっていません。"
    buf = []
    for m in msgs:
        role = "ユーザー" if isinstance(m, HumanMessage) else "AI"
        buf.append(f"{role}: {m.content}")
    return "\n".join(buf)


# ==== API 関数群 =====================================================
async def set_context(ctx: ChatContext) -> Dict[str, Any]:
    """会話コンテキストを設定し、最初の挨拶を返す"""
    global current_context
    current_context = ctx
    memory.clear()

    sys_prompt = (
        "あなたは日記アプリの会話パートナーです。"
        "以下のコンテキストを踏まえ自然な会話を開始してください:\n"
        f"{format_context_info(ctx)}"
    )

    # OpenAI 呼び出しは同期なので別スレッドへ
    resp = await asyncio.to_thread(
        openai.chat.completions.create,
        model="gpt-4",
        messages=[{"role": "system", "content": sys_prompt}],
        max_tokens=150,
    )
    first_msg = resp.choices[0].message.content.strip()
    memory.add_message(AIMessage(content=first_msg))
    return {"initial_message": first_msg, "context": ctx}


async def send_message(content: str) -> str:
    """ユーザーがチャットを送信"""
    if current_context is None:
        await set_context(get_default_context())

    memory.add_message(HumanMessage(content=content))

    prompt = (
        f"{format_context_info(current_context)}\n\n"
        f"会話履歴:\n{format_messages(memory.messages)}\n\n"
        f"ユーザー: {content}\nAI:"
    )

    resp = await asyncio.to_thread(
        openai.chat.completions.create,
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000,
    )
    answer = resp.choices[0].message.content.strip()
    memory.add_message(AIMessage(content=answer))
    return answer


async def get_summary() -> str:
    """会話を要約し `current_summary` にキャッシュする"""
    global current_summary

    convo = format_messages(memory.messages)
    if convo.startswith("まだ会話は"):
        raise ValueError("要約する会話がありません")

    sys_prompt = (
        "以下の会話を要約してください。重要な出来事・感情を箇条書き3-5点で:\n"
        f"{convo}"
    )

    resp = await asyncio.to_thread(
        openai.chat.completions.create,
        model="gpt-4",
        messages=[{"role": "system", "content": sys_prompt}],
        max_tokens=200,
    )
    summary = resp.choices[0].message.content.strip()
    if not summary:
        raise ValueError("要約の生成に失敗しました")

    current_summary = summary  # ★キャッシュ
    memory.clear()             # 履歴は破棄
    return summary


async def save_summary(db: Session) -> Diary:
    """`current_summary` を DB に保存（無ければ先に生成）"""
    global current_summary

    summary = current_summary or await get_summary()
    if not summary:
        raise ValueError("要約が存在しません")

    diary = Diary(
        date=datetime.now(),
        context=[current_context.model_dump()] if current_context else [],
        summary=summary,
    )

    try:
        db.add(diary)
        db.commit()
        db.refresh(diary)
        return diary
    except Exception as exc:
        db.rollback()
        raise ValueError(f"データベース保存に失敗しました: {exc}") from exc
    finally:
        current_summary = None  # 保存完了後にキャッシュ破棄

async def save_summary_to_db(
    summary: str,
    context: Optional[ChatContext],
    db: Session,
) -> Diary:
    """受け取った summary / context をそのまま DB 保存"""
    # contextのdatetimeを文字列に変換
    context_dict = None
    if context:
        context_dict = context.model_dump()
        context_dict["date"] = context_dict["date"].isoformat()

    diary = Diary(
        date=datetime.now(),
        context=[context_dict] if context_dict else [],
        summary=summary,
    )

    try:
        db.add(diary)
        db.commit()
        db.refresh(diary)
        return diary
    except Exception as exc:
        db.rollback()
        raise ValueError(f"データベース保存に失敗: {exc}") from exc