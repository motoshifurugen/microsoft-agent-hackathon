"""src/tools/ の各関数の単体テスト。

Azure 接続不要。MVP の mock 実装が dataclass I/F を満たすことを検証する。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from unittest.mock import patch

import pytest

from src.tools.cosmos_io import (
    ColdStartTemplate,
    PainPoint,
    SuccessCase,
    fetch_success_cases,
    get_all_embeddings,
    get_all_success_cases,
    get_cold_start_templates,
    register_embedding,
    save_pain_point,
    seed_cold_start_template,
    seed_success_case,
)
from src.tools.graph_observe import Signal, fetch_signals
from src.tools.registry import tool_get_cold_start_templates
from src.tools.search_query import semantic_search


@pytest.fixture(autouse=True)
def _reset_in_memory_store() -> Iterator[None]:
    """テストごとに in-memory store と embedding キャッシュをクリアする。"""
    get_all_success_cases().clear()
    get_all_embeddings().clear()
    get_cold_start_templates().clear()
    yield
    get_all_success_cases().clear()
    get_all_embeddings().clear()
    get_cold_start_templates().clear()


class TestPainPoint:
    def test_save_and_returns_id(self) -> None:
        pp = PainPoint(
            user_id="u-1",
            business_context="月次レポート作成",
            pain_description="毎月 8 時間かかる",
            source_signal="teams_message",
        )
        saved_id = save_pain_point(pp)
        assert saved_id == pp.id

    def test_default_status_is_pending(self) -> None:
        pp = PainPoint(
            user_id="u-1",
            business_context="x",
            pain_description="y",
            source_signal="z",
        )
        assert pp.status == "pending"

    def test_immutable(self) -> None:
        pp = PainPoint(user_id="u-1", business_context="x", pain_description="y", source_signal="z")
        with pytest.raises(AttributeError):
            # frozen dataclass は実行時に AttributeError を出す
            pp.user_id = "u-2"  # type: ignore[misc]


class TestSuccessCase:
    def test_seed_and_fetch_roundtrip(self) -> None:
        case = SuccessCase(
            user_id="u-success",
            business_type="月次レポート作成",
            what_worked="Copilot のプロンプトで雛形を出力",
            why_worked="繰り返し作業のテンプレ化が効いた",
            reproducibility_score=0.8,
        )
        seed_success_case(case)

        fetched = fetch_success_cases([case.id])
        assert len(fetched) == 1
        assert fetched[0].user_id == case.user_id
        assert fetched[0].reproducibility_score == 0.8

    def test_fetch_missing_id_returns_empty(self) -> None:
        assert fetch_success_cases(["does-not-exist"]) == []

    def test_fetch_preserves_order_of_existing(self) -> None:
        a = SuccessCase(
            user_id="ua",
            business_type="A",
            what_worked="x",
            why_worked="y",
            reproducibility_score=0.5,
        )
        b = SuccessCase(
            user_id="ub",
            business_type="B",
            what_worked="x",
            why_worked="y",
            reproducibility_score=0.5,
        )
        seed_success_case(a)
        seed_success_case(b)

        fetched = fetch_success_cases([b.id, a.id, "missing"])
        assert [c.id for c in fetched] == [b.id, a.id]


class TestFetchSignals:
    def test_empty_user_id_returns_empty(self) -> None:
        assert fetch_signals(user_id="") == []

    def test_returns_mock_signal_for_user(self) -> None:
        signals = fetch_signals(user_id="u-1")
        assert len(signals) == 1
        assert isinstance(signals[0], Signal)
        assert signals[0].user_id == "u-1"
        assert signals[0].source_signal == "teams_message"


class TestSemanticSearch:
    def test_empty_query_returns_empty(self) -> None:
        assert semantic_search("") == []

    def test_no_match_returns_empty(self) -> None:
        assert semantic_search("全く関係のないクエリ") == []

    def test_business_type_match(self) -> None:
        case = SuccessCase(
            user_id="u-success",
            business_type="月次レポート",
            what_worked="copilot template",
            why_worked="time saved",
            reproducibility_score=0.9,
        )
        seed_success_case(case)

        hits = semantic_search("経理部の月次レポートで困っている")
        assert len(hits) >= 1
        assert hits[0].case_id == case.id
        assert hits[0].score > 0.0

    def test_top_k_limits_results(self) -> None:
        for i in range(5):
            seed_success_case(
                SuccessCase(
                    user_id=f"u-{i}",
                    business_type="月次レポート",
                    what_worked=f"way-{i}",
                    why_worked="x",
                    reproducibility_score=0.5,
                )
            )

        hits = semantic_search("月次レポート", top_k=2)
        assert len(hits) <= 2


class TestEmbeddingFallback:
    def test_logs_warning_when_embedding_fails(self, caplog: pytest.LogCaptureFixture) -> None:
        """_embedding_search 失敗時に WARNING が記録され、string_match へフォールバックする。"""
        case = SuccessCase(
            user_id="u-embed",
            business_type="月次レポート",
            what_worked="Copilot でテンプレ生成",
            why_worked="テンプレ化が効く",
            reproducibility_score=0.8,
        )
        seed_success_case(case)
        register_embedding(case.id, [0.1, 0.2, 0.3])

        with (
            patch("src.tools.search_query.embed_text", side_effect=RuntimeError("Azure down")),
            caplog.at_level(logging.WARNING, logger="src.tools.search_query"),
        ):
            results = semantic_search("月次レポート")

        warning_messages = [r.message for r in caplog.records]
        assert any("embed" in m.lower() or "fallback" in m.lower() for m in warning_messages), (
            f"No warning logged. Records: {warning_messages}"
        )
        # string-match fallback should still find the case
        assert any(h.case_id == case.id for h in results)


def _make_template(category: str) -> ColdStartTemplate:
    return ColdStartTemplate(
        business_category=category,
        title=f"{category}テンプレート",
        description="説明",
        common_pain="困りごと",
        prompt="プロンプト",
        steps=["step1", "step2"],
        suitable_for="向いている人",
        cautions="注意点",
        feedback_question="？",
    )


class TestToolGetColdStartTemplates:
    def test_returns_empty_when_store_is_empty(self) -> None:
        result = tool_get_cold_start_templates()
        assert result == []

    def test_returns_all_templates_when_no_category(self) -> None:
        seed_cold_start_template(_make_template("月次レポート作成"))
        seed_cold_start_template(_make_template("議事録要約"))

        result = tool_get_cold_start_templates()
        assert len(result) == 2
        categories = {r["business_category"] for r in result}
        assert categories == {"月次レポート作成", "議事録要約"}

    def test_filters_by_category(self) -> None:
        seed_cold_start_template(_make_template("月次レポート作成"))
        seed_cold_start_template(_make_template("議事録要約"))

        result = tool_get_cold_start_templates(business_category="月次レポート作成")
        assert len(result) == 1
        assert result[0]["business_category"] == "月次レポート作成"

    def test_returns_empty_for_unknown_category(self) -> None:
        seed_cold_start_template(_make_template("月次レポート作成"))

        result = tool_get_cold_start_templates(business_category="存在しないカテゴリ")
        assert result == []

    def test_result_contains_expected_fields(self) -> None:
        seed_cold_start_template(_make_template("メール作成"))

        result = tool_get_cold_start_templates(business_category="メール作成")
        assert len(result) == 1
        tpl = result[0]
        for field in (
            "business_category",
            "title",
            "prompt",
            "steps",
            "cautions",
            "feedback_question",
        ):
            assert field in tpl

    def test_result_is_json_serializable(self) -> None:
        import json

        seed_cold_start_template(_make_template("提案書作成"))
        result = tool_get_cold_start_templates()
        assert json.dumps(result)  # raises if not serializable
