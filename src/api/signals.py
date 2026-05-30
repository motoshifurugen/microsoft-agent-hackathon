"""Slack から拾った支援候補シグナルの参照 API とデモ用投入 API。

- GET  /api/signals      : ダッシュボードで「Slackから拾った声」を表示するための一覧
- POST /api/slack/mock   : Slack 連携が動かない環境でも投稿相当のデータを投入できる開発用
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from src.signals.config import DEFAULT_CHANNEL_NAME, load_slack_config
from src.signals.service import handle_message
from src.signals.store import Signal, list_signals

router = APIRouter(prefix="/api", tags=["signals"])


class SignalView(BaseModel):
    """支援候補シグナルの表示用スキーマ (フロントが自然に乗せられる形)。"""

    id: str
    source: str
    channel_id: str
    channel_name: str
    slack_user_id: str
    display_name: str
    text: str
    summary: str
    business_category: str
    confidence: float
    status: str
    kodama_url: str
    created_at: str


class SlackMockRequest(BaseModel):
    """Slack 投稿相当のデータを投入するデモ用リクエスト。"""

    text: str = Field(min_length=1, description="投稿本文")
    channel_id: str = Field(default="C_MOCK")
    channel_name: str = Field(default=DEFAULT_CHANNEL_NAME)
    slack_user_id: str = Field(default="U_MOCK")
    display_name: str = Field(default="")
    ts: str = Field(default="", description="重複排除キー。空なら現在時刻から生成")

    @field_validator("text")
    @classmethod
    def _text_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        return stripped


class SlackMockResponse(BaseModel):
    """検知結果。detected=False なら支援候補にしなかったことを示す。"""

    detected: bool
    signal: SignalView | None = None


def _to_view(signal: Signal) -> SignalView:
    return SignalView(
        id=signal.id,
        source=signal.source,
        channel_id=signal.channel_id,
        channel_name=signal.channel_name,
        slack_user_id=signal.slack_user_id,
        display_name=signal.display_name,
        text=signal.text,
        summary=signal.summary,
        business_category=signal.business_category,
        confidence=signal.confidence,
        status=signal.status,
        kodama_url=signal.kodama_url,
        created_at=signal.created_at,
    )


@router.get("/signals", response_model=list[SignalView])
def get_signals() -> list[SignalView]:
    """Slack から拾った支援候補シグナルを新しい順で返す。"""
    return [_to_view(s) for s in list_signals()]


@router.post("/slack/mock", response_model=SlackMockResponse)
def post_slack_mock(req: SlackMockRequest) -> SlackMockResponse:
    """Slack 投稿相当のデータを投入し、検知結果を返す (開発・デモ用)。"""
    base_url = load_slack_config().kodama_base_url
    ts = req.ts or f"{datetime.now(UTC).timestamp():.6f}"
    signal = handle_message(
        channel_id=req.channel_id,
        channel_name=req.channel_name,
        slack_user_id=req.slack_user_id,
        display_name=req.display_name,
        text=req.text,
        ts=ts,
        base_url=base_url,
    )
    if signal is None:
        return SlackMockResponse(detected=False, signal=None)
    return SlackMockResponse(detected=True, signal=_to_view(signal))
