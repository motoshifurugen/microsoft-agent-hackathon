"""5 Agent (Orchestrator + 4 子) を Foundry に作成し、ConnectedAgentTool で結合する。

実行例:
    PROJECT_ENDPOINT=https://<foundry>.services.ai.azure.com/api/projects/<project> \\
    MODEL_DEPLOYMENT=gpt-4o \\
    uv run python scripts/create_agents.py

出力された AGENT_ID_* を `.env` に転記する:
    AGENT_ID=<orchestrator id>           # 後方互換: src/app.py は AGENT_ID を Orchestrator として参照
    AGENT_ID_OBSERVER=<observer id>
    AGENT_ID_COLLECTOR=<collector id>
    AGENT_ID_MATCHER=<matcher id>
    AGENT_ID_PROPOSER=<proposer id>

注意: 既存の `business-agent` は本スクリプトとは独立して残る。不要なら手動で削除する。
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

# scripts/ から実行された際にリポジトリルートを sys.path に追加して src を import 可能にする
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from azure.ai.agents import AgentsClient
from azure.ai.agents.models import (
    ConnectedAgentTool,  # pyright: ignore[reportPrivateImportUsage]
)
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from src.agents import collector, matcher, observer, proposer
from src.agents import orchestrator as orch_module

load_dotenv()

ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "").strip()
MODEL_DEPLOYMENT = os.environ.get("MODEL_DEPLOYMENT", "gpt-4o").strip()


@dataclass(frozen=True)
class ChildAgentSpec:
    """子 Agent の定義モジュール束ね用。"""

    name: str
    description: str
    instructions: str


CHILD_AGENTS: list[ChildAgentSpec] = [
    ChildAgentSpec(
        name=observer.NAME, description=observer.DESCRIPTION, instructions=observer.INSTRUCTIONS
    ),
    ChildAgentSpec(
        name=collector.NAME, description=collector.DESCRIPTION, instructions=collector.INSTRUCTIONS
    ),
    ChildAgentSpec(
        name=matcher.NAME, description=matcher.DESCRIPTION, instructions=matcher.INSTRUCTIONS
    ),
    ChildAgentSpec(
        name=proposer.NAME, description=proposer.DESCRIPTION, instructions=proposer.INSTRUCTIONS
    ),
]


def main() -> int:
    if not ENDPOINT:
        sys.stderr.write("PROJECT_ENDPOINT が空です\n")
        return 1

    client = AgentsClient(endpoint=ENDPOINT, credential=AzureCliCredential())

    # 1. 子 Agent を順次作成
    child_ids: dict[str, str] = {}
    child_tools: list = []
    for spec in CHILD_AGENTS:
        created = client.create_agent(
            model=MODEL_DEPLOYMENT,
            name=spec.name,
            instructions=spec.instructions,
        )
        child_ids[spec.name] = created.id
        sys.stderr.write(f"created child agent: {spec.name} ({created.id})\n")

        connected = ConnectedAgentTool(
            id=created.id,
            name=spec.name,
            description=spec.description,
        )
        child_tools.extend(connected.definitions)

    # 2. Orchestrator を子 Agent を ConnectedAgentTool として登録した上で作成
    orchestrator_agent = client.create_agent(
        model=MODEL_DEPLOYMENT,
        name=orch_module.NAME,
        instructions=orch_module.INSTRUCTIONS,
        tools=child_tools,
    )
    sys.stderr.write(f"created orchestrator: {orch_module.NAME} ({orchestrator_agent.id})\n")

    # 3. .env 転記用に標準出力
    print(f"AGENT_ID={orchestrator_agent.id}")
    print(f"AGENT_ID_OBSERVER={child_ids[observer.NAME]}")
    print(f"AGENT_ID_COLLECTOR={child_ids[collector.NAME]}")
    print(f"AGENT_ID_MATCHER={child_ids[matcher.NAME]}")
    print(f"AGENT_ID_PROPOSER={child_ids[proposer.NAME]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
