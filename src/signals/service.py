"""投稿を支援候補シグナルに変換して保存する検知サービス。

Slack Bot (src/slack/bot.py)、Teams アダプタ (src/teams/adapter.py)、
デモ用 API (POST /api/slack/mock 等) の共通入口。
分類 (classify) → URL 生成 → ストア保存 を 1 つの関数にまとめる。
プラットフォーム差分は source ("slack" / "teams") として受け取り、それ以外は共通化する。
"""

from __future__ import annotations

from dataclasses import replace

from src.signals.classify import build_kodama_url, classify
from src.signals.store import Signal, add_signal


def handle_message(
    *,
    channel_id: str,
    channel_name: str,
    slack_user_id: str,
    display_name: str,
    text: str,
    ts: str,
    base_url: str,
    source: str = "slack",
) -> Signal | None:
    """投稿を分類し、支援候補ならシグナルとして保存して返す。

    業務改善に無関係な投稿は分類で None になり、保存もしない (None を返す)。
    同一 (channel_id, ts) の重複投稿は既存シグナルを返す (二重登録しない)。

    Args:
        source: 検知元プラットフォーム ("slack" / "teams")。Signal と kodama_url の
            クエリに反映され、ダッシュボードがチャネルを区別できるようにする。

    Returns:
        登録 (or 既存) の Signal。無視した場合は None。
    """
    result = classify(text)
    if result is None:
        return None

    # kodama_url に signal_id を含めるため、先に Signal を組み立て、確定 URL で差し替える。
    signal = Signal(
        channel_id=channel_id,
        channel_name=channel_name,
        slack_user_id=slack_user_id,
        display_name=display_name,
        text=text.strip(),
        summary=result.summary,
        business_category=result.business_category,
        confidence=result.confidence,
        kodama_url="",
        source=source,
    )
    signal = replace(
        signal,
        kodama_url=build_kodama_url(base_url, result.business_category, signal.id, source=source),
    )

    stored, _is_new = add_signal(signal, ts=ts)
    return stored
