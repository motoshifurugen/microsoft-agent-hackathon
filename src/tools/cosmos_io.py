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
    """成功事例データ (要件定義書 §6.1 `success_cases` コンテナ)。

    owner_label / concrete_prompt / quantitative_effect は提示時の現実感と
    具体性を高めるためのフィールドで、本実装 (Cosmos DB) でも同じスキーマで保存する。
    """

    user_id: str
    business_type: str
    what_worked: str
    why_worked: str
    reproducibility_score: float  # 0.0-1.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    embedding_id: str | None = None
    owner_label: str = ""  # 例: "営業部 佐藤さん"
    concrete_prompt: str = ""  # ユーザーがコピペできる実プロンプト
    quantitative_effect: str = ""  # 例: "月 8h → 2.5h (約 70% 削減)"


@dataclass(frozen=True)
class ColdStartTemplate:
    """Cold Start 用テンプレート (成功事例が少ない業務カテゴリ向け)。

    成功事例が 0 件のカテゴリでも、すぐ使えるプロンプトと手順を提供する。
    """

    business_category: str
    title: str
    description: str
    common_pain: str
    prompt: str
    # list[str] を使う理由: asdict() がタプルをそのまま返すため JSON 互換のリストが必要。
    # frozen=True により属性の再代入は禁止されており、要素の変更は慣例として行わない。
    steps: list[str]
    suitable_for: str
    cautions: str
    feedback_question: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


# MVP: in-memory ストア。データ担当の実装で Cosmos DB に差し替え。
_pain_points: dict[str, dict] = {}
_success_cases: dict[str, dict] = {}
# 成功事例 ID → embedding ベクトル。seed 時に register_embedding で投入される。
# 本実装では Azure AI Search の index に置き換える前提。
_embeddings: dict[str, list[float]] = {}
# Cold Start テンプレート in-memory ストア。
_cold_start_templates: dict[str, dict] = {}


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


def register_embedding(case_id: str, vector: list[float]) -> None:
    """成功事例 ID に対する embedding ベクトルを登録する。

    本実装では Azure AI Search の index push に置き換える前提。
    """
    _embeddings[case_id] = vector


def has_embeddings() -> bool:
    """1 件以上の embedding が登録されているか。"""
    return bool(_embeddings)


def get_all_embeddings() -> dict[str, list[float]]:
    """全 embedding を返す (テスト・検索エンジンからのアクセス用)。"""
    return _embeddings


def get_all_success_cases() -> dict[str, dict]:
    """全成功事例を返す (テスト・検索エンジンからのアクセス用)。"""
    return _success_cases


def seed_cold_start_template(template: ColdStartTemplate) -> str:
    """Cold Start テンプレートを in-memory store に投入し ID を返す。

    本実装では Cosmos DB の `cold_start_templates` コンテナへの書き込みに差し替える。
    """
    _cold_start_templates[template.id] = asdict(template)
    return template.id


def get_cold_start_templates() -> dict[str, dict]:
    """全 Cold Start テンプレートを返す (テスト・API からのアクセス用)。"""
    return _cold_start_templates
