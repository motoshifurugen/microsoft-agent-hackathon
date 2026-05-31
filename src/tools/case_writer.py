"""成功事例の書き込み経路を 1 本に集約する。

成功事例は in-memory store への保存 (seed_success_case) だけでは
semantic_search の対象にならない。_embedding_search は embedding 登録済みの
事例しか走査しないため、登録と同時に embedding も作る必要がある。

ShareForm 経由 (src/api/cases.py) と Agent 経由 (tool_register_success_case)
の両方がこの register_success_case を通ることで、「登録された成功事例が
次の誰かの検索に必ずヒットする」という組織知の蓄積ループを保証する。
"""

from __future__ import annotations

import logging

from src.tools.cosmos_io import SuccessCase, register_embedding, seed_success_case

_logger = logging.getLogger(__name__)


def build_embedding_text(case: SuccessCase) -> str:
    """成功事例を embedding 化するときのテキスト表現。

    business_type と what_worked を結合し、検索クエリとの類似度が出やすい形にする。
    seed と登録 API で同じ表現を使うため共通化している。
    """
    return f"{case.business_type}\n{case.what_worked}"


def register_success_case(case: SuccessCase, *, with_embedding: bool = True) -> str:
    """成功事例を永続化し、検索可能にするため embedding も登録する。

    embedding 生成は Azure OpenAI 呼び出しを伴うため、失敗しても登録自体は
    成立させる (検索ヒットしないだけで一覧・カテゴリには現れる)。
    embed の import は遅延させ、embedding 不要なテスト環境で openai 認証を避ける。

    Args:
        case: 保存する SuccessCase。
        with_embedding: False なら embedding 生成をスキップ (テスト用)。

    Returns:
        保存された成功事例の ID。
    """
    seed_success_case(case)
    if with_embedding:
        try:
            from src.tools.embed import embed_text

            vector = embed_text(build_embedding_text(case))
            register_embedding(case.id, vector)
        except Exception as exc:
            _logger.warning("embedding 生成に失敗 (登録は継続): %s", exc)
    return case.id
