"""WebApp の「AIに相談」向け Foundry Orchestrator ストリーミング API。

ホームの困りごと入力 (固定検索) を廃止し、エージェントとの対話で探す方針に統一する。
Orchestrator (LLM) が tool_* 関数を自律的に呼び分けながら応答するため、本 API は
runs.stream() のイベントを SSE (text/event-stream) でフロントへ逐次中継する。

tool_* の実行は SDK に委ねる。enable_auto_function_calls(toolset) を一度呼んでおくと、
stream() のデフォルト AgentEventHandler が requires_action を検知して toolset を実行し
submit_tool_outputs_stream を自動で回す (src/app.py の create_and_process と同じ仕組み)。
本 API は MessageDeltaChunk のトークンを中継するだけでよい。

Azure クライアントは遅延初期化する。import 時に PROJECT_ENDPOINT / AGENT_ID を要求すると
Azure 資格情報のないテスト環境で main.py の import が壊れるため。
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    AgentStreamEvent,
    FunctionTool,  # pyright: ignore[reportPrivateImportUsage]
    MessageDeltaChunk,
    MessageRole,
    ThreadRun,
    ToolSet,  # pyright: ignore[reportPrivateImportUsage]
)
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config import Settings, load_settings
from src.tools.credential import get_default_credential
from src.tools.registry import ORCHESTRATOR_FUNCTIONS

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent", tags=["agent"])

ANONYMOUS_USER_ID = "anonymous-webapp"
MAX_MESSAGE_LEN = 2000


class AgentChatRequest(BaseModel):
    """AIに相談チャットの 1 発話。"""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LEN)
    client_id: str | None = None


@dataclass(frozen=True)
class _AgentState:
    agents: AgentsClient
    settings: Settings


_state: _AgentState | None = None
_state_lock = threading.Lock()
# client_id -> Foundry thread_id。会話の継続性を保つため client 単位で thread を再利用する。
# in-memory のため再起動で消えるが、既存の永続化方針 (cosmos_io) と同等で許容。
_threads: dict[str, str] = {}
_threads_lock = threading.Lock()


def _get_state() -> _AgentState:
    """AgentsClient を一度だけ初期化して返す (遅延初期化)。"""
    global _state
    if _state is None:
        with _state_lock:
            if _state is None:
                settings = load_settings()
                agents = AgentsClient(
                    endpoint=settings.project_endpoint,
                    credential=get_default_credential(),
                )
                # stream() 中の requires_action で SDK が tool_* を自動実行できるよう登録する。
                toolset = ToolSet()
                toolset.add(FunctionTool(functions=ORCHESTRATOR_FUNCTIONS))
                agents.enable_auto_function_calls(toolset)
                _state = _AgentState(agents=agents, settings=settings)
    return _state


def _get_or_create_thread(state: _AgentState, client_id: str) -> str:
    with _threads_lock:
        thread_id = _threads.get(client_id)
        if thread_id is None:
            thread_id = state.agents.threads.create().id
            _threads[client_id] = thread_id
        return thread_id


def _sse(payload: dict) -> str:
    """SSE の 1 イベント。token テキストに改行が含まれても壊れないよう JSON で包む。"""
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _registrant_instructions(client_id: str) -> str:
    """成功事例登録時に使う登録者 user_id を Run 単位で Orchestrator に注入する。

    list_my_cases は user_id == client_id で絞り込むため、登録の user_id を
    呼び出し元の client_id に固定しないと「自分の事例」に反映されない。
    匿名 (anonymous-webapp) でも安定した識別子なので同じ規則で扱う。
    """
    return (
        f"登録者の user_id は {client_id} です。"
        "成功事例を登録 (tool_register_success_case) する際は必ずこの user_id を使い、"
        "推測した値や別の値を使わないこと。owner_label (表示名) は本人に確認すること。"
    )


def _stream_agent_reply(message: str, client_id: str):
    """Orchestrator Run を stream し、SSE 文字列を yield するジェネレータ。"""
    try:
        state = _get_state()
    except Exception:
        _logger.exception("agent client init failed")
        yield _sse({"type": "error", "message": "AI サービスに接続できませんでした"})
        return

    thread_id = _get_or_create_thread(state, client_id)
    agent_id = state.settings.agent_ids.orchestrator

    try:
        state.agents.messages.create(
            thread_id=thread_id,
            role=MessageRole.USER,
            content=message,
        )

        # tool 呼び出しがあると stream は「ツール実行 run の完了 (DONE) → 自動 submit →
        # 応答テキストの continuation run」と複数 run にまたがる。DONE で break すると
        # 本文 (continuation の MessageDelta) を取りこぼすため、イテレータを自然枯渇させる。
        with state.agents.runs.stream(
            thread_id=thread_id,
            agent_id=agent_id,
            additional_instructions=_registrant_instructions(client_id),
        ) as stream:
            for event_type, event_data, _ in stream:
                if isinstance(event_data, MessageDeltaChunk):
                    if event_data.text:
                        yield _sse({"type": "token", "text": event_data.text})
                elif isinstance(event_data, ThreadRun):
                    # requires_action は SDK が enable_auto_function_calls 経由で自動処理する。
                    if event_data.status == "failed":
                        yield _sse({"type": "error", "message": "エージェントの実行に失敗しました"})
                elif event_type == AgentStreamEvent.ERROR:
                    yield _sse({"type": "error", "message": "ストリーム中にエラーが発生しました"})

        yield _sse({"type": "done"})
    except Exception:
        _logger.exception("agent chat stream failed")
        yield _sse({"type": "error", "message": "エージェント実行中にエラーが発生しました"})


@router.post("/chat")
def agent_chat(req: AgentChatRequest) -> StreamingResponse:
    """ユーザー発話を Orchestrator に渡し、応答を SSE でストリーム配信する。"""
    client_id = req.client_id or ANONYMOUS_USER_ID
    return StreamingResponse(
        _stream_agent_reply(req.message, client_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx 等のバッファリングを無効化
        },
    )
