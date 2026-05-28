"""社員モード (Kodama Home) 向けのエンドポイント群。

社員自身が「自分の業務に合う AI 活用を探す」体験を提供する軽量 API。
本実装ではフィードバック/共有/試したマークはローカル管理 (フロントの localStorage) を想定し、
サーバー側は閲覧 API に絞る (MVP)。
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    CategoryCasesResponse,
    CategorySummary,
    TodayPick,
    build_case_detail,
)
from src.tools.cosmos_io import get_all_success_cases

router = APIRouter(prefix="/api", tags=["employee"])


def _index_by_category(cases: dict[str, dict]) -> dict[str, list[dict]]:
    """business_type ごとに事例をグループ化する。"""
    grouped: dict[str, list[dict]] = {}
    for case in cases.values():
        bt = case.get("business_type", "")
        if not bt:
            continue
        grouped.setdefault(bt, []).append(case)
    return grouped


@router.get("/categories", response_model=list[CategorySummary])
def list_categories() -> list[CategorySummary]:
    """業務カテゴリ一覧 (Kodama Home の chip 群)。

    success_cases.business_type を集約し、件数とサンプル owner を返す。
    """
    grouped = _index_by_category(get_all_success_cases())
    summaries = [
        CategorySummary(
            name=name,
            case_count=len(cases),
            sample_owner_label=cases[0].get("owner_label", "") if cases else "",
        )
        for name, cases in grouped.items()
    ]
    # 件数の多い順に並べる (UX として人気カテゴリが目につく)
    summaries.sort(key=lambda c: c.case_count, reverse=True)
    return summaries


@router.get("/categories/{name}/cases", response_model=CategoryCasesResponse)
def cases_in_category(name: str) -> CategoryCasesResponse:
    """指定カテゴリの事例一覧。"""
    grouped = _index_by_category(get_all_success_cases())
    cases = grouped.get(name)
    if not cases:
        raise HTTPException(status_code=404, detail=f"unknown category: {name}")
    # reproducibility_score 降順で並べる (試しやすい順)
    cases_sorted = sorted(
        cases, key=lambda c: float(c.get("reproducibility_score", 0.0)), reverse=True
    )
    return CategoryCasesResponse(
        category=name,
        cases=[build_case_detail(c) for c in cases_sorted],
    )


@router.get("/today", response_model=TodayPick)
def today_pick() -> TodayPick:
    """今日のおすすめ事例 (日替わり)。

    日付をシードに事例を 1 件選ぶ決定論的アルゴリズム。
    複数のユーザーが同じ日にアクセスすれば同じ事例が出る。
    """
    cases = list(get_all_success_cases().values())
    if not cases:
        raise HTTPException(status_code=503, detail="no success cases seeded")

    today = datetime.now(UTC).date().isoformat()
    digest = hashlib.sha256(today.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % len(cases)
    case = cases[index]

    effect = case.get("quantitative_effect", "")
    business = case.get("business_type", "業務")
    owner = case.get("owner_label", "社内の誰か")
    # 業務名が重複する効果文 (例: "月次レポート作成 3h → 45min") の二重表記を避ける
    if effect:
        effect_short = effect.replace(business, "").strip(" :;,—-")
        headline = (
            f"{owner}の{business} — {effect_short}"
            if effect_short
            else f"{owner}の{business} — {effect}"
        )
    else:
        headline = f"{owner}の{business}"

    return TodayPick(case=build_case_detail(case), headline=headline)
