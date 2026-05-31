"""Teams Bot Framework アダプタ (src/teams/adapter.py) の単体テスト。"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from src.signals.store import reset_signals_for_tests
from src.teams.adapter import (
    DEFAULT_CHANNEL_NAME,
    SOURCE,
    build_reply_activity,
    detect_from_activity,
    extract_message,
    is_target_activity,
)

BASE_URL = "https://kodama.example.com"


def _message_activity(text: str, **overrides) -> dict:
    activity = {
        "type": "message",
        "text": text,
        "id": "act-1",
        "from": {"id": "29:user-aad-id", "name": "細川さん", "role": "user"},
        "conversation": {"id": "19:conv-id", "name": "業務相談"},
    }
    activity.update(overrides)
    return activity


@pytest.fixture(autouse=True)
def _clean_store() -> Iterator[None]:
    reset_signals_for_tests()
    yield
    reset_signals_for_tests()


class TestIsTargetActivity:
    def test_accepts_user_message_with_text(self) -> None:
        assert is_target_activity(_message_activity("月次レポートだりい")) is True

    def test_rejects_non_message_type(self) -> None:
        assert is_target_activity(_message_activity("hi", type="typing")) is False

    def test_rejects_bot_sender(self) -> None:
        activity = _message_activity("月次レポート", **{"from": {"id": "b", "role": "bot"}})
        assert is_target_activity(activity) is False

    def test_rejects_blank_text(self) -> None:
        assert is_target_activity(_message_activity("   ")) is False


class TestExtractMessage:
    def test_extracts_fields(self) -> None:
        msg = extract_message(_message_activity("月次レポートだりい"))
        assert msg is not None
        assert msg.text == "月次レポートだりい"
        assert msg.user_id == "29:user-aad-id"
        assert msg.display_name == "細川さん"
        assert msg.conversation_id == "19:conv-id"
        assert msg.activity_id == "act-1"
        assert msg.channel_name == "業務相談"

    def test_defaults_channel_name_when_missing(self) -> None:
        activity = _message_activity("月次レポート", conversation={"id": "19:c"})
        msg = extract_message(activity)
        assert msg is not None
        assert msg.channel_name == DEFAULT_CHANNEL_NAME

    def test_returns_none_for_out_of_target(self) -> None:
        assert extract_message(_message_activity("hi", type="typing")) is None


class TestDetectFromActivity:
    def test_business_text_becomes_teams_signal(self) -> None:
        signal = detect_from_activity(_message_activity("月次レポートだりい"), base_url=BASE_URL)
        assert signal is not None
        assert signal.source == SOURCE
        assert signal.business_category == "月次レポート作成"
        assert signal.slack_user_id == "29:user-aad-id"
        assert "source=teams" in signal.kodama_url
        assert signal.kodama_url.startswith(BASE_URL)

    def test_non_business_text_is_ignored(self) -> None:
        assert detect_from_activity(_message_activity("今日は疲れた"), base_url=BASE_URL) is None

    def test_out_of_target_is_ignored(self) -> None:
        activity = _message_activity("月次レポート", type="conversationUpdate")
        assert detect_from_activity(activity, base_url=BASE_URL) is None

    def test_duplicate_activity_id_not_double_registered(self) -> None:
        a = _message_activity("月次レポートだりい")
        first = detect_from_activity(a, base_url=BASE_URL)
        second = detect_from_activity(a, base_url=BASE_URL)
        assert first is not None and second is not None
        assert first.id == second.id


class TestBuildReplyActivity:
    def test_contains_text_and_adaptive_card(self) -> None:
        reply = build_reply_activity("月次レポート作成", f"{BASE_URL}/categories/x?source=teams")
        assert reply["type"] == "message"
        assert "月次レポート作成" in reply["text"]
        card = reply["attachments"][0]
        assert card["contentType"] == "application/vnd.microsoft.card.adaptive"
        action = card["content"]["actions"][0]
        assert action["type"] == "Action.OpenUrl"
        assert action["url"].endswith("source=teams")
