"""Microsoft Graph 観測 tool (F-1 の入力源)。

ユーザーの Outlook メール / Teams メッセージから困りごとシグナルを検知する。
Application permission (Mail.Read, User.Read.All) を Managed Identity に付与済み。

Graph 接続失敗時 (権限不足・ネットワーク・ローカル開発で az login が DefaultAzureCredential
を満たさない場合など) は安全にデモ用 mock シグナルを返す。これによりオフラインでも
シナリオを再現できる。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import quote

import httpx
from azure.core.exceptions import ClientAuthenticationError

from src.tools.credential import get_default_credential

SignalSource = Literal["teams_message", "copilot_abandon", "repetitive_pattern"]

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"

# 困りごとを示唆する日本語キーワード (シンプルなマッチング)
PAIN_KEYWORDS = (
    "困って",
    "わからない",
    "分からない",
    "教えて",
    "どうやって",
    "助けて",
    "やり方",
    "時間がかか",
    "また",  # 反復作業の暗示
)


@dataclass(frozen=True)
class Signal:
    """観測 Agent の出力単位。"""

    user_id: str
    timestamp: str  # ISO8601
    source_signal: SignalSource
    raw_excerpt: str  # 140 字以内
    business_context_hint: str


def _build_excerpt(text: str, limit: int = 140) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1] + "…"


def _looks_like_pain(text: str) -> bool:
    if not text:
        return False
    return any(kw in text for kw in PAIN_KEYWORDS)


def _get_graph_token() -> str | None:
    """Graph API 用の bearer token を取得する。失敗時 None。"""
    try:
        credential = get_default_credential()
        return credential.get_token(GRAPH_SCOPE).token
    except ClientAuthenticationError:
        return None


def _fetch_recent_messages(user_id: str, token: str, top: int = 25) -> list[dict]:
    """Microsoft Graph 経由でユーザーの最近のメールを取得する。

    application permission Mail.Read が Managed Identity に付与されている必要がある。
    """
    headers = {"Authorization": f"Bearer {token}"}
    select_fields = "id,subject,bodyPreview,receivedDateTime"
    url = f"{GRAPH_BASE}/users/{quote(user_id, safe='')}/messages?$top={top}&$select={select_fields}&$orderby=receivedDateTime desc"
    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError:
        return []
    return response.json().get("value", [])


def _signals_from_messages(user_id: str, messages: list[dict]) -> list[Signal]:
    signals: list[Signal] = []
    for msg in messages:
        subject = msg.get("subject", "") or ""
        body = msg.get("bodyPreview", "") or ""
        combined = f"{subject} {body}".strip()
        if not _looks_like_pain(combined):
            continue
        timestamp = msg.get("receivedDateTime") or datetime.now(UTC).isoformat()
        signals.append(
            Signal(
                user_id=user_id,
                timestamp=timestamp,
                source_signal="teams_message",
                raw_excerpt=_build_excerpt(combined),
                business_context_hint=subject[:40] if subject else "",
            )
        )
    return signals


def _mock_signal(user_id: str) -> Signal:
    """Graph 経由でシグナルが得られなかった場合のデモ用 mock。"""
    return Signal(
        user_id=user_id,
        timestamp=datetime.now(UTC).isoformat(),
        source_signal="teams_message",
        raw_excerpt="月次レポート、また 8 時間かかった…",
        business_context_hint="月次レポート作成",
    )


def fetch_signals(user_id: str, since_iso: str | None = None) -> list[Signal]:
    """観測対象ユーザーの最近のシグナル候補を返す。

    実装方針:
      1. Microsoft Graph 経由でメールを取得し、キーワードマッチで困りごとを抽出
      2. 取得失敗 or ヒットなしならデモ用 mock を 1 件返す
         (ハッカソンデモの安定性を優先するためのフォールバック)

    Args:
        user_id: 観測対象の Entra ID オブジェクト ID または UPN
        since_iso: 未使用 (Phase 2 で $filter receivedDateTime ge ... に対応予定)

    Returns:
        Signal のリスト。
    """
    _ = since_iso  # Phase 2 で利用
    if not user_id:
        return []

    token = _get_graph_token()
    if token is None:
        return [_mock_signal(user_id)]

    messages = _fetch_recent_messages(user_id, token)
    signals = _signals_from_messages(user_id, messages)
    if not signals:
        return [_mock_signal(user_id)]
    return signals
