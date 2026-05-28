"""CI が import エラーで落ちないことを保証する最低限のスモークテスト。

Agent 呼び出しは Azure 接続が必要なため、ここでは行わない。
PROJECT_ENDPOINT / AGENT_ID が未設定でも import まで通る構造になっているかは
src/app.py の起動時 raise でカバー（このテストはダミー値を入れて import 経路を確認）。
"""

from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import MagicMock, patch


def test_src_package_is_importable() -> None:
    """src パッケージが import 可能であること。"""
    pkg = importlib.import_module("src")
    assert pkg is not None


def test_app_module_requires_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """環境変数未設定時に明示的にエラーを出す挙動。"""
    monkeypatch.delenv("PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AGENT_ID", raising=False)
    # 既に import 済みの場合はキャッシュを落とす
    sys.modules.pop("src.app", None)

    try:
        importlib.import_module("src.app")
    except RuntimeError as e:
        assert "PROJECT_ENDPOINT" in str(e) or "AGENT_ID" in str(e)
    else:
        # ダミー値が環境に残っていた等で raise しなかった場合は環境を疑う
        assert os.environ.get("PROJECT_ENDPOINT") and os.environ.get("AGENT_ID")


def test_app_seeds_cold_start_templates_on_startup(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """app.py 起動時に cold_start_templates が in-memory store へ投入されること。"""
    monkeypatch.setenv("PROJECT_ENDPOINT", "https://dummy.example.com")
    monkeypatch.setenv("AGENT_ID", "asst_dummy")
    sys.modules.pop("src.app", None)

    with (
        patch("src.tools.seed.load_cold_start_templates", return_value=8) as mock_load,
        patch("azure.ai.agents.AgentsClient", return_value=MagicMock()),
        patch("src.tools.credential.get_default_credential", return_value=MagicMock()),
    ):
        importlib.import_module("src.app")

    mock_load.assert_called_once()
