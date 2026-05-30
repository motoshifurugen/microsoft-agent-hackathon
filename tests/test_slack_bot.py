"""Slack Bot のイベント処理 (process_event) のテスト。

slack_bolt の say を Mock に差し替え、フィルタ → 分類 → スレッド返信の流れを検証する。
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest

from src.signals.config import SlackConfig
from src.signals.store import list_signals, reset_signals_for_tests
from src.slack.bot import process_event

CONFIG = SlackConfig(
    bot_token="xoxb-x",
    app_token="xapp-x",
    channel_id="C_HATENA",
    channel_name="はてなボックス",
    kodama_base_url="http://localhost:8000",
)


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    reset_signals_for_tests()
    yield
    reset_signals_for_tests()


def _event(**overrides: object) -> dict:
    base: dict[str, object] = {
        "channel": "C_HATENA",
        "user": "U_HUMAN",
        "text": "月次レポートだりい",
        "ts": "1700000000.0001",
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_detected_message_replies_in_thread() -> None:
    say = AsyncMock()
    await process_event(_event(), config=CONFIG, say=say, bot_user_id="U_BOT")

    say.assert_awaited_once()
    assert say.await_args is not None
    kwargs = say.await_args.kwargs
    assert kwargs["thread_ts"] == "1700000000.0001"
    assert "その“はてな”、月次レポート作成に近そうです" in kwargs["text"]
    assert "http://localhost:8000/categories/" in kwargs["text"]
    assert len(list_signals()) == 1


@pytest.mark.asyncio
async def test_out_of_scope_message_does_not_reply() -> None:
    say = AsyncMock()
    await process_event(_event(text="今日は疲れた"), config=CONFIG, say=say, bot_user_id="U_BOT")

    say.assert_not_awaited()
    assert list_signals() == []


@pytest.mark.asyncio
async def test_other_channel_is_ignored() -> None:
    say = AsyncMock()
    await process_event(_event(channel="C_OTHER"), config=CONFIG, say=say, bot_user_id="U_BOT")

    say.assert_not_awaited()
    assert list_signals() == []


@pytest.mark.asyncio
async def test_bot_own_message_is_ignored() -> None:
    say = AsyncMock()
    await process_event(_event(user="U_BOT"), config=CONFIG, say=say, bot_user_id="U_BOT")

    say.assert_not_awaited()
    assert list_signals() == []


@pytest.mark.asyncio
async def test_thread_reply_is_ignored() -> None:
    say = AsyncMock()
    await process_event(
        _event(ts="1700000000.0002", thread_ts="1700000000.0001"),
        config=CONFIG,
        say=say,
        bot_user_id="U_BOT",
    )

    say.assert_not_awaited()
    assert list_signals() == []
