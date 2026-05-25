"""Azure AI Search I/F (RAG 担当との接続点)。

MVP では in-memory に登録された success_cases をキーワードマッチで返す mock。
データ準備担当が embedding 索引を構築後、本実装に差し替える。
"""

from __future__ import annotations

from dataclasses import dataclass

from src.tools.cosmos_io import _success_cases


@dataclass(frozen=True)
class SearchHit:
    """セマンティック検索結果の 1 件。"""

    case_id: str
    score: float  # 0.0-1.0
    snippet: str  # 抜粋 (UI 表示用)


def semantic_search(text: str, top_k: int = 3) -> list[SearchHit]:
    """困りごとテキストから類似成功事例を返す。

    MVP 実装: business_type 文字列の部分一致でスコアリング。
    Phase 2: Azure AI Search の embedding ベクトル検索に差し替え。

    Args:
        text: クエリ (困りごとの自然文)
        top_k: 上位何件を返すか

    Returns:
        SearchHit のリスト (score 降順)。空配列もあり得る。
    """
    if not text:
        return []

    needle = text.lower()
    scored: list[SearchHit] = []
    for cid, raw in _success_cases.items():
        business_type = raw.get("business_type", "").lower()
        what_worked = raw.get("what_worked", "").lower()
        # 簡易スコアリング: business_type マッチを重視
        score = 0.0
        if business_type and business_type in needle:
            score += 0.7
        if what_worked and any(w in needle for w in what_worked.split()):
            score += 0.3
        if score == 0.0:
            continue
        snippet = f"{raw.get('business_type', '')}: {raw.get('what_worked', '')[:60]}"
        scored.append(SearchHit(case_id=cid, score=min(score, 1.0), snippet=snippet))

    scored.sort(key=lambda h: h.score, reverse=True)
    return scored[:top_k]
