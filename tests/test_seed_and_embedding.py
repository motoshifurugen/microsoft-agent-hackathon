"""seed loader と embedding ベース検索の単体テスト。

Azure OpenAI への実通信は行わず、embed_text を monkeypatch でモック化する。
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from src.tools import embed, search_query
from src.tools.cosmos_io import _embeddings, _success_cases
from src.tools.embed import cosine_similarity
from src.tools.search_query import semantic_search
from src.tools.seed import load_success_cases


@pytest.fixture(autouse=True)
def _reset_stores() -> Iterator[None]:
    """各テストで in-memory store と embedding cache をクリア。"""
    _success_cases.clear()
    _embeddings.clear()
    yield
    _success_cases.clear()
    _embeddings.clear()


class TestLoadSuccessCases:
    def test_loads_default_seed_file(self) -> None:
        count = load_success_cases()
        assert count >= 5
        assert len(_success_cases) == count
        # embedding は使わないモードなので未登録
        assert len(_embeddings) == 0

    def test_with_embeddings_true_calls_embed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # 2 件の最小 seed を書き出す
        seed_data = [
            {
                "user_id": "u-1",
                "business_type": "月次レポート",
                "what_worked": "copilot template",
                "why_worked": "x",
                "reproducibility_score": 0.8,
            },
            {
                "user_id": "u-2",
                "business_type": "議事録要約",
                "what_worked": "transcript summarize",
                "why_worked": "y",
                "reproducibility_score": 0.7,
            },
        ]
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps(seed_data), encoding="utf-8")

        # embed_text を monkeypatch (実 API は呼ばない)
        call_log: list[str] = []

        def fake_embed(text: str) -> list[float]:
            call_log.append(text)
            return [float(len(text))] * 4

        monkeypatch.setattr(embed, "embed_text", fake_embed)

        count = load_success_cases(path=seed_file, with_embeddings=True)
        assert count == 2
        assert len(call_log) == 2
        assert len(_embeddings) == 2

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_success_cases(path=tmp_path / "nonexistent.json")

    def test_invalid_json_root_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text('{"not": "a list"}', encoding="utf-8")
        with pytest.raises(ValueError, match="JSON array"):
            load_success_cases(path=bad)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        seed_data = [{"user_id": "u-1", "business_type": "x"}]  # 他フィールド欠落
        bad = tmp_path / "missing.json"
        bad.write_text(json.dumps(seed_data), encoding="utf-8")
        with pytest.raises(ValueError, match="missing required fields"):
            load_success_cases(path=bad)


class TestCosineSimilarity:
    def test_identical_vectors_returns_one(self) -> None:
        v = [1.0, 2.0, 3.0]
        assert cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors_returns_zero(self) -> None:
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors_returns_negative(self) -> None:
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_zero_vector_returns_zero(self) -> None:
        assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0

    def test_mismatched_length_returns_zero(self) -> None:
        assert cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0


class TestSemanticSearchEmbeddingMode:
    def test_uses_embedding_when_registered(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        seed_data = [
            {
                "user_id": "u-a",
                "business_type": "月次レポート",
                "what_worked": "copilot で雛形生成",
                "why_worked": "x",
                "reproducibility_score": 0.8,
            },
            {
                "user_id": "u-b",
                "business_type": "議事録要約",
                "what_worked": "transcript を要約",
                "why_worked": "y",
                "reproducibility_score": 0.7,
            },
        ]
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps(seed_data), encoding="utf-8")

        # embed_text: テキストに応じて異なるベクトルを返す
        def fake_embed(text: str) -> list[float]:
            if "月次" in text:
                return [1.0, 0.0, 0.0]
            if "議事録" in text:
                return [0.0, 1.0, 0.0]
            return [0.5, 0.5, 0.0]

        monkeypatch.setattr(embed, "embed_text", fake_embed)
        # search_query は import 時に embed.embed_text を直接 import しているため両方差し替え
        monkeypatch.setattr(search_query, "embed_text", fake_embed)

        load_success_cases(path=seed_file, with_embeddings=True)
        assert len(_embeddings) == 2

        hits = semantic_search("月次レポートで困っています", top_k=2)
        assert len(hits) >= 1
        # 月次レポートのケースが先頭
        top_case_business = _success_cases[hits[0].case_id]["business_type"]
        assert top_case_business == "月次レポート"

    def test_fallback_to_string_match_when_no_embeddings(self) -> None:
        # embeddings 未登録の場合は文字列マッチへフォールバック
        from src.tools.cosmos_io import SuccessCase, seed_success_case

        seed_success_case(
            SuccessCase(
                user_id="u-1",
                business_type="月次レポート",
                what_worked="copilot",
                why_worked="x",
                reproducibility_score=0.5,
            )
        )

        hits = semantic_search("月次レポートで困っている")
        assert len(hits) == 1

    def test_fallback_on_embedding_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        seed_data = [
            {
                "user_id": "u-1",
                "business_type": "月次レポート",
                "what_worked": "copilot",
                "why_worked": "x",
                "reproducibility_score": 0.5,
            }
        ]
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps(seed_data), encoding="utf-8")

        # seed 時の embedding はモックで成功させる
        monkeypatch.setattr(embed, "embed_text", lambda t: [1.0, 0.0])

        load_success_cases(path=seed_file, with_embeddings=True)

        # 検索時に embed が失敗するよう差し替え
        def fail_embed(text: str) -> list[float]:
            raise RuntimeError("simulated Azure failure")

        monkeypatch.setattr(search_query, "embed_text", fail_embed)

        # 文字列マッチへフォールバックして空でない結果が返る
        hits = semantic_search("月次レポートで困っている")
        assert len(hits) >= 1


class TestEnrichedFields:
    """SuccessCase の新フィールド (owner_label / concrete_prompt / quantitative_effect) のテスト。"""

    def test_load_with_enriched_fields(self, tmp_path: Path) -> None:
        seed_data = [
            {
                "user_id": "u-sato",
                "business_type": "月次レポート作成",
                "what_worked": "Copilot で雛形生成",
                "why_worked": "テンプレ化が効いた",
                "reproducibility_score": 0.9,
                "owner_label": "営業部 佐藤さん",
                "concrete_prompt": "添付の Excel から...",
                "quantitative_effect": "月 8h → 2.5h",
            }
        ]
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps(seed_data), encoding="utf-8")

        load_success_cases(path=seed_file, with_embeddings=False)

        assert len(_success_cases) == 1
        case_id = next(iter(_success_cases.keys()))
        case = _success_cases[case_id]
        assert case["owner_label"] == "営業部 佐藤さん"
        assert case["concrete_prompt"].startswith("添付の Excel")
        assert case["quantitative_effect"] == "月 8h → 2.5h"

    def test_load_without_enriched_fields_uses_defaults(self, tmp_path: Path) -> None:
        seed_data = [
            {
                "user_id": "u-old",
                "business_type": "x",
                "what_worked": "y",
                "why_worked": "z",
                "reproducibility_score": 0.5,
            }
        ]
        seed_file = tmp_path / "seed.json"
        seed_file.write_text(json.dumps(seed_data), encoding="utf-8")

        load_success_cases(path=seed_file, with_embeddings=False)
        case = next(iter(_success_cases.values()))
        assert case["owner_label"] == ""
        assert case["concrete_prompt"] == ""
        assert case["quantitative_effect"] == ""


class TestExcludeUserId:
    """対象ユーザー本人の事例を除外する機能のテスト。"""

    def test_excludes_specified_user(self) -> None:
        from src.tools.cosmos_io import SuccessCase, seed_success_case

        seed_success_case(
            SuccessCase(
                user_id="u-takahashi",
                business_type="経費精算",
                what_worked="copilot",
                why_worked="x",
                reproducibility_score=0.9,
            )
        )
        seed_success_case(
            SuccessCase(
                user_id="u-other",
                business_type="経費精算",
                what_worked="copilot",
                why_worked="y",
                reproducibility_score=0.5,
            )
        )

        # exclude しない場合は両方ヒット
        all_hits = semantic_search("経費精算で困っている")
        all_user_ids = {_success_cases[h.case_id]["user_id"] for h in all_hits}
        assert "u-takahashi" in all_user_ids

        # u-takahashi を除外
        filtered = semantic_search("経費精算で困っている", exclude_user_id="u-takahashi")
        filtered_user_ids = {_success_cases[h.case_id]["user_id"] for h in filtered}
        assert "u-takahashi" not in filtered_user_ids
        assert "u-other" in filtered_user_ids


class TestScoringWeights:
    """業務種別ボーナスと再現可能性重みのテスト。"""

    def test_business_type_bonus_lifts_matching_case(self) -> None:
        from src.tools.cosmos_io import SuccessCase, seed_success_case

        # business_type 不一致だが reproducibility 高い
        seed_success_case(
            SuccessCase(
                user_id="u-x",
                business_type="議事録要約",
                what_worked="経費精算",  # what_worked にだけ「経費精算」を含めて文字列マッチさせる
                why_worked="y",
                reproducibility_score=0.95,
            )
        )
        # business_type 一致 (低 reproducibility)
        seed_success_case(
            SuccessCase(
                user_id="u-y",
                business_type="経費精算",
                what_worked="領収書 OCR",
                why_worked="x",
                reproducibility_score=0.4,
            )
        )

        # 「経費精算」を含むクエリでは business_type 一致 (u-y) が上位に来る期待
        hits = semantic_search("経費精算チェックで困っている")
        assert len(hits) >= 1
        top_user = _success_cases[hits[0].case_id]["user_id"]
        assert top_user == "u-y", (
            f"business_type 一致 u-y が上位のはず: {[h.case_id for h in hits]}"
        )

    def test_reproducibility_affects_ordering(self) -> None:
        from src.tools.cosmos_io import SuccessCase, seed_success_case

        # 同じ business_type / 同じマッチ度、reproducibility のみ違い
        high = SuccessCase(
            user_id="u-high",
            business_type="月次レポート",
            what_worked="月次レポート copilot",
            why_worked="x",
            reproducibility_score=0.95,
        )
        low = SuccessCase(
            user_id="u-low",
            business_type="月次レポート",
            what_worked="月次レポート copilot",
            why_worked="y",
            reproducibility_score=0.10,
        )
        seed_success_case(high)
        seed_success_case(low)

        hits = semantic_search("月次レポートで困っている")
        # 高 reproducibility が上位
        assert hits[0].case_id == high.id
