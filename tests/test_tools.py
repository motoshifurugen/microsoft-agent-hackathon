"""src/tools/ の各関数の単体テスト。

Azure 接続不要。MVP の mock 実装が dataclass I/F を満たすことを検証する。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from unittest.mock import patch

import pytest

from src.tools.cosmos_io import (
    PainPoint,
    SuccessCase,
    fetch_success_cases,
    get_all_embeddings,
    get_all_success_cases,
    register_embedding,
    save_pain_point,
    seed_success_case,
)
from src.tools.graph_observe import Signal, fetch_signals
from src.tools.search_query import semantic_search


@pytest.fixture(autouse=True)
def _reset_in_memory_store() -> Iterator[None]:
    """テストごとに in-memory store と embedding キャッシュをクリアする。"""
    get_all_success_cases().clear()
    get_all_embeddings().clear()
    yield
    get_all_success_cases().clear()
    get_all_embeddings().clear()


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
