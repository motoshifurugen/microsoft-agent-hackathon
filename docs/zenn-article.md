---
title: "社内のAI活用を伝播させる自律エージェント『Kodama』をMicrosoft Agent Hackathon 2026に向けて作った話"
emoji: "🌿"
type: "tech"
topics: ["azure", "azureai", "fastapi", "react", "hackathon"]
published: false
---

# はじめに：私が直面した現場の課題

会社で Claude や Copilot の導入推進を担当しているのですが、導入したはいいものの利用率は伸び悩んでいました。使い方がわからない人はまったく使わず、使いこなしている人はどんどん業務を AI に置き換えていく。この「AI活用格差」を日々実感していました。

格差が広がると、一部の人だけが AI で定時に帰り、残りの人は相変わらず手作業に追われます。効率化のはずの AI が、かえって「働き具合」の差を広げてしまう。使い方をレクチャーしても、いかに効率化できるかを伝えても、この溝は埋まりませんでした。

私が本当に変えたかったのは、生産性の数字そのものではありません。**特定の誰かではなく、誰もが AI を使いこなせる状態をつくり、組織全体の働き具合をよくすること**。そのために、個人の中に閉じた「業務に対する AI の活用方法」という暗黙知を、組織の形式知に変えて浸透させたい。その想いで、Microsoft Agent Hackathon 2026 に向けて開発したのが『Kodama』です。

---

# コンセプト：まっさらなAIより、みんなが育てたAIを。

「自由にプロンプトを書いてください」

と、まっさらな AI を渡されるのは、実は多くの人にとって心理的ハードルが高いお願いです。使いこなせる人はそれでいい。けれど「何を書けばいいか分からない」人を置き去りにする限り、AI 活用は一部の人のものであり続けます。

そこで Kodama が目指すのは、「みんなが育てた AI」です。

オフィスの給湯室で交わされる「それ、こうやったらすぐ終わったよ」という何気ない立ち話。あの自然な知見の共有に、システムでレバレッジをかける。

ゼロから AI の使い方を考えるのではなく、先輩や同僚が試行錯誤して見つけたコツを、ただなぞってみるだけでいい。

ねらいは、AI を使いこなす人を増やすこと、そのものです。一部の人の生産性をさらに伸ばすことではなく、**今まで使えなかった人が「自分にもできた」と一歩を踏み出せること**。その小さな成功体験が積み重なれば、組織全体の働き具合は少しずつ底上げされていく。AI 活用の最初の一歩をそっと後押しする。それが Kodama です。

---

# Kodamaが提供する体験（デモシナリオ）

Kodama は **「困っている人と成功事例を、限りなくシームレスにマッチングする」** AI 活用提案エージェントです。

一般的なチャットボットとは設計の思想が少し違います。「聞かれたら答える」のではなく、「その人の今の業務に刺さるものを、選ぶだけで使えるように提示する」ことを目指しました。

## ホーム：今日の成功事例と「AIに相談」

Kodama を開くと、まず **「今日のおすすめ」** が目に飛び込んできます。

![Kodama のホーム画面。今日のおすすめと「AIに相談」チャット](images/zenn/kodama-home.png)

「今日のおすすめ」は日付をシードにしたアルゴリズムで選ばれるので、同じ日にアクセスした社員はみんな同じ事例を見ることになります。「あ、今日トップに出てたあのプロンプト、使えそうだったね」という共通認識を生むためのちょっとした工夫です。

その下にあるのが、Kodama の中心的な入り口である **「AIに相談」** です。困りごとを自然な言葉で話すと、AI が社内の似た事例を探して提案します。入力に詰まらないよう、「議事録の要約に時間がかかる」といった相談例のチップも置いてあります。

### チャット中心に至るまでの試行錯誤

実は Kodama の最初のプロトタイプは Chainlit を使ったシンプルなチャットでした。しかしテストすると、**AI に不慣れな人ほど「チャットの窓に何を入力していいか分からない」** という壁にぶつかりました。

そこで一度は「ぽちぽち選ぶだけ」のダッシュボード型に振り切ることも検討しました。ただ、選択肢を眺めるだけでは「自分の業務に引きつけた相談」までは届きません。最終的に Kodama がたどり着いたのは、**2 つの入り口を併せ持つハイブリッド** です。

