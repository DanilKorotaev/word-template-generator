from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Word Template Generator")
    static_dir = Path(__file__).parent / "static"

    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(router)

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (static_dir / "index.html").read_text(encoding="utf-8")

    return app

