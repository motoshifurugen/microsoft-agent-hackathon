"""各 Agent モジュールが必須メタデータ (NAME / DESCRIPTION / INSTRUCTIONS) を持つこと。

scripts/create_agents.py が参照する属性が欠落していないことを保証する。
"""

from __future__ import annotations

from types import ModuleType

import pytest

from src.agents import collector, matcher, orchestrator, proposer

ALL_AGENTS: list[ModuleType] = [orchestrator, collector, matcher, proposer]
CHILD_AGENTS: list[ModuleType] = [collector, matcher, proposer]


@pytest.mark.parametrize("agent_module", ALL_AGENTS)
def test_agent_has_required_metadata(agent_module: ModuleType) -> None:
    assert hasattr(agent_module, "NAME"), f"{agent_module.__name__} missing NAME"
    assert hasattr(agent_module, "DESCRIPTION"), f"{agent_module.__name__} missing DESCRIPTION"
    assert hasattr(agent_module, "INSTRUCTIONS"), f"{agent_module.__name__} missing INSTRUCTIONS"

    assert isinstance(agent_module.NAME, str) and agent_module.NAME.strip()
    assert isinstance(agent_module.DESCRIPTION, str) and agent_module.DESCRIPTION.strip()
    assert isinstance(agent_module.INSTRUCTIONS, str) and agent_module.INSTRUCTIONS.strip()


def test_agent_names_are_unique() -> None:
    names = [m.NAME for m in ALL_AGENTS]
    assert len(names) == len(set(names)), f"duplicate agent names: {names}"


def test_orchestrator_instructions_reference_all_children() -> None:
    """Orchestrator の instructions が 3 子 Agent の名前を参照していること。

    instructions と実際のエージェント名がズレると Orchestrator が子を呼べないため。
    """
    for child in CHILD_AGENTS:
        assert child.NAME in orchestrator.INSTRUCTIONS, (
            f"orchestrator INSTRUCTIONS does not reference child '{child.NAME}'"
        )


def test_child_agents_names_match_expected() -> None:
    expected = {"collector", "matcher", "proposer"}
    actual = {m.NAME for m in CHILD_AGENTS}
    assert actual == expected
