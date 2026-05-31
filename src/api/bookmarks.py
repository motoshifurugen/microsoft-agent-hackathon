"""Skill ブックマーク API (サーバー側永続)。

認証基盤が無いため、localStorage で生成した client_id を所有者キーとして
ブックマークを保存する。GET/POST/DELETE はいずれも当該 client_id の
ブックマーク事例一覧 (CaseDetail) を返し、フロントが状態を同期しやすくする。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import BookmarkRequest, CaseDetail, build_case_detail
from src.tools.cosmos_io import (
    add_bookmark,
    get_all_success_cases,
    get_bookmarked_case_ids,
    remove_bookmark,
)

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


def _bookmarked_cases(client_id: str) -> list[CaseDetail]:
    """client_id のブックマーク事例を追加順 (新しい順) で返す。

    既に削除された事例 ID はスキップする。
    """
    all_cases = get_all_success_cases()
    return [
        build_case_detail(all_cases[case_id])
        for case_id in get_bookmarked_case_ids(client_id)
        if case_id in all_cases
    ]


@router.get("", response_model=list[CaseDetail])
def list_bookmarks(client_id: str = Query(min_length=1)) -> list[CaseDetail]:
    return _bookmarked_cases(client_id)


@router.post("", response_model=list[CaseDetail])
def create_bookmark(req: BookmarkRequest) -> list[CaseDetail]:
    if req.case_id not in get_all_success_cases():
        raise HTTPException(status_code=404, detail=f"unknown case: {req.case_id}")
    add_bookmark(req.client_id, req.case_id)
    return _bookmarked_cases(req.client_id)


@router.delete("", response_model=list[CaseDetail])
def delete_bookmark(
    client_id: str = Query(min_length=1),
    case_id: str = Query(min_length=1),
) -> list[CaseDetail]:
    remove_bookmark(client_id, case_id)
    return _bookmarked_cases(client_id)
