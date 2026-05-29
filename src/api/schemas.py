"""Pydantic schemas shared by employee/admin routers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class UserSummary(BaseModel):
    """サイドバー (管理者) に表示するメンバー概要。"""

    user_id: str
    owner_label: str
    business_type: str
    quantitative_effect: str = ""


class CaseDetail(BaseModel):
    """成功事例の表示用詳細。"""

    case_id: str
    owner_label: str
    business_type: str
    what_worked: str
    why_worked: str
    concrete_prompt: str
    quantitative_effect: str
    reproducibility_score: float
    score: float = Field(default=0.0, description="検索スコア (0.0-1.0)。一覧 API では 0.0")


class CategorySummary(BaseModel):
    """社員側のカテゴリ chip 用。"""

    name: str
    case_count: int
    sample_owner_label: str = ""


class CategoryCasesResponse(BaseModel):
    """カテゴリ別事例一覧のレスポンス。"""

    category: str
    cases: list[CaseDetail]


class TodayPick(BaseModel):
    """今日のおすすめ事例 (Home トップに大きく出す)。"""

    case: CaseDetail
    headline: str  # 「Copilot で月次レポートを 8h → 2.5h に」のような一文


class Strategy(BaseModel):
    """管理者が提示する伝播戦略。"""

    id: Literal["A", "B"]
    title: str
    description: str


class RecommendationResponse(BaseModel):
    """管理者向け推薦事例レスポンス。"""

    target_user_id: str
    target_owner_label: str
    target_business_type: str
    cases: list[CaseDetail]
    strategies: list[Strategy]


class PainMatchRequest(BaseModel):
    """WebApp 困りごと入力欄からのマッチング依頼。"""

    text: str = Field(min_length=1, description="困りごとの自然文")
    client_id: str = Field(default="", description="localStorage 由来の識別子。空なら匿名扱い")
    business_context: str = Field(default="", description="業務文脈 (任意)")
    top_k: int = Field(default=3, ge=1, le=10, description="返す事例の最大件数")

    @field_validator("text")
    @classmethod
    def _text_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        return stripped


class PainMatchResponse(BaseModel):
    """困りごとマッチング結果。"""

    pain_point_id: str
    query: str
    cases: list[CaseDetail]


class StrategyExecuteRequest(BaseModel):
    target_user_id: str
    case_id: str


class StrategyExecuteResponse(BaseModel):
    execution_id: str
    strategy_id: Literal["A", "B"]
    target_user_id: str
    case_id: str
    message_preview: str
    executed_at: str


def build_case_detail(case: dict, score: float = 0.0) -> CaseDetail:
    """in-memory store の dict から CaseDetail を組み立てる共通ヘルパー。

    admin / employee 両ルーターで同じ変換が必要だったため共通化。
    """
    return CaseDetail(
        case_id=case["id"],
        owner_label=case.get("owner_label", ""),
        business_type=case.get("business_type", ""),
        what_worked=case.get("what_worked", ""),
        why_worked=case.get("why_worked", ""),
        concrete_prompt=case.get("concrete_prompt", ""),
        quantitative_effect=case.get("quantitative_effect", ""),
        reproducibility_score=float(case.get("reproducibility_score", 0.0)),
        score=score,
    )


def build_user_summary(case: dict) -> UserSummary:
    """SuccessCase dict から UserSummary を組み立てる共通ヘルパー。"""
    return UserSummary(
        user_id=case["user_id"],
        owner_label=case.get("owner_label", ""),
        business_type=case.get("business_type", ""),
        quantitative_effect=case.get("quantitative_effect", ""),
    )
