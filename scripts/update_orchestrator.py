"""既存の Orchestrator を AGENT_ID を変えずに in-place 更新する。

create_agents.py は delete+create で AGENT_ID が変わるため、更新のたびに
コンテナの再デプロイ (.env 転記) が必要になる。本スクリプトは
update_agent() で既存 Orchestrator の instructions と tools だけを差し替えるため、
AGENT_ID が安定し、Chainlit (src/app.py) と Kodama の両方が再デプロイ無しで
新しい instructions / tool (tool_register_success_case 等) を即座に利用できる。

実行例:
    PROJECT_ENDPOINT=https://<foundry>.services.ai.azure.com/api/projects/<project> \\
    uv run python scripts/update_orchestrator.py

子 Agent (collector/matcher/proposer) は既存のものを名前で再解決して
ConnectedAgentTool を組み直す。子を作り直したい場合は create_agents.py を使う。
"""

from __future__ import annotations

import os
import sys
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

from src.agents import collector, matcher, proposer
from src.agents import orchestrator as orch_module
from src.tools.registry import ORCHESTRATOR_FUNCTIONS

load_dotenv()

ENDPOINT = os.environ.get("PROJECT_ENDPOINT", "").strip()

# 子 Agent: 名前 → DESCRIPTION (ConnectedAgentTool 再構築に必要)
CHILD_DESCRIPTIONS: dict[str, str] = {
    collector.NAME: collector.DESCRIPTION,
    matcher.NAME: matcher.DESCRIPTION,
    proposer.NAME: proposer.DESCRIPTION,
}


def main() -> int:
    if not ENDPOINT:
        sys.stderr.write("PROJECT_ENDPOINT が空です\n")
        return 1

    client = AgentsClient(endpoint=ENDPOINT, credential=AzureCliCredential())

    # 1. 既存 Agent を名前で解決 (最新の 1 件)
    by_name: dict[str, object] = {}
    for agent in client.list_agents():
        if agent.name in ({orch_module.NAME} | set(CHILD_DESCRIPTIONS)):
            by_name.setdefault(agent.name, agent)

    orchestrator = by_name.get(orch_module.NAME)
    if orchestrator is None:
        sys.stderr.write(
            f"Orchestrator '{orch_module.NAME}' が見つかりません。先に create_agents.py を実行してください\n"
        )
        return 1

    missing = [name for name in CHILD_DESCRIPTIONS if name not in by_name]
    if missing:
        sys.stderr.write(
            f"子 Agent が見つかりません: {missing}。先に create_agents.py を実行してください\n"
        )
        return 1

    # 2. 既存子 ID から ConnectedAgentTool を組み直す
    connected_tools: list = []
    for name, description in CHILD_DESCRIPTIONS.items():
        child = by_name[name]
        connected = ConnectedAgentTool(id=child.id, name=name, description=description)  # type: ignore[attr-defined]
        connected_tools.extend(connected.definitions)

    # 3. FunctionTool (tool_register_success_case を含む最新セット) を合成
    function_tool = FunctionTool(functions=ORCHESTRATOR_FUNCTIONS)
    orchestrator_tools = connected_tools + function_tool.definitions

    # 4. AGENT_ID を変えずに instructions / tools を差し替え。model は既存値を維持。
    updated = client.update_agent(
        agent_id=orchestrator.id,  # type: ignore[attr-defined]
        model=orchestrator.model,  # type: ignore[attr-defined]
        name=orch_module.NAME,
        description=orch_module.DESCRIPTION,
        instructions=orch_module.INSTRUCTIONS,
        tools=orchestrator_tools,
    )
    sys.stderr.write(f"updated orchestrator in place: {orch_module.NAME} ({updated.id})\n")
    print(f"AGENT_ID={updated.id}  (変更なし。再デプロイ不要)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
