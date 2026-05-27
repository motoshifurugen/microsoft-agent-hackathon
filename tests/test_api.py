"""Kodama dashboard API のエンドポイントテスト。

社員系 (/api/categories, /api/today) と管理者系 (/api/admin/*) の両方をカバーする。
Azure 接続なしで動かすため、起動時 lifespan は embedding 失敗 → 文字列マッチへフォールバック経路。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.admin import _strategy_executions
from src.api.main import app
from src.tools.cosmos_io import _embeddings, _success_cases


@pytest.fixture
def client() -> Iterator[TestClient]:
    """毎テストで in-memory store を初期化してから lifespan 起動。"""
    _success_cases.clear()
    _embeddings.clear()
    _strategy_executions.clear()
    with TestClient(app) as c:
        yield c
    _success_cases.clear()
    _embeddings.clear()
    _strategy_executions.clear()


# --- ヘルスチェック ---


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "kodama"


# --- 社員系 (employee) ---


class TestCategories:
    def test_list_categories(self, client: TestClient) -> None:
        response = client.get("/api/categories")
        assert response.status_code == 200
        categories = response.json()
        # サンプルデータには複数カテゴリが存在
        assert len(categories) >= 3
        # 件数の多い順 (= 月次レポート作成が先頭の想定)
        counts = [c["case_count"] for c in categories]
        assert counts == sorted(counts, reverse=True)
        # 必須フィールド
        for c in categories:
            assert c.get("name")
            assert "case_count" in c
            assert c["case_count"] >= 1

    def test_cases_in_category(self, client: TestClient) -> None:
        response = client.get("/api/categories/月次レポート作成/cases")
        assert response.status_code == 200
        body = response.json()
        assert body["category"] == "月次レポート作成"
        assert len(body["cases"]) >= 2
        # reproducibility 降順
        scores = [c["reproducibility_score"] for c in body["cases"]]
        assert scores == sorted(scores, reverse=True)
        # 各事例に owner_label / concrete_prompt がある
        for c in body["cases"]:
            assert c["owner_label"]
            assert c["concrete_prompt"]

    def test_unknown_category_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/categories/存在しないカテゴリ/cases")
        assert response.status_code == 404


class TestToday:
    def test_today_returns_one_case(self, client: TestClient) -> None:
        response = client.get("/api/today")
        assert response.status_code == 200
        body = response.json()
        assert "case" in body
        assert body.get("headline")
        assert body["case"]["owner_label"]

    def test_today_is_deterministic_within_a_day(self, client: TestClient) -> None:
        """同じ日に複数回呼んでも同じ事例が返る。"""
        a = client.get("/api/today").json()
        b = client.get("/api/today").json()
        assert a["case"]["case_id"] == b["case"]["case_id"]


# --- 管理者系 (admin) ---


class TestAdminUsers:
    def test_returns_ten_users(self, client: TestClient) -> None:
        response = client.get("/api/admin/users")
        assert response.status_code == 200
        users = response.json()
        assert len(users) == 10
        for u in users:
            assert "user_id" in u
            assert "owner_label" in u
            assert "business_type" in u

    def test_users_have_unique_ids(self, client: TestClient) -> None:
        users = client.get("/api/admin/users").json()
        user_ids = [u["user_id"] for u in users]
        assert len(user_ids) == len(set(user_ids))


class TestAdminRecommendations:
    def test_returns_three_with_strategies(self, client: TestClient) -> None:
        response = client.get("/api/admin/users/u-takahashi-008/recommendations")
        assert response.status_code == 200
        body = response.json()
        assert body["target_user_id"] == "u-takahashi-008"
        assert len(body["cases"]) <= 3
        # 戦略 A/B が両方返る
        ids = {s["id"] for s in body["strategies"]}
        assert ids == {"A", "B"}

    def test_target_user_excluded(self, client: TestClient) -> None:
        body = client.get("/api/admin/users/u-takahashi-008/recommendations").json()
        # 経費精算チェック事例は高橋さんのみ → 除外で別カテゴリが上位に来る
        business_types = {c["business_type"] for c in body["cases"]}
        assert "経費精算チェック" not in business_types

    def test_unknown_user_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/admin/users/u-not-exist/recommendations")
        assert response.status_code == 404

    def test_cases_have_enriched_fields(self, client: TestClient) -> None:
        body = client.get("/api/admin/users/u-sato-001/recommendations").json()
        for case in body["cases"]:
            assert "owner_label" in case
            assert "concrete_prompt" in case
            assert "quantitative_effect" in case
            assert isinstance(case["score"], float)


class TestAdminStrategyExecute:
    def _first_case_id(self, client: TestClient) -> str:
        body = client.get("/api/admin/users/u-sato-001/recommendations").json()
        return body["cases"][0]["case_id"]

    def test_execute_a(self, client: TestClient) -> None:
        case_id = self._first_case_id(client)
        response = client.post(
            "/api/admin/strategies/A/execute",
            json={"target_user_id": "u-sato-001", "case_id": case_id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["strategy_id"] == "A"
        assert "お時間" in body["message_preview"] or "紹介" in body["message_preview"]
        assert body["execution_id"].startswith("exec-")

    def test_execute_b(self, client: TestClient) -> None:
        case_id = self._first_case_id(client)
        response = client.post(
            "/api/admin/strategies/B/execute",
            json={"target_user_id": "u-sato-001", "case_id": case_id},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["strategy_id"] == "B"
        # 戦略 B は concrete_prompt を含む
        assert "プロンプト" in body["message_preview"]

    def test_invalid_strategy_id(self, client: TestClient) -> None:
        # FastAPI が Literal["A", "B"] でバリデートするため 422
        response = client.post(
            "/api/admin/strategies/X/execute",
            json={"target_user_id": "u-sato-001", "case_id": "any"},
        )
        assert response.status_code == 422

    def test_unknown_case_id(self, client: TestClient) -> None:
        response = client.post(
            "/api/admin/strategies/A/execute",
            json={"target_user_id": "u-sato-001", "case_id": "case-does-not-exist"},
        )
        assert response.status_code == 404

    def test_executions_persisted_in_memory(self, client: TestClient) -> None:
        case_id = self._first_case_id(client)
        client.post(
            "/api/admin/strategies/A/execute",
            json={"target_user_id": "u-sato-001", "case_id": case_id},
        )
        response = client.get("/api/admin/executions")
        assert response.status_code == 200
        executions = response.json()
        assert len(executions) == 1
        assert executions[0]["strategy_id"] == "A"
