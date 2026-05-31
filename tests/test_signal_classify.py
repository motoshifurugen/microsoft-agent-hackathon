"""Slack 投稿 → 業務カテゴリ分類ロジックのテスト (Azure 非依存・純粋関数)。"""

from __future__ import annotations

import pytest

from src.signals.classify import build_kodama_url, build_reply, classify

# 支援候補として検知したい投稿 → 期待カテゴリ
DETECT_CASES = [
    ("月次レポートだりい", "月次レポート作成"),
    ("月次レポート、また8時間か…", "月次レポート作成"),
    ("議事録まとめるの毎回しんどい", "議事録要約"),
    ("会議メモを毎回整理するのが大変", "議事録要約"),
    ("問い合わせ返信のトーンを整えるのに時間がかかる", "問い合わせ対応"),
    ("PRの設計観点レビュー、毎回抜け漏れが不安", "コードレビュー"),
    ("経費精算チェックが面倒", "経費精算"),
    ("提案書のたたき台作るのに時間がかかる", "提案書作成"),
    ("アンケート集計がつらい", "アンケート集計"),
    ("データ集計が毎回手作業でしんどい", "データ集計"),
]

# 支援候補にしない投稿 (業務改善に無関係 / 感情のみ)
IGNORE_CASES = [
    "今日は疲れた",
    "眠い",
    "会議多い",
    "雑談しよう",
    "体調があまりよくない",
    "家庭の事情で早退します",
    "人間関係がしんどい",
]


class TestClassify:
    @pytest.mark.parametrize(("text", "expected"), DETECT_CASES)
    def test_detects_business_category(self, text: str, expected: str) -> None:
        result = classify(text)
        assert result is not None
        assert result.business_category == expected
        assert 0.0 < result.confidence <= 1.0
        assert result.summary  # 要約が生成される

    @pytest.mark.parametrize("text", IGNORE_CASES)
    def test_ignores_non_business(self, text: str) -> None:
        assert classify(text) is None

    def test_blank_text_is_ignored(self) -> None:
        assert classify("   ") is None

    def test_more_keyword_hits_higher_confidence(self) -> None:
        strong = classify("月次レポートのKPI売上報告")
        weak = classify("レポート書くの面倒")
        assert strong is not None
        assert weak is not None
        assert strong.confidence >= weak.confidence


class TestBuildKodamaUrl:
    def test_includes_category_source_and_signal_id(self) -> None:
        url = build_kodama_url("http://localhost:8000", "月次レポート作成", "signal-001")
        assert url.startswith("http://localhost:8000/categories/")
        assert "source=slack" in url
        assert "signal_id=signal-001" in url
        # 日本語カテゴリは URL エンコードされる
        assert "月次レポート作成" not in url

    def test_strips_trailing_slash_on_base(self) -> None:
        url = build_kodama_url("http://localhost:8000/", "経費精算", "s1")
        assert "//categories" not in url.replace("http://", "")


class TestBuildReply:
    def test_uses_soft_tone_and_category(self) -> None:
        reply = build_reply("月次レポート作成", "http://x/y")
        assert "その“はてな”、月次レポート作成に近そうです" in reply
        assert "http://x/y" in reply
        # 避けたい表現を含まない
        assert "監視" not in reply
        assert "検知" not in reply

    def test_known_category_has_specific_hint(self) -> None:
        reply = build_reply("議事録要約", "http://x/y")
        assert "その“はてな”、議事録要約に近そうです" in reply
        assert "👇" in reply
