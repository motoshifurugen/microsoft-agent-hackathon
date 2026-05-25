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
    FunctionTool,  # pyright: ignore[reportPrivateImportUsage]
)
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

from src.agents import collector, matcher, observer, proposer
from src.agents import orchestrator as orch_module
from src.tools.registry import ORCHESTRATOR_FUNCTIONS

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


MANAGED_AGENT_NAMES = {
    orch_module.NAME,
    observer.NAME,
    collector.NAME,
    matcher.NAME,
    proposer.NAME,
}


def _delete_existing(client: AgentsClient) -> None:
    """同名の既存 Agent を削除する (再実行時の冪等性確保)。

    business-agent 等、本スクリプト管理外の Agent は触らない。
    """
    for agent in client.list_agents():
        if agent.name in MANAGED_AGENT_NAMES:
            client.delete_agent(agent.id)
            sys.stderr.write(f"deleted existing agent: {agent.name} ({agent.id})\n")


def main() -> int:
    if not ENDPOINT:
        sys.stderr.write("PROJECT_ENDPOINT が空です\n")
        return 1

    client = AgentsClient(endpoint=ENDPOINT, credential=AzureCliCredential())

    # 0. 同名の既存 Agent を削除 (冪等性)
    _delete_existing(client)

    # 1. 子 Agent を順次作成
    child_ids: dict[str, str] = {}
    connected_tools: list = []
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
        connected_tools.extend(connected.definitions)

    # 2. Orchestrator に渡す tools を合成 (ConnectedAgentTool + FunctionTool)
    function_tool = FunctionTool(functions=ORCHESTRATOR_FUNCTIONS)
    orchestrator_tools = connected_tools + function_tool.definitions

    # 3. Orchestrator を作成
    orchestrator_agent = client.create_agent(
        model=MODEL_DEPLOYMENT,
        name=orch_module.NAME,
        instructions=orch_module.INSTRUCTIONS,
        tools=orchestrator_tools,
    )
    sys.stderr.write(f"created orchestrator: {orch_module.NAME} ({orchestrator_agent.id})\n")

    # 4. .env 転記用に標準出力
    print(f"AGENT_ID={orchestrator_agent.id}")
    print(f"AGENT_ID_OBSERVER={child_ids[observer.NAME]}")
    print(f"AGENT_ID_COLLECTOR={child_ids[collector.NAME]}")
    print(f"AGENT_ID_MATCHER={child_ids[matcher.NAME]}")
    print(f"AGENT_ID_PROPOSER={child_ids[proposer.NAME]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
