# アーキテクチャ

> Microsoft Agent Hackathon 2026 提出作品: AI 浸透加速エージェント
> 最終更新: 2026-05-26

このドキュメントは現在 main にマージされている実装をベースに記述している。
要件定義は [requirements.md](./requirements.md) を、構築手順は [azure-setup.md](./azure-setup.md) と [operations.md](./operations.md) を参照。

---

## 1. 全体構成

```mermaid
graph TB
    User[エンドユーザー]
    Browser[ブラウザ]
    User -->|HTTPS| Browser

    subgraph CA["Azure Container Apps"]
        Chainlit["Chainlit UI<br/>(src/app.py)"]
        FunctionTool["Function Tool<br/>(src/tools/registry.py)"]
        Chainlit --> FunctionTool
    end
    Browser -->|HTTPS| Chainlit

    subgraph Foundry["Azure AI Foundry (mah-project)"]
        Orch["Orchestrator Agent"]
        Observer["観測 Agent"]
        Collector["収集 Agent"]
        Matcher["マッチング Agent"]
        Proposer["提案 Agent"]
        Orch -.ConnectedAgentTool.-> Observer
        Orch -.ConnectedAgentTool.-> Collector
        Orch -.ConnectedAgentTool.-> Matcher
        Orch -.ConnectedAgentTool.-> Proposer
    end
    Chainlit -->|"thread/run + ToolSet"| Orch

    subgraph LLM["LLM 層 (mah2026-bcc1cb)"]
        GPT4o["gpt-4o (推論)"]
        EmbModel["text-embedding-3-small (1536 dim)"]
    end
    Orch --> GPT4o
    FunctionTool --> EmbModel

    subgraph Graph["Microsoft Graph"]
        Mail["/users/{id}/messages"]
    end
    FunctionTool -->|"Mail.Read (App)"| Mail

    subgraph Local["コンテナ内 (in-memory)"]
        PainPoints[("pain_points<br/>(dict)")]
        SuccessCases[("success_cases<br/>(dict + embedding cache)")]
        Seed["docs/sample_data/<br/>success_cases.json (10 件)"]
        Seed -->|"起動時 load_success_cases"| SuccessCases
    end
    FunctionTool --> PainPoints
    FunctionTool --> SuccessCases

    classDef azure fill:#e6f3ff,stroke:#0078d4
    classDef data fill:#fff2cc,stroke:#d6b656
    class CA,Foundry,LLM azure
    class PainPoints,SuccessCases,Seed data
```

### レイヤー別責務

| 層 | 構成要素 | 責務 |
|---|---|---|
| UI | Chainlit on Container Apps | ブラウザからのチャット入出力 / WebSocket セッション |
| エージェント | Foundry の Orchestrator + 4 子 Agent | 意図解釈と専門タスクへの委譲 (Connected Agents) |
| Function Tool | `src/tools/registry.py` | Foundry から Python 関数として呼ばれる data layer 入口 |
| LLM | gpt-4o / text-embedding-3-small | 推論と embedding 生成 |
| データ | in-memory + JSON seed | success_cases (10 件) と pain_points を保持 |
| 観測 | Microsoft Graph Mail.Read | Outlook メールから困りごとシグナル検知 |

### Azure リソース構成

| 種別 | 名前 | リージョン | 役割 |
|---|---|---|---|
| Resource Group | `rg-mah-2026` | eastus2 | 全リソースの束ね |
| Foundry (Cognitive Services) | `mah2026-bcc1cb` | eastus2 | Agent と LLM の拠点 |
| Foundry Project | `mah-project` | (account 配下) | Agent の論理単位 |
| Model deployment | `gpt-4o` (Standard 50K TPM) | (account 配下) | Orchestrator の推論 |
| Model deployment | `text-embedding-3-small` (Standard 50) | (account 配下) | RAG の embedding |
| ACR | `mahacr551974` | eastus2 | コンテナイメージのレジストリ (Basic) |
| Container Apps Environment | `mah-cae` | eastus2 | Container App 実行環境 |
| Container App | `microsoft-agent-hackathon` | eastus2 | Chainlit UI + Function Tool |

公開 URL: `https://microsoft-agent-hackathon.nicebay-ff60cde9.eastus2.azurecontainerapps.io/`

