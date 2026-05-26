"""Azure OpenAI の embedding API ヘルパー。

semantic_search が text-embedding-3-small (Foundry にデプロイ済み) を呼び、
cosine similarity ベースの類似度ランキングを行うための基盤。
"""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from urllib.parse import urlparse

from azure.identity import get_bearer_token_provider
from openai import AzureOpenAI

from src.tools.credential import get_default_credential

_AAD_SCOPE = "https://cognitiveservices.azure.com/.default"
_API_VERSION = "2024-02-01"
_DEFAULT_DEPLOYMENT = "text-embedding-3-small"

_client: AzureOpenAI | None = None


def _build_openai_endpoint() -> str:
    """PROJECT_ENDPOINT から Azure OpenAI 用 endpoint を導出する。

    PROJECT_ENDPOINT は Foundry の services.ai.azure.com 系。
    embeddings API は同リソースの openai.azure.com 系 endpoint を使う。
    """
    project_endpoint = os.environ.get("PROJECT_ENDPOINT", "").strip()
    if not project_endpoint:
        raise RuntimeError("PROJECT_ENDPOINT が未設定です。embedding API endpoint を構築できません")
    host = urlparse(project_endpoint).hostname
    if not host:
        raise RuntimeError(f"PROJECT_ENDPOINT を解析できません: {project_endpoint}")
    resource_name = host.split(".")[0]
    return f"https://{resource_name}.openai.azure.com/"


def _get_client() -> AzureOpenAI:
    """Lazy に AzureOpenAI client を初期化して返す。"""
    global _client
    if _client is None:
        # ローカル (環境変数/VSCode) + Container Apps (Managed Identity) 両対応
        token_provider = get_bearer_token_provider(get_default_credential(), _AAD_SCOPE)
        _client = AzureOpenAI(
            azure_endpoint=_build_openai_endpoint(),
            api_version=_API_VERSION,
            azure_ad_token_provider=token_provider,
        )
    return _client


def embed_text(text: str) -> list[float]:
    """テキストを埋め込みベクトルに変換する。

    Args:
        text: 任意の文字列。空文字は不可。

    Returns:
        embedding ベクトル (float のリスト)。

    Raises:
        ValueError: text が空。
    """
    if not text:
        raise ValueError("text は空にできません")
    deployment = os.environ.get("EMBEDDING_DEPLOYMENT", _DEFAULT_DEPLOYMENT).strip()
    client = _get_client()
    response = client.embeddings.create(model=deployment, input=text)
    return list(response.data[0].embedding)


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """2 つのベクトルの cosine similarity を返す (0.0〜1.0、不一致時 0.0)。"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)
