"""Kodama dashboard 用 FastAPI アプリケーション。

社員モード (Home / カテゴリ閲覧) と管理者モード (メンバー支援 / 戦略実行) の
両方を 1 つの FastAPI に同居させる。Chainlit (src/app.py) とは独立して動作する。

エンドポイント概要:
- /api/health                        ヘルスチェック
- /api/categories                    カテゴリ一覧 (社員)
- /api/categories/{name}/cases       カテゴリ別事例 (社員)
- /api/today                         今日のおすすめ (社員)
- /api/pain/match                     困りごと入力 → 類似事例マッチング (社員)
- /api/bookmarks                      Skill ブックマーク GET/POST/DELETE (社員)
- /api/cases                          成功事例の登録 POST (社員)
- /api/admin/users                   メンバー一覧 (管理者)
- /api/admin/users/{id}/recommendations  推薦事例 + 戦略 A/B (管理者)
- /api/admin/strategies/{id}/execute 戦略実行プレビュー (管理者)
- /api/admin/executions              実行履歴 (管理者)

設計方針:
- データ層 (src/tools/) は Chainlit と共通
- 起動時に load_success_cases(with_embeddings=True) で in-memory に投入
- フロント (frontend/) とは CORS で接続
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.admin import router as admin_router
from src.api.board import router as board_router
from src.api.board import seed_sample_board
from src.api.bookmarks import router as bookmarks_router
from src.api.cases import router as cases_router
from src.api.employee import router as employee_router
from src.api.pain import router as pain_router
from src.tools.cosmos_io import reset_in_memory_stores
from src.tools.seed import load_success_cases

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    """起動時に in-memory store へダミー成功事例 + embedding を投入。

    uvicorn --reload で複数回呼ばれても冪等になるよう、毎回 store をクリアしてから load する。
    """
    reset_in_memory_stores()

    try:
        count = load_success_cases(with_embeddings=True)
        _logger.info("seeded %d success cases with embeddings", count)
    except Exception as exc:
        # embedding 失敗時、部分 load された state を捨ててから fallback で全件再 load
        _logger.warning("embedding seed failed, retrying without embeddings: %s", exc)
        reset_in_memory_stores()
        count = load_success_cases(with_embeddings=False)
        _logger.info("seeded %d success cases (no embeddings)", count)

    # 掲示板にサンプル質問を投入 (空表示を避けるため)
    seed_sample_board()

    yield


app = FastAPI(
    title="Kodama Dashboard API",
    description="社内の小さな成功を、次の誰かの力に",
    version="0.3.0",
    lifespan=_lifespan,
)

# CORS は開発時は緩める。本番では origin を絞ること
_cors_origins = os.environ.get("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "kodama"}


app.include_router(employee_router)
app.include_router(admin_router)
app.include_router(board_router)
app.include_router(pain_router)
app.include_router(bookmarks_router)
app.include_router(cases_router)

# Vite ビルド成果物 (frontend/dist) を静的配信。Container では /app/frontend_dist にコピーされる前提。
# ローカルでは frontend/dist ディレクトリがあれば配信、無ければ Vite dev server を別途使う。
_STATIC_CANDIDATES = (
    Path(__file__).resolve().parents[2] / "frontend_dist",
    Path(__file__).resolve().parents[2] / "frontend" / "dist",
)
_static_dir = next((p for p in _STATIC_CANDIDATES if p.exists()), None)
if _static_dir is not None:
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
    _logger.info("serving static frontend from %s", _static_dir)
else:
    _logger.info("no static frontend found; API-only mode (use Vite dev server for UI)")
