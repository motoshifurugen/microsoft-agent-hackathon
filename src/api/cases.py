"""成功事例の登録 API。

ShareCTA のトーストに代わり、ユーザーが自分の成功事例をフォームから登録できる。
本実装 (Cosmos DB) では DX 推進部のフォーム入力経路に相当する書き込み口。
登録された事例は in-memory store に入り、カテゴリ一覧・検索の対象になる。
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Query, status

from src.api.categories import normalize_category
from src.api.schemas import CaseCreateRequest, CaseDetail, build_case_detail
from src.tools.case_writer import register_success_case
from src.tools.cosmos_io import SuccessCase, get_all_success_cases

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CaseDetail])
def list_my_cases(client_id: str = Query(min_length=1)) -> list[CaseDetail]:
    """呼び出し元 (client_id) が登録した成功事例を新しい順で返す。

    認証が無いため localStorage 由来の client_id を登録者キー (user_id) として絞り込む。
    in-memory store は挿入順を保持するため、新しい登録が先頭に来るよう逆順にする。
    """
    mine = [c for c in get_all_success_cases().values() if c.get("user_id") == client_id]
    mine.reverse()
    return [build_case_detail(c) for c in mine]


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
    register_success_case(case)
    return build_case_detail(asdict(case))
