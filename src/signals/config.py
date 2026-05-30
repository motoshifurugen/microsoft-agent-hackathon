"""Slack 連携用の独立した設定ローダー。

Azure 用の src/config.py:load_settings() とは混ぜない。Slack env が無くても
Web (FastAPI) は起動できるようにし、Slack env が揃っているときだけ Bot を有効化する。
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# 対象チャネルの表示名 (Slack のメッセージイベントにはチャネル名が含まれないため固定)。
DEFAULT_CHANNEL_NAME = "はてなボックス"
DEFAULT_KODAMA_BASE_URL = "http://localhost:8000"


@dataclass(frozen=True)
class SlackConfig:
    """Slack Socket Mode に必要な設定。"""

    bot_token: str
    app_token: str
    channel_id: str
    channel_name: str
    kodama_base_url: str

    @property
    def enabled(self) -> bool:
        """Bot を起動できる最小限の env が揃っているか。"""
        return bool(self.bot_token and self.app_token and self.channel_id)


def load_slack_config() -> SlackConfig:
    """環境変数から Slack 設定を読み込む (欠落していても例外は投げない)。

    KODAMA_BASE_URL は Slack 無効時でも /api/slack/mock が使うため常に解決する。
    """
    return SlackConfig(
        bot_token=os.environ.get("SLACK_BOT_TOKEN", "").strip(),
        app_token=os.environ.get("SLACK_APP_TOKEN", "").strip(),
        channel_id=os.environ.get("SLACK_HATENA_CHANNEL_ID", "").strip(),
        channel_name=os.environ.get("SLACK_HATENA_CHANNEL_NAME", DEFAULT_CHANNEL_NAME).strip(),
        kodama_base_url=os.environ.get("KODAMA_BASE_URL", DEFAULT_KODAMA_BASE_URL).strip()
        or DEFAULT_KODAMA_BASE_URL,
    )
