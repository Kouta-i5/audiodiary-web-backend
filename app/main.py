from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, diary
from app.database import Base, engine

# データベーステーブルの作成
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audio Diary API")

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # フロントエンドのURL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(chat.router)
app.include_router(diary.router)
