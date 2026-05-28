"""Pydantic schemas shared by employee/admin routers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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
