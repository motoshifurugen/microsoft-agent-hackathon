"""類似成功事例の検索 (RAG)。

embedding ベースの cosine similarity を基本ランキングに、
業務種別マッチのボーナスと再現可能性スコアの重み付けを加えて最終スコアを算出する。
embedding 未登録時 / Azure 失敗時は文字列マッチへフォールバックする。

本実装では Azure AI Search の embedding ベクトル検索に置き換える前提で、
データ層 (cosmos_io._embeddings) との接続点を関数経由で抽象化している。
"""

from __future__ import annotations

from dataclasses import dataclass

from src.tools.cosmos_io import _embeddings, _success_cases, has_embeddings
from src.tools.embed import cosine_similarity, embed_text

# スコアリングのチューニングパラメータ
TOP_K_DEFAULT = 3
# embedding cosine similarity に対する基本重み
SEMANTIC_WEIGHT = 0.7
# SuccessCase.reproducibility_score (0-1) に対する重み
REPRODUCIBILITY_WEIGHT = 0.3
# クエリに business_type が含まれていた場合のボーナス (0-1 で加算)
BUSINESS_TYPE_BONUS = 0.2
# 文字列マッチ fallback の重み
STRING_BUSINESS_TYPE_WEIGHT = 0.7
STRING_WHAT_WORKED_WEIGHT = 0.3


@dataclass(frozen=True)
class SearchHit:
    """セマンティック検索結果の 1 件。"""

    case_id: str
    score: float  # 0.0-1.0
    snippet: str  # 抜粋 (UI 表示用)


def _snippet_for(case_id: str) -> str:
    raw = _success_cases.get(case_id, {})
    owner = raw.get("owner_label", "")
    business_type = raw.get("business_type", "")
    what_worked = raw.get("what_worked", "")[:60]
    if owner:
        return f"{owner} ({business_type}): {what_worked}"
    return f"{business_type}: {what_worked}"


def _should_exclude(case: dict, exclude_user_id: str | None) -> bool:
    """対象ユーザー本人の事例を除外すべきかを判定する。

    困っている本人に本人の事例を推薦してしまう不自然さを避ける。
    """
    if exclude_user_id is None:
        return False
    return case.get("user_id") == exclude_user_id


def _final_score(semantic_score: float, case: dict, query_text: str) -> float:
    """semantic スコアに業務種別ボーナスと再現可能性を反映した最終スコアを返す。

    final = semantic * SEMANTIC_WEIGHT + reproducibility * REPRODUCIBILITY_WEIGHT
            + (business_type がクエリに含まれていれば) BUSINESS_TYPE_BONUS
    """
    base = semantic_score * SEMANTIC_WEIGHT
    reproducibility = float(case.get("reproducibility_score", 0.0))
    base += reproducibility * REPRODUCIBILITY_WEIGHT

    business_type = str(case.get("business_type", ""))
    if business_type and business_type in query_text:
        base += BUSINESS_TYPE_BONUS

    return min(base, 1.0)


def _embedding_search(text: str, top_k: int, exclude_user_id: str | None) -> list[SearchHit]:
    query_vec = embed_text(text)
    scored: list[SearchHit] = []
    for case_id, vec in _embeddings.items():
        case = _success_cases.get(case_id, {})
        if _should_exclude(case, exclude_user_id):
            continue
        semantic = cosine_similarity(query_vec, vec)
        if semantic <= 0.0:
            continue
        final = _final_score(semantic, case, text)
        scored.append(SearchHit(case_id=case_id, score=final, snippet=_snippet_for(case_id)))
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:top_k]


def _string_match_search(text: str, top_k: int, exclude_user_id: str | None) -> list[SearchHit]:
    needle = text.lower()
    scored: list[SearchHit] = []
    for case_id, case in _success_cases.items():
        if _should_exclude(case, exclude_user_id):
            continue
        business_type = str(case.get("business_type", "")).lower()
        what_worked = str(case.get("what_worked", "")).lower()
        score = 0.0
        if business_type and business_type in needle:
            score += STRING_BUSINESS_TYPE_WEIGHT
        if what_worked and any(w in needle for w in what_worked.split()):
            score += STRING_WHAT_WORKED_WEIGHT
        if score == 0.0:
            continue
        final = _final_score(score, case, text)
        scored.append(SearchHit(case_id=case_id, score=final, snippet=_snippet_for(case_id)))
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:top_k]


def semantic_search(
    text: str,
    top_k: int = TOP_K_DEFAULT,
    exclude_user_id: str | None = None,
) -> list[SearchHit]:
    """困りごとテキストから類似成功事例を返す。

    embedding が 1 件以上登録されていれば cosine similarity ベース、
    そうでなければ business_type の文字列マッチへフォールバックする。
    どちらの場合も:
      - 業務種別マッチ時に BUSINESS_TYPE_BONUS を加算
      - reproducibility_score を REPRODUCIBILITY_WEIGHT で加重
      - exclude_user_id 指定時はその user_id の事例を除外

    Args:
        text: クエリ (困りごとの自然文)
        top_k: 上位何件を返すか (デフォルト 3)
        exclude_user_id: 推薦対象から外したい user_id (例: 困りごとを持つ本人)

    Returns:
        SearchHit のリスト (score 降順)。空配列もあり得る。
    """
    if not text:
        return []

    if has_embeddings():
        try:
            return _embedding_search(text, top_k, exclude_user_id)
        except Exception:
            # Azure 接続エラー時は文字列マッチへフォールバック (デモ継続のため)
            pass

    return _string_match_search(text, top_k, exclude_user_id)