---

## 2. Multi-Agent 構成

```mermaid
graph LR
    User((ユーザー))
    User --> Orch[Orchestrator]
    Orch -.ConnectedAgentTool.-> Observer
    Orch -.ConnectedAgentTool.-> Collector
    Orch -.ConnectedAgentTool.-> Matcher
    Orch -.ConnectedAgentTool.-> Proposer
    Orch -->|FunctionTool| Tools[(Python tools)]
    Tools --> Graph[(Microsoft Graph)]
    Tools --> Embed[(Azure OpenAI Embedding)]
    Tools --> Mem[(in-memory store)]
```

| Agent | NAME | 主な責務 (instructions の核) |
|---|---|---|
| Orchestrator | `orchestrator` | ユーザー対話の窓口。意図解釈し子 Agent を呼び分け、Function Tool で data layer を直接操作 |
| 観測 | `observer` | Microsoft Graph 経由で困りごとシグナルを検知して構造化候補を返す |
| 収集 | `collector` | 候補シグナルを構造化し、本人承認文を生成 |
| マッチング | `matcher` | 困りごとから類似成功事例を embedding 検索し、戦略 A/B を提示 |
| 提案 | `proposer` | 個別最適化されたプロンプト/テンプレを生成 |

### Function Tool (Orchestrator が自律呼び出し)

| Tool | 機能 | データ層への接続 |
|---|---|---|
| `tool_fetch_signals(user_id, since_iso?)` | 困りごとシグナル取得 | Microsoft Graph `/users/{id}/messages` |
| `tool_save_pain_point(user_id, business_context, ...)` | 困りごとを永続化 | in-memory `pain_points` |
| `tool_semantic_search(text, top_k=3)` | 類似成功事例検索 | text-embedding-3-small で cosine similarity |
| `tool_fetch_success_cases(case_ids)` | 成功事例詳細取得 | in-memory `success_cases` |

---

## 3. メインシナリオのシーケンス

Orchestrator が判断する入力パターンは 2 種類ある。どちらも最終的に
「最大 3 件の事例 + 戦略 A/B」というフォーマットに収束する。

### 3.1 パターン A: 能動的な検索依頼

「○○さんに合う事例を探して」のような、検索意図が明確な発話。
Orchestrator は本人 user_id を抽出して **`exclude_user_id`** に渡し、
本人の事例が自己推薦されることを防ぐ。

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー (ブラウザ)
    participant Chainlit as Chainlit (Container Apps)
    participant Orch as Orchestrator Agent
    participant LLM as Azure OpenAI gpt-4o
    participant Tool as Function Tool (Python)
    participant Embed as text-embedding-3-small
    participant Mem as in-memory store

    Note over Chainlit: 起動時に load_success_cases(with_embeddings=True)<br/>10 件の SuccessCase + 1536 次元 embedding を投入
    User->>Chainlit: 「経費精算で困っている高橋さんに合う事例を 3 件」
    Chainlit->>Orch: thread/run.create_and_process(toolset)
    Orch->>LLM: 意図解釈 (パターン A と判定)
    LLM-->>Orch: tool_semantic_search 呼び出し計画 (本人 user_id を exclude)
    Orch->>Tool: tool_semantic_search(text=..., top_k=3, exclude_user_id="u-takahashi-008")
    Tool->>Embed: クエリを埋め込みベクトルに変換
    Embed-->>Tool: query_vec[1536]
    loop 各 success_case
        Tool->>Mem: case の embedding を取得
        Mem-->>Tool: case_vec[1536]
        Tool->>Tool: _should_exclude(case, "u-takahashi-008") をチェック
        alt 本人の事例
            Tool->>Tool: スキップ
        else 他者の事例
            Tool->>Tool: _final_score = cosine × 0.7 + reproducibility × 0.3 + business_type_bonus
        end
    end
    Tool-->>Orch: SearchHit[] (score 降順, 最大 3 件)
    Orch->>LLM: 上位 3 件で回答生成 + 戦略 A/B 提示
    LLM-->>Orch: 自然言語回答 (owner_label / concrete_prompt / quantitative_effect を含む)
    Orch-->>Chainlit: run.status=COMPLETED
    Chainlit-->>User: 「営業部 佐藤さんの事例...」+ 戦略 A/B を表示
