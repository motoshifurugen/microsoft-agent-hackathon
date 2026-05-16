# TDD Command

description: Enforce test-driven development with pytest. Always write tests first, then minimal implementation, then refactor.

---

## Purpose

このプロジェクト (Python 3.12 + pytest + Azure AI Foundry Agent Service) における TDD の手順を強制する。
実装より先にテストを書くことで、Azure 接続に依存しない堅牢なロジックを育てる。

---

## Core Rule (CRITICAL)

テストより先に実装を書いてはいけない。

正しい順序:

1. 要件を平易な言葉で確認する
2. 入力・出力・副作用を定義する
3. pytest テストを書く
4. テストが失敗することを確認する (`uv run pytest -v`)
5. テストが通る最小の実装を書く
6. 再度テストを実行して GREEN を確認する
7. リファクタ後、再実行する

---

## Azure 固有のルール

- Azure Foundry Agent (`AgentsClient`, `ThreadsClient`) の呼び出しは **必ずモック** する
- `azure.identity.DefaultAzureCredential` は CI 上で使えないため、テストでは差し替える
- 環境変数 (`PROJECT_ENDPOINT`, `AGENT_ID`) は `monkeypatch` で注入する

モックの例:
```python
from unittest.mock import MagicMock, patch

def test_on_message(monkeypatch):
    monkeypatch.setenv("PROJECT_ENDPOINT", "https://dummy.example.com")
    monkeypatch.setenv("AGENT_ID", "asst_dummy")
    with patch("src.app._agents") as mock_agents:
        mock_agents.messages.create.return_value = MagicMock()
        # テスト本体
```

---

## テスト実行コマンド

```bash
# 全テスト
uv run pytest -v

# 特定ファイル
uv run pytest tests/test_smoke.py -v

# カバレッジ付き（pytest-cov を追加した場合）
uv run pytest --cov=src --cov-report=term-missing
```

---

## TDD サイクル

RED:
- テストが期待する振る舞いを記述する
- 実装が存在しないため失敗が期待される

GREEN:
- テストが通る最小のコードを書く
- 最適化しない

REFACTOR:
- 構造・命名を改善する
- 振る舞いを変えない
- `uv run ruff check src tests` と `uv run pyright` を通す

---

## カバレッジ指針

- 目標: 80% 以上
- `src/app.py` の各ハンドラ (`on_chat_start`, `on_message`) は個別にテストする
- Azure 接続部分は integration test に分類し、CI では skip しても良い（`@pytest.mark.skip(reason="requires Azure")` を明示する）

---

## 推奨ワークフロー

1. `/plan` で実装の方針を決める
2. `/tdd` でテスト → 実装 → リファクタ
3. `/code-review` でレビュー
4. `uv run ruff format src tests` でフォーマット整理してコミット
