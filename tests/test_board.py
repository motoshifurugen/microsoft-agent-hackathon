"""困りごと掲示板 API のテスト。"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.api.board import reset_board_for_tests
from src.api.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    reset_board_for_tests()
    with TestClient(app) as c:
        yield c
    reset_board_for_tests()


class TestQuestions:
    def test_list_seeded_questions(self, client: TestClient) -> None:
        # lifespan で seed_sample_board が走る → 2 件投入
        response = client.get("/api/board/questions")
        assert response.status_code == 200
        questions = response.json()
        assert len(questions) == 2
        # 新しい順 (タイ的に順序は気にしない)
        for q in questions:
            assert "id" in q
            assert q["title"]
            assert q["body"]
            assert q["answer_count"] >= 0

    def test_create_question(self, client: TestClient) -> None:
        response = client.post(
            "/api/board/questions",
            json={
                "title": "議事録要約のコツを教えてください",
                "body": "会議が多くて議事録に時間がかかります",
                "business_category": "議事録要約",
                "author": "総務部 鈴木",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "議事録要約のコツを教えてください"
        assert body["author"] == "総務部 鈴木"
        assert body["answer_count"] == 0
        assert body["id"]

    def test_create_question_anonymous_when_author_missing(self, client: TestClient) -> None:
        response = client.post(
            "/api/board/questions",
            json={"title": "テスト", "body": "本文"},
        )
        assert response.status_code == 200
        assert response.json()["author"] == "匿名"

    def test_get_question_with_answers(self, client: TestClient) -> None:
        # seed されている既存の質問 ID を取得
        first = client.get("/api/board/questions").json()[0]
        detail = client.get(f"/api/board/questions/{first['id']}")
        assert detail.status_code == 200
        body = detail.json()
        assert body["id"] == first["id"]
        assert "answers" in body
        # seed では各質問に 1 件回答が付いている
        assert len(body["answers"]) >= 1

    def test_get_unknown_question_404(self, client: TestClient) -> None:
        response = client.get("/api/board/questions/does-not-exist")
        assert response.status_code == 404


class TestAnswers:
    def test_create_answer(self, client: TestClient) -> None:
        question = client.post(
            "/api/board/questions",
            json={"title": "新規質問", "body": "本文"},
        ).json()
        response = client.post(
            f"/api/board/questions/{question['id']}/answers",
            json={"body": "こうしたら良いです", "author": "営業 田中"},
        )
        assert response.status_code == 200
        answer = response.json()
        assert answer["body"] == "こうしたら良いです"
        assert answer["author"] == "営業 田中"
        assert answer["question_id"] == question["id"]
        # 質問詳細で answer_count が増えていること
        detail = client.get(f"/api/board/questions/{question['id']}").json()
        assert detail["answer_count"] == 1
        assert len(detail["answers"]) == 1

    def test_create_answer_404_for_unknown_question(self, client: TestClient) -> None:
        response = client.post(
            "/api/board/questions/does-not-exist/answers",
            json={"body": "回答"},
        )
        assert response.status_code == 404

    def test_empty_body_rejected(self, client: TestClient) -> None:
        question = client.post(
            "/api/board/questions",
            json={"title": "新規質問", "body": "本文"},
        ).json()
        response = client.post(
            f"/api/board/questions/{question['id']}/answers",
            json={"body": ""},
        )
        # pydantic min_length=1 で 422 になる
        assert response.status_code == 422
