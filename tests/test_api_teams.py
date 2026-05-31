"""POST /api/teams/messages のエンドポイントテスト。"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.signals.store import reset_signals_for_tests


@pytest.fixture
def client() -> Iterator[TestClient]:
    reset_signals_for_tests()
    with TestClient(app) as c:
        yield c
    reset_signals_for_tests()


def _activity(text: str, **overrides) -> dict:
    activity = {
        "type": "message",
        "text": text,
        "id": "act-1",
        "from": {"id": "29:user", "name": "佐藤さん", "role": "user"},
        "conversation": {"id": "19:conv", "name": "業務相談"},
    }
    activity.update(overrides)
    return activity


class TestTeamsMessagesApi:
    def test_business_message_replies_and_lists_signal(self, client: TestClient) -> None:
        res = client.post("/api/teams/messages", json=_activity("議事録まとめるの毎回しんどい"))
        assert res.status_code == 200
        body = res.json()
        assert body["replied"] is True
        assert body["signal"]["source"] == "teams"
        assert body["signal"]["business_category"] == "議事録要約"
        card = body["reply_activity"]["attachments"][0]
        assert card["contentType"] == "application/vnd.microsoft.card.adaptive"

        listed = client.get("/api/signals").json()
        assert len(listed) == 1
        assert listed[0]["source"] == "teams"

    def test_non_business_message_not_replied(self, client: TestClient) -> None:
        res = client.post("/api/teams/messages", json=_activity("今日は疲れた"))
        assert res.status_code == 200
        body = res.json()
        assert body["replied"] is False
        assert body["reply_activity"] is None
        assert client.get("/api/signals").json() == []

    def test_bot_message_ignored(self, client: TestClient) -> None:
        res = client.post(
            "/api/teams/messages",
            json=_activity("月次レポート", **{"from": {"id": "b", "role": "bot"}}),
        )
        assert res.status_code == 200
        assert res.json()["replied"] is False

    def test_typing_activity_ignored(self, client: TestClient) -> None:
        res = client.post("/api/teams/messages", json=_activity("月次レポート", type="typing"))
        assert res.status_code == 200
        assert res.json()["replied"] is False
