"""困りごと掲示板 (Q&A) のエンドポイント群。

AI の使い方に対する困りごとを誰でも投稿でき、他の社員が回答できる軽量掲示板。
ランキング・いいね・通報などの過度な機能は持たず、やさしく循環する世界観を維持する。

データは in-memory (Phase 2 で Cosmos DB に置換予定)。サンプル質問と回答を起動時に投入。
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from threading import Lock

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/board", tags=["board"])

_lock = Lock()
_questions: dict[str, dict] = {}
_answers_by_question: dict[str, list[dict]] = {}


# --- Schemas ---


class Question(BaseModel):
    id: str
    title: str
    body: str
    business_category: str | None = None
    author: str = "匿名"
    created_at: str
    answer_count: int = 0


class Answer(BaseModel):
    id: str
    question_id: str
    body: str
    author: str = "匿名"
    created_at: str


class QuestionWithAnswers(Question):
    answers: list[Answer]


class QuestionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    business_category: str | None = None
    author: str | None = None


class AnswerCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)
    author: str | None = None


# --- Helpers ---


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _author_or_anonymous(author: str | None) -> str:
    if author and author.strip():
        return author.strip()
    return "匿名"


def _question_view(question: dict) -> Question:
    answers = _answers_by_question.get(question["id"], [])
    return Question(
        id=question["id"],
        title=question["title"],
        body=question["body"],
        business_category=question.get("business_category"),
        author=question["author"],
        created_at=question["created_at"],
        answer_count=len(answers),
    )


def reset_board_for_tests() -> None:
    """テスト用に in-memory store をクリア (本番からは呼ばない)。"""
    with _lock:
        _questions.clear()
        _answers_by_question.clear()


def seed_sample_board() -> None:
    """初期表示で空っぽにならないよう、サンプル質問と回答を 2 件投入する。"""
    with _lock:
        if _questions:
            return
        # 質問 1: 月次レポート
        q1_id = str(uuid.uuid4())
        _questions[q1_id] = {
            "id": q1_id,
            "title": "月次レポートをもっと楽に書きたいです",
            "body": "毎月 6 時間以上かけて Excel データから月次レポートを書いています。"
            "Copilot を活用したいのですが、どこから始めればよいでしょうか。",
            "business_category": "月次レポート作成",
            "author": "経理部 渡辺",
            "created_at": _now_iso(),
        }
        _answers_by_question[q1_id] = [
            {
                "id": str(uuid.uuid4()),
                "question_id": q1_id,
                "body": "上の事例カード「営業部 佐藤さんの事例」のプロンプトをコピーして、"
                "まずは前月データの要約だけ Copilot に出してもらうのが始めやすいです。"
                "数値の正確性は自分で必ず確認してください。",
                "author": "DX 推進部 田島",
                "created_at": _now_iso(),
            },
        ]

        # 質問 2: メール
        q2_id = str(uuid.uuid4())
        _questions[q2_id] = {
            "id": q2_id,
            "title": "謝罪メールのトーンを Copilot に揃えてもらえますか",
            "body": "お詫びメールを書くのが苦手で時間がかかります。社内の標準的なトーンで"
            "下書きを作りたいのですが、コツがあれば教えてください。",
            "business_category": "メール作成",
            "author": "営業部 高田",
            "created_at": _now_iso(),
        }
        _answers_by_question[q2_id] = [
            {
                "id": str(uuid.uuid4()),
                "question_id": q2_id,
                "body": "過去に自分が書いた / 送信されたお詫びメールを 1 通そのまま貼り付けて、"
                "「同じトーンで以下の状況の謝罪メールを 200 字程度で」と頼むのが一番速かったです。"
                "個人情報は伏せ字にしてから渡すのを忘れないようにしてください。",
                "author": "営業部 伊藤",
                "created_at": _now_iso(),
            },
        ]


# --- Endpoints ---


@router.get("/questions", response_model=list[Question])
def list_questions() -> list[Question]:
    """質問一覧を新しい順で返す。"""
    with _lock:
        items = list(_questions.values())
    items.sort(key=lambda q: q.get("created_at", ""), reverse=True)
    return [_question_view(q) for q in items]


@router.post("/questions", response_model=Question)
def create_question(payload: QuestionCreateRequest) -> Question:
    qid = str(uuid.uuid4())
    record = {
        "id": qid,
        "title": payload.title.strip(),
        "body": payload.body.strip(),
        "business_category": payload.business_category,
        "author": _author_or_anonymous(payload.author),
        "created_at": _now_iso(),
    }
    with _lock:
        _questions[qid] = record
        _answers_by_question[qid] = []
    return _question_view(record)


@router.get("/questions/{question_id}", response_model=QuestionWithAnswers)
def get_question(question_id: str) -> QuestionWithAnswers:
    with _lock:
        question = _questions.get(question_id)
        answers = list(_answers_by_question.get(question_id, []))
    if question is None:
        raise HTTPException(status_code=404, detail=f"question_id not found: {question_id}")
    return QuestionWithAnswers(
        id=question["id"],
        title=question["title"],
        body=question["body"],
        business_category=question.get("business_category"),
        author=question["author"],
        created_at=question["created_at"],
        answer_count=len(answers),
        answers=[Answer(**a) for a in answers],
    )


@router.post("/questions/{question_id}/answers", response_model=Answer)
def create_answer(question_id: str, payload: AnswerCreateRequest) -> Answer:
    with _lock:
        if question_id not in _questions:
            raise HTTPException(status_code=404, detail=f"question_id not found: {question_id}")
        record = {
            "id": str(uuid.uuid4()),
            "question_id": question_id,
            "body": payload.body.strip(),
            "author": _author_or_anonymous(payload.author),
            "created_at": _now_iso(),
        }
        _answers_by_question.setdefault(question_id, []).append(record)
    return Answer(**record)
