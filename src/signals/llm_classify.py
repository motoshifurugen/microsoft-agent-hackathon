"""投稿文の業務カテゴリ分類 (LLM 文脈判断、ルールベース fallback 付き)。

検知の中核判断を Azure OpenAI (chat.completions) の文脈解釈で行う。キーワード一致では
取りこぼす言い回し (例「議事録まとめ直すの今日もか…」) も意味で拾える。
クレデンシャル欠落や API 失敗・不正応答時は、決定論的な rule 分類器 (classify) に fallback し、
オフライン/CI でも検知が止まらないようにする (embed.py の埋め込み fallback と同じ思想)。

設計上の判断:
- LLM の出力カテゴリは KNOWN_CATEGORIES で検証する。集合外を返したら不正応答として fallback。
- LLM が業務無関係と判断した場合は "none" を返させ、None (= 支援候補にしない) として尊重する。
- PROJECT_ENDPOINT 未設定時はネットワークを試みず即 rule fallback (テスト/ローカルの決定論性)。
"""

from __future__ import annotations

import json
import logging
import os
from urllib.parse import urlparse

from src.signals.classify import KNOWN_CATEGORIES, Classification, classify

_logger = logging.getLogger(__name__)

_AAD_SCOPE = "https://cognitiveservices.azure.com/.default"
_API_VERSION = "2024-08-01-preview"
_DEFAULT_DEPLOYMENT = "gpt-4o-mini"
_NONE_LABEL = "none"
# 回線断時に SDK 既定 (timeout 600s / retries 2) で長時間ブロックせず、素早くルール分類に
# fallback させるための fail-fast 設定 (embed.py と同じ思想)。
_REQUEST_TIMEOUT = 10.0
_MAX_RETRIES = 0

_client = None  # type: ignore[var-annotated]


def _build_openai_endpoint() -> str:
    """PROJECT_ENDPOINT (Foundry) から Azure OpenAI 用 endpoint を導出する。"""
    project_endpoint = os.environ.get("PROJECT_ENDPOINT", "").strip()
    if not project_endpoint:
        raise RuntimeError("PROJECT_ENDPOINT が未設定です")
    host = urlparse(project_endpoint).hostname
    if not host:
        raise RuntimeError(f"PROJECT_ENDPOINT を解析できません: {project_endpoint}")
    return f"https://{host.split('.')[0]}.openai.azure.com/"


def _get_client():  # type: ignore[no-untyped-def]
    """Lazy に AzureOpenAI client を初期化して返す (embed.py と同じ認証パターン)。"""
    global _client
    if _client is None:
        from azure.identity import get_bearer_token_provider
        from openai import AzureOpenAI

        from src.tools.credential import get_default_credential

        token_provider = get_bearer_token_provider(get_default_credential(), _AAD_SCOPE)
        _client = AzureOpenAI(
            azure_endpoint=_build_openai_endpoint(),
            api_version=_API_VERSION,
            azure_ad_token_provider=token_provider,
            timeout=_REQUEST_TIMEOUT,
            max_retries=_MAX_RETRIES,
        )
    return _client


def _build_prompt(text: str) -> list[dict[str, str]]:
    categories = "、".join(KNOWN_CATEGORIES)
    system = (
        "あなたは社内 AI 活用支援ツールの分類器です。社員の短い発話を読み、"
        "業務上の手間・困りごとが次のどのカテゴリに当たるかを判定します。\n"
        f"カテゴリ: {categories}\n"
        "判定ルール:\n"
        "- いずれかのカテゴリの作業に負荷・困りごとを感じている発話なら、そのカテゴリ名を返す。\n"
        f'- 感情のみ・雑談・業務に無関係なら "{_NONE_LABEL}" を返す。\n'
        '- 必ず次の JSON のみを返す: {"category": <カテゴリ名 または '
        f'"{_NONE_LABEL}">, "confidence": <0〜1 の数値>, "summary": <日本語の短い要約>}}'
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": text},
    ]


def _invoke_llm(text: str) -> Classification | None:
    """LLM を呼んで分類する。応答が不正なら例外を送出する (呼び出し側で fallback)。

    Returns:
        分類結果。LLM が業務無関係 ("none") と判断した場合は None。
    """
    deployment = (
        os.environ.get("MODEL_DEPLOYMENT", _DEFAULT_DEPLOYMENT).strip() or _DEFAULT_DEPLOYMENT
    )
    response = _get_client().chat.completions.create(
        model=deployment,
        messages=_build_prompt(text),  # type: ignore[arg-type]
        response_format={"type": "json_object"},
        temperature=0,
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    category = str(payload.get("category", "")).strip()

    if category == _NONE_LABEL:
        return None
    if category not in KNOWN_CATEGORIES:
        raise ValueError(f"LLM が未知カテゴリを返しました: {category!r}")

    confidence = float(payload.get("confidence", 0.7))
    confidence = min(max(confidence, 0.0), 1.0)
    summary = str(payload.get("summary", "")).strip() or f"{category}に負荷を感じている可能性"
    return Classification(
        business_category=category, confidence=round(confidence, 2), summary=summary
    )


def classify_with_llm(text: str) -> Classification | None:
    """投稿文を LLM 文脈判断で分類する。失敗時はルールベースに fallback。

    Slack Bot / Teams アダプタ / デモ API の共通検知サービス (service.handle_message) から使う。
    """
    normalized = text.strip()
    if not normalized:
        return None

    # PROJECT_ENDPOINT 未設定ならネットワークを試みず即ルール分類 (CI/ローカルの決定論性)。
    if not os.environ.get("PROJECT_ENDPOINT", "").strip():
        return classify(normalized)

    try:
        return _invoke_llm(normalized)
    except Exception:
        _logger.warning("LLM classification failed; falling back to rule-based", exc_info=True)
        return classify(normalized)
