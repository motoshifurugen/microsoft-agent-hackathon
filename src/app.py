"""Chainlit dev UI: Foundry Orchestrator Agent を呼び出す開発用フロントエンド。

本番 UI は Teams + Copilot Studio (要件定義書 §5.1)。Chainlit は開発中の動作確認用に維持。

`AGENT_ID` は Orchestrator の ID を指す (scripts/create_agents.py の出力)。
Orchestrator が ConnectedAgentTool で 4 子 Agent (observer / collector / matcher / proposer) を
呼び分けるため、本ファイルからは Orchestrator のみを直接叩く。

ローカル起動: `uv run chainlit run src/app.py`
コンテナ起動: Dockerfile の CMD で chainlit を headless で起動する。
"""

from __future__ import annotations

import chainlit as cl
from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    FunctionTool,  # pyright: ignore[reportPrivateImportUsage]
    MessageRole,
    MessageTextContent,
    ToolSet,  # pyright: ignore[reportPrivateImportUsage]
)
from dotenv import load_dotenv

from src.config import load_settings
from src.tools.credential import get_default_credential
from src.tools.registry import ORCHESTRATOR_FUNCTIONS
from src.tools.seed import load_success_cases

load_dotenv()

# 環境変数チェックを最初に行い、欠落時は即発見させる。
# Azure I/O (embedding 計算など) より先に実行することで、
# 認証エラーが env var エラーを隠蔽する問題を防ぐ。
_settings = load_settings()

# 起動時に in-memory store へダミー成功事例を投入する。
# embedding 計算は起動時の Azure 依存を避けるため with_embeddings=False。
# データ担当の Cosmos DB + Azure AI Search 本実装が来たらこの呼び出しは不要になる。
_seeded_count = load_success_cases(with_embeddings=False)

_agents = AgentsClient(
    endpoint=_settings.project_endpoint,
    credential=get_default_credential(),
)

# Orchestrator が function tool を呼ぶ際、ローカル Python の tool_* 関数を実行するための ToolSet。
# ConnectedAgentTool は Foundry 内部で処理されるため、ToolSet には FunctionTool のみ登録する。
_function_tool = FunctionTool(functions=ORCHESTRATOR_FUNCTIONS)
_toolset = ToolSet()
_toolset.add(_function_tool)
_agents.enable_auto_function_calls(_toolset)


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
        agent_id=_settings.agent_ids.orchestrator,
        toolset=_toolset,
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