- **話せる人には、チャットで。** 「AIに相談」に困りごとを書けば、その文脈に最も近い事例が返ってくる。
- **話せない人には、受動検知で。** 普段の Slack の何気ない投稿を Kodama が拾い、「それ、こうやると楽になりますよ」とそっと声をかける（後述の `#はてなボックス` 連携）。

「何を入力していいか分からない」層こそ一番助けたい。その答えが、相談を待つだけでなく Kodama 側から歩み寄る設計でした。

### 「AIに相談」の実際

たとえば「議事録の要約に毎回30分以上かかっていて困っています」と相談すると、Kodama は社内の成功事例を最大 3 件まで提示し、続けて 2 つの次アクション（戦略 A / 戦略 B）を返します。

![AIに相談の応答。成功事例3件と戦略A/Bの提案](images/zenn/kodama-chat-proposal.png)

各事例には「誰の事例か（例：管理部 西田さん）」「何が変わったか（例：取締役会議事録 2h → 30min）」「今すぐ使えるプロンプト（原文のまま引用）」がまとまっています。そして締めくくりに必ず次の 2 択が提示されます。

- **戦略 A：紹介** — 成功者に 15 分だけ時間をもらい、直接ノウハウを聞く
- **戦略 B：テンプレ共有** — 上記プロンプトを自分のペースで試す

ここで効いているのが「**提示は最大 3 件**」「**戦略 A / B を必ず両方出す**」「**社内 ID は絶対に表示せず表示名で語る**」といった厳守ルールです。これらは LLM に「覚えさせる」のではなく、後述する Orchestrator の Instructions に直接書いて強制しています。

### 成功事例がまだ無いとき（Cold Start）

社内にまだ近い事例が無い場合、Kodama は黙り込みません。業務カテゴリに合う「すぐ使える基本テンプレート」を提示し、「うまくいったら、このカテゴリの最初の成功事例として共有してください」と促します。

![Cold Start 時の応答。テンプレートのプロンプト・手順・注意点を提示](images/zenn/kodama-chat-coldstart.png)

*（開発用の Chainlit UI で Cold Start の挙動を確認したもの）*

## カテゴリで探す

チャットだけでなく、業務カテゴリから探す動線も用意しています。「議事録要約」「月次レポート作成」といったカテゴリのグリッドから、紐づく成功事例をカード形式で一覧できます。

![カテゴリ一覧画面](images/zenn/kodama-categories.png)

カテゴリを選ぶと、その業務の成功事例カードが並びます。各カードにはプロンプトのワンクリックコピーが付いており、気に入ったものは「保存したスキル」に残せます（履歴は localStorage に保持し、サーバーには送りません）。

![カテゴリ詳細。成功事例カードが並ぶ](images/zenn/kodama-category-detail.png)

## 困りごと掲示板

「わざわざ相談するほどでもないけど…」という小さな引っかかりの受け皿が **困りごと掲示板** です。カテゴリで絞り込みながら、社内の困りごととその回答を眺められます。

![困りごと掲示板。カテゴリフィルタと投稿一覧](images/zenn/kodama-board.png)

## 事例を共有する

成功体験は 2 つのルートで蓄積できます。1 つは「AIに相談」の会話の中で Kodama が「これ、登録しておきますか？」と尋ねるルート。もう 1 つが、自分で書いて登録する **「事例を共有」** フォームです。

![事例を共有フォーム](images/zenn/kodama-share.png)

必須項目は「表示名」「業務カテゴリ」「うまくいったこと」の 3 つだけ。プロンプトや定量効果は任意です。登録された事例はその場で検索対象に加わり、翌日には同じ業務で困っている誰かのもとへ届きます。

## Slack `#はてなボックス`：話せない人への受動的な導線

「チャットに何を書けばいいか分からない」人にこそ届けたい——その答えが Slack 連携です。

社内の `#はてなボックス` チャンネルに「月次レポートだりい」のような何気ない投稿があると、Kodama の Slack Bot がそれを検知して業務カテゴリを推定し、スレッドにそっと返信します。

```
その"はてな"、月次レポート作成に近そうです。

近い成功事例とすぐ使えるプロンプトを見つけました👇
https://kodama.../categories/月次レポート作成?source=slack&signal_id=...
```

相談しようと身構えなくても、いつもの愚痴をこぼすだけで Kodama の方から歩み寄ってくる。これが Kodama のもう 1 つの入り口です。

---

# 裏側で働く4つのAgent（技術構成）

