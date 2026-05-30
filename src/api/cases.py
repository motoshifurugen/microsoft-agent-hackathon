"""成功事例の登録 API。

ShareCTA のトーストに代わり、ユーザーが自分の成功事例をフォームから登録できる。
本実装 (Cosmos DB) では DX 推進部のフォーム入力経路に相当する書き込み口。
登録された事例は in-memory store に入り、カテゴリ一覧・検索の対象になる。
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, status

from src.api.categories import normalize_category
from src.api.schemas import CaseCreateRequest, CaseDetail, build_case_detail
from src.tools.cosmos_io import SuccessCase, seed_success_case

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.post("", response_model=CaseDetail, status_code=status.HTTP_201_CREATED)
def create_case(req: CaseCreateRequest) -> CaseDetail:
    case = SuccessCase(
        user_id=req.client_id,
        business_type=normalize_category(req.business_type),
        what_worked=req.what_worked,
        why_worked=req.why_worked,
        reproducibility_score=req.reproducibility_score,
        owner_label=req.owner_label,
        concrete_prompt=req.concrete_prompt,
        quantitative_effect=req.quantitative_effect,
    )
    seed_success_case(case)
    return build_case_detail(asdict(case))
