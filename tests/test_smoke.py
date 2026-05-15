"""CI が import エラーで落ちないことを保証する最低限のスモークテスト。

Agent 呼び出しは Azure 接続が必要なため、ここでは行わない。
PROJECT_ENDPOINT / AGENT_ID が未設定でも import まで通る構造になっているかは
src/app.py の起動時 raise でカバー（このテストはダミー値を入れて import 経路を確認）。
"""

from __future__ import annotations

import importlib
import os


def test_src_package_is_importable() -> None:
    """src パッケージが import 可能であること。"""
    pkg = importlib.import_module("src")
    assert pkg is not None


def test_app_module_requires_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """環境変数未設定時に明示的にエラーを出す挙動。"""
    monkeypatch.delenv("PROJECT_ENDPOINT", raising=False)
    monkeypatch.delenv("AGENT_ID", raising=False)
    # 既に import 済みの場合はキャッシュを落とす
    import sys

    sys.modules.pop("src.app", None)

    try:
        importlib.import_module("src.app")
    except RuntimeError as e:
        assert "PROJECT_ENDPOINT" in str(e) or "AGENT_ID" in str(e)
    else:
        # ダミー値が環境に残っていた等で raise しなかった場合は環境を疑う
        assert os.environ.get("PROJECT_ENDPOINT") and os.environ.get("AGENT_ID")