Kodama のバックエンドは、Azure AI Foundry Agent Service 上で動く **4 つの Agent の協調** によって成り立っています。Orchestrator が窓口となり、3 つの子 Agent（収集・マッチング・提案）を文脈に応じて呼び分けます。

## アーキテクチャ全体像

```mermaid
flowchart TD
    subgraph UI["ユーザー接点"]
        Dash["React ダッシュボード<br/>(Vite + TypeScript)"]
        Chainlit["Chainlit<br/>(開発用チャット)"]
        Slack["Slack #はてなボックス<br/>(Socket Mode Bot)"]
    end

    Dash -->|REST / SSE| API
    Chainlit -->|Foundry SDK| Orch
    Slack -->|message event| API

    subgraph Backend["FastAPI バックエンド"]
        API["API ルーター<br/>(/api/agent, /api/board ...)"]
        Signals["Signal 検知<br/>(classify / store)"]
        API --> Signals
    end

    API -->|Foundry SDK| Orch

    subgraph Foundry["Azure AI Foundry Agent Service"]
        Orch["Orchestrator Agent"]
        Orch -->|ConnectedAgentTool| Collector["Collector Agent"]
        Orch -->|ConnectedAgentTool| Matcher["Matcher Agent"]
        Orch -->|ConnectedAgentTool| Proposer["Proposer Agent"]
        Orch -->|FunctionTool x5| Tools["tool_save_pain_point<br/>tool_semantic_search<br/>tool_fetch_success_cases<br/>tool_get_cold_start_templates<br/>tool_register_success_case"]
    end

    Orch --> AOAI["Azure OpenAI<br/>(gpt-4o-mini / 4o)"]
    Tools --> Embed["text-embedding-3-small<br/>(1536次元)"]
    Tools --> Store["Cosmos DB /<br/>Azure AI Search(予定) /<br/>in-memory フォールバック"]
```

## Orchestrator Agent：全体の指揮官

Orchestrator はユーザーと Kodama の **唯一の窓口** です。チャット発話を解釈し、5 つの function tool と 3 つの子 Agent を適切に呼び分けます。

直接呼べる function tool は次の 5 つです。

| tool | 役割 |
| --- | --- |
| `tool_save_pain_point` | 本人承認済みの困りごとを永続化（チャット由来は `source_signal="chat_input"`） |
| `tool_semantic_search` | 困りごとテキストから類似成功事例を embedding 検索（`top_k ≤ 3`、`exclude_user_id` で本人除外） |
| `tool_fetch_success_cases` | 成功事例の詳細（表示名 / プロンプト / 定量効果）を取得 |
| `tool_get_cold_start_templates` | 事例 0 件のときに業務カテゴリ向けテンプレートを取得 |
| `tool_register_success_case` | 本人同意のもとで成功事例を登録し検索可能にする |

Instructions には入力パターンごとの判断ルールが明示されています。

- **パターン 1：本人が述べた困りごと**（「○○で困っている」）→ 必要性を自分で判断し、`tool_semantic_search` で関連事例を検索して提案。本人が同意した場合のみ `tool_save_pain_point` で保存
- **パターン 2：能動的な検索依頼**（「高橋さんに合う事例を探して」）→ `exclude_user_id` を設定して `tool_semantic_search` を呼ぶ
- **パターン 3：一般的な質問・雑談** → tool 呼び出し不要で通常回答
- **パターン 4：成功体験の検知 → 登録提案**（「○○を AI でやったらうまくいった」）→ 不足項目を 1 つずつ確認し、本人同意のもとで `tool_register_success_case` を呼ぶ（Human-in-the-Loop）

DX 推進担当者向けの「誰に何を届けるか」も、専用の管理画面を作らずこのパターン 2 で実現しています。「○○さんに合う事例を探して」と相談すれば、本人の事例を除外したうえで関連事例と戦略 A / B が返ってきます。

> なお、初期構想にあった Microsoft Graph で組織活動を観測する「Observer Agent」は、ハッカソン MVP では Slack `#はてなボックス` のルールベース検知に置き換えました。Agent 構成も 5 → 4 にスリム化しています。

## Collector Agent：Human-in-the-Loopの守り人

Collector の仕事は **「データを保存してよいかどうかを確かめること」** です。困りごとを構造化し、本人確認のメッセージ（「月次レポート作業でお困りですか？」）を生成します。本人が同意した場合のみ永続化します。

