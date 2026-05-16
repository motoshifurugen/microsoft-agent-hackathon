# Build and Fix Command

description: Incrementally fix ruff / pyright / pytest errors one at a time. Explain before changing. Never guess.

---

## Purpose

このプロジェクト (Python 3.12 + ruff + pyright + pytest) のビルドエラーを安全に1つずつ直す。
速さより安定性を優先する。

---

## Core Policy

- 1回に1エラーだけ修正する
- 修正前に原因を説明する
- 修正後に必ずチェックコマンドを再実行する
- 不確かなときは止まってユーザーに相談する

---

## Step 1: エラーの確認

以下を順に実行し、エラーを把握する:

```bash
# Lint エラー
uv run ruff check src tests

# フォーマットエラー
uv run ruff format --check src tests

# 型エラー
uv run pyright

# テスト失敗
PROJECT_ENDPOINT=dummy AGENT_ID=dummy uv run pytest -v
```

---

## Step 2: エラーの優先順位付け

優先順位:
1. pyright のコンパイルエラー（インポート失敗、型不整合）
2. ruff の lint エラー（バグにつながるルール: B, F）
3. pytest の失敗
4. ruff の format エラー
5. ruff の警告（W, SIM 等）

---

## Step 3: エラーを1つずつ修正する

各エラーに対して以下のループを実行する:

### 3.1 コンテキストを表示
- ファイルパス
- 行番号
- エラー前後 5 行

まだコードを変更しない。

### 3.2 原因を説明
- ツールが何を指摘しているか
- なぜこのエラーが発生したか
- 根本原因か、派生エラーか

不明なら「わかりません」と言う。

### 3.3 修正案を提示
- 何を変えるか
- なぜこの修正が最小・安全か
- 副作用があれば明記

### 3.4 修正を適用
ルール:
- 必要な箇所だけ変更する
- 無関係なコードをリファクタしない
- `# type: ignore` で黙らせない（原因を直す）
- Azure SDK の型スタブがない場合は `reportMissingTypeStubs = false` で対応済みなので、無理に型注釈を追加しない

### 3.5 チェックを再実行
```bash
uv run ruff check src tests
uv run pyright
PROJECT_ENDPOINT=dummy AGENT_ID=dummy uv run pytest -v
```

### 3.6 確認
- 元のエラーが消えたか
- 新しいブロッキングエラーが出ていないか

確認できたら次のエラーへ進む。

---

## 自動修正できるエラー

以下は自動修正可能（確認の上で適用する）:

```bash
# ruff の自動修正（安全なもの）
uv run ruff check --fix src tests

# フォーマット自動適用
uv run ruff format src tests
```

pyright のエラーは自動修正しない。必ず原因を理解してから直す。

---

## Stop Conditions

以下のときは即座に停止し、状況をユーザーに報告する:

- 修正が新しいエラーを増やした
- 同じエラーが 3 回試みても消えない
- Azure SDK の内部挙動が原因で根本的に不明
- ユーザーが「止めて」と言った

---

## Final Summary

最後に以下を報告する:

- 修正したエラー（ファイル名とエラー内容）
- 残っているエラー
- 新たに発生したエラー（あれば）
- 根本原因の推測

---

## Absolute Rules

- 複数のエラーを一度に修正しない
- 黙って推測しない
- 速さより正確さを優先する
