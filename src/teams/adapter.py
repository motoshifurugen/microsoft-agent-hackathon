"""Bot Framework Activity → 支援候補シグナルへの変換アダプタ (純粋関数)。

Azure Bot Service / Teams は、ユーザー発話を Bot Framework Activity という JSON で
Bot の messaging endpoint に POST する。本モジュールはその Activity から本文・発話者を
取り出し、Slack と共通の `handle_message` (source="teams") に渡す。返信は Teams ネイティブな
Adaptive Card を含む outbound Activity として組み立てる。

注意 (MVP の割り切り):
- Bot Framework の JWT (Authorization ヘッダ) 検証は本番要件。ここでは未実装で、
  endpoint 側の責務とする (src/api/teams.py のドキュメント参照)。
- 本番では返信を Connector API (activity.serviceUrl) へ POST する。MVP では
  組み立てた Activity を HTTP レスポンスで返し、検証とデモを可能にする。
- Signal.slack_user_id フィールドは Teams では発話者の AAD ユーザー ID を保持する
  (フィールド名は Slack 由来だが、検知元は source="teams" で区別する)。
"""

from __future__ import annotations

from dataclasses import dataclass

from src.signals.classify import build_reply
from src.signals.service import handle_message
from src.signals.store import Signal

SOURCE = "teams"
DEFAULT_CHANNEL_NAME = "Teams 相談"


@dataclass(frozen=True)
class TeamsMessage:
    """Activity から取り出した、検知に必要な最小限の発話情報。"""

    text: str
    user_id: str
    display_name: str
    conversation_id: str
    activity_id: str
    channel_name: str


def is_target_activity(activity: dict) -> bool:
    """Activity を検知対象にするか判定する。

    対象は本文のある message タイプのユーザー発話のみ。以下は無視する:
    - message 以外のタイプ (typing / conversationUpdate 等)
    - Bot 自身の発話 (from.role == "bot")
    - 本文が空
    """
    if activity.get("type") != "message":
        return False
    sender = activity.get("from") or {}
    if str(sender.get("role", "")).lower() == "bot":
        return False
    return bool(str(activity.get("text", "")).strip())


def extract_message(activity: dict) -> TeamsMessage | None:
    """Activity から TeamsMessage を取り出す。対象外なら None。"""
    if not is_target_activity(activity):
        return None

    sender = activity.get("from") or {}
    conversation = activity.get("conversation") or {}
    channel_name = str(conversation.get("name", "")).strip() or DEFAULT_CHANNEL_NAME
    return TeamsMessage(
        text=str(activity.get("text", "")).strip(),
        user_id=str(sender.get("id", "")),
        display_name=str(sender.get("name", "")),
        conversation_id=str(conversation.get("id", "")),
        activity_id=str(activity.get("id", "")),
        channel_name=channel_name,
    )


def detect_from_activity(activity: dict, *, base_url: str) -> Signal | None:
    """Activity を分類し、支援候補なら Signal として保存して返す。対象外/無関係なら None。

    同一 (conversation_id, activity_id) の重複配信は既存シグナルを返す (Bot Framework は
    再送しうるため)。activity_id が空の Activity は dedup できないため毎回新規登録になる。
    """
    msg = extract_message(activity)
    if msg is None:
        return None

    return handle_message(
        channel_id=msg.conversation_id,
        channel_name=msg.channel_name,
        slack_user_id=msg.user_id,
        display_name=msg.display_name,
        text=msg.text,
        ts=msg.activity_id,
        base_url=base_url,
        source=SOURCE,
    )


def build_reply_activity(category: str, kodama_url: str) -> dict:
    """Teams へ返す outbound Activity を組み立てる。

    text はカード非対応クライアント向けのフォールバック、attachments は Teams ネイティブな
    Adaptive Card (本文 + Kodama を開くボタン)。
    """
    return {
        "type": "message",
        "text": build_reply(category, kodama_url),
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"その“はてな”、{category}に近そうです",
                            "weight": "Bolder",
                            "wrap": True,
                        },
                        {
                            "type": "TextBlock",
                            "text": "近い成功事例とすぐ使えるプロンプトを Kodama にまとめています。",
                            "wrap": True,
                            "isSubtle": True,
                        },
                    ],
                    "actions": [
                        {"type": "Action.OpenUrl", "title": "Kodama で見る", "url": kodama_url}
                    ],
                },
            }
        ],
    }