**PII は user_id（内部 ID）のみを扱い、氏名・メールアドレスは DB に保存しません。** 表示が必要なときにのみ外部から解決する設計です。

## Matcher Agent：決定論とLLMのハイブリッド

Matcher は「誰と誰を繋ぐか」を判断します。設計のポイントは **決定論でスコアを計算し、LLM で最終戦略を選ぶ** ハイブリッド構成です。

```python
final_score = (cosine_similarity * 0.7) + (reproducibility_score * 0.3) + business_type_bonus(0.2)
```

- **コサイン類似度（重み 0.7）**：困りごとテキストを text-embedding-3-small（1536 次元）でベクトル化し、成功事例との類似度を計算
- **再現可能性スコア（重み 0.3）**：その事例が他者でも再現できる可能性（0〜1）
- **業務種別ボーナス（+0.2）**：クエリに成功事例の `business_type` が含まれる場合に加算

embedding が未登録の場合は `business_type` / `what_worked` のテキストマッチへ自動フォールバックします。本番（Azure AI Search）への切り替えも関数単位で差し替え可能な抽象化です。

## Proposer Agent：文脈に合わせた提案の生成

Proposer は Matcher が選んだ事例を元に、依頼者向けメッセージをカスタマイズします。戦略 A（紹介）では成功者への依頼文を、戦略 B（テンプレ共有）では成功者のプロンプトを対象者の業務名にローカライズして生成します。Instructions には「出典（表示名）を必ず示す」「押し付けず選択肢として提示する」という制約が書かれています。

## Slack `#はてなボックス` 検知の仕組み

Slack 連携は Foundry の Agent とは独立した、Azure 非依存のルールベースで実装しています。公開 HTTP エンドポイント不要の **Socket Mode** で動き、FastAPI の lifespan からバックグラウンド常駐します。

```mermaid
sequenceDiagram
    participant U as 社員
    participant S as Slack #はてなボックス
    participant Bot as Kodama Slack Bot
    participant C as classify (ルールベース)
    participant K as Kodama ダッシュボード

    U->>S: 「月次レポートだりい」と投稿
    S->>Bot: message イベント (Socket Mode)
    Bot->>Bot: is_target_message でフィルタ
    Bot->>C: 投稿文を業務カテゴリに分類
    alt 業務改善に関係あり
        C-->>Bot: business_category (+confidence)
        Bot->>S: スレッドに Kodama リンクを返信
        U->>K: リンクを開き成功事例に出会う
    else 感情のみ等 (無関係)
        C-->>Bot: None
        Bot->>Bot: 無視 (返信しない)
    end
```

分類はキーワード辞書でカテゴリごとのヒット数をスコア化し、最も合致するカテゴリを選びます。感情のみの投稿（「会議多い」等）を誤検知しないよう、汎用語は辞書から外しています。どのカテゴリにもヒットしなければ `None` を返し、返信もしません。必要な Bot Token Scope は `channels:history` と `chat:write` の最小構成です。

デモ用に `POST /api/slack/mock` も用意し、Slack ワークスペースなしでも検知フローを再現できるようにしています。

## Microsoft Teams への展開：Bot Framework アダプタ

`#はてなボックス` の受動検知は Slack 専用ではありません。同じ検知パイプラインを **Microsoft Teams** でも成立させる Bot Framework アダプタを実装しました。

Slack が Socket Mode（常駐接続）なのに対し、Teams は Azure Bot Service が発話を HTTP で push する方式です。そこで messaging endpoint `POST /api/teams/messages` を 1 本用意し、受け取った Bot Framework Activity を解釈して、Slack と同じ `handle_message`（`source="teams"`）へ橋渡しします。分類・URL 生成・保存はプラットフォーム共通で、差分はアダプタ層だけに閉じ込めました。

```python
# src/teams/adapter.py（要点）
def detect_from_activity(activity: dict, *, base_url: str) -> Signal | None:
    msg = extract_message(activity)        # message タイプ・本文あり・Bot 以外のみ
    if msg is None:
        return None
    return handle_message(                  # Slack とまったく同じ検知サービス
        channel_id=msg.conversation_id,
        slack_user_id=msg.user_id,
        text=msg.text,
        base_url=base_url,
        source="teams",                     # 検知元だけを差し替える
        ...,
    )
```

