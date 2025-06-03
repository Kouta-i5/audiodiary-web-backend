FROM python:3.11-slim

# Poetryのインストール
RUN pip install poetry

# 作業ディレクトリ
WORKDIR /app

# poetryファイルをコピー
COPY pyproject.toml poetry.lock* ./

# 依存関係インストール
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction

# アプリケーションコピー
COPY app ./app

# ポート公開 & 起動
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]