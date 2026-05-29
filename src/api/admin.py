"""管理者モード (Kodama メンバー支援) 向けのエンドポイント群。

DX 推進担当者が困っている社員を選び、推薦事例と戦略 A/B を提示する。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    RecommendationResponse,
    Strategy,
    StrategyExecuteRequest,
    StrategyExecuteResponse,
    UserSummary,
    build_case_detail,
    build_user_summary,
)
from src.tools.cosmos_io import get_all_success_cases
from src.tools.registry import tool_fetch_success_cases, tool_semantic_search

router = APIRouter(prefix="/api/admin", tags=["admin"])

# 戦略実行履歴 (in-memory; 本実装では Cosmos DB match_history に保存予定)
_strategy_executions: list[dict] = []


def _build_strategies(top_case_owner: str) -> list[Strategy]:
    return [
        Strategy(
            id="A",
            title="紹介",
            description=f"{top_case_owner} に 15 分の紹介を依頼し、直接対話のきっかけを作る",
        ),
        Strategy(
            id="B",
            title="テンプレ共有",
            description="使えるプロンプトを Teams DM で送付し、本人ペースで試してもらう",
        ),
    ]


@router.get("/users", response_model=list[UserSummary])
def list_users() -> list[UserSummary]:
    """サイドバーに表示するメンバー一覧 (success_cases から 1 人 1 件で集約)。"""
    cases = get_all_success_cases()
    seen: dict[str, dict] = {}
    for case in cases.values():
        user_id = case.get("user_id")
        if not user_id or user_id in seen:
            continue
        seen[user_id] = case
    return [build_user_summary(c) for c in seen.values()]


@router.get("/users/{user_id}/recommendations", response_model=RecommendationResponse)
def get_recommendations(user_id: str, top_k: int = 3) -> RecommendationResponse:
    """対象ユーザー向けの推薦事例 + 戦略 A/B。本人の事例は除外する。"""
    cases = get_all_success_cases()
    target_case = next(
        (c for c in cases.values() if c.get("user_id") == user_id),
        None,
    )
    if target_case is None:
        raise HTTPException(status_code=404, detail=f"user_id not found: {user_id}")

    query = (
        f"{target_case.get('business_type', '')} で困っている {target_case.get('owner_label', '')}"
    )
    hits = tool_semantic_search(text=query, top_k=top_k, exclude_user_id=user_id)
    case_ids = [h["case_id"] for h in hits]
    details = tool_fetch_success_cases(case_ids=case_ids)

    score_map = {h["case_id"]: h["score"] for h in hits}
    case_payload = [build_case_detail(d, score_map.get(d["id"], 0.0)) for d in details]

    top_owner = case_payload[0].owner_label if case_payload else "成功者の方"
    return RecommendationResponse(
        target_user_id=user_id,
        target_owner_label=target_case.get("owner_label", ""),
        target_business_type=target_case.get("business_type", ""),
        cases=case_payload,
        strategies=_build_strategies(top_owner),
    )


@router.post(
    "/strategies/{strategy_id}/execute",
    response_model=StrategyExecuteResponse,
)
def execute_strategy(
    strategy_id: Literal["A", "B"],
    body: StrategyExecuteRequest,
) -> StrategyExecuteResponse:
    """戦略 A/B の実行プレビューを生成 (実送信はしない)。"""
    cases = get_all_success_cases()
    case = cases.get(body.case_id)
    if case is None:
        raise HTTPException(status_code=404, detail=f"case_id not found: {body.case_id}")

    target_case = next(
        (c for c in cases.values() if c.get("user_id") == body.target_user_id),
        None,
    )
    target_owner = (
        target_case.get("owner_label", body.target_user_id) if target_case else body.target_user_id
    )

    case_owner = case.get("owner_label", "成功者")
    business_type = case.get("business_type", "")
    if strategy_id == "A":
        preview = (
            f"{case_owner} さま\n\n"
            f"お忙しい中失礼します。{target_owner} さまが {business_type} の効率化で困っており、"
            f"以前 {case_owner} さまが実施された取り組みが参考になりそうです。\n"
            f"15 分ほどお時間いただき、ご経験を共有いただけませんでしょうか？\n"
        )
    else:
        prompt = case.get("concrete_prompt", "(プロンプト未登録)")
        preview = (
            f"{target_owner} さま\n\n"
            f"{business_type} の効率化に、社内の成功事例 ({case_owner}) で使われた "
            f"プロンプトを共有します。\n\n"
            f"--- プロンプト ---\n{prompt}\n----------------\n\n"
            f"まずは現状の作業に合わせて試してみていただけますか？\n"
        )

    execution = StrategyExecuteResponse(
        execution_id=f"exec-{len(_strategy_executions) + 1}",
        strategy_id=strategy_id,
        target_user_id=body.target_user_id,
        case_id=body.case_id,
        message_preview=preview,
        executed_at=datetime.now(UTC).isoformat(),
    )
    _strategy_executions.append(execution.model_dump())
    return execution


@router.get("/executions")
def list_executions() -> list[dict]:
    """戦略実行履歴 (Phase 2 で Cosmos DB match_history に置換予定)。"""
    return list(_strategy_executions)