返信は Teams ネイティブな **Adaptive Card**（本文 + 「Kodama で見る」ボタン）として組み立てて返します。同じ「困りごと → 該当カテゴリへ誘導」の体験を、Slack でも Teams でも同一ロジックで届けられます。

正直に書いておくと、**実際に Teams へメッセージが届くまで通すには Azure Bot Service への登録（App ID・公開エンドポイント）と Bot Framework JWT の検証が必要**で、そこはハッカソン MVP では未実装です。アダプタと検知ロジックは単体・API テストで検証済みで、Azure Bot を後付けすれば本番 Teams 配信にそのまま載る設計にしています。

## 採用技術一覧

| 層 | 技術 | 役割 |
| --- | --- | --- |
| フロントエンド | React + Vite + TypeScript + Tailwind CSS | Web ダッシュボード |
| バックエンド API | FastAPI | エンドポイント提供・Agent 呼び出し・SSE ストリーミング |
| 開発用チャット | Chainlit | Orchestrator の動作確認用 UI |
| Agent 基盤 | Azure AI Foundry Agent Service | Multi-Agent Orchestration |
| LLM | Azure OpenAI（gpt-4o-mini / gpt-4o） | 全 Agent 共通の推論エンジン |
| Embedding | text-embedding-3-small（1536 次元） | 類似事例のセマンティック検索 |
| データ | Azure Cosmos DB | 成功事例・困りごとの永続化 |
| 検索 | Azure AI Search（予定）/ in-memory フォールバック | ベクトル検索 |
| インフラ | Azure Container Apps | スケールアウト・公開 URL（scale-to-zero） |
| 認証 | Microsoft Entra ID + Managed Identity | ローカル〜本番でコード変更なし |
| 外部連携（Slack） | Slack（Socket Mode / Bolt） | `#はてなボックス` の受動検知 |
| 外部連携（Teams） | Microsoft Teams（Bot Framework Activity / Adaptive Card） | 同じ検知を Teams でも受信・返信 |

## 実装上のこだわりポイント

**① ConnectedAgentTool で子 Agent を「必要なときだけ」呼ぶ**

Orchestrator は基本を function tool で完結させ、判断が難しいときだけ子 Agent に委譲します。LLM のコール数（コストとレイテンシ）を抑えつつ、複雑なケースへの対応力を残すバランスを狙いました。

**② embedding は lazy load で、失敗してもサービスを止めない**

FastAPI の起動時に成功事例の embedding を一括登録します。Azure OpenAI の呼び出しが失敗しても embedding なしで全件再ロードしてサービスを継続し、検索はベクトル検索からテキストマッチへ透過的にフォールバックします。

**③ 履歴はサーバーに送らず localStorage に留める（MVP段階）**

「保存したスキル」やコピー履歴はブラウザの localStorage に留めています。集計基盤を先に作るより、まずは「プレッシャーなく使われる体験」を優先したかったからです。

**④ DefaultAzureCredential で認証コードを変えない**

ローカルでは `az login` の認証情報、Azure Container Apps では Managed Identity を自動で使い分けます。環境ごとに認証コードを書き替える必要も、シークレットを環境変数に晒す必要もありません。

---

# 今後の展望とおわりに

AI は魔法ではありません。強力なツールを導入したからといって、翌月に全員の業務が変わるわけではありません。

AI 導入で本当に必要なのは、現場の誰かが生み出した「小さな工夫」をこぼさずにすくいあげること。そして、それを組織の中に伝播させていく仕組みです。

Kodama が目指すのは、こんな循環が当たり前に回る世界です。

1. 誰かが AI で、面倒な作業の時間を削減する。
2. Kodama がそれを静かに検知し、「これ、みんなにも共有していいですか？」と尋ねる。
3. うなずけば、新しい知恵として蓄積される。
4. 翌日、同じ業務で頭を抱えている別の誰かのもとへ、その知見が届く。

今回のハッカソンでは、「手動登録＋セマンティック検索からの提案」に加え、Slack と Microsoft Teams（Bot Framework）の両チャネルからの **受動的な困りごと検知** までを MVP として実装しました。今後は Microsoft Graph を通じたより広範な自動検知や、Power Automate 連携まで広げていく予定です。

「孤独な AI 活用」を終わらせるために開発した、AI 活用浸透エージェント『Kodama』。誰かの小さな成功体験が、木霊のように、次の誰かのもとへ飛んでいく。そんな温かいエージェントを作り続けたいと思います。
