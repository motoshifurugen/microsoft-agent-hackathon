"""LLM 分類器 (src/signals/llm_classify.py) の単体テスト。

実際の Azure OpenAI は呼ばず、_get_client / _invoke_llm を差し替えて、
LLM 経路・ルール fallback・"none" 尊重・不正応答の各分岐を検証する。
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.signals import llm_classify
from src.signals.classify import Classification


@pytest.fixture(autouse=True)
def _reset_client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(llm_classify, "_client", None)
    yield


def _fake_client(content: str):
    """chat.completions.create が固定 content を返すダミー client。"""
    message = SimpleNamespace(content=content)
    choice = SimpleNamespace(message=message)
    response = SimpleNamespace(choices=[choice])
    completions = SimpleNamespace(create=lambda **_: response)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions))


class TestFallbackGate:
    def test_blank_text_returns_none(self) -> None:
        assert llm_classify.classify_with_llm("   ") is None

    def test_unconfigured_uses_rule_classifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PROJECT_ENDPOINT", raising=False)
        result = llm_classify.classify_with_llm("月次レポートだりい")
        assert result is not None
        assert result.business_category == "月次レポート作成"

    def test_llm_error_falls_back_to_rule(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PROJECT_ENDPOINT", "https://x.services.ai.azure.com")

        def _boom(_: str) -> Classification | None:
            raise RuntimeError("api down")

        monkeypatch.setattr(llm_classify, "_invoke_llm", _boom)
        result = llm_classify.classify_with_llm("月次レポートだりい")
        assert result is not None
        assert result.business_category == "月次レポート作成"  # ルール fallback


class TestLlmDecision:
    def test_llm_category_is_used(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PROJECT_ENDPOINT", "https://x.services.ai.azure.com")
        monkeypatch.setattr(
            llm_classify,
            "_invoke_llm",
            lambda _: Classification("議事録要約", 0.88, "議事録に負荷"),
        )
        result = llm_classify.classify_with_llm("会議のあといつも記録づくりで消耗する")
        assert result is not None
        assert result.business_category == "議事録要約"
        assert result.confidence == 0.88

    def test_llm_none_is_respected_over_rule(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # ルールなら "月次レポート" にヒットするが、LLM が無関係と判断したら None を尊重する。
        monkeypatch.setenv("PROJECT_ENDPOINT", "https://x.services.ai.azure.com")
        monkeypatch.setattr(llm_classify, "_invoke_llm", lambda _: None)
        assert llm_classify.classify_with_llm("月次レポートの打ち上げ楽しかった") is None


class TestInvokeLlmParsing:
    def test_parses_valid_category(self, monkeypatch: pytest.MonkeyPatch) -> None:
        content = json.dumps(
            {"category": "コードレビュー", "confidence": 0.9, "summary": "PR 負荷"}
        )
        monkeypatch.setattr(llm_classify, "_get_client", lambda: _fake_client(content))
        result = llm_classify._invoke_llm("PR のレビュー観点が毎回抜ける")
        assert result is not None
        assert result.business_category == "コードレビュー"
        assert result.confidence == 0.9
        assert result.summary == "PR 負荷"

    def test_none_label_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        content = json.dumps({"category": "none", "confidence": 0.2, "summary": ""})
        monkeypatch.setattr(llm_classify, "_get_client", lambda: _fake_client(content))
        assert llm_classify._invoke_llm("今日はいい天気") is None

    def test_unknown_category_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        content = json.dumps({"category": "宇宙開発", "confidence": 0.9, "summary": "x"})
        monkeypatch.setattr(llm_classify, "_get_client", lambda: _fake_client(content))
        with pytest.raises(ValueError):
            llm_classify._invoke_llm("ロケットを飛ばしたい")

    def test_confidence_clamped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        content = json.dumps({"category": "メール作成", "confidence": 5, "summary": "x"})
        monkeypatch.setattr(llm_classify, "_get_client", lambda: _fake_client(content))
        result = llm_classify._invoke_llm("メールの文面いつも悩む")
        assert result is not None
        assert result.confidence == 1.0
