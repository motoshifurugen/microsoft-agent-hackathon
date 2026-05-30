"""支援候補シグナルの in-memory ストアと検知サービスのテスト。"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from src.signals.service import handle_message
from src.signals.store import list_signals, reset_signals_for_tests


@pytest.fixture(autouse=True)
def _reset() -> Iterator[None]:
    reset_signals_for_tests()
    yield
    reset_signals_for_tests()


class TestHandleMessage:
    def test_detected_message_is_stored(self) -> None:
        signal = handle_message(
            channel_id="C123",
            channel_name="はてなボックス",
            slack_user_id="U123",
            display_name="細川さん",
            text="月次レポートだりい",
            ts="1700000000.000100",
            base_url="http://localhost:8000",
        )
        assert signal is not None
        assert signal.source == "slack"
        assert signal.business_category == "月次レポート作成"
        assert signal.status == "detected"
        assert signal.channel_id == "C123"
        assert signal.kodama_url.startswith("http://localhost:8000/categories/")
        assert len(list_signals()) == 1

    def test_non_business_message_is_ignored(self) -> None:
        signal = handle_message(
            channel_id="C123",
            channel_name="はてなボックス",
            slack_user_id="U123",
            display_name="",
            text="今日は疲れた",
            ts="1700000000.000200",
            base_url="http://localhost:8000",
        )
        assert signal is None
        assert list_signals() == []

    def test_duplicate_ts_is_not_double_registered(self) -> None:
        kwargs = {
            "channel_id": "C123",
            "channel_name": "はてなボックス",
            "slack_user_id": "U123",
            "display_name": "",
            "text": "議事録まとめるの毎回しんどい",
            "ts": "1700000000.000300",
            "base_url": "http://localhost:8000",
        }
        first = handle_message(**kwargs)
        second = handle_message(**kwargs)
        assert first is not None
        assert second is not None
        # 同一 (channel_id, ts) は同じ signal を返し、二重登録しない
        assert first.id == second.id
        assert len(list_signals()) == 1

    def test_list_signals_is_newest_first(self) -> None:
        handle_message(
            channel_id="C1",
            channel_name="はてなボックス",
            slack_user_id="U1",
            display_name="",
            text="経費精算チェックが面倒",
            ts="1700000000.000001",
            base_url="http://localhost:8000",
        )
        handle_message(
            channel_id="C1",
            channel_name="はてなボックス",
            slack_user_id="U1",
            display_name="",
            text="アンケート集計がつらい",
            ts="1700000000.000002",
            base_url="http://localhost:8000",
        )
        signals = list_signals()
        assert len(signals) == 2
        assert signals[0].created_at >= signals[1].created_at
