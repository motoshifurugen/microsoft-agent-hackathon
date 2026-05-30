"""/api/signals と /api/slack/mock のエンドポイントテスト。"""

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


class TestSignalsApi:
    def test_signals_empty_initially(self, client: TestClient) -> None:
        response = client.get("/api/signals")
        assert response.status_code == 200
        assert response.json() == []

    def test_mock_detects_and_lists_signal(self, client: TestClient) -> None:
        response = client.post(
            "/api/slack/mock",
            json={"text": "月次レポートだりい", "display_name": "細川さん"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["detected"] is True
        signal = body["signal"]
        assert signal["business_category"] == "月次レポート作成"
        assert signal["source"] == "slack"
        assert signal["text"] == "月次レポートだりい"
        assert signal["summary"]
        assert signal["kodama_url"].startswith("http")
        assert "created_at" in signal

        listed = client.get("/api/signals").json()
        assert len(listed) == 1
        assert listed[0]["id"] == signal["id"]

    def test_mock_ignores_non_business(self, client: TestClient) -> None:
        response = client.post("/api/slack/mock", json={"text": "今日は疲れた"})
        assert response.status_code == 200
        body = response.json()
        assert body["detected"] is False
        assert body["signal"] is None
        assert client.get("/api/signals").json() == []

    def test_mock_rejects_blank_text(self, client: TestClient) -> None:
        response = client.post("/api/slack/mock", json={"text": "   "})
        assert response.status_code == 422

    def test_signal_response_shape(self, client: TestClient) -> None:
        client.post(
            "/api/slack/mock",
            json={
                "text": "議事録まとめるの毎回しんどい",
                "channel_id": "C999",
                "channel_name": "はてなボックス",
                "slack_user_id": "U999",
                "display_name": "佐藤さん",
            },
        )
        signal = client.get("/api/signals").json()[0]
        for key in (
            "id",
            "source",
            "channel_id",
            "channel_name",
            "slack_user_id",
            "display_name",
            "text",
            "summary",
            "business_category",
            "confidence",
            "status",
            "kodama_url",
            "created_at",
        ):
            assert key in signal, f"missing {key}"
        assert signal["source"] == "slack"
        assert signal["channel_id"] == "C999"
