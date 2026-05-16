---
description: Think before coding. Clarify requirements, identify risks, and create a simple step-by-step plan. DO NOT write any code until the user explicitly approves.
---

# Plan Command

## Purpose

このプロジェクト (Microsoft Agent Hackathon 2026、締切 2026-06-01) で実装に入る前の思考・整理に使う。

目標:
- 要件を正確に把握する
- Azure AI Foundry / Chainlit に特有のリスクを早期に発見する
- 実装順序を小さく刻んで制御を手放さない

---

## What This Command Must Do

`/plan` が使われたとき、エージェントは以下を必ず行う:

1. 要件をシンプルな言葉で再確認する
2. 不明点があれば質問する
3. Azure 接続・認証・非同期処理に関するリスクを洗い出す
4. 段階的な実装計画（小さなステップ）を提示する
5. **承認が得られるまでコードを書かない**

---

## Output Format

以下のセクションのみで計画を表現する:

```
## 要件の再確認

## 質問 / 不明点

## 実装ステップ
1. ...
2. ...

## リスク
- Azure 接続: ...
- 非同期処理: ...
- デプロイ: ...

## 複雑度の見積もり
小 / 中 / 大
```

説明は簡潔に、初見でも読める言葉で書く。

---

## このプロジェクト固有のリスク観点

計画時に必ず以下を検討する:

**Azure AI Foundry**
- `PROJECT_ENDPOINT` / `AGENT_ID` がない状態でも起動時に明示的に失敗するか
- `AgentsClient` の呼び出しはローカルで `az login` 済みか
- `DefaultAzureCredential` が Container Apps の Managed Identity でも動くか

**Chainlit 非同期**
- `@cl.on_message` ハンドラが `async def` になっているか
- `cl.user_session` が正しく初期化されているか
- streaming が必要か (MVP では `create_and_process` で同期的に取得する方針)

**締切リスク (2026-06-01)**
- 追加する機能が MVP に必要か、それとも YAGNI か
- RAG / multi-agent は業務テーマが確定してから追加する（README 方針）

---

## When to Use

以下のときに `/plan` を使う:
- 新しい機能 (tool / RAG / multi-agent) を追加するとき
- 複数ファイルを変更するとき
- Chainlit の挙動や Azure SDK を初めて使うとき
- 「この実装で合ってるかな」と感じたとき

---

## Confirmation Rule (CRITICAL)

計画を提示したあと、必ずユーザーの確認を待つ。

受け入れられる返答:
- "yes" / "proceed" / "進めて"
- "modify: ..." / "変更: ..."

それ以外の返答では実装を始めない。

---

## Next Steps After Approval

承認後のフロー:
- `/tdd` でテスト → 実装
- `/code-review` でレビュー
- `uv run ruff format src tests` でフォーマット
- コミット
