"""Microsoft Graph 観測の単体テスト。

実際の Graph API には接続せず、httpx と credential をモックして
キーワード判定 / シグナル変換 / フォールバックの 3 点を検証する。
"""

from __future__ import annotations

import pytest

from src.tools import graph_observe
from src.tools.graph_observe import (
    Signal,
    _build_excerpt,
    _looks_like_pain,
    _signals_from_messages,
    fetch_signals,
)


class TestLooksLikePain:
    @pytest.mark.parametrize(
        "text",
        [
            "月次レポートで困っています",
            "やり方が分からない",
            "教えてほしい",
            "またこれかかった",
            "8 時間がかかる",
        ],
    )
    def test_pain_keywords_match(self, text: str) -> None:
        assert _looks_like_pain(text) is True

    @pytest.mark.parametrize(
        "text", ["", "今日は晴れです", "完了しました", "ご対応ありがとうございます"]
    )
    def test_non_pain_text(self, text: str) -> None:
        assert _looks_like_pain(text) is False


class TestBuildExcerpt:
    def test_short_text_unchanged(self) -> None:
        assert _build_excerpt("hello") == "hello"

    def test_collapses_whitespace(self) -> None:
        assert _build_excerpt("a\n\n  b\t  c") == "a b c"

    def test_truncates_long(self) -> None:
        text = "あ" * 200
        excerpt = _build_excerpt(text, limit=20)
        assert len(excerpt) == 20
        assert excerpt.endswith("…")


class TestSignalsFromMessages:
    def test_extracts_only_pain_messages(self) -> None:
        messages = [
            {
                "subject": "月次レポートで困っている",
                "bodyPreview": "毎月 8 時間もかかる",
                "receivedDateTime": "2026-05-26T10:00:00Z",
            },
            {
                "subject": "お疲れさまでした",
                "bodyPreview": "本日の業務完了です",
                "receivedDateTime": "2026-05-26T11:00:00Z",
            },
        ]
        signals = _signals_from_messages("u-1", messages)
        assert len(signals) == 1
        assert signals[0].user_id == "u-1"
        assert signals[0].source_signal == "teams_message"
        assert "月次レポート" in signals[0].business_context_hint

    def test_empty_messages_returns_empty(self) -> None:
        assert _signals_from_messages("u-1", []) == []


class TestFetchSignals:
    def test_empty_user_id_returns_empty(self) -> None:
        assert fetch_signals("") == []

    def test_falls_back_to_mock_when_token_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(graph_observe, "_get_graph_token", lambda: None)
        signals = fetch_signals("u-tanaka")
        assert len(signals) == 1
        assert isinstance(signals[0], Signal)
        assert "月次レポート" in signals[0].business_context_hint

    def test_falls_back_to_mock_when_no_pain_messages(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(graph_observe, "_get_graph_token", lambda: "fake-token")
        monkeypatch.setattr(
            graph_observe,
            "_fetch_recent_messages",
            lambda user_id, token, top=25: [
                {
                    "subject": "今日のミーティング",
                    "bodyPreview": "アジェンダ確認",
                    "receivedDateTime": "2026-05-26T10:00:00Z",
                }
            ],
        )
        signals = fetch_signals("u-1")
        assert len(signals) == 1
        # fallback の mock シグナルが返る
        assert "月次レポート" in signals[0].business_context_hint

    def test_returns_graph_signals_when_pain_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(graph_observe, "_get_graph_token", lambda: "fake-token")
        monkeypatch.setattr(
            graph_observe,
            "_fetch_recent_messages",
            lambda user_id, token, top=25: [
                {
                    "subject": "経費精算で困っています",
                    "bodyPreview": "領収書の処理がわからない",
                    "receivedDateTime": "2026-05-26T10:00:00Z",
                }
            ],
        )
        signals = fetch_signals("u-1")
        assert len(signals) == 1
        assert signals[0].user_id == "u-1"
        assert "経費精算" in signals[0].business_context_hint
