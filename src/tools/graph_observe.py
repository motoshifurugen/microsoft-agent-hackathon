"""Microsoft Graph 観測 tool (F-1 の入力源)。

MVP 段階では fetch_signals は mock データを返す。
Phase 2 で `/me/chats/{id}/messages` 等のエンドポイントに差し替える。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

SignalSource = Literal["teams_message", "copilot_abandon", "repetitive_pattern"]


@dataclass(frozen=True)
class Signal:
    """観測 Agent の出力単位。"""

    user_id: str
    timestamp: str  # ISO8601
    source_signal: SignalSource
    raw_excerpt: str  # 140 字以内
    business_context_hint: str


def fetch_signals(user_id: str, since_iso: str | None = None) -> list[Signal]:
    """観測対象ユーザーの最近のシグナル候補を返す。

    MVP 実装: 月次レポートで困っている田中さんを想定した mock を 1 件返す。
    Phase 2: Microsoft Graph (`/me/chats/.../messages`) に差し替え、since_iso 以降で絞り込み。

    Args:
        user_id: 観測対象の内部 ID
        since_iso: この時刻以降の発話のみ取得 (None なら直近 1 時間)

    Returns:
        Signal のリスト。空配列もあり得る。
    """
    _ = since_iso  # MVP では未使用 (Phase 2 で利用)
    if not user_id:
        return []

    return [
        Signal(
            user_id=user_id,
            timestamp=datetime.now(UTC).isoformat(),
            source_signal="teams_message",
            raw_excerpt="月次レポート、また 8 時間かかった…",
            business_context_hint="月次レポート作成",
        )
    ]