```

### 3.2 パターン B: Teams 投稿トリガー (自律判断)

ユーザーが観測情報を引用する発話 (「○○さんが Teams にこう投稿した」)。
Orchestrator は **支援要否を自分で判断** し、必要なら能動的に検索 → 提案まで進める。

```mermaid
sequenceDiagram
    autonumber
    actor User as ユーザー (ブラウザ)
    participant Chainlit as Chainlit (Container Apps)
    participant Orch as Orchestrator Agent
    participant LLM as Azure OpenAI gpt-4o
    participant Tool as Function Tool (Python)
    participant Graph as Microsoft Graph
    participant Embed as text-embedding-3-small
    participant Mem as in-memory store

    User->>Chainlit: 「田中さんが『月次レポート、また 8 時間か…』と Teams 投稿。支援が必要か判断して」
    Chainlit->>Orch: thread/run.create_and_process(toolset)
    Orch->>LLM: 意図解釈 (パターン B と判定)
    LLM-->>Orch: まず tool_fetch_signals で観測補完
    Orch->>Tool: tool_fetch_signals(user_id=tanaka)
    Tool->>Graph: GET /users/{id}/messages (Mail.Read app perm)
    alt 困りごとメールあり
        Graph-->>Tool: messages[]
        Tool->>Tool: キーワードマッチで pain を抽出
    else 該当なし / 権限エラー
        Tool->>Tool: _mock_signal() でデモ用シグナル生成
    end
    Tool-->>Orch: Signal[]
    Orch->>LLM: 引用 + Signal を統合して「支援要否」を判断
    alt 支援必要と判断
        LLM-->>Orch: tool_semantic_search 呼び出し (exclude_user_id=tanaka)
        Orch->>Tool: tool_semantic_search(text=..., top_k=3, exclude_user_id=tanaka)
        Tool->>Embed: クエリ embedding
        Tool->>Mem: cosine similarity + 重み付けで Top 3
        Tool-->>Orch: SearchHit[]
        Orch->>LLM: 3 件 + 戦略 A/B で回答生成
        LLM-->>Orch: 自然言語回答
    else 不要と判断
        LLM-->>Orch: 「現時点では介入不要」の短い説明
    end
    Orch-->>Chainlit: run.status=COMPLETED
    Chainlit-->>User: 提案 or 介入不要メッセージ
```

### 3.3 スコアリング詳細

`tool_semantic_search` の最終スコア:

```
final_score = (cosine_similarity * SEMANTIC_WEIGHT)        # 0.7
            + (reproducibility_score * REPRODUCIBILITY_WEIGHT)  # 0.3
            + (BUSINESS_TYPE_BONUS if business_type in query else 0)  # +0.2
