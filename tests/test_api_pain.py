"""WebApp 困りごと入力欄のマッチング API (POST /api/pain/match) テスト。

ユーザーが画面に入力した困りごとを semantic_search で類似事例に紐づけ、
同時に PainPoint として source_signal="webapp_input" で永続化する。
Azure 接続なしで動かすため、検索は文字列マッチ fallback 経路。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.tools.cosmos_io import get_all_pain_points, reset_in_memory_stores


@pytest.fixture
def client() -> Iterator[TestClient]:
    reset_in_memory_stores()
    with TestClient(app) as c:
        yield c
    reset_in_memory_stores()


class TestPainMatch:
    def test_returns_matched_cases(self, client: TestClient) -> None:
        response = client.post(
            "/api/pain/match",
            json={"text": "月次レポート作成に毎月時間がかかって困っている"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "月次レポート作成に毎月時間がかかって困っている"
        assert body["pain_point_id"]
        assert len(body["cases"]) >= 1
        for case in body["cases"]:
            assert case["owner_label"]
            assert "score" in case

    def test_persists_pain_point_with_webapp_source(self, client: TestClient) -> None:
        client.post("/api/pain/match", json={"text": "議事録の要約が面倒"})
        points = list(get_all_pain_points().values())
        assert len(points) == 1
        pp = points[0]
        assert pp["source_signal"] == "webapp_input"
        assert pp["pain_description"] == "議事録の要約が面倒"

    def test_persists_client_id_and_business_context(self, client: TestClient) -> None:
        client.post(
            "/api/pain/match",
            json={
                "text": "提案書作成が苦手",
                "client_id": "c-abc123",
                "business_context": "営業",
            },
        )
        pp = next(iter(get_all_pain_points().values()))
        assert pp["user_id"] == "c-abc123"
        assert pp["business_context"] == "営業"

    def test_anonymous_when_no_client_id(self, client: TestClient) -> None:
        client.post("/api/pain/match", json={"text": "メール作成が大変"})
        pp = next(iter(get_all_pain_points().values()))
        assert pp["user_id"] == "anonymous-webapp"

    def test_empty_text_rejected(self, client: TestClient) -> None:
        response = client.post("/api/pain/match", json={"text": ""})
        assert response.status_code == 422

    def test_whitespace_only_text_rejected(self, client: TestClient) -> None:
        response = client.post("/api/pain/match", json={"text": "   "})
        assert response.status_code == 422

    def test_top_k_caps_results(self, client: TestClient) -> None:
        response = client.post(
            "/api/pain/match",
            json={"text": "月次レポート", "top_k": 2},
        )
        assert response.status_code == 200
        assert len(response.json()["cases"]) <= 2

    def test_top_k_out_of_range_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/pain/match",
            json={"text": "月次レポート", "top_k": 99},
        )
        assert response.status_code == 422

    def test_no_match_still_persists_pain(self, client: TestClient) -> None:
        response = client.post(
            "/api/pain/match",
            json={"text": "全く関係のないクエリ xyzzy"},
        )
        assert response.status_code == 200
        # マッチが 0 件でも困りごとは記録される
        assert len(get_all_pain_points()) == 1
