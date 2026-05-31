"""Microsoft Teams (Bot Framework) の受信エンドポイント。

- POST /api/teams/messages : Azure Bot Service が Teams 発話を配信する messaging endpoint。
  受信した Bot Framework Activity を分類し、支援候補なら返信 Activity (Adaptive Card 付き) を返す。

Slack の Socket Mode と異なり Teams は HTTP push 型のため、本番の配信先もこの 1 本に集約される
(別途デモ用エンドポイントは設けない)。最小 Activity を curl で POST すればデモ検証もできる。

本番化の TODO (MVP では未実装):
- Authorization ヘッダの Bot Framework JWT 検証 (なりすまし防止)。
- 返信は本来 activity.serviceUrl の Connector API へ POST する。ここでは検証/デモのため
  組み立てた返信 Activity を HTTP レスポンスで返している。
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from src.api.signals import SignalView, _to_view
from src.signals.config import load_kodama_base_url
from src.teams.adapter import build_reply_activity, detect_from_activity

router = APIRouter(prefix="/api", tags=["teams"])


class TeamsFrom(BaseModel):
    """Activity の発話者 (Bot Framework ChannelAccount の部分集合)。"""

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""
    role: str = ""


class TeamsConversation(BaseModel):
    """Activity の会話 (チャネル/スレッド)。"""

    model_config = ConfigDict(extra="ignore")

    id: str = ""
    name: str = ""


class TeamsActivity(BaseModel):
    """Bot Framework Activity の、検知に必要なフィールドのみを受理するスキーマ。

    Teams は多数のフィールドを送るため extra="ignore" で未知フィールドを捨てる。
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    type: str = ""
    text: str = ""
    id: str = ""
    sender: TeamsFrom = Field(default_factory=TeamsFrom, alias="from")
    conversation: TeamsConversation = Field(default_factory=TeamsConversation)


class TeamsReplyResponse(BaseModel):
    """検知結果。replied=False は支援候補にしなかった (= 返信しない) ことを示す。"""

    replied: bool
    reply_activity: dict | None = None
    signal: SignalView | None = None


@router.post("/teams/messages", response_model=TeamsReplyResponse)
def post_teams_messages(activity: TeamsActivity) -> TeamsReplyResponse:
    """Teams 発話を分類し、支援候補なら Adaptive Card 付きの返信 Activity を返す。"""
    signal = detect_from_activity(
        activity.model_dump(by_alias=True), base_url=load_kodama_base_url()
    )
    if signal is None:
        return TeamsReplyResponse(replied=False)
    reply = build_reply_activity(signal.business_category, signal.kodama_url)
    return TeamsReplyResponse(replied=True, reply_activity=reply, signal=_to_view(signal))
