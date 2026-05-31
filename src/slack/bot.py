"""Slack Socket Mode Bot。`#はてなボックス` の投稿を検知し、スレッド返信する。

実装方式は Socket Mode (公開 HTTP endpoint 不要)。AsyncApp + AsyncSocketModeHandler を使い、
FastAPI の lifespan からバックグラウンドタスクとして起動する想定 (src/api/main.py)。

必要な Bot Token Scopes (最小):
- channels:history  (対象チャネルの message イベント受信)
- chat:write        (スレッド返信)
※ チャネル ID を固定指定するため channels:read は不要。app_mentions は使わない。
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from src.signals.classify import build_reply
from src.signals.config import SlackConfig
from src.signals.service import handle_message
from src.slack.filters import is_target_message

if TYPE_CHECKING:
    from slack_bolt.async_app import AsyncApp

_logger = logging.getLogger(__name__)


async def process_event(
    event: dict,
    *,
    config: SlackConfig,
    say: Callable[..., Awaitable[object]],
    bot_user_id: str | None,
    logger: logging.Logger | None = None,
) -> None:
    """1 件の message イベントを処理する (フィルタ → 分類 → スレッド返信)。

    Slack SDK から切り離してテストできるよう、listener 本体をここに抽出している。
    """
    log = logger or _logger
    if not is_target_message(event, target_channel_id=config.channel_id, bot_user_id=bot_user_id):
        log.debug("ignored message: channel=%s ts=%s", event.get("channel"), event.get("ts"))
        return

    ts = event.get("ts", "")
    log.info("received message in #%s ts=%s", config.channel_name, ts)

    signal = handle_message(
        channel_id=event.get("channel", ""),
        channel_name=config.channel_name,
        slack_user_id=event.get("user", ""),
        display_name="",  # message イベントに表示名は含まれない (scope 最小化のため解決しない)
        text=event.get("text", ""),
        ts=ts,
        base_url=config.kodama_base_url,
    )
    if signal is None:
        log.info("classified as out-of-scope, ignored: ts=%s", ts)
        return

    log.info("classified as '%s' (signal=%s)", signal.business_category, signal.id)
    try:
        await say(text=build_reply(signal.business_category, signal.kodama_url), thread_ts=ts)
        log.info("replied in thread: ts=%s", ts)
    except Exception:
        log.exception("failed to post Slack reply: ts=%s", ts)


def build_app(config: SlackConfig) -> AsyncApp:
    """AsyncApp を構築し、message ハンドラを登録して返す。

    slack_bolt は任意依存のため、関数内で遅延 import する (env 無効時に import しない)。
    """
    from slack_bolt.async_app import AsyncApp

    app = AsyncApp(token=config.bot_token)

    # 引数 (event/say/context/logger) は slack_bolt が名前で動的に注入するため型注釈は付けない。
    @app.event("message")
    async def _on_message(event, say, context, logger):
        await process_event(
            event,
            config=config,
            say=say,
            bot_user_id=context.get("bot_user_id"),
            logger=logger,
        )

    return app


async def run_slack_bot(config: SlackConfig) -> None:
    """Socket Mode 接続を開始し、切断されるまで常駐する。

    呼び出し側 (lifespan) で asyncio.create_task し、shutdown で cancel する想定。
    """
    from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

    _logger.info("starting Slack Socket Mode bot for channel %s", config.channel_id)
    app = build_app(config)
    handler = AsyncSocketModeHandler(app, config.app_token)
    await handler.start_async()
