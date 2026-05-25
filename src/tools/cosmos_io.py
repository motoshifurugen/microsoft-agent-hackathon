"""Cosmos DB I/F (データ準備担当との接続点)。

MVP では in-memory dict で代替し、データ担当が Cosmos DB 接続を実装後に差し替える。
スキーマは要件定義書 §6.1 を踏襲する。
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Literal

PainPointStatus = Literal["pending", "confirmed", "rejected", "matched"]


@dataclass(frozen=True)
class PainPoint:
    """困りごとデータ (要件定義書 §6.1 `pain_points` コンテナ)。"""

    user_id: str
    business_context: str
    pain_description: str
    source_signal: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: PainPointStatus = "pending"


@dataclass(frozen=True)
class SuccessCase:
    """成功事例データ (要件定義書 §6.1 `success_cases` コンテナ)。"""

    user_id: str
    business_type: str
    what_worked: str
    why_worked: str
    reproducibility_score: float  # 0.0-1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embedding_id: str | None = None


# MVP: in-memory ストア。データ担当の実装で Cosmos DB に差し替え。
_pain_points: dict[str, dict] = {}
_success_cases: dict[str, dict] = {}


def save_pain_point(pain_point: PainPoint) -> str:
    """困りごとを永続化し ID を返す。

    Args:
        pain_point: 構造化済み PainPoint。本人承認後に呼び出すこと。

    Returns:
        保存された PainPoint の ID。
    """
    _pain_points[pain_point.id] = asdict(pain_point)
    return pain_point.id


def fetch_success_cases(case_ids: list[str]) -> list[SuccessCase]:
    """指定 ID の成功事例を取得する。

    Args:
        case_ids: 取得対象の case_id リスト。

    Returns:
        見つかった SuccessCase のリスト (順序保存)。
    """
    result: list[SuccessCase] = []
    for cid in case_ids:
        raw = _success_cases.get(cid)
        if raw is None:
            continue
        result.append(SuccessCase(**raw))
    return result


def seed_success_case(case: SuccessCase) -> str:
    """データ担当の本実装が来るまでの mock 投入用。

    本番では DX 推進部のフォーム入力 (要件定義書 §2.2 サブシナリオ) 経由で書き込まれる。
    """
    _success_cases[case.id] = asdict(case)
    return case.id
