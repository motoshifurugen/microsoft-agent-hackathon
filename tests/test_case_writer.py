"""case_writer と tool_register_success_case の単体テスト。

Azure OpenAI への実通信は行わず、embed_text を monkeypatch でモック化する。
登録 → 検索 (semantic_search) / 自分の事例 (user_id 絞り込み) のループを検証する。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

from src.tools import search_query
from src.tools.case_writer import build_embedding_text, register_success_case
from src.tools.cosmos_io import (
    SuccessCase,
    get_all_embeddings,
    get_all_success_cases,
)
from src.tools.registry import tool_register_success_case
from src.tools.search_query import semantic_search


@pytest.fixture(autouse=True)
def _reset_stores(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    get_all_success_cases().clear()
    get_all_embeddings().clear()
    # 既定で embed をローカル fake にして Azure 通信を防ぐ。
    # 個別テストが必要に応じて再 monkeypatch で上書きする。
    monkeypatch.setattr("src.tools.embed.embed_text", lambda text: [0.0, 0.0, 0.0])
    yield
    get_all_success_cases().clear()
    get_all_embeddings().clear()


class TestBuildEmbeddingText:
    def test_combines_business_type_and_what_worked(self) -> None:
        case = SuccessCase(
            user_id="u-1",
            business_type="月次レポート",
            what_worked="Copilot で雛形生成",
            why_worked="x",
            reproducibility_score=0.5,
        )
        assert build_embedding_text(case) == "月次レポート\nCopilot で雛形生成"


class TestRegisterSuccessCase:
    def test_stores_and_searchable_via_string_match(self) -> None:
        case = SuccessCase(
            user_id="u-1",
            business_type="月次レポート",
            what_worked="Copilot で雛形生成",
            why_worked="x",
            reproducibility_score=0.6,
        )
        case_id = register_success_case(case, with_embedding=False)

        assert case_id == case.id
        assert case.id in get_all_success_cases()
        # embedding 無しでも文字列マッチで検索可能
        hits = semantic_search("月次レポートで困っている")
        assert any(h.case_id == case.id for h in hits)

    def test_registers_embedding_and_searchable_via_embedding(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def fake_embed(text: str) -> list[float]:
            if "月次" in text:
                return [1.0, 0.0, 0.0]
            return [0.0, 1.0, 0.0]

        # case_writer は関数内で遅延 import するため src.tools.embed を差し替える
        monkeypatch.setattr("src.tools.embed.embed_text", fake_embed)
        monkeypatch.setattr(search_query, "embed_text", fake_embed)

        case = SuccessCase(
            user_id="u-1",
            business_type="月次レポート",
            what_worked="Copilot で雛形生成",
            why_worked="x",
            reproducibility_score=0.6,
        )
        register_success_case(case, with_embedding=True)

        assert case.id in get_all_embeddings()
        hits = semantic_search("月次レポートで困っている", top_k=3)
        assert any(h.case_id == case.id for h in hits)

    def test_registration_succeeds_even_if_embedding_fails(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        def fail_embed(text: str) -> list[float]:
            raise RuntimeError("simulated Azure failure")

        monkeypatch.setattr("src.tools.embed.embed_text", fail_embed)

        case = SuccessCase(
            user_id="u-1",
            business_type="月次レポート",
            what_worked="Copilot で雛形生成",
            why_worked="x",
            reproducibility_score=0.6,
        )
        with caplog.at_level(logging.WARNING, logger="src.tools.case_writer"):
            case_id = register_success_case(case, with_embedding=True)

        # 登録自体は成立 (検索ヒットしないだけ)
        assert case_id == case.id
        assert case.id in get_all_success_cases()
        assert case.id not in get_all_embeddings()
        assert any("embedding" in r.message.lower() for r in caplog.records)


class TestToolRegisterSuccessCase:
    def test_registers_with_normalized_category(self) -> None:
        # "経費精算チェック" は alias 経由で "経費精算" に正規化される想定
        result = tool_register_success_case(
            user_id="u-sato",
            owner_label="営業部 佐藤さん",
            business_type="経費精算チェック",
            what_worked="領収書を Copilot で OCR",
        )

        assert result["status"] == "registered"
        assert result["business_type"] == "経費精算"
        stored = list(get_all_success_cases().values())
        assert len(stored) == 1
        assert stored[0]["user_id"] == "u-sato"
        assert stored[0]["business_type"] == "経費精算"

    def test_missing_required_field_returns_error(self) -> None:
        result = tool_register_success_case(
            user_id="u-1",
            owner_label="",  # 必須欠落
            business_type="月次レポート",
            what_worked="x",
        )
        assert "error" in result
        assert get_all_success_cases() == {}

    def test_blank_user_id_returns_error(self) -> None:
        result = tool_register_success_case(
            user_id="   ",
            owner_label="佐藤さん",
            business_type="月次レポート",
            what_worked="x",
        )
        assert "error" in result

    def test_score_clamped_to_upper_bound(self) -> None:
        tool_register_success_case(
            user_id="u-1",
            owner_label="佐藤さん",
            business_type="月次レポート",
            what_worked="x",
            reproducibility_score=5.0,
        )
        stored = next(iter(get_all_success_cases().values()))
        assert stored["reproducibility_score"] == 1.0

    def test_score_clamped_to_lower_bound(self) -> None:
        tool_register_success_case(
            user_id="u-1",
            owner_label="佐藤さん",
            business_type="月次レポート",
            what_worked="x",
            reproducibility_score=-2.0,
        )
        stored = next(iter(get_all_success_cases().values()))
        assert stored["reproducibility_score"] == 0.0

    def test_non_numeric_score_defaults(self) -> None:
        tool_register_success_case(
            user_id="u-1",
            owner_label="佐藤さん",
            business_type="月次レポート",
            what_worked="x",
            reproducibility_score="not-a-number",  # type: ignore[arg-type]
        )
        stored = next(iter(get_all_success_cases().values()))
        assert stored["reproducibility_score"] == 0.5

    def test_registered_case_reflected_in_user_filter(self) -> None:
        """list_my_cases 相当の user_id 絞り込みに登録事例が反映される。"""
        tool_register_success_case(
            user_id="client-abc",
            owner_label="佐藤さん",
            business_type="月次レポート",
            what_worked="Copilot で雛形生成",
        )
        mine = [c for c in get_all_success_cases().values() if c.get("user_id") == "client-abc"]
        assert len(mine) == 1
        assert mine[0]["owner_label"] == "佐藤さん"
