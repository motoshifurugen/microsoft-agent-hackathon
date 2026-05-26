# 運用手順 (operations)

> Microsoft Agent Hackathon 2026 提出作品: AI 浸透加速エージェント
> 最終更新: 2026-05-26

このドキュメントは **既存リソース (`rg-mah-2026`) を前提とした日常運用手順** をまとめる。
ゼロからの初期構築は [azure-setup.md](./azure-setup.md) を参照。
アーキテクチャの全体像は [architecture.md](./architecture.md) を参照。

---

## 1. クイックリファレンス

| 操作 | コマンド |
|---|---|
| ローカル起動 | `uv run chainlit run src/app.py` |
| テスト | `uv run pytest` |
| Lint / Format / Type | `uv run ruff check . && uv run ruff format --check . && uv run pyright src tests scripts` |
| Foundry に Agent 再作成 | `uv run python scripts/create_agents.py` |
| Container 再ビルド & 再デプロイ | §5 参照 |
| ログ確認 | `az containerapp logs show --name microsoft-agent-hackathon -g rg-mah-2026 --type console --tail 30` |

公開 URL: `https://microsoft-agent-hackathon.nicebay-ff60cde9.eastus2.azurecontainerapps.io/`

---

## 2. ローカル開発

### 2.1 前提

