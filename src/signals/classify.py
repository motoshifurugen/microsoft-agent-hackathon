"""Slack 投稿 → 業務カテゴリのルールベース分類 (Azure 非依存の純粋関数)。

高度な LLM 分類は今回スコープ外 (要件: まずはルールベース)。
キーワード辞書でカテゴリごとのヒット数をスコアにし、最も合致するカテゴリを選ぶ。
業務改善に無関係な投稿 (感情のみ等) はどのカテゴリにもヒットせず None を返し、無視する。

分類先カテゴリは src/api/categories.py の CATEGORY_MASTER と一致させること。
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote, urlencode

# カテゴリ → キーワード群。表示順は CATEGORY_MASTER に合わせ、同点時の優先順位にもなる。
# 注意: 感情のみの投稿 (例「会議多い」) を誤検知しないよう、汎用語 (例「会議」単体) は採用しない。
_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "データ集計": ("データ集計", "データ", "CSV", "Excel", "エクセル"),
    "メール作成": ("メール", "文面", "メール返信"),
    "提案書作成": ("提案書", "たたき台", "資料"),
    "議事録要約": ("議事録", "会議メモ", "会議メモ", "minutes", "ミーティングメモ"),
    "コードレビュー": ("コードレビュー", "レビュー観点", "レビュー", "プルリク", "PR"),
    "問い合わせ対応": ("問い合わせ", "カスタマー", "CS", "FAQ", "一次返信"),
    "月次レポート作成": ("月次", "レポート", "KPI", "売上報告", "売上"),
    "経費精算": ("経費", "精算", "領収書"),
    "アンケート集計": ("アンケート", "自由記述", "集計"),
}

# カテゴリ別の返信ヒント文 (2 行目)。未定義カテゴリは _DEFAULT_HINT を使う。
_REPLY_HINTS: dict[str, str] = {
    "月次レポート作成": "近い成功事例とすぐ使えるプロンプトを見つけました",
    "議事録要約": "会議メモを短く整理するテンプレートがあります",
    "コードレビュー": "レビュー観点の抜け漏れを減らす事例があります",
    "問い合わせ対応": "一次返信を楽にするテンプレートがあります",
    "経費精算": "チェックの手間を減らす事例があります",
    "提案書作成": "たたき台づくりが速くなる事例があります",
    "アンケート集計": "集計と傾向出しを楽にする事例があります",
    "メール作成": "文面づくりが楽になるテンプレートがあります",
    "データ集計": "集計を自動化する事例があります",
}

_DEFAULT_HINT = "近い事例とすぐ使えるプロンプトがあります"


@dataclass(frozen=True)
class Classification:
    """分類結果。"""

    business_category: str
    confidence: float  # 0.0-1.0
    summary: str


def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    """text 中に出現するキーワード種類数を数える (重複語は 1 とカウント)。"""
    return sum(1 for kw in set(keywords) if kw and kw in text)


def classify(text: str) -> Classification | None:
    """投稿文を業務カテゴリに分類する。

    どのカテゴリにもヒットしなければ None (= 支援候補にしない)。

    Args:
        text: Slack 投稿の本文。

    Returns:
        最も合致するカテゴリの Classification。無関係なら None。
    """
    normalized = text.strip()
    if not normalized:
        return None

    # (ヒット数, -優先順位) が最大のカテゴリを選ぶ。dict は CATEGORY_MASTER 順なので
    # enumerate の index が小さいほど優先度が高い。
    best_category: str | None = None
    best_hits = 0
    best_rank = len(_CATEGORY_KEYWORDS)
    for rank, (category, keywords) in enumerate(_CATEGORY_KEYWORDS.items()):
        hits = _count_hits(normalized, keywords)
        if hits == 0:
            continue
        if hits > best_hits or (hits == best_hits and rank < best_rank):
            best_category, best_hits, best_rank = category, hits, rank

    if best_category is None:
        return None

    # ヒット数が多いほど確信度を上げる (1→0.7, 2→0.9, 3 以上→0.95 で頭打ち)。
    confidence = min(0.5 + 0.2 * best_hits, 0.95)
    summary = f"{best_category}に負荷を感じている可能性"
    return Classification(
        business_category=best_category, confidence=round(confidence, 2), summary=summary
    )


def build_kodama_url(base_url: str, category: str, signal_id: str, source: str = "slack") -> str:
    """カテゴリ詳細画面 (/categories/{name}) への URL を組み立てる。

    フロントの React Router ルート `categories/:name` に合わせ、カテゴリ名 (日本語) を
    パスに URL エンコードして埋め込む。検知元 (slack / teams) と signal_id をクエリに付与する。
    """
    base = base_url.rstrip("/")
    path = quote(category, safe="")
    query = urlencode({"source": source, "signal_id": signal_id})
    return f"{base}/categories/{path}?{query}"


def build_reply(category: str, kodama_url: str) -> str:
    """Slack スレッドへの返信文を組み立てる (やさしく短いトーン)。"""
    hint = _REPLY_HINTS.get(category, _DEFAULT_HINT)
    return f"その“はてな”、{category}に近そうです。\n\n{hint}👇\n{kodama_url}"
