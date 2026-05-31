"""成功事例の登録 API (POST /api/cases) のテスト。

ShareCTA のトーストに代わり、ユーザーが自分の成功事例をフォームから登録できるようにする。
登録された事例は in-memory store に入り、カテゴリ一覧や検索の対象になる。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.tools.cosmos_io import get_all_success_cases, reset_in_memory_stores


@pytest.fixture
def client() -> Iterator[TestClient]:
    reset_in_memory_stores()
    with TestClient(app) as c:
        yield c
    reset_in_memory_stores()


def _valid_payload(**overrides: object) -> dict:
    payload = {
        "client_id": "c-author",
        "owner_label": "テスト部 サンプルさん",
        "business_type": "週次報告作成",
        "what_worked": "Copilot で前週ログから下書きを生成",
        "why_worked": "定型作業のテンプレ化が効いた",
        "concrete_prompt": "以下のログを週次報告の体裁にまとめて: ...",
        "quantitative_effect": "週 2h → 30min",
        "reproducibility_score": 0.7,
    }
    payload.update(overrides)
    return payload


class TestCreateCase:
    def test_creates_and_returns_case(self, client: TestClient) -> None:
        res = client.post("/api/cases", json=_valid_payload())
        assert res.status_code == 201
        body = res.json()
        assert body["case_id"]
        assert body["owner_label"] == "テスト部 サンプルさん"
        assert body["business_type"] == "週次報告作成"
        assert body["reproducibility_score"] == 0.7

    def test_case_is_persisted(self, client: TestClient) -> None:
        before = len(get_all_success_cases())
        client.post("/api/cases", json=_valid_payload())
        assert len(get_all_success_cases()) == before + 1

    def test_created_case_appears_in_category(self, client: TestClient) -> None:
        client.post("/api/cases", json=_valid_payload(business_type="新カテゴリXYZ"))
        res = client.get("/api/categories/新カテゴリXYZ/cases")
        assert res.status_code == 200
        assert len(res.json()["cases"]) == 1

    def test_reproducibility_defaults_when_omitted(self, client: TestClient) -> None:
        payload = _valid_payload()
        del payload["reproducibility_score"]
        res = client.post("/api/cases", json=payload)
        assert res.status_code == 201
        assert 0.0 <= res.json()["reproducibility_score"] <= 1.0

    def test_optional_fields_default_empty(self, client: TestClient) -> None:
        payload = _valid_payload()
        for k in ("why_worked", "concrete_prompt", "quantitative_effect"):
            del payload[k]
        res = client.post("/api/cases", json=payload)
        assert res.status_code == 201

    def test_missing_required_field_rejected(self, client: TestClient) -> None:
        payload = _valid_payload()
        del payload["what_worked"]
        res = client.post("/api/cases", json=payload)
        assert res.status_code == 422

    def test_blank_business_type_rejected(self, client: TestClient) -> None:
        res = client.post("/api/cases", json=_valid_payload(business_type="   "))
        assert res.status_code == 422

    def test_reproducibility_out_of_range_rejected(self, client: TestClient) -> None:
        res = client.post("/api/cases", json=_valid_payload(reproducibility_score=1.5))
        assert res.status_code == 422


class TestListMyCases:
    def test_returns_only_callers_cases(self, client: TestClient) -> None:
        client.post("/api/cases", json=_valid_payload(client_id="c-A", business_type="メール作成"))
        client.post("/api/cases", json=_valid_payload(client_id="c-A", business_type="提案書作成"))
        client.post("/api/cases", json=_valid_payload(client_id="c-B", business_type="データ集計"))

        res = client.get("/api/cases", params={"client_id": "c-A"})
        assert res.status_code == 200
        body = res.json()
        assert len(body) == 2
        assert {c["business_type"] for c in body} == {"メール作成", "提案書作成"}

    def test_unknown_client_returns_empty(self, client: TestClient) -> None:
        # seed 事例の user_id とは一致しない client_id
        res = client.get("/api/cases", params={"client_id": "c-nobody"})
        assert res.status_code == 200
        assert res.json() == []

    def test_newest_registered_first(self, client: TestClient) -> None:
        client.post("/api/cases", json=_valid_payload(client_id="c-A", business_type="メール作成"))
        client.post("/api/cases", json=_valid_payload(client_id="c-A", business_type="提案書作成"))
        body = client.get("/api/cases", params={"client_id": "c-A"}).json()
        assert [c["business_type"] for c in body] == ["提案書作成", "メール作成"]

    def test_blank_client_id_rejected(self, client: TestClient) -> None:
        res = client.get("/api/cases", params={"client_id": ""})
        assert res.status_code == 422

    def test_missing_client_id_rejected(self, client: TestClient) -> None:
        res = client.get("/api/cases")
        assert res.status_code == 422
