# プロジェクト現状サマリ

> Microsoft Agent Hackathon 2026 提出作品: AI 浸透加速エージェント
> 最終更新: 2026-05-26
> 締切まで: 残り 6 日 (5/31 23:59)

---

## 1. 提出物の進捗

| 提出物 | 状態 | 場所 |
|---|---|---|
| 成果物の公開 URL | ✅ 完了 | https://microsoft-agent-hackathon.nicebay-ff60cde9.eastus2.azurecontainerapps.io/ |
| GitHub リポジトリ | ✅ 完了 | https://github.com/motoshifurugen/microsoft-agent-hackathon |
| Zenn ブログ記事 | ❌ 未着手 | - |
| デモ動画 (任意) | ❌ 未収録 | - |

ハッカソン必須要件 (Azure 実行基盤 + Microsoft AI 技術) は満たし済み。

---

## 2. 実装の到達点

### 2.1 動いているもの

| カテゴリ | 内容 |
|---|---|
| Multi-Agent 構成 | Foundry に Orchestrator + 4 子 Agent (observer/collector/matcher/proposer) を `ConnectedAgentTool` で結合 |
| Function Tool | Orchestrator が 4 つの Python 関数 (fetch_signals / save_pain_point / semantic_search / fetch_success_cases) を自律呼び出し |
| RAG | text-embedding-3-small で 1536 次元 embedding、cosine similarity ベースの semantic search |
| データ | success_cases 10 件 (`docs/sample_data/success_cases.json`) を起動時 in-memory に seed |
| Microsoft Graph | `/users/{id}/messages` を Mail.Read (App permission) で取得、キーワード検知で困りごと抽出 |
| Container Apps | Chainlit UI を公開 URL でホスティング、Managed Identity で Foundry / Graph 認証 |
| 認証 | Container では Managed Identity、ローカルでは az login を自動切り替え |
| テスト | 53 件 PASS (ruff / pyright / pytest 全クリア) |
| CI | GitHub Actions で lint + type + test を毎 PR で実行 |

### 2.2 実機で確認できているシナリオ

入力例:
> 「月次レポート作成に毎月時間がかかっている田中さんに合う成功事例を tool_semantic_search で探してください」

Orchestrator の自律実行 (Run Steps):
1. `tool_fetch_signals(user_id="u-tanaka")` → 困りごとシグナル取得
2. `tool_semantic_search(text="月次レポート ...", top_k=3)` → 類似事例 3 件取得
3. ユーザーへの自然言語応答 + 戦略 A (直接紹介) / B (テンプレ送付) の選択肢提示

要件定義書 §2.1 メインシナリオ + §2.3 Cold Start 両方を再現済み。

---

## 3. 主要な意思決定とその理由

| 決定 | 理由 |
|---|---|
| Multi-Agent パターンは ConnectedAgentTool (1.x GA) を採用 | 締切まで時間が短く、preview API (azure-ai-projects 2.0.0b2 の A2APreviewTool) は避けた |
| Foundry のリソースは既存 `rg-mah-2026` 流用 | 新規 RG / Foundry account の作成コストとクォータ確保を回避 |
| RAG は Azure AI Search ではなく in-memory + Azure OpenAI embedding | Free tier の管理コストを節約。MVP として 10 件規模で実用十分 |
| Cosmos DB は使わず in-memory + JSON seed | データ永続化は本実装フェーズの責務。差し替え点は `src/tools/cosmos_io.py` に明確に分離 |
| UI は Chainlit on Container Apps、Copilot Studio は採用せず | 必須要件は「Azure 実行基盤 _または_ Copilot Studio」のためどちらかで OK。締切に間に合う方を選択 |
| Container では `exclude_cli_credential=True`、ローカルでは False | DefaultAzureCredential のチェーン挙動で CLI 不在エラーが伝播するのを防ぎつつ、ローカル開発体験を維持 |
| ACR Tasks 不可 → ローカル `docker buildx --push` | 無料試用版の制限への対応 |

---

## 4. 既知の制約・未実装

