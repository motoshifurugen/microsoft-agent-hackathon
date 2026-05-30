"""Slack メッセージイベントの受理判定 (Azure/Slack 非依存の純粋関数)。

対象は `#はてなボックス` のトップレベル投稿のみ。以下は無視する:
- 対象チャネル以外
- Bot 自身の投稿 (bot_id あり / user が Bot)
- スレッド返信 (thread_ts != ts)
- 編集・参加など subtype 付きイベント
- 本文が空
"""

from __future__ import annotations


def is_target_message(
    event: dict,
    *,
    target_channel_id: str,
    bot_user_id: str | None = None,
) -> bool:
    """メッセージイベントを支援候補の検知対象にするか判定する。"""
    if event.get("channel") != target_channel_id:
        return False

    # 編集 (message_changed)・参加 (channel_join)・bot_message などの subtype は無視。
    if event.get("subtype"):
        return False

    # Bot 自身の投稿を無視 (bot_id 有り、または user が自分の Bot ユーザー)。
    if event.get("bot_id"):
        return False
    if bot_user_id and event.get("user") == bot_user_id:
        return False

    # スレッド返信を無視。thread_ts が無い、または ts と一致する親メッセージのみ受理。
    thread_ts = event.get("thread_ts")
    if thread_ts and thread_ts != event.get("ts"):
        return False

    return bool(str(event.get("text", "")).strip())
