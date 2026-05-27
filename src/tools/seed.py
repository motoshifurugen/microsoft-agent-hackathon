"""JSON ファイルからダミーデータを in-memory store に投入する。

src/app.py の起動時に呼び出されることを想定。
データ担当の本実装 (Cosmos DB) に差し替えるまでの暫定 RAG ソース。
"""

from __future__ import annotations

import json
from pathlib import Path

from src.tools.cosmos_io import (
    ColdStartTemplate,
    SuccessCase,
    register_embedding,
    seed_cold_start_template,
    seed_success_case,
)

DEFAULT_SEED_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "sample_data" / "success_cases.json"
)
DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "sample_data" / "cold_start_templates.json"
)


def _build_embedding_text(case: SuccessCase) -> str:
    """成功事例を embedding 化するときのテキスト表現。

    business_type と what_worked を結合し、検索クエリとの類似度が出やすい形にする。
    """
    return f"{case.business_type}\n{case.what_worked}"


def load_success_cases(path: Path | None = None, with_embeddings: bool = False) -> int:
    """JSON から SuccessCase を読み込み、in-memory store に投入する。

    Args:
        path: JSON ファイルのパス。None の場合 docs/sample_data/success_cases.json を使用。
        with_embeddings: True の場合、各 SuccessCase の embedding を計算して登録する
            (Azure OpenAI API 呼び出しが発生する)。テスト時は False のままに。

    Returns:
        投入された件数。

    Raises:
        FileNotFoundError: 指定パスが存在しない場合。
        ValueError: JSON が SuccessCase の必須フィールドを欠く場合。
    """
    seed_path = path or DEFAULT_SEED_PATH
    if not seed_path.exists():
        raise FileNotFoundError(f"seed file not found: {seed_path}")

    raw = json.loads(seed_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"seed file must be a JSON array, got {type(raw).__name__}")

    # 遅延 import: embedding を使わないテスト時に openai 認証を回避するため
    if with_embeddings:
        from src.tools.embed import embed_text
    else:
        embed_text = None  # type: ignore[assignment]

    count = 0
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValueError(f"each entry must be an object, got {type(entry).__name__}")
        required = {
            "user_id",
            "business_type",
            "what_worked",
            "why_worked",
            "reproducibility_score",
        }
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"entry missing required fields: {missing}")

        case = SuccessCase(
            user_id=entry["user_id"],
            business_type=entry["business_type"],
            what_worked=entry["what_worked"],
            why_worked=entry["why_worked"],
            reproducibility_score=float(entry["reproducibility_score"]),
            owner_label=entry.get("owner_label", ""),
            concrete_prompt=entry.get("concrete_prompt", ""),
            quantitative_effect=entry.get("quantitative_effect", ""),
        )
        seed_success_case(case)
        if with_embeddings and embed_text is not None:
            vector = embed_text(_build_embedding_text(case))
            register_embedding(case.id, vector)
        count += 1

    return count


def load_cold_start_templates(path: Path | None = None) -> int:
    """JSON から ColdStartTemplate を読み込み、in-memory store に投入する。

    Args:
        path: JSON ファイルのパス。None の場合 docs/sample_data/cold_start_templates.json を使用。

    Returns:
        投入された件数。

    Raises:
        FileNotFoundError: 指定パスが存在しない場合。
        ValueError: JSON が ColdStartTemplate の必須フィールドを欠く場合。
    """
    tpl_path = path or DEFAULT_TEMPLATE_PATH
    if not tpl_path.exists():
        raise FileNotFoundError(f"template file not found: {tpl_path}")

    raw = json.loads(tpl_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"template file must be a JSON array, got {type(raw).__name__}")

    required = {
        "business_category",
        "title",
        "description",
        "common_pain",
        "prompt",
        "steps",
        "suitable_for",
        "cautions",
        "feedback_question",
    }

    count = 0
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValueError(f"each entry must be an object, got {type(entry).__name__}")
        missing = required - entry.keys()
        if missing:
            raise ValueError(f"template entry missing required fields: {missing}")

        template = ColdStartTemplate(
            business_category=entry["business_category"],
            title=entry["title"],
            description=entry["description"],
            common_pain=entry["common_pain"],
            prompt=entry["prompt"],
            steps=list(entry["steps"]),
            suitable_for=entry["suitable_for"],
            cautions=entry["cautions"],
            feedback_question=entry["feedback_question"],
        )
        seed_cold_start_template(template)
        count += 1

    return count
