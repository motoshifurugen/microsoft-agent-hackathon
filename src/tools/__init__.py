"""Tool function implementations called by child agents via function calling.

データ準備担当 (RAG 担当) との接続点。MVP では mock 実装で動作させ、
段階的に Cosmos DB / Azure AI Search / Microsoft Graph 実装に差し替える。
"""

from __future__ import annotations
