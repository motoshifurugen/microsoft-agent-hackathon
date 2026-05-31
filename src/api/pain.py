"""WebApp 困りごと入力欄向けのマッチング API。

ユーザーが画面に入力した困りごとを semantic_search で類似成功事例に紐づけ、
同時に PainPoint として永続化する (source_signal="webapp_input")。
メール監視を廃止し、明示入力で困りごとを拾う方針 (Phase A の置き換え)。
"""

from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import PainMatchRequest, PainMatchResponse, build_case_detail
from src.tools.cosmos_io import PainPoint, get_all_success_cases, save_pain_point
from src.tools.search_query import semantic_search

router = APIRouter(prefix="/api/pain", tags=["pain"])

# client_id 未提供時の匿名ユーザー識別子。
ANONYMOUS_USER_ID = "anonymous-webapp"


@router.post("/match", response_model=PainMatchResponse)
def match_pain(req: PainMatchRequest) -> PainMatchResponse:
    """困りごとテキストを類似事例にマッチングし、困りごとを記録する。

    マッチが 0 件でも困りごと自体は永続化する (収集が主目的のため)。
    """
    pain_point = PainPoint(
        user_id=req.client_id or ANONYMOUS_USER_ID,
        business_context=req.business_context,
        pain_description=req.text,
        source_signal="webapp_input",
    )
    pain_point_id = save_pain_point(pain_point)

    hits = semantic_search(text=req.text, top_k=req.top_k)
    all_cases = get_all_success_cases()
    cases = [
        build_case_detail(all_cases[hit.case_id], score=hit.score)
        for hit in hits
        if hit.case_id in all_cases
    ]

    return PainMatchResponse(pain_point_id=pain_point_id, query=req.text, cases=cases)
