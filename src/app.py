"""Chainlit dev UI: Foundry Orchestrator Agent を呼び出す開発用フロントエンド。

本番 UI は Teams + Copilot Studio (要件定義書 §5.1)。Chainlit は開発中の動作確認用に維持。

`AGENT_ID` は Orchestrator の ID を指す (scripts/create_agents.py の出力)。
Orchestrator が ConnectedAgentTool で 4 子 Agent (observer / collector / matcher / proposer) を
呼び分けるため、本ファイルからは Orchestrator のみを直接叩く。

ローカル起動: `uv run chainlit run src/app.py`
コンテナ起動: Dockerfile の CMD で chainlit を headless で起動する。
"""

from __future__ import annotations

import os

import chainlit as cl
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import MessageRole, MessageTextContent
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

PROJECT_ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "").strip()
AGENT_ID = os.environ.get("AGENT_ID", "").strip()

if not PROJECT_ENDPOINT or not AGENT_ID:
    # 起動時に欠落を即発見させる。Chainlit ログに警告が出る
    raise RuntimeError("PROJECT_ENDPOINT と AGENT_ID を .env または環境変数で設定してください")

_agents = AgentsClient(
    endpoint=PROJECT_ENDPOINT,
    credential=DefaultAzureCredential(),
)


@cl.on_chat_start
async def on_chat_start() -> None:
    """新しいチャットセッションごとに Foundry の thread を作る。"""
    thread = _agents.threads.create()
    cl.user_session.set("thread_id", thread.id)


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """ユーザー発話を Foundry Agent に渡し、応答を返す。"""
    thread_id: str | None = cl.user_session.get("thread_id")
    if thread_id is None:
        await cl.Message(content="セッションが初期化されていません。リロードしてください。").send()
        return

    _agents.messages.create(
        thread_id=thread_id,
        role=MessageRole.USER,
        content=message.content,
    )

    run = _agents.runs.create_and_process(
        thread_id=thread_id,
        agent_id=AGENT_ID,
    )

    if run.status == "failed":
        await cl.Message(content=f"Agent 実行に失敗しました: {run.last_error}").send()
        return

    # 最新のアシスタント発話を取り出して返す
    messages = _agents.messages.list(thread_id=thread_id, order="desc", limit=1)
    for msg in messages:
        if msg.role != MessageRole.AGENT:
            continue
        for content in msg.content:
            if isinstance(content, MessageTextContent):
                await cl.Message(content=content.text.value).send()
                return

    await cl.Message(content="(応答を取得できませんでした)").send()