- Python 3.12+ (`uv python install 3.12`)
- [uv](https://docs.astral.sh/uv/) ≥ 0.5
- Docker Desktop (デプロイ時のみ)
- Azure CLI (`brew install azure-cli`)
- `az login` 済み (free.nakashima@gmail.com アカウント)

### 2.2 セットアップ

```bash
git clone https://github.com/motoshifurugen/microsoft-agent-hackathon.git
cd microsoft-agent-hackathon
uv sync
cp .env.example .env
# .env を編集 (実値はチーム DM で受け取る)
```

`.env` に必須の値:

```
PROJECT_ENDPOINT=https://mah2026-bcc1cb.services.ai.azure.com/api/projects/mah-project
MODEL_DEPLOYMENT=gpt-4o
EMBEDDING_DEPLOYMENT=text-embedding-3-small
AGENT_ID=asst_IOpovt838dR6HO1xC9RN5Atj
AGENT_ID_OBSERVER=asst_j2xqkcqT3wPixDbOwybVrnjB
AGENT_ID_COLLECTOR=asst_m5PhfYfOu6x0BdyBMXcgXhpT
AGENT_ID_MATCHER=asst_JU2bqqviBdU0vTq0PjlWrzqr
AGENT_ID_PROPOSER=asst_CWgn1cKNbaBB2T8TWIjZY05m
```

### 2.3 起動

```bash
uv run chainlit run src/app.py
# → http://localhost:8000
```

### 2.4 テスト

```bash
uv run pytest -v
# 53 件 PASS を期待
```

ダミー env vars でも import 系のテストは通る:

```bash
PROJECT_ENDPOINT="https://dummy.services.ai.azure.com/api/projects/dummy" \
AGENT_ID="asst_dummy" uv run pytest
```

---

## 3. Foundry の Agent 管理

### 3.1 5 Agent を一括作成 (冪等)

`scripts/create_agents.py` は同名 Agent を削除してから再作成するため何度でも安全に実行できる。

```bash
uv run python scripts/create_agents.py
```

標準出力に新しい AGENT_ID 系が出るので `.env` と (使っていれば) Container App の env vars に転記する。

### 3.2 既存 Agent の確認

```bash
az rest --method GET \
  --uri "https://mah2026-bcc1cb.services.ai.azure.com/api/projects/mah-project/assistants?api-version=2024-12-01-preview" \
  --resource "https://cognitiveservices.azure.com" \
  --query "data[].{id:id, name:name}" -o table
```

### 3.3 Agent を個別削除

```bash
# 例: 不要になった business-agent を削除
AGENT_ID="asst_xxxxx"
az rest --method DELETE \
  --uri "https://mah2026-bcc1cb.services.ai.azure.com/api/projects/mah-project/assistants/$AGENT_ID?api-version=2024-12-01-preview" \
  --resource "https://cognitiveservices.azure.com"
```

---

## 4. ダミーデータの管理

`docs/sample_data/success_cases.json` を編集すると、次回 Container 起動時に新しい seed が反映される。

スキーマ:

```json
[
  {
    "user_id": "u-xxx-001",
    "business_type": "月次レポート作成",
    "what_worked": "...",
    "why_worked": "...",
    "reproducibility_score": 0.0-1.0
  }
]
```

注意:
- PII (実在の個人名・メール・電話) は含めない
- `reproducibility_score` は 0.0-1.0
- 起動時に `load_success_cases(with_embeddings=True)` が embedding を計算 (text-embedding-3-small の API call 発生)

---

## 5. Container Apps への再デプロイ

### 5.1 通常フロー (コード変更時)

```bash
# 1. ローカルで Docker イメージをビルドして ACR に push
ACR_NAME=mahacr551974
az acr login --name "$ACR_NAME"
docker buildx build --platform linux/amd64 \
  -t "$ACR_NAME.azurecr.io/microsoft-agent-hackathon:latest" \
  --push .

# 2. Container App の revision を再起動 (同 tag の image を再 pull)
az containerapp revision restart \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --revision microsoft-agent-hackathon--0000001

# 3. ヘルスチェック
URL="https://microsoft-agent-hackathon.nicebay-ff60cde9.eastus2.azurecontainerapps.io/"
curl -s -o /dev/null -w "%{http_code}\n" "$URL"
# 200 が出れば OK (起動完了まで 30-60 秒)
```

### 5.2 環境変数を変更したい時

```bash
az containerapp update \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --set-env-vars KEY=VALUE
```

複数同時:

```bash
az containerapp update \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --set-env-vars AGENT_ID=asst_xxx AGENT_ID_OBSERVER=asst_yyy
```

### 5.3 新しい revision を強制作成

```bash
az containerapp update \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --image "$ACR_NAME.azurecr.io/microsoft-agent-hackathon:latest" \
  --revision-suffix "v$(date +%s)"
```

---

## 6. ログとモニタリング

### 6.1 コンソールログ (Chainlit / Python の stdout/stderr)

```bash
az containerapp logs show \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --type console \
  --tail 50
```

### 6.2 リビジョン状態

```bash
az containerapp revision list \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --query "[].{name:name, active:properties.active, state:properties.runningState, healthState:properties.healthState, replicas:properties.replicas}" \
  -o table
```

`ActivationFailed` / `Unhealthy` の場合は §6.1 でログを見る。

### 6.3 Agent 利用状況

Foundry プロジェクトの thread / run / message は Azure Portal の AI Foundry Studio で閲覧可能。CLI からは:

```bash
az rest --method GET \
  --uri "https://mah2026-bcc1cb.services.ai.azure.com/api/projects/mah-project/threads?api-version=2024-12-01-preview" \
  --resource "https://cognitiveservices.azure.com" \
  --query "data[].{id:id, created:created_at}" -o table
```

---

## 7. Microsoft Graph 権限の追加付与

新しい権限が必要になったとき (例: `Calendars.Read` を追加したい)。

```bash
GRAPH_APP_ID="00000003-0000-0000-c000-000000000000"
NEW_ROLE_VALUE="Calendars.Read"  # 付与したい権限

ROLE_ID=$(az ad sp show --id "$GRAPH_APP_ID" \
  --query "appRoles[?value=='$NEW_ROLE_VALUE' && contains(allowedMemberTypes, 'Application')].id | [0]" -o tsv)

MI_ID=$(az containerapp show \
  --name microsoft-agent-hackathon \
  --resource-group rg-mah-2026 \
  --query identity.principalId -o tsv)

GRAPH_SP_ID=$(az ad sp show --id "$GRAPH_APP_ID" --query id -o tsv)

az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$MI_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{\"principalId\":\"$MI_ID\",\"resourceId\":\"$GRAPH_SP_ID\",\"appRoleId\":\"$ROLE_ID\"}"
```

確認:

```bash
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$MI_ID/appRoleAssignments" \
  --query "value[].{role:appRoleId, resource:resourceDisplayName}" -o table
```

---

## 8. トラブルシュート

### 8.1 公開 URL に繋がらない (HTTP 000 や 502)

1. `az containerapp revision list` で `Unhealthy` でないか確認
2. `az containerapp logs show` でスタックトレースを見る
3. よくある原因:
   - `ModuleNotFoundError: No module named 'src'` → `PYTHONPATH=/app` が env vars に入っているか確認
   - `CredentialUnavailableError: Azure CLI not found` → `src/tools/credential.py` の `CONTAINER_APP_NAME` 検知が効いているか
   - `FileNotFoundError: docs/sample_data/...` → Dockerfile の `COPY docs/sample_data` 行を確認

### 8.2 Orchestrator のレスポンスが返ってこない

1. `.env` の `AGENT_ID` が **Orchestrator の id** (子 Agent ではない) を指しているか確認
2. Foundry にロール `Cognitive Services User` が付いているか確認:
   ```bash
   SUB_ID=$(az account show --query id -o tsv)
   SCOPE="/subscriptions/$SUB_ID/resourceGroups/rg-mah-2026/providers/Microsoft.CognitiveServices/accounts/mah2026-bcc1cb"
   az role assignment list --scope "$SCOPE" -o table
   ```
3. `scripts/create_agents.py` を再実行して Agent を作り直す

### 8.3 semantic_search が空配列を返す

1. `_embeddings` に値が入っているか (起動ログ確認)
2. `EMBEDDING_DEPLOYMENT=text-embedding-3-small` が env vars にあるか
3. text-embedding-3-small が Foundry にデプロイされているか:
   ```bash
   az cognitiveservices account deployment list \
     --name mah2026-bcc1cb --resource-group rg-mah-2026 -o table
   ```

### 8.4 ACR Tasks (`az acr build`) が "TasksOperationsNotAllowed"

無料試用版サブスクリプションの制限。ローカル Docker でビルド & push に切り替える (§5.1 参照)。

### 8.5 Microsoft Graph で 401 / 403

1. Managed Identity に `Mail.Read` / `User.Read.All` の application permission が付与されているか (§7 で確認)
2. テナント内にデータがない場合 (個人 MS テナント) は実データが取れないが、`_mock_signal()` にフォールバックする設計なのでアプリは落ちない

---

## 9. クリーンアップ (ハッカソン終了後)

```bash
# 一括削除 (非同期)
az group delete --name rg-mah-2026 --yes --no-wait

# Cognitive Services は soft delete → 完全消去には purge が必要
az cognitiveservices account purge \
  --name mah2026-bcc1cb \
  --resource-group rg-mah-2026 \
  --location eastus2

# Foundry の Agent はリソース削除で自動的に消える
```

コスト集計 (実績):
- Foundry / モデル推論 / Container App / ACR / Storage の合計でハッカソン期間 ¥1,000 未満想定
- 無料試用クレジット ¥30,000 内に余裕で収まる

---

## 10. 提出物の場所

| 提出物 | 取得元 |
|---|---|
| 公開 URL | `https://microsoft-agent-hackathon.nicebay-ff60cde9.eastus2.azurecontainerapps.io/` |
| GitHub | `https://github.com/motoshifurugen/microsoft-agent-hackathon` |
| Zenn 記事 | (執筆中) |
| デモ動画 | (収録予定) |
