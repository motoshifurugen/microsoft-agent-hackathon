"""Skill ブックマーク API (/api/bookmarks) のテスト。

認証が無いため、localStorage 由来の client_id で所有者を区別してサーバー側に永続化する。
GET/POST/DELETE すべて当該 client_id のブックマーク事例一覧 (CaseDetail) を返す。
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


def _any_case_id(client: TestClient) -> str:
    # lifespan で seed 済みの成功事例から 1 件取得する
    return next(iter(get_all_success_cases().keys()))


class TestBookmarks:
    def test_empty_for_new_client(self, client: TestClient) -> None:
        res = client.get("/api/bookmarks", params={"client_id": "c-new"})
        assert res.status_code == 200
        assert res.json() == []

    def test_add_then_list(self, client: TestClient) -> None:
        case_id = _any_case_id(client)
        add = client.post("/api/bookmarks", json={"client_id": "c-1", "case_id": case_id})
        assert add.status_code == 200
        cases = add.json()
        assert any(c["case_id"] == case_id for c in cases)

        listed = client.get("/api/bookmarks", params={"client_id": "c-1"}).json()
        assert [c["case_id"] for c in listed] == [case_id]

    def test_add_is_idempotent(self, client: TestClient) -> None:
        case_id = _any_case_id(client)
        client.post("/api/bookmarks", json={"client_id": "c-1", "case_id": case_id})
        client.post("/api/bookmarks", json={"client_id": "c-1", "case_id": case_id})
        listed = client.get("/api/bookmarks", params={"client_id": "c-1"}).json()
        assert len(listed) == 1

    def test_bookmarks_are_per_client(self, client: TestClient) -> None:
        case_id = _any_case_id(client)
        client.post("/api/bookmarks", json={"client_id": "c-1", "case_id": case_id})
        other = client.get("/api/bookmarks", params={"client_id": "c-2"}).json()
        assert other == []

    def test_delete_removes(self, client: TestClient) -> None:
        case_id = _any_case_id(client)
        client.post("/api/bookmarks", json={"client_id": "c-1", "case_id": case_id})
        deleted = client.delete("/api/bookmarks", params={"client_id": "c-1", "case_id": case_id})
        assert deleted.status_code == 200
        assert deleted.json() == []

    def test_delete_is_idempotent(self, client: TestClient) -> None:
        case_id = _any_case_id(client)
        res = client.delete("/api/bookmarks", params={"client_id": "c-1", "case_id": case_id})
        assert res.status_code == 200
        assert res.json() == []

    def test_add_unknown_case_returns_404(self, client: TestClient) -> None:
        res = client.post("/api/bookmarks", json={"client_id": "c-1", "case_id": "does-not-exist"})
        assert res.status_code == 404

    def test_missing_client_id_rejected(self, client: TestClient) -> None:
        res = client.get("/api/bookmarks")
        assert res.status_code == 422

    def test_blank_client_id_rejected(self, client: TestClient) -> None:
        case_id = _any_case_id(client)
        res = client.post("/api/bookmarks", json={"client_id": "", "case_id": case_id})
        assert res.status_code == 422
