"""業務カテゴリのマスタ定義と正規化。

カテゴリを自由文字列のまま集約すると表記ゆれで分裂するため、
固定マスタを単一の真実とし、登録セレクトの選択肢として提供する。
登録時は既知の別名を正規化し、マスタ外の自由入力 (その他) は素通しする。
"""

from __future__ import annotations

# 登録セレクトに出す正規カテゴリ (表示順)。success_cases と cold_start_templates の
# 既存値の和集合を正規化したもの。並びはそのままグリッド/セレクトの表示順に使える。
CATEGORY_MASTER: list[str] = [
    "データ集計",
    "メール作成",
    "提案書作成",
    "議事録要約",
    "コードレビュー",
    "問い合わせ対応",
    "月次レポート作成",
    "経費精算",
    "アンケート集計",
]

# 表記ゆれ → 正規カテゴリ。データ実体に存在した不一致のみ登録する。
_CATEGORY_ALIASES: dict[str, str] = {
    "経費精算チェック": "経費精算",
}


def normalize_category(raw: str) -> str:
    """カテゴリ名を正規化する。

    前後空白を除去し、既知の別名は正規カテゴリへ寄せる。
    マスタ外の値 (その他=自由入力) はそのまま返す。
    """
    stripped = raw.strip()
    return _CATEGORY_ALIASES.get(stripped, stripped)
