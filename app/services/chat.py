from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from app.schemas.chat import ChatContext
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
    model="gpt-4",
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
上記の状況と会話履歴を考慮して、以下の点に注意して自然な会話を続けてください：
1. コンテキストの情報（時間、場所、一緒にいる人、気分）を自然な形で会話に組み込む
2. ユーザーの気分や状況に合わせた質問や話題を提供する
3. 具体的な質問をして、より詳細な情報を引き出す
4. 会話の流れを維持しながら、新しい話題に自然に移行する
5. 簡潔で親しみやすい表現を使用する

AI:
"""

# 最初のメッセージ用のプロンプトテンプレート
initial_message_template = """
あなたは日記アプリの会話パートナーです。
以下の情報を元に、ユーザーとの会話を始めてください。

【現在の状況】
{context_info}

【最初のメッセージ】
上記の状況を考慮して、以下の点に注意して自然な会話を始めてください：
1. 時間帯に応じた適切な挨拶をする
2. 場所や一緒にいる人の情報を自然に会話に組み込む
3. ユーザーの気分に合わせた話題を提供する
4. その日の出来事について、具体的な質問をする
5. 簡潔で親しみやすい表現を使用する

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
class InMemoryChatMessageHistory(BaseChatMessageHistory):
    def __init__(self):
        self.messages = []
        self.k = 5  # 保持するメッセージ数

    def add_message(self, message):
        self.messages.append(message)
        if len(self.messages) > self.k * 2:  # ユーザーとAIのメッセージを考慮
            self.messages = self.messages[-self.k * 2:]

    def clear(self):
        self.messages = []

memory = InMemoryChatMessageHistory()

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

def format_context_info(context: ChatContext) -> str:
    """コンテキスト情報を文字列にフォーマット"""
    return f"""日付: {context.date.strftime('%Y-%m-%d')}
時間帯: {context.time_of_day}
場所: {context.location}
一緒にいる人: {context.companion}
気分: {context.mood}"""

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

async def set_context(context: ChatContext) -> Dict[str, Any]:
    """会話のコンテキストを設定"""
    global current_context
    current_context = context
    
    # メモリをクリア
    memory.clear()
    
    # 初期メッセージを生成
    prompt = f"""
    以下のコンテキストに基づいて、自然な会話の開始メッセージを生成してください：
    
    日付: {context.date.strftime('%Y-%m-%d')}
    時間: {context.time_of_day}
    場所: {context.location}
    相手: {context.companion}
    気分: {context.mood}
    
    メッセージは以下の条件を満たしてください：
    1. 自然な会話の流れを作る
    2. コンテキストの情報を自然に組み込む
    3. 相手の気分や状況に配慮する
    4. 簡潔で親しみやすい表現を使用する
    """
    
    # 新しいAPIバージョンに対応
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=150
    )
    
    initial_message = response.choices[0].message.content
    memory.add_message(AIMessage(content=initial_message))
    
    return {
        "initial_message": initial_message,
        "context": context
    }

async def send_message(content: str) -> str:
    """メッセージを送信"""
    if not current_context:
        # デフォルトコンテキストを設定
        default_context = get_default_context()
        context = ChatContext(
            date=datetime.now(),
            time_of_day=default_context["time_of_day"],
            location=default_context["location"],
            companion=default_context["companion"],
            mood=default_context["mood"]
        )
        await set_context(context)
    
    # ユーザーのメッセージをメモリに追加
    memory.add_message(HumanMessage(content=content))
    
    # コンテキストと会話履歴を取得
    context_str = format_context_info(current_context)
    history = memory.messages
    
    # プロンプトの作成
    prompt = f"""
{context_str}

会話履歴:
{format_messages(history)}

ユーザー: {content}
AI: """
    
    # OpenAI APIを呼び出し
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": template},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    # 応答を取得
    ai_response = response.choices[0].message.content.strip()
    
    # AIの応答をメモリに追加
    memory.add_message(AIMessage(content=ai_response))
    
    return ai_response

async def get_summary() -> str:
    """会話を要約"""
    # メモリから会話履歴を取得
    conversation = format_messages(memory.messages)
    
    prompt = f"""
    以下の会話を要約してください。重要なポイントや感情、出来事を簡潔にまとめてください。

    会話内容:
    {conversation}

    要約は以下の条件を満たしてください：
    1. 重要なポイントを簡潔にまとめる
    2. 会話の流れを保持する
    3. 感情や雰囲気も含める
    4. 箇条書きで3-5点程度にまとめる
    """
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=200
    )
    
    return response.choices[0].message.content 