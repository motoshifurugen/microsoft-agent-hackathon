# Code Review Command

description: Perform a careful code review focused on security, correctness, and Python quality. Strict on secrets and Azure credential handling.

---

## Purpose

このプロジェクト (Python 3.12 + Chainlit + Azure AI Foundry) に特化したコードレビューを行う。
Azure 認証情報の漏洩と、非同期処理のバグを特に重視する。

---

## Review Scope

**コミット前の差分のみ** を対象にする。

```bash
git diff --name-only HEAD
```

上記で表示されたファイルのみレビューし、関係のないファイルは無視する。

---

## Security Issues (CRITICAL)

以下が1つでも発見されたらレビューをブロックする。

- `PROJECT_ENDPOINT` / `AGENT_ID` / Azure 接続文字列のハードコード
- `.env` ファイルをコードで直接 open している
- `DefaultAzureCredential` 以外の認証情報をコードに埋め込んでいる
- `AzureCliCredential` / `ClientSecretCredential` にシークレットをベタ書きしている
- 外部入力を検証せずに Azure API へ渡している
- ユーザー入力を `eval()` や `exec()` に渡している

---

## Code Quality Issues (HIGH)

以下は原則ブロック（ユーザーが明示的に承認した場合のみ通過）。

- 50 行超の関数
- 800 行超のファイル
- ネストが 4 段超
- `except Exception: pass` または例外を握りつぶすパターン
- `print()` のデバッグ出力をコードに残している
- `# type: ignore` を理由なく使っている
- `asyncio` / `chainlit` の非同期パターンの誤用（`await` 抜け、同期関数内で `asyncio.run()` 等）

---

## Python/Azure 固有チェック (MEDIUM)

報告するが原則ブロックしない。

- `ruff check` / `ruff format` が通っていない
- `pyright` のエラーや `reportMissingImports` が残っている
- Azure SDK の Deprecated API を使っている
- `_agents` 等のモジュールレベルの可変状態が増えている
- Chainlit の `cl.user_session` から取得した値を None チェックなしで使っている
- テストが追加されていない新規ロジック

---

## 自動チェック手順

レビュー前に必ず以下を実行して結果を確認する:

```bash
# Lint
uv run ruff check src tests

# Format
uv run ruff format --check src tests

# Type check
uv run pyright

# Tests
PROJECT_ENDPOINT=dummy AGENT_ID=dummy uv run pytest -v
```

いずれかが失敗していたら、レビューより先に修正する。

---

## Review Output Format

各問題を以下の形式で報告する:

- Severity: CRITICAL / HIGH / MEDIUM
- ファイルパス
- 行番号 (可能な場合)
- 問題の説明
- 改善の具体的な提案

曖昧なコメントは書かない。

---

## Approval Rules

- CRITICAL がある: ❌ 承認しない
- HIGH がある: ❌ 承認しない（ユーザーが明示的に受け入れた場合のみ）
- MEDIUM のみ: ⚠️ コメント付きで承認

問題が残っているのに「全体的に良さそうです」と言わない。

---

## 推奨ワークフロー

1. コードを書く / 修正する
2. `uv run pytest -v` を実行する
3. `/code-review` を実行する
4. CRITICAL・HIGH を修正する
5. `uv run ruff format src tests` を実行する
6. コミットする
