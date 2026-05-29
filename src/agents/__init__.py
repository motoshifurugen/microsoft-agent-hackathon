"""Multi-Agent definitions for the AI 浸透加速エージェント.

各モジュールは Agent の `name`・`instructions`・`description` を提供する。
Foundry への登録は scripts/create_agents.py が担当する。
"""

from __future__ import annotations

from src.agents import collector, matcher, orchestrator, proposer

__all__ = ["collector", "matcher", "orchestrator", "proposer"]
