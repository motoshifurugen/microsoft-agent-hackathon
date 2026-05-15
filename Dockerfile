# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# uv をインストール
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

# 依存だけ先に解決してキャッシュ層を作る
COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# アプリ本体
COPY src/ ./src/
COPY README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.12-slim

WORKDIR /app

# 実行時に必要なファイルだけコピー
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8000

EXPOSE 8000

# Chainlit を headless で起動。Container Apps の ingress port と合わせる
CMD ["chainlit", "run", "src/app.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]
