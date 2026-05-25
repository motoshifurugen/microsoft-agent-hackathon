"""Azure AI Search I/F (RAG 担当との接続点)。

embedding ベースの類似度検索を優先し、embedding 未登録時は文字列マッチへ
フォールバックする。本実装では _embeddings の代わりに Azure AI Search の
embedding ベクトル検索を呼び出す前提。
"""

from __future__ import annotations

from dataclasses import dataclass

from src.tools.cosmos_io import _embeddings, _success_cases, has_embeddings
from src.tools.embed import cosine_similarity, embed_text


@dataclass(frozen=True)
class SearchHit:
    """セマンティック検索結果の 1 件。"""

    case_id: str
    score: float  # 0.0-1.0
    snippet: str  # 抜粋 (UI 表示用)


def _snippet_for(case_id: str) -> str:
    raw = _success_cases.get(case_id, {})
    return f"{raw.get('business_type', '')}: {raw.get('what_worked', '')[:60]}"


def _embedding_search(text: str, top_k: int) -> list[SearchHit]:
    query_vec = embed_text(text)
    scored: list[SearchHit] = []
    for cid, vec in _embeddings.items():
        score = cosine_similarity(query_vec, vec)
        if score <= 0.0:
            continue
        scored.append(SearchHit(case_id=cid, score=score, snippet=_snippet_for(cid)))
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:top_k]


def _string_match_search(text: str, top_k: int) -> list[SearchHit]:
    needle = text.lower()
    scored: list[SearchHit] = []
    for cid, raw in _success_cases.items():
        business_type = raw.get("business_type", "").lower()
        what_worked = raw.get("what_worked", "").lower()
        score = 0.0
        if business_type and business_type in needle:
            score += 0.7
        if what_worked and any(w in needle for w in what_worked.split()):
            score += 0.3
        if score == 0.0:
            continue
        scored.append(SearchHit(case_id=cid, score=min(score, 1.0), snippet=_snippet_for(cid)))
    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:top_k]


def semantic_search(text: str, top_k: int = 3) -> list[SearchHit]:
    """困りごとテキストから類似成功事例を返す。

    embedding が 1 件以上登録されていれば cosine similarity ベース、
    そうでなければ business_type の文字列マッチへフォールバックする。

    Args:
        text: クエリ (困りごとの自然文)
        top_k: 上位何件を返すか

    Returns:
        SearchHit のリスト (score 降順)。空配列もあり得る。
    """
    if not text:
        return []

    if has_embeddings():
        try:
            return _embedding_search(text, top_k)
        except Exception:
            # Azure 接続エラー時は文字列マッチへフォールバック (デモ継続のため)
            pass

    return _string_match_search(text, top_k)
