"""FastAPI ベースの REST API (ダッシュボード UI の backend)。

Chainlit (src/app.py) と独立して動作する HTTP API を提供する。
データ層 (src/tools/) は両者で共有する。
"""

from __future__ import annotations
