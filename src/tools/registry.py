"""Foundry FunctionTool に登録するためのラッパー関数群。

src/tools/cosmos_io.py 等の Python 内部 API は dataclass を返すが、
Foundry FunctionTool は JSON シリアライズ可能な値 (dict/list/プリミティブ) を要求する。
ここで dataclass → dict 変換を吸収し、Foundry から呼べる薄いラッパーとして提供する。

Orchestrator はこれらの関数を function_tool 経由で呼び出す。
"""

from __future__ import annotations

from dataclasses import asdict

from src.api.categories import normalize_category
from src.tools.case_writer import register_success_case
from src.tools.cosmos_io import (
    PainPoint,
    SuccessCase,
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


def tool_register_success_case(
    user_id: str,
    owner_label: str,
    business_type: str,
    what_worked: str,
    why_worked: str = "",
    concrete_prompt: str = "",
    quantitative_effect: str = "",
    reproducibility_score: float = 0.5,
) -> dict:
    """本人承認済みの AI 活用成功事例を登録し、検索可能にする。

    チャットでユーザーが「うまくいった」体験を話し、本人が共有に同意した場合のみ呼ぶ
    (Human-in-the-Loop)。登録された事例は embedding 化され、次の誰かの困りごと検索に
    ヒットするようになる (組織知の継続蓄積)。

    :param user_id: 登録者の ID (additional_instructions で渡される登録者本人)
    :param owner_label: 表示名 (例: "営業部 佐藤さん")。本人に確認した値を渡す
    :param business_type: 業務カテゴリ (例: "議事録要約")
    :param what_worked: うまくいったこと / やったこと (必須)
    :param why_worked: なぜ効いたか (任意)
    :param concrete_prompt: 使った実プロンプト (任意)
    :param quantitative_effect: 定量効果 (任意、例: "30分 → 5分")
    :param reproducibility_score: 再現性 0.0-1.0 (範囲外は丸める)
    :return: 登録結果 dict。必須項目が空なら error を返す
    """
    owner = owner_label.strip()
    what = what_worked.strip()
    category = normalize_category(business_type)
    if not user_id.strip() or not owner or not category or not what:
        return {
            "error": "user_id・owner_label・business_type・what_worked は必須です",
        }

    try:
        score = float(reproducibility_score)
    except (TypeError, ValueError):
        score = 0.5
    score = max(0.0, min(1.0, score))

    case = SuccessCase(
        user_id=user_id.strip(),
        business_type=category,
        what_worked=what,
        why_worked=why_worked.strip(),
        reproducibility_score=score,
        owner_label=owner,
        concrete_prompt=concrete_prompt.strip(),
        quantitative_effect=quantitative_effect.strip(),
    )
    register_success_case(case)
    return {"status": "registered", "owner_label": owner, "business_type": category}


# Foundry の FunctionTool に渡す関数セット。
# Orchestrator がこれらすべてを保有し、ConnectedAgentTool 経由で子 Agent を呼びつつ
# 自身も直接データ層を操作する設計。
ORCHESTRATOR_FUNCTIONS = {
    tool_save_pain_point,
    tool_semantic_search,
    tool_fetch_success_cases,
    tool_get_cold_start_templates,
    tool_register_success_case,
}
