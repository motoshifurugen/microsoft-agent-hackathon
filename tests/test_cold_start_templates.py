"""Cold Start テンプレートのローダーと in-memory store の単体テスト。

Azure 接続不要。cosmos_io の template store と seed.py のローダー関数を検証する。
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from src.tools.cosmos_io import (
    ColdStartTemplate,
    get_cold_start_templates,
    seed_cold_start_template,
)
from src.tools.seed import load_cold_start_templates


@pytest.fixture(autouse=True)
def _reset_template_store() -> Iterator[None]:
    """各テストで in-memory template store をクリア。"""
    get_cold_start_templates().clear()
    yield
    get_cold_start_templates().clear()


class TestColdStartTemplateDataclass:
    def test_required_fields_stored(self) -> None:
        tpl = ColdStartTemplate(
            business_category="月次レポート作成",
            title="月次レポート作成テンプレート",
            description="月次レポートのたたき台を作るテンプレートです。",
            common_pain="毎月同じ形式のレポートを書くのに時間がかかる。",
            prompt="添付の月次データを読み込み、前月比の要点と経営層向けコメントを出力してください。",
            steps=["データを用意する", "プロンプトを実行する", "出力を確認する"],
            suitable_for="毎月同じ形式のレポートを作っている人",
            cautions="個人情報や顧客名はマスキングしてから使ってください。",
            feedback_question="このテンプレートでレポート作成時間は短くなりましたか？",
        )
        assert tpl.business_category == "月次レポート作成"
        assert tpl.title == "月次レポート作成テンプレート"
        assert len(tpl.steps) == 3

    def test_immutable(self) -> None:
        tpl = ColdStartTemplate(
            business_category="テスト",
            title="テスト",
            description="テスト",
            common_pain="テスト",
            prompt="テスト",
            steps=["step1"],
            suitable_for="テスト",
            cautions="テスト",
            feedback_question="テスト？",
        )
        with pytest.raises(AttributeError):
            tpl.business_category = "変更"  # type: ignore[misc]

    def test_id_auto_generated(self) -> None:
        tpl1 = ColdStartTemplate(
            business_category="A",
            title="A",
            description="A",
            common_pain="A",
            prompt="A",
            steps=["s"],
            suitable_for="A",
            cautions="A",
            feedback_question="A?",
        )
        tpl2 = ColdStartTemplate(
            business_category="B",
            title="B",
            description="B",
            common_pain="B",
            prompt="B",
            steps=["s"],
            suitable_for="B",
            cautions="B",
            feedback_question="B?",
        )
        assert tpl1.id != tpl2.id


class TestSeedColdStartTemplate:
    def test_seed_stores_template(self) -> None:
        tpl = ColdStartTemplate(
            business_category="議事録要約",
            title="議事録要約テンプレート",
            description="会議の文字起こしを要約するテンプレートです。",
            common_pain="会議後の議事録まとめに30分以上かかる。",
            prompt="以下の会議文字起こしを、決定事項・アクションアイテム・宿題の3セクションで整理してください。",
            steps=["文字起こしを用意する", "プロンプトを実行する", "結果を確認する"],
            suitable_for="会議の議事録を毎回手作業でまとめている人",
            cautions="参加者の個人名が含まれる場合は共有前に確認してください。",
            feedback_question="議事録作成の時間は短くなりましたか？",
        )
        returned_id = seed_cold_start_template(tpl)
        assert returned_id == tpl.id

        store = get_cold_start_templates()
        assert tpl.id in store
        assert store[tpl.id]["business_category"] == "議事録要約"

    def test_multiple_templates_stored(self) -> None:
        categories = ["月次レポート作成", "議事録要約", "メール作成"]
        for cat in categories:
            seed_cold_start_template(
                ColdStartTemplate(
                    business_category=cat,
                    title=f"{cat}テンプレート",
                    description="説明",
                    common_pain="困りごと",
                    prompt="プロンプト",
                    steps=["step1", "step2"],
                    suitable_for="向いている人",
                    cautions="注意点",
                    feedback_question="フィードバック？",
                )
            )
        assert len(get_cold_start_templates()) == 3


class TestLoadColdStartTemplates:
    def test_loads_from_json_file(self, tmp_path: Path) -> None:
        template_data = [
            {
                "business_category": "月次レポート作成",
                "title": "月次レポート作成テンプレート",
                "description": "月次レポートのたたき台を作るテンプレートです。",
                "common_pain": "毎月同じ形式のレポートを書くのに時間がかかる。",
                "prompt": "添付の月次データを読み込み、前月比の要点を出力してください。",
                "steps": ["データを用意する", "プロンプトを実行する", "出力を確認する"],
                "suitable_for": "毎月同じ形式のレポートを作っている人",
                "cautions": "個人情報はマスキングしてください。",
                "feedback_question": "時間は短くなりましたか？",
            }
        ]
        tpl_file = tmp_path / "cold_start_templates.json"
        tpl_file.write_text(json.dumps(template_data, ensure_ascii=False), encoding="utf-8")

        count = load_cold_start_templates(path=tpl_file)
        assert count == 1
        assert len(get_cold_start_templates()) == 1

    def test_loads_multiple_templates(self, tmp_path: Path) -> None:
        template_data = [
            {
                "business_category": cat,
                "title": f"{cat}テンプレート",
                "description": "説明",
                "common_pain": "困りごと",
                "prompt": "プロンプト",
                "steps": ["step1"],
                "suitable_for": "向いている人",
                "cautions": "注意点",
                "feedback_question": "？",
            }
            for cat in ["月次レポート作成", "議事録要約", "メール作成"]
        ]
        tpl_file = tmp_path / "templates.json"
        tpl_file.write_text(json.dumps(template_data, ensure_ascii=False), encoding="utf-8")

        count = load_cold_start_templates(path=tpl_file)
        assert count == 3
        assert len(get_cold_start_templates()) == 3

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_cold_start_templates(path=tmp_path / "nonexistent.json")

    def test_invalid_json_root_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text('{"not": "a list"}', encoding="utf-8")
        with pytest.raises(ValueError, match="JSON array"):
            load_cold_start_templates(path=bad)

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        bad_data = [{"business_category": "月次レポート作成"}]  # 他フィールド欠落
        bad = tmp_path / "missing.json"
        bad.write_text(json.dumps(bad_data), encoding="utf-8")
        with pytest.raises(ValueError, match="missing required fields"):
            load_cold_start_templates(path=bad)

    def test_loads_default_seed_file(self) -> None:
        """デフォルトの cold_start_templates.json が読み込めること。"""
        count = load_cold_start_templates()
        assert count >= 4
        assert len(get_cold_start_templates()) == count

    def test_steps_stored_as_list(self, tmp_path: Path) -> None:
        template_data = [
            {
                "business_category": "メール作成",
                "title": "メール作成テンプレート",
                "description": "説明",
                "common_pain": "困りごと",
                "prompt": "プロンプト",
                "steps": ["step1", "step2", "step3"],
                "suitable_for": "向いている人",
                "cautions": "注意点",
                "feedback_question": "？",
            }
        ]
        tpl_file = tmp_path / "templates.json"
        tpl_file.write_text(json.dumps(template_data, ensure_ascii=False), encoding="utf-8")

        load_cold_start_templates(path=tpl_file)
        store = get_cold_start_templates()
        assert len(store) == 1
        tpl = next(iter(store.values()))
        assert isinstance(tpl["steps"], list)
        assert len(tpl["steps"]) == 3
