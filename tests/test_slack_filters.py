"""Slack メッセージイベントのフィルタリングロジックのテスト。

対象チャネル以外 / Bot 自身 / スレッド返信 / 編集等の subtype を無視する。
"""

from __future__ import annotations

from src.slack.filters import is_target_message

TARGET = "C_HATENA"
BOT_USER = "U_BOT"


def _msg(**overrides: object) -> dict:
    base: dict[str, object] = {
        "channel": TARGET,
        "user": "U_HUMAN",
        "text": "月次レポートだりい",
        "ts": "1.1",
    }
    base.update(overrides)
    return base


class TestIsTargetMessage:
    def test_accepts_plain_message_in_target_channel(self) -> None:
        assert is_target_message(_msg(), target_channel_id=TARGET, bot_user_id=BOT_USER) is True

    def test_rejects_other_channel(self) -> None:
        assert (
            is_target_message(
                _msg(channel="C_OTHER"), target_channel_id=TARGET, bot_user_id=BOT_USER
            )
            is False
        )

    def test_rejects_bot_own_message_by_bot_id(self) -> None:
        assert (
            is_target_message(_msg(bot_id="B1"), target_channel_id=TARGET, bot_user_id=BOT_USER)
            is False
        )

    def test_rejects_bot_own_message_by_user_id(self) -> None:
        assert (
            is_target_message(_msg(user=BOT_USER), target_channel_id=TARGET, bot_user_id=BOT_USER)
            is False
        )

    def test_rejects_thread_reply(self) -> None:
        # thread_ts != ts はスレッド返信
        assert (
            is_target_message(
                _msg(ts="2.2", thread_ts="1.1"), target_channel_id=TARGET, bot_user_id=BOT_USER
            )
            is False
        )

    def test_accepts_thread_parent(self) -> None:
        # thread_ts == ts は親メッセージ (スレッド未発生扱い)
        assert (
            is_target_message(
                _msg(ts="1.1", thread_ts="1.1"), target_channel_id=TARGET, bot_user_id=BOT_USER
            )
            is True
        )

    def test_rejects_subtype_events(self) -> None:
        # message_changed / channel_join などの subtype は無視
        assert (
            is_target_message(
                _msg(subtype="message_changed"), target_channel_id=TARGET, bot_user_id=BOT_USER
            )
            is False
        )

    def test_rejects_empty_text(self) -> None:
        assert (
            is_target_message(_msg(text="  "), target_channel_id=TARGET, bot_user_id=BOT_USER)
            is False
        )
