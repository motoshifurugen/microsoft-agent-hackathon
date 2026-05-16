"""Foundry Agent を作成し agent_id を出力する一回限りのスクリプト。

使用例:
    PROJECT_ENDPOINT=https://<foundry>.services.ai.azure.com/api/projects/<project> \\
    MODEL_DEPLOYMENT=gpt-4o \\
    uv run python scripts/create_agent.py

出力の `AGENT_ID=...` を `.env` に書き写す。
"""

from __future__ import annotations

import os
import sys

from azure.ai.agents import AgentsClient
from azure.identity import AzureCliCredential

ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "").strip()
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT", "gpt-4o").strip()
AGENT_NAME = os.environ.get("AGENT_NAME", "business-agent").strip()

if not ENDPOINT:
    sys.stderr.write("PROJECT_ENDPOINT が空です\n")
    sys.exit(1)

INSTRUCTIONS = """\
あなたは業務改革を支援する Agentic AI アシスタントです。

ユーザーの業務課題を聞き取り、AI エージェントで解決できる切り口を具体的に提案してください。
- まず課題の構造（誰が・何に・なぜ困っているか）を整理する
- AI エージェントで自動化・支援できる範囲と、人間の判断が必要な範囲を切り分ける
- 段階的な実装ステップ（MVP → 拡張）を示す
- 日本語で簡潔に、必要なら箇条書きで回答する
"""


def main() -> int:
    client = AgentsClient(endpoint=ENDPOINT, credential=AzureCliCredential())

    agent = client.create_agent(
        model=MODEL_DEPLOYMENT,
        name=AGENT_NAME,
        instructions=INSTRUCTIONS,
    )

    print(f"AGENT_ID={agent.id}")
    print(f"AGENT_NAME={agent.name}")
    print(f"MODEL={agent.model}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
