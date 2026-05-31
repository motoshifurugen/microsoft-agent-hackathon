"""支援候補シグナルの in-memory ストア。

Slack 投稿を「業務カテゴリ + 困りごとの要約」に変換した軽量データのみを保持する
(Slack 全文の大量・恒久保存はしない方針)。board.py と同じく Lock + dict で実装し、
本実装では Cosmos DB への置き換えを想定する。

重複対策: (channel_id, ts) を一意キーにして二重登録を防ぐ。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock

_lock = Lock()
# signal id → Signal
_signals: dict[str, Signal] = {}
# 重複排除キー (channel_id + ts) → signal id
_dedup: dict[str, str] = {}


@dataclass(frozen=True)
class Signal:
    """Slack から拾った支援候補シグナル。"""

    channel_id: str
    channel_name: str
    slack_user_id: str
    display_name: str
    text: str
    summary: str
    business_category: str
    confidence: float
    kodama_url: str
    source: str = "slack"
    status: str = "detected"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def _dedup_key(channel_id: str, ts: str) -> str:
    return f"{channel_id}:{ts}"


def add_signal(signal: Signal, *, ts: str) -> tuple[Signal, bool]:
    """シグナルを登録する。

    同一 (channel_id, ts) が既に存在する場合は登録済みのものを返す (二重登録しない)。

    Returns:
        (登録 or 既存の Signal, 新規登録なら True)。
    """
    key = _dedup_key(signal.channel_id, ts)
    with _lock:
        existing_id = _dedup.get(key)
        if existing_id is not None:
            return _signals[existing_id], False
        _signals[signal.id] = signal
        _dedup[key] = signal.id
        return signal, True


def list_signals() -> list[Signal]:
    """全シグナルを作成日時の新しい順で返す。"""
    with _lock:
        items = list(_signals.values())
    items.sort(key=lambda s: s.created_at, reverse=True)
    return items


def reset_signals_for_tests() -> None:
    """テスト用に in-memory store をクリアする (本番からは呼ばない)。"""
    with _lock:
        _signals.clear()
        _dedup.clear()
