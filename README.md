# microsoft-agent-hackathon

[Microsoft Agent Hackathon 2026](https://zenn.dev/hackathons/microsoft-agent-hackathon-2026) エントリー用リポジトリ。

> テーマ: **業務改革につながる Agentic AI を作ろう**
> 締切: **2026-06-01 (月) 23:59**
> 必須要件: Azure アプリ実行基盤 または Copilot Studio + Microsoft AI 技術

---

## 技術スタックと選定根拠

| 層 | 選定 | 根拠 |
|---|---|---|
| 言語 | **Python 3.12** | Agentic AI エコシステム最厚。Foundry / SK / Chainlit すべて Python ファースト |
| Agent | **Azure AI Foundry Agent Service** (`azure-ai-projects`) | 2025 GA。Microsoft 公式の最上位 Agent プラットフォーム。tool / thread / run / RAG が SDK 標準。ハッカソン要件「Azure 実行基盤 + Microsoft AI」と直結 |
| UI | **Chainlit** | 数十行で chat UI が立つ。streaming / file upload / human-in-the-loop が標準装備。締切まで 17 日で「成果物 URL」を出す最短経路 |
| デプロイ | **Azure Container Apps** | Dockerfile 1 枚で公開 URL。Foundry と同リージョン配置で低 latency。scale-to-zero でコスト最適 |
| パッケージ | **uv + pyproject.toml** | 2026 時点の事実上標準。`uv.lock` で再現性、CI も最速 |
| Lint / Type / Test | **ruff + pyright + pytest** | 3 つで CI が 1 分以内に終わる軽量構成 |
| 認証 | **DefaultAzureCredential** | ローカルは `az login`、Container Apps は Managed Identity でコード変更なし |

**初期で入れないもの (YAGNI):**
- RAG (`azure-ai-search`) — 業務テーマが固まったら追加
- multi-agent (`connected_agents`) — single-agent で MVP 検証後に拡張
- Bicep / Terraform — 初回は Azure Portal でリソース作成、固まったら IaC 化

---

## セットアップ

### 前提
- Python 3.12+ (推奨: `uv python install 3.12`)
- [uv](https://docs.astral.sh/uv/) ≥ 0.5
- Azure サブスクリプション + Azure AI Foundry プロジェクト
- `az login` でログイン済み

### 手順

```bash
# 1. 依存をインストール
uv sync

# 2. 環境変数を設定
cp .env.example .env
# .env を編集して PROJECT_ENDPOINT / AGENT_ID を設定

# 3. ローカルで起動
uv run chainlit run src/app.py
# → http://localhost:8000
```

### Azure AI Foundry 側の準備

1. [Azure AI Foundry](https://ai.azure.com/) でプロジェクトを作成
2. Models + endpoints で `gpt-4o-mini` (または `gpt-4o`) をデプロイ
3. Agents タブで Agent を作成し、`asst_xxx` の ID を `.env` の `AGENT_ID` に設定
4. プロジェクトの `endpoint` を `PROJECT_ENDPOINT` に設定

---

## デプロイ (Azure Container Apps)

```bash
# 1. ACR にイメージをビルド & push
az acr build --registry <ACR_NAME> --image microsoft-agent-hackathon:latest .

# 2. Container App を作成 (Managed Identity 付き)
az containerapp create \
  --name microsoft-agent-hackathon \
  --resource-group <RG> \
  --environment <ENV> \
  --image <ACR_NAME>.azurecr.io/microsoft-agent-hackathon:latest \
  --target-port 8000 --ingress external \
  --system-assigned \
  --env-vars PROJECT_ENDPOINT=<...> AGENT_ID=<...>

# 3. Managed Identity に Foundry のロールを付与
#    (Azure AI Developer ロールを Foundry project スコープで)
```

公開 URL がそのままハッカソン提出物になります。

---

## ディレクトリ構成

```
.
├── README.md                # この文書
├── pyproject.toml           # uv プロジェクト定義
├── uv.lock                  # ロックファイル (commit する)
├── .python-version          # 3.12
├── .env.example             # 環境変数テンプレ
├── .gitignore
├── Dockerfile               # Container Apps 用
├── src/
│   ├── __init__.py
│   └── app.py               # Chainlit + Foundry Agent エントリポイント
├── tests/
│   └── test_smoke.py        # 最低限の import / 健全性テスト
└── .github/
    └── workflows/
        └── ci.yml           # ruff + pyright + pytest
```

---

## 開発フロー

- `main` 直 push 可（小規模チーム前提）。複数人で衝突が増えたら feature branch + PR に切り替え
- commit message: 変更の **理由** を書く。何をしたかは diff で読める
- CI が落ちたら直してから次の push (CI green を保つ)

---

## 里程標 (締切 2026-06-01)

| 期日 | マイルストーン |
|------|----------------|
| 〜 5/18 | 業務テーマ確定 / Foundry リソース作成 / ローカルで Agent 1 往復 |
| 〜 5/22 | MVP デモ動作 (Chainlit から Agent 応答)。Container Apps にデプロイして公開 URL 確保 |
| 〜 5/27 | テーマ深掘り (tool / RAG / プロンプト改善)。Zenn 記事 draft |
| 〜 5/31 | UX 仕上げ・デモ動画録画・Zenn 記事公開 |
| **6/1 23:59** | **提出** |

---

## 参考

- [Microsoft Agent Hackathon 2026](https://zenn.dev/hackathons/microsoft-agent-hackathon-2026)
- [Azure AI Foundry Agent Service ドキュメント](https://learn.microsoft.com/azure/ai-services/agents/)
- [Chainlit ドキュメント](https://docs.chainlit.io/)
- [Azure Container Apps ドキュメント](https://learn.microsoft.com/azure/container-apps/)
