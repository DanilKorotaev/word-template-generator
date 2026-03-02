from __future__ import annotations

import socket
import threading
import webbrowser

import uvicorn

from .app import create_app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _can_bind(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def run_web_ui(host: str = "127.0.0.1", port: int | None = None, open_browser: bool = True) -> None:
    if port is None:
        port = _free_port()
    elif not _can_bind(host, port):
        raise RuntimeError(
            f"Port {port} is already in use. Close previous app instance or run with --port <another-port>."
        )
    app = create_app()
    url = f"http://{host}:{port}"
    if open_browser:
        timer = threading.Timer(0.7, lambda: webbrowser.open(url))
        timer.daemon = True
        timer.start()
    uvicorn.run(app, host=host, port=port, log_level="warning")

