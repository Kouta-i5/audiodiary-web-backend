from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime
import openai

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAI APIキーの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# 会話コンテキストの保存用
current_context = None

# ChatOpenAI インスタンスを作成（APIキーを環境変数から読み込む）
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# プロンプトテンプレート
template = """
あなたは日記アプリの会話パートナーです。
以下の情報を元に、ユーザーと日常会話を通じてその日の出来事を引き出してください。

【現在の状況】
{context_info}

【会話履歴】
{history}

【新しいメッセージ】
ユーザー: {input}

【応答】
上記の状況と会話履歴を考慮して、自然な会話を続けてください。
AI:
"""

# 最初のメッセージ用のプロンプトテンプレート
initial_message_template = """
あなたは日記アプリの会話パートナーです。
以下の情報を元に、ユーザーとの会話を始めてください。
状況に応じた自然な挨拶と、その日の出来事について尋ねる質問を含めてください。

【現在の状況】
{context_info}

【最初のメッセージ】
上記の状況を考慮して、自然な会話を始めてください。
AI:
"""

prompt = PromptTemplate(
    input_variables=["context_info", "history", "input"],
    template=template
)

initial_message_prompt = PromptTemplate(
    input_variables=["context_info"],
    template=initial_message_template
)

# 要約用のプロンプトテンプレート
summary_template = """
以下の会話を要約してください。重要なポイントや感情、出来事を簡潔にまとめてください。

【会話内容】
{conversation}

【要約】
"""

summary_prompt = PromptTemplate(
    input_variables=["conversation"],
    template=summary_template
)

# 会話メモリ（直近5発話まで記憶）
memory = ConversationBufferWindowMemory(k=5, return_messages=True)

def get_default_context() -> Dict:
    """デフォルトのコンテキストを生成"""
    now = datetime.now()
    return {
        "date": now.strftime("%Y-%m-%d"),
        "time_of_day": "不明",
        "location": "不明",
        "companion": "不明",
        "mood": "不明"
    }

def format_context_info(context: Dict) -> str:
    """コンテキスト情報を文字列にフォーマット"""
    return f"""日付: {context['date']}
時間帯: {context['time_of_day']}
場所: {context['location']}
一緒にいる人: {context['companion']}
気分: {context['mood']}"""

def format_messages(messages: List) -> str:
    """メッセージ履歴を文字列にフォーマット"""
    if not messages:
        return "まだ会話は始まっていません。"
    
    formatted = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            formatted += f"ユーザー: {msg.content}\n"
        elif isinstance(msg, AIMessage):
            formatted += f"AI: {msg.content}\n"
    return formatted

async def set_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """会話のコンテキストを設定"""
    global current_context
    current_context = context
    
    # 初期メッセージを生成
    prompt = f"""
    以下のコンテキストに基づいて、自然な会話の開始メッセージを生成してください：
    
    日付: {context.date.strftime('%Y-%m-%d')}
    時間: {context.time}
    場所: {context.where}
    相手: {context.who}
    気分: {context.mood}
    
    メッセージは以下の条件を満たしてください：
    1. 自然な会話の流れを作る
    2. コンテキストの情報を自然に組み込む
    3. 相手の気分や状況に配慮する
    4. 簡潔で親しみやすい表現を使用する
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=150
    )
    
    return {
        "initial_message": response.choices[0].message.content,
        "context": context
    }

async def send_message(message: str) -> str:
    """メッセージを送信して応答を取得"""
    if not current_context:
        raise ValueError("コンテキストが設定されていません")
    
    prompt = f"""
    以下のコンテキストと会話履歴に基づいて、自然な応答を生成してください：
    
    コンテキスト:
    日付: {current_context.date.strftime('%Y-%m-%d')}
    時間: {current_context.time}
    場所: {current_context.where}
    相手: {current_context.who}
    気分: {current_context.mood}
    
    ユーザーのメッセージ: {message}
    
    応答は以下の条件を満たしてください：
    1. コンテキストを考慮した自然な会話の流れを維持する
    2. 相手の気分や状況に配慮する
    3. 簡潔で親しみやすい表現を使用する
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=150
    )
    
    return response.choices[0].message.content

async def get_summary(conversation: str) -> str:
    """会話を要約"""
    if not current_context:
        raise ValueError("コンテキストが設定されていません")
    
    prompt = f"""
    以下の会話を要約してください：
    
    コンテキスト:
    日付: {current_context.date.strftime('%Y-%m-%d')}
    時間: {current_context.time}
    場所: {current_context.where}
    相手: {current_context.who}
    気分: {current_context.mood}
    
    会話内容:
    {conversation}
    
    要約は以下の条件を満たしてください：
    1. 重要なポイントを簡潔にまとめる
    2. 会話の流れを保持する
    3. 感情や雰囲気も含める
    4. 箇条書きで3-5点程度にまとめる
    """
    
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=200
    )
    
    return response.choices[0].message.content 