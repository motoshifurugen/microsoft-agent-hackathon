"""業務カテゴリのマスタ定義と正規化のテスト。

カテゴリを自由文字列のまま集約すると表記ゆれで分裂するため、
固定マスタ (GET /api/categories/master) を登録セレクトの単一の真実とし、
登録時に既知の別名を正規化する。マスタ外の自由入力 (その他) は素通しする。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.categories import CATEGORY_MASTER, normalize_category
from src.api.main import app
from src.tools.cosmos_io import reset_in_memory_stores


@pytest.fixture
def client() -> Iterator[TestClient]:
    reset_in_memory_stores()
    with TestClient(app) as c:
        yield c
    reset_in_memory_stores()


def _payload(**overrides: object) -> dict:
    base = {
        "client_id": "c-author",
        "owner_label": "テスト部 サンプルさん",
        "business_type": "メール作成",
        "what_worked": "下書きを生成",
    }
    base.update(overrides)
    return base


class TestNormalizeCategory:
    def test_known_alias_is_canonicalized(self) -> None:
        assert normalize_category("経費精算チェック") == "経費精算"

    def test_trims_whitespace(self) -> None:
        assert normalize_category("  メール作成  ") == "メール作成"

    def test_unknown_value_passes_through(self) -> None:
        assert normalize_category("独自カテゴリABC") == "独自カテゴリABC"

    def test_master_value_unchanged(self) -> None:
        for name in CATEGORY_MASTER:
            assert normalize_category(name) == name


class TestCategoryMasterEndpoint:
    def test_returns_ordered_canonical_list(self, client: TestClient) -> None:
        res = client.get("/api/categories/master")
        assert res.status_code == 200
        body = res.json()
        assert body == CATEGORY_MASTER

    def test_includes_expected_categories(self, client: TestClient) -> None:
        body = client.get("/api/categories/master").json()
        assert "経費精算" in body
        assert "アンケート集計" in body
        # 正規化前の表記はマスタに含めない
        assert "経費精算チェック" not in body

    def test_master_has_no_duplicates(self, client: TestClient) -> None:
        body = client.get("/api/categories/master").json()
        assert len(body) == len(set(body))


class TestCreateCaseNormalization:
    def test_alias_normalized_on_create(self, client: TestClient) -> None:
        res = client.post("/api/cases", json=_payload(business_type="経費精算チェック"))
        assert res.status_code == 201
        assert res.json()["business_type"] == "経費精算"

    def test_normalized_case_grouped_under_canonical(self, client: TestClient) -> None:
        client.post("/api/cases", json=_payload(business_type="経費精算チェック"))
        # 正規化後のカテゴリ名で取得できる
        res = client.get("/api/categories/経費精算/cases")
        assert res.status_code == 200
        assert any(c["business_type"] == "経費精算" for c in res.json()["cases"])
        # 正規化前の名前ではヒットしない
        assert client.get("/api/categories/経費精算チェック/cases").status_code == 404

    def test_free_text_category_preserved(self, client: TestClient) -> None:
        res = client.post("/api/cases", json=_payload(business_type="独自カテゴリABC"))
        assert res.status_code == 201
        assert res.json()["business_type"] == "独自カテゴリABC"
