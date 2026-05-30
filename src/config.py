"""環境変数集約モジュール。

`.env` の値を一元的に読み出し、欠落時には起動時に即発見できるよう raise する。
複数の Agent ID (Orchestrator + 4 子 Agent) を扱うため、変数名で責務を分離する。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AgentIds:
    """4 Agent の ID 集合。create_agents.py の出力を .env に転記する。

    AGENT_ID は Orchestrator の ID を指す (後方互換のため変数名は維持)。
    """

    orchestrator: str
    collector: str
    matcher: str
    proposer: str


@dataclass(frozen=True)
class Settings:
    project_endpoint: str
    model_deployment: str
    agent_ids: AgentIds


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} が未設定です。.env または環境変数で指定してください")
    return value


def _optional(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_settings(require_child_agents: bool = False) -> Settings:
    """環境変数から設定を読み込む。

    Args:
        require_child_agents: True の場合、子 Agent の ID も必須にする。
            create_agents.py 実行前 (子 Agent 未作成) はスケルトン import 可能にするため False を許容。
    """
    orchestrator_id = _require("AGENT_ID")

    if require_child_agents:
        agent_ids = AgentIds(
            orchestrator=orchestrator_id,
            collector=_require("AGENT_ID_COLLECTOR"),
            matcher=_require("AGENT_ID_MATCHER"),
            proposer=_require("AGENT_ID_PROPOSER"),
        )
    else:
        agent_ids = AgentIds(
            orchestrator=orchestrator_id,
            collector=_optional("AGENT_ID_COLLECTOR"),
            matcher=_optional("AGENT_ID_MATCHER"),
            proposer=_optional("AGENT_ID_PROPOSER"),
        )

    return Settings(
        project_endpoint=_require("PROJECT_ENDPOINT"),
        model_deployment=_optional("MODEL_DEPLOYMENT", "gpt-4o"),
        agent_ids=agent_ids,
    )