| 領域 | 現状 | Phase 2 で対応予定 |
|---|---|---|
| データ永続化 | in-memory (Container 再起動でリセット) | Azure Cosmos DB へ swap (関数シグネチャは固定済み) |
| マッチング | 業務文脈 embedding のみ | 5 グラフ統合 (公式組織図 / コラボ / 専門性 / 過去案件 / 負荷) |
| 伝播戦略 | A (直接紹介) / B (テンプレ送付) のみ | C (ミニ勉強会) / D (Just-in-time) |
| Power Automate | 未連携 | 会議自動セット連携 |
| Microsoft Graph 実データ | テナントに AAD ユーザー無しのため mock fallback | 本番テナントで稼働 (実装は完了済み) |
| 学習ループ (F-5) | 簡易ログのみ | 戦略選択の重み自動更新 |
| 認証 (ユーザー側) | 無し (公開 URL) | Entra ID SSO |
| レビューモード | 未実装 | 承認者向け要約と観点 |

---

## 5. テスト構成 (53 件)

| ファイル | 件数 | 範囲 |
|---|---|---|
| `tests/test_smoke.py` | 2 | パッケージ import + env vars チェック |
| `tests/test_agents_metadata.py` | 8 | 各 Agent モジュールの NAME / DESCRIPTION / INSTRUCTIONS が揃っていること |
| `tests/test_tools.py` | 12 | PainPoint / SuccessCase / fetch_signals / 既存 string-match semantic_search |
| `tests/test_seed_and_embedding.py` | 13 | seed loader / cosine similarity / embedding 検索 / フォールバック |
| `tests/test_graph_observe.py` | 18 | Graph キーワード検知 / signals_from_messages / token 失敗時 mock fallback |

Azure 実 API には接続せず、`monkeypatch` でモック化。CI は GitHub Actions で毎 PR 実行。

---

## 6. リポジトリの commit / PR 履歴

| PR | 内容 |
|---|---|
| #1 | requirements 初版 |
| #2 | Multi-Agent スケルトン (ConnectedAgentTool) |
| #3 | FunctionTool 統合 + 単体テスト |
| #4 | seed data 10 件 + embedding ベース semantic_search |
| #5 | Container Apps デプロイ (公開 URL 化) + Managed Identity |
| #6 | Microsoft Graph 統合 (Mail.Read application permission) |

すべて main にマージ済み (本ドキュメントの PR を除く)。

---

## 7. コスト実績

| リソース | 想定月額 | ハッカソン期間 (約 10 日) |
|---|---|---|
| Foundry account | ¥0 | ¥0 |
| gpt-4o 推論 | 従量 (¥2.50/1M tokens 入力) | < ¥500 |
| text-embedding-3-small | 従量 (¥0.02/1M tokens) | < ¥10 |
| Container App (1 vCPU / 2 GiB 常時) | ¥11,000/月 | < ¥3,500 |
| ACR Basic | ¥750/月 | < ¥250 |
| Storage / Egress | 微量 | < ¥100 |
| **合計** | - | **< ¥5,000** |

無料試用クレジット ¥30,000 内に余裕で収まる。締切後は §9 でクリーンアップ可能。

---

## 8. 次にやるべきこと (締切まで 6 日)

| 優先度 | タスク | 工数 |
|---|---|---|
| 必須 | Zenn 記事 draft (背景 → コンセプト → 実装 → デモ → 考察) | 2-3h |
| 必須 | 提出フォーム入力 + 公開 URL 動作確認 | 30m |
| 推奨 | デモ動画 (3-5 分) | 1-2h |
| 推奨 | success_cases.json を 20 件に増やす (デモ映え向上) | 1h |
| 任意 | 子 Agent への function tool 個別登録 (現状は Orchestrator 一括) | 3h |
| 任意 | Power Automate 連携 (会議自動セット) | 4h |
| 任意 | 5 グラフ統合の一部追加 (組織図 + コラボ) | 4h |

---

## 9. 提出時チェックリスト

提出フォームへの入力前に以下を確認:

- [ ] 公開 URL がブラウザで動作する
- [ ] チャットで「月次レポートで困っている田中さんの成功事例を探して」と送ってレスポンスが返る
- [ ] tool_fetch_signals → tool_semantic_search の自律実行が確認できる
- [ ] GitHub リポジトリが public でアクセス可能
- [ ] README.md にプロジェクト概要が書かれている
- [ ] Zenn 記事のドラフト URL を確保
- [ ] .env / secrets が GitHub に漏れていない (`git log -p .env` で確認)
- [ ] CI が green
