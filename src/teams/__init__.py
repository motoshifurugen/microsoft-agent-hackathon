"""Microsoft Teams 連携 (Bot Framework Activity アダプタ)。

Slack「はてなボックス」と対称の受動検知を Teams 上でも成立させる。
Azure Bot Service が POST する Bot Framework Activity を解釈し、共通の
検知サービス (src/signals/service.py) に橋渡しする薄いアダプタ。
"""
