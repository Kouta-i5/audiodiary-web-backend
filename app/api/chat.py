from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from app.services.langchain_client import run_conversation

router = APIRouter()

class ChatRequest(BaseModel):
    content: str

@router.get("/")
async def root():
    return RedirectResponse(url="/docs")

@router.post("/chat")
async def chat(request: ChatRequest):
    reply = run_conversation(request.content)
    return {"response": reply}