```

定数はすべて `src/tools/search_query.py` の冒頭にまとめてあり、
チューニングは数値変更だけで完結する。

### 3.4 自律ループの停止条件

- 全テンプレ項目が埋まった
- ユーザーにしか聞けない情報が残り、確認質問を発した
- 同じ Tool を 3 回以上呼んでも進展しない (LLM 側の判断)

---

## 4. 認証フロー

```mermaid
sequenceDiagram
    participant CA as Container App
    participant MI as Managed Identity (System Assigned)
    participant AAD as Microsoft Entra ID
    participant Foundry as Azure AI Foundry
    participant Graph as Microsoft Graph

    Note over CA: get_default_credential() を呼ぶ<br/>(Container 検知で CLI を除外)
    CA->>MI: トークン要求 (https://cognitiveservices.azure.com/.default)
    MI->>AAD: アクセストークン取得
    AAD-->>MI: Bearer token
    MI-->>CA: token
    CA->>Foundry: Authorization: Bearer ...

    Note over CA: 別途 Graph 用トークン
    CA->>MI: トークン要求 (https://graph.microsoft.com/.default)
    MI->>AAD: アクセストークン取得
    AAD-->>MI: Bearer token
    MI-->>CA: graph_token
    CA->>Graph: Authorization: Bearer ...
```

### 付与済み権限 (Managed Identity `cb5e0d0f-...`)

| スコープ | 権限 | 種別 |
|---|---|---|
| Foundry account `mah2026-bcc1cb` | `Cognitive Services User` | Azure RBAC |
| Microsoft Graph | `Mail.Read` | Application permission |
| Microsoft Graph | `User.Read.All` | Application permission |

ローカル開発時は `DefaultAzureCredential` が `az login` の認証情報を使い同じ機能を提供する (`exclude_cli_credential=False`)。

---

## 5. データフロー

```mermaid
flowchart LR
    Start[Container App 起動] --> Load[load_success_cases]
    Load --> JSON[/docs/sample_data/<br/>success_cases.json/]
    JSON --> Mem1[(in-memory _success_cases)]
    Load -->|with_embeddings=True| Embed[text-embedding-3-small]
    Embed --> Mem2[(in-memory _embeddings)]

    UserMsg[ユーザー発話] --> Orch2[Orchestrator]
    Orch2 -->|tool_fetch_signals| Graph2[Microsoft Graph]
    Graph2 --> Signal[Signal]
    Signal --> Orch2

    Orch2 -->|tool_semantic_search| Embed2[query embedding]
    Embed2 --> Sim[cosine similarity]
    Sim --> Mem2
    Mem2 --> Hit[SearchHit Top-K]
    Hit --> Orch2

    Orch2 --> Reply[自然言語回答 + 戦略 A/B]
    Reply --> UserMsg
```

### 検索ロジックの優先順位

1. **embedding が 1 件以上登録されていれば**: クエリ embedding と cos similarity でランキング
2. **embedding 未登録 or 取得失敗時**: business_type の文字列マッチへフォールバック
3. **クエリが空文字列**: 即 `[]` を返す

---

## 6. ディレクトリ構成

```
.
├── src/
│   ├── app.py                  Chainlit エントリ + ToolSet 設定
│   ├── config.py               環境変数集約
│   ├── agents/                 5 Agent の NAME/DESCRIPTION/INSTRUCTIONS
│   │   ├── orchestrator.py
│   │   ├── observer.py
│   │   ├── collector.py
│   │   ├── matcher.py
│   │   └── proposer.py
│   └── tools/                  Function Tool 実装 + data layer
│       ├── registry.py         Foundry 用 wrapper (asdict 変換)
│       ├── credential.py       Container / Local 両対応の DefaultAzureCredential
│       ├── cosmos_io.py        pain_points / success_cases (in-memory)
│       ├── embed.py            Azure OpenAI embedding ヘルパー
│       ├── graph_observe.py    Microsoft Graph 経由のメール観測
│       ├── search_query.py     embedding ベース semantic_search
│       └── seed.py             起動時 JSON → in-memory loader
├── scripts/
│   ├── create_agent.py         (legacy) 単一 Agent 作成
│   └── create_agents.py        5 Agent + ConnectedAgentTool 結合
├── tests/                      53 件 (ruff + pyright + pytest)
├── docs/
│   ├── architecture.md         本ドキュメント
│   ├── operations.md           デプロイ・運用手順
│   ├── requirements.md         要件定義書
│   ├── status.md               現状サマリ
│   ├── azure-setup.md          Azure リソース構築手順 (詳細)
│   └── sample_data/
│       └── success_cases.json  ダミー成功事例 10 件 (PII なし)
├── Dockerfile                  Container Apps 用 (multi-stage build)
├── pyproject.toml
└── README.md
```

---

## 7. 既知の制約と前提

| 項目 | 内容 |
|---|---|
| データ永続化 | in-memory dict のみ。Container 再起動でリセット (起動時に JSON から再 seed) |
| マルチユーザー | 単一 Container App で sticky session なし。pain_points は user 間で共有 |
| Microsoft Graph データ | テナント (free.nakashima@gmail.com) に AAD ユーザーが居ないため `_mock_signal()` にフォールバックして動作 |
| Cosmos DB / AI Search | MVP では未使用。`src/tools/cosmos_io.py` / `search_query.py` の差し替え点は明確に分離済み |
| Phase 2 想定 | Cosmos DB へのスワップ、5 グラフ統合 (組織図/コラボ/専門性/負荷/過去案件)、Power Automate での会議自動化、レビューモード |
