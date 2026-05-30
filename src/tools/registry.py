"""Foundry FunctionTool に登録するためのラッパー関数群。

src/tools/cosmos_io.py 等の Python 内部 API は dataclass を返すが、
Foundry FunctionTool は JSON シリアライズ可能な値 (dict/list/プリミティブ) を要求する。
ここで dataclass → dict 変換を吸収し、Foundry から呼べる薄いラッパーとして提供する。

Orchestrator はこれらの関数を function_tool 経由で呼び出す。
"""

from __future__ import annotations

from dataclasses import asdict

from src.tools.cosmos_io import (
    PainPoint,
    fetch_success_cases,
    get_cold_start_templates,
    save_pain_point,
)
from src.tools.search_query import semantic_search


def tool_save_pain_point(
    user_id: str,
    business_context: str,
    pain_description: str,
    source_signal: str,
) -> dict:
    """本人承認済みの困りごとを Cosmos DB に永続化する。

    :param user_id: 困りごとを持つユーザー ID
    :param business_context: 業務文脈 (例: 月次レポート作成)
    :param pain_description: 具体的な困りごとの説明
    :param source_signal: 検知元 (chat_input / webapp_input 等)
    :return: 保存された PainPoint の id を含む dict
    """
    pp = PainPoint(
        user_id=user_id,
        business_context=business_context,
        pain_description=pain_description,
        source_signal=source_signal,
    )
    saved_id = save_pain_point(pp)
    return {"id": saved_id, "status": pp.status}


def tool_semantic_search(
    text: str,
    top_k: int = 3,
    exclude_user_id: str | None = None,
) -> list[dict]:
    """困りごとテキストから類似成功事例を検索する。

    :param text: クエリ (困りごとの自然文)
    :param top_k: 上位何件を返すか
    :param exclude_user_id: 推薦から除外したい user_id (例: 困りごとを持つ本人)。
        本人に本人の事例を推薦しないために使う。
    :return: SearchHit のリスト (score 降順)
    """
    # Foundry function tool 経由では数値が文字列で届くことがあるため明示的にキャスト
    hits = semantic_search(
        text=text,
        top_k=int(top_k),
        exclude_user_id=exclude_user_id or None,
    )
    return [asdict(h) for h in hits]


def tool_fetch_success_cases(case_ids: list[str]) -> list[dict]:
    """指定 ID の成功事例を取得する。

    :param case_ids: 取得対象の case_id のリスト
    :return: SuccessCase のリスト
    """
    return [asdict(c) for c in fetch_success_cases(case_ids=case_ids)]


def tool_get_cold_start_templates(business_category: str | None = None) -> list[dict]:
    """業務カテゴリに合う Cold Start テンプレートを取得する。

    類似成功事例が見つからなかった場合 (Cold Start 状態) に呼び出す。
    業務カテゴリを指定すると合致するテンプレートだけを返す。
    省略すると全テンプレートを返す。

    :param business_category: 業務カテゴリ名 (例: "月次レポート作成")。None の場合は全件。
    :return: ColdStartTemplate の dict リスト
    """
    templates = get_cold_start_templates()
    if business_category is None:
        return list(templates.values())
    return [t for t in templates.values() if t.get("business_category") == business_category]


# Foundry の FunctionTool に渡す関数セット。
# Orchestrator がこれらすべてを保有し、ConnectedAgentTool 経由で子 Agent を呼びつつ
# 自身も直接データ層を操作する設計。
ORCHESTRATOR_FUNCTIONS = {
    tool_save_pain_point,
    tool_semantic_search,
    tool_fetch_success_cases,
    tool_get_cold_start_templates,
}
