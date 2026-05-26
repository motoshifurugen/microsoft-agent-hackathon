"""Azure credential のヘルパー。

ローカル開発 (az login) と Container Apps (Managed Identity) の両方で
動く DefaultAzureCredential を構成する。Container 内では Azure CLI が
存在しないため CLI クレデンシャルを除外する (DefaultAzureCredential の
チェーン挙動で例外が伝播するのを防ぐ)。
"""

from __future__ import annotations

import os

from azure.identity import DefaultAzureCredential


def _is_running_in_container_apps() -> bool:
    """Container Apps 上で実行中かを判定する。

    Container Apps は CONTAINER_APP_NAME / CONTAINER_APP_HOSTNAME を自動設定する。
    """
    return bool(os.environ.get("CONTAINER_APP_NAME") or os.environ.get("CONTAINER_APP_HOSTNAME"))


def get_default_credential() -> DefaultAzureCredential:
    """ローカル / Container Apps の両方で動く credential を返す。

    Container 内では CLI クレデンシャルを除外し、Managed Identity を使う。
    ローカルでは az login の CLI クレデンシャルを含めて全 chain を試す。
    """
    return DefaultAzureCredential(exclude_cli_credential=_is_running_in_container_apps())
