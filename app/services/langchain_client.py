from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# ChatOpenAI インスタンスを作成
llm = ChatOpenAI(
    model="gpt-3.5-turbo",  # 必要に応じて "gpt-4" も可
    temperature=0.7,
)

# プロンプトテンプレート（適宜更新可能）
template = """
あなたは日記アプリの会話パートナーです。
ユーザーと日常会話を通じてその日の出来事を引き出してください。

{history}
ユーザー: {input}
AI:
"""

prompt = PromptTemplate(
    input_variables=["history", "input"],
    template=template
)

# 会話メモリ（直近5発話まで記憶）
memory = ConversationBufferWindowMemory(k=5)

# 会話チェーンの定義
conversation = ConversationChain(
    llm=llm,
    prompt=prompt,
    memory=memory,
    verbose=True,
)

# 外部から呼び出す関数
def run_conversation(user_input: str) -> str:
    response = conversation.predict(input=user_input)
    return response