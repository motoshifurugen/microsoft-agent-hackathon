# Azure リソースセットアップ手順と現状

Microsoft Agent Hackathon 2026 用に作成した Azure リソース一式と、ゼロから再構築できる手順をまとめる。

> ⚠️ シークレット（Subscription ID、Agent ID、Project Endpoint の実値、Principal Object ID 等）は本書には書かない。実値は `.env` (gitignore 対象) と Azure Portal にのみ存在する。

---

## 1. 構築済みリソース一覧（2026-05-16 時点）

| 種別 | 名前 | リージョン | SKU / 設定 | 役割 |
|------|------|-----------|-----------|------|
| Resource Group | `rg-mah-2026` | eastus2 | — | 全リソースを束ねる。終了時に一括削除 |
| Cognitive Services Account (kind=AIServices) | `mah2026-<rand6>` | eastus2 | S0 / Custom domain / System Assigned Identity | Foundry のルート |
| Foundry Project | `mah-project` | (account 配下) | isDefault=true / System Assigned Identity | Agent / Thread が属する論理単位 |
| モデルデプロイ | `gpt-4o` | (account 配下) | Standard SKU / Capacity 50K TPM / `gpt-4o` `2024-11-20` | Agent の推論モデル |
| Agent | `business-agent` | (project 配下) | model=`gpt-4o` / 業務改革支援用システムプロンプト | Chainlit から呼ばれる Agent |
| ロール割当 | サインインユーザー | account scope | `Cognitive Services User` | Agent API データ操作権限 |

### メンバー（チーム）

| ユーザー | テナント上の表示 | ロール / スコープ | 操作範囲 |
|---|---|---|---|
| Owner（cmb-sy） | `free.nakashima@gmail.com` | Subscription `Owner`（実質） | 全権限。課金・サブスク削除も可 |
| Guest（motoshifurugen） | `amanogawa_m_icloud.com#EXT#@freenakashimagmail.onmicrosoft.com` | RG `rg-mah-2026` の `Owner` + Foundry account の `Cognitive Services User` | RG 内 全リソース操作（作成/更新/削除/ロール変更）+ Agent data plane |

`.env` には以下 2 値が入る（実値は git 管理外）:

```
PROJECT_ENDPOINT=https://<foundry-name>.services.ai.azure.com/api/projects/mah-project
AGENT_ID=asst_xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 2. 構築フロー（再現手順）

### 2.1 前提

```bash
brew install azure-cli            # macOS
az login                          # ブラウザ認証
az account show                   # サブスクリプションが Enabled であること
```

サブスクリプションを未取得の場合は Azure 無料試用版 (https://azure.microsoft.com/ja-jp/free) で取得する（クレジットカード本人確認のみで自動課金なし、¥30,000 / 30 日のクレジット）。

### 2.2 変数定義

```bash
RAND=$(openssl rand -hex 3)
RG="rg-mah-2026"
LOC="eastus2"
FOUNDRY="mah2026-${RAND}"
PROJECT_NAME="mah-project"
```

### 2.3 Provider 登録 + Resource Group

```bash
az provider register --namespace Microsoft.CognitiveServices --wait
az group create --name "$RG" --location "$LOC"
```

### 2.4 Foundry リソース（AIServices kind）

```bash
az cognitiveservices account create \
  --name "$FOUNDRY" \
  --resource-group "$RG" \
  --location "$LOC" \
  --kind AIServices \
  --sku S0 \
  --custom-domain "$FOUNDRY" \
  --assign-identity \
  --yes
```

ポイント:
- `--kind AIServices` が Foundry（複数 AI サービス統合）の正しい kind。`OpenAI` ではない
- `--custom-domain` を指定するとエンドポイントが `https://<name>.cognitiveservices.azure.com/` の形式になる（必須）
- `--assign-identity` で System Assigned Managed Identity を有効化し、Container Apps デプロイ時に活用

### 2.5 モデルデプロイ

```bash
az cognitiveservices account deployment create \
  --name "$FOUNDRY" \
  --resource-group "$RG" \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-11-20" \
  --model-format OpenAI \
  --sku-name "Standard" \
  --sku-capacity 50
```

ポイント:
- 無料試用版の初期クォータは限定的。後述「トラブル」参照
- `deployment-name` は `.env` の `MODEL_DEPLOYMENT_NAME` と一致させる（コード側で参照）

### 2.6 Foundry Project（REST API）

az CLI に `account project create` サブコマンドが無いため、REST API を直接叩く。

```bash
SUB_ID=$(az account show --query id -o tsv)
URI="https://management.azure.com/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY}/projects/${PROJECT_NAME}?api-version=2025-04-01-preview"

az rest --method PUT --uri "$URI" \
  --body '{"location":"eastus2","identity":{"type":"SystemAssigned"},"properties":{}}'
```

成功すると以下が返る:

```json
{
  "properties": {
    "endpoints": {
      "AI Foundry API": "https://<foundry>.services.ai.azure.com/api/projects/<project>"
    },
    "isDefault": true,
    "provisioningState": "Succeeded"
  }
}
```

この `AI Foundry API` のエンドポイント URL が `PROJECT_ENDPOINT` の実値。

### 2.7 ロール割当

`Cognitive Services User` を account スコープに付与する（Agent の data plane 操作に必要）。

```bash
USER_OBJ_ID=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/me?\$select=id" --query id -o tsv)
ACCOUNT_SCOPE="/subscriptions/${SUB_ID}/resourceGroups/${RG}/providers/Microsoft.CognitiveServices/accounts/${FOUNDRY}"

az role assignment create \
  --assignee-object-id "$USER_OBJ_ID" \
  --assignee-principal-type User \
  --role "Cognitive Services User" \
  --scope "$ACCOUNT_SCOPE"
```

ポイント:
- 個人 Microsoft アカウント（無料試用）では `az ad signed-in-user show` が使えないため Graph API 経由で objectId 取得
- ロール名候補:
  - `Cognitive Services User` ✅ 使用中（data plane 操作）
  - `Cognitive Services Contributor` (control plane も含む。デプロイ作成等まで）
  - `Azure AI User` ❌ 存在しない（一部ドキュメントに記載されているが現状未定義）
  - `Azure AI Developer` 開発者向け、Agent 作成可

### 2.8 メンバー招待（B2B Guest）

外部メンバーを招待してチーム開発する場合の手順。`az ad invitation create` は CLI 2.86 で未対応のため Graph API を直接叩く。

```bash
EMAIL="guest@example.com"
DISPLAY="Guest Name"

INVITATION=$(az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/invitations" \
  --body "$(python3 -c "import json;print(json.dumps({
    'invitedUserEmailAddress':'$EMAIL',
    'invitedUserDisplayName':'$DISPLAY',
    'inviteRedirectUrl':'https://portal.azure.com/',
    'sendInvitationMessage':True}))")")

GUEST_OBJ_ID=$(echo "$INVITATION" | python3 -c "import json,sys;print(json.loads(sys.stdin.read())['invitedUser']['id'])")
```

ロール付与（RG 全権限 + Foundry data plane）:

```bash
SUB_ID=$(az account show --query id -o tsv)
RG_SCOPE="/subscriptions/${SUB_ID}/resourceGroups/rg-mah-2026"
ACCOUNT_SCOPE="${RG_SCOPE}/providers/Microsoft.CognitiveServices/accounts/<FOUNDRY>"

az role assignment create --assignee-object-id "$GUEST_OBJ_ID" --assignee-principal-type User \
  --role "Owner" --scope "$RG_SCOPE"

az role assignment create --assignee-object-id "$GUEST_OBJ_ID" --assignee-principal-type User \
  --role "Cognitive Services User" --scope "$ACCOUNT_SCOPE"
```

ゲスト側のセットアップ:
1. 招待メール (`Microsoft Invitations` from `invites@microsoft.com`) のリンクをクリック
2. Microsoft アカウントでサインインして承諾
3. https://portal.azure.com/ に移動し、ディレクトリ選択で `freenakashimagmail.onmicrosoft.com` に切替
4. `rg-mah-2026` が見えれば成功
5. ローカル開発する場合: `brew install azure-cli && az login --tenant freenakashimagmail.onmicrosoft.com`

### 2.8 Agent 作成（Python SDK 経由）

`scripts/create_agent.py` に同等スクリプトを置く想定（現状は使い捨てで `/tmp/create_agent.py` に作って実行した）:

```python
from azure.ai.agents import AgentsClient
from azure.identity import AzureCliCredential

ENDPOINT = "<PROJECT_ENDPOINT>"  # 環境変数から
MODEL_DEPLOYMENT = "gpt-4o"

client = AgentsClient(endpoint=ENDPOINT, credential=AzureCliCredential())

agent = client.create_agent(
    model=MODEL_DEPLOYMENT,
    name="business-agent",
    instructions="あなたは業務改革を支援する Agentic AI アシスタントです。...",
)
print(f"AGENT_ID={agent.id}")
```

実行:

```bash
cd ~/develop/microsoft-agent-hackathon
PROJECT_ENDPOINT="<実値>" uv run python scripts/create_agent.py
```

出力された `AGENT_ID` を `.env` に書き込む。

### 2.9 ローカル起動

```bash
uv sync
uv run chainlit run src/app.py
# → http://localhost:8000
```

---

## 3. 直面したトラブルと回避策

### 3.1 リージョン × モデルのクォータ不一致

**症状**: `japaneast` で `gpt-4o-mini GlobalStandard` をデプロイしようとして `InsufficientQuota`。

**原因**: 無料試用版の初期クォータは region/model/SKU の組合せごとに 0 のものが多い。

**確認コマンド**:

```bash
az cognitiveservices usage list --location <region> --output table | grep -i '<model>'
```

**今回の調査結果**:

| Region | 利用可能 quota (Standard SKU) |
|--------|------------------------------|
| japaneast | gpt 系の Standard SKU クォータがほぼ無い（finetune 用のみ） |
| eastus2 | `gpt-4o-mini 200K`, `gpt-4o 50K`, `gpt-35-turbo 200K` |
| swedencentral | `gpt-4o-mini 200K`, `gpt-4o 50K` |

**対処**: japaneast を諦め eastus2 で再構築（RG・Foundry を作り直し）。

### 3.2 モデルの先行 deprecation

**症状**: `gpt-4o-mini 2024-07-18` のデプロイで `ServiceModelDeprecated: deprecated since 03/31/2026`。

**原因**: Microsoft の deprecation スケジュールが進行しており、テナント側 inference が先行終了済み。

**確認コマンド**:

```bash
az cognitiveservices model list --location eastus2 -o json | \
  python3 -c "import json,sys;[print(m['model']['name'], m['model']['version'], m['model'].get('deprecation',{}).get('inference')) for m in json.load(sys.stdin)]" | sort -u
```

**選択基準**:
- deprecation 日が遠い（半年以上先）
- quota が割り当てられている
- Agent Service 対応

**今回の選定**: `gpt-4o` `2024-11-20`（deprecation 2026-10-01、Standard 50K quota あり）。

### 3.3 個人アカウントでの `az ad` 不可

**症状**: `az ad signed-in-user show` が個人 MS アカウント（無料試用）では使えない。

**対処**: Microsoft Graph 直接呼び出し:

```bash
USER_OBJ_ID=$(az rest --method GET --uri "https://graph.microsoft.com/v1.0/me?\$select=id" --query id -o tsv)
```

---

## 4. 削除（クリーンアップ）

ハッカソン終了後、または途中で作り直したい場合:

```bash
# 全リソース一括削除（非同期で進む）
az group delete --name rg-mah-2026 --yes --no-wait

# 完了待ちが必要な場合
az group wait --name rg-mah-2026 --deleted --timeout 600

# Cognitive Services アカウントは soft delete されるため、完全削除には purge が必要
# （同名でリソース再作成したい場合のみ）
az cognitiveservices account purge \
  --name <foundry-name> \
  --resource-group rg-mah-2026 \
  --location eastus2
```

---

## 5. コスト感

| 項目 | 課金 | 備考 |
|------|------|------|
| Resource Group | ¥0 | コンテナのみ |
| Cognitive Services Account | ¥0 | アカウントそれ自体は無料 |
| Project | ¥0 | account 配下の論理リソース |
| モデル推論 | 従量 | gpt-4o は入力 ≒ $2.50 / 1M tokens、出力 ≒ $10 / 1M tokens（2026 時点） |
| Agent / Thread | ¥0 | メタデータのみ |
| Managed Identity | ¥0 | |

**開発期間中の現実的な総額**: ¥500 未満（往復 100 回程度、コンテキスト数千トークン）。

無料試用クレジット ¥30,000 / 30 日の範囲で十分に収まる。

---

## 6. 次の手順（環境構築完了後）

1. **ローカル動作確認**: ブラウザで http://localhost:8000 を開き、業務課題を投げて応答を確認
2. **業務テーマ確定**: README の里程標に従い、5/18 までに何の業務領域に絞るか決める
3. **Agent 改善**:
   - `instructions` (システムプロンプト) の調整
   - tool / function calling の追加（必要に応じて）
   - 必要なら `azure-ai-search` で RAG 追加
4. **Container Apps デプロイ**: README §デプロイ手順を実行 → 公開 URL を取得（提出物の必須項目）
5. **Zenn 記事 draft**: テーマ決定後並走で書き始める
6. **提出（2026-06-01 23:59 まで）**: 成果物 URL + Zenn 記事 + GitHub URL

---

## 7. 参考リンク

- [Microsoft Agent Hackathon 2026](https://zenn.dev/hackathons/microsoft-agent-hackathon-2026)
- [Azure AI Foundry Agent Service](https://learn.microsoft.com/azure/ai-services/agents/)
- [`azure-ai-agents` Python SDK](https://learn.microsoft.com/python/api/overview/azure/ai-agents-readme)
- [Chainlit ドキュメント](https://docs.chainlit.io/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)
- [Foundry プロジェクト REST API](https://learn.microsoft.com/rest/api/aiservices/accountmanagement/projects/create-or-update)
