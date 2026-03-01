from __future__ import annotations

from pathlib import Path
import socket
import subprocess
import sys
import threading
import webbrowser

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from .generator import build_one, load_workspace


class WorkspacePayload(BaseModel):
    workspace: str


class BuildOnePayload(BaseModel):
    workspace: str
    act: str


def _pick_workspace_native() -> str | None:
    if sys.platform == "darwin":
        script = 'POSIX path of (choose folder with prompt "Выберите папку workspace проекта")'
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    if sys.platform.startswith("win"):
        powershell_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$d=New-Object System.Windows.Forms.FolderBrowserDialog; "
            "$d.Description='Выберите папку workspace проекта'; "
            "$r=$d.ShowDialog(); "
            "if ($r -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $d.SelectedPath }"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", powershell_script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            selected = proc.stdout.strip()
            return selected or None
        return None

    return None


def _html() -> str:
    return """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Word Template Generator</title>
  <style>
    body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background: #f4f6f8; }
    .wrap { max-width: 980px; margin: 24px auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px; }
    .row { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
    input, select, button, textarea { font: inherit; }
    input, select { padding: 8px; border: 1px solid #cfd4dc; border-radius: 8px; }
    button { padding: 8px 12px; border: 0; border-radius: 8px; background: #0b769f; color: #fff; cursor: pointer; }
    button.secondary { background: #64748b; }
    button:disabled { opacity: 0.6; cursor: not-allowed; }
    .grow { flex: 1; }
    textarea { width: 100%; min-height: 260px; border: 1px solid #cfd4dc; border-radius: 8px; padding: 8px; }
    .hint { color: #475569; font-size: 13px; margin-bottom: 10px; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; margin-bottom: 12px; background: #fafafa; }
    .muted { color: #64748b; font-size: 12px; }
  </style>
</head>
<body>
  <div class="wrap">
    <h2 style="margin-top: 0;">Word Template Generator</h2>
    <div class="hint">Локальный режим: укажите путь к workspace на этом компьютере.</div>

    <div class="row">
      <input id="workspace" class="grow" placeholder="/путь/к/workspace" />
      <button class="secondary" onclick="pickFolder()">Выбрать папку...</button>
      <button class="secondary" onclick="loadActs()">Загрузить акты</button>
      <button class="secondary" onclick="validateWs()">Проверить</button>
    </div>

    <div class="card">
      <div class="row" style="margin-bottom: 6px;">
        <strong>Недавние проекты</strong>
      </div>
      <div class="row">
        <select id="recent" class="grow"></select>
        <button class="secondary" onclick="useRecent()">Использовать</button>
        <button class="secondary" onclick="removeRecent()">Удалить</button>
        <button class="secondary" onclick="clearRecent()">Очистить все</button>
      </div>
      <div class="muted">Пути сохраняются только в этом браузере (localStorage).</div>
    </div>

    <div class="row">
      <button onclick="buildAll()">Сгенерировать все</button>
      <select id="acts" class="grow"></select>
      <button onclick="buildOne()">Сгенерировать выбранный</button>
    </div>

    <textarea id="log" readonly></textarea>
  </div>

  <script>
    const RECENT_KEY = 'word_template_generator.recent_workspaces.v1';
    const RECENT_MAX = 8;

    function log(line) {
      const el = document.getElementById('log');
      el.value += line + "\\n";
      el.scrollTop = el.scrollHeight;
    }

    function ws() {
      return document.getElementById('workspace').value.trim();
    }

    function readRecent() {
      try {
        const raw = localStorage.getItem(RECENT_KEY);
        if (!raw) return [];
        const data = JSON.parse(raw);
        if (!Array.isArray(data)) return [];
        return data.filter(item => item && typeof item.path === 'string');
      } catch {
        return [];
      }
    }

    function writeRecent(items) {
      localStorage.setItem(RECENT_KEY, JSON.stringify(items.slice(0, RECENT_MAX)));
    }

    function renderRecent() {
      const sel = document.getElementById('recent');
      const items = readRecent();
      sel.innerHTML = '';
      if (!items.length) {
        const opt = document.createElement('option');
        opt.value = '';
        opt.textContent = 'Недавних проектов пока нет';
        sel.appendChild(opt);
        return;
      }
      for (const item of items) {
        const opt = document.createElement('option');
        opt.value = item.path;
        const time = item.lastUsed ? (' [' + new Date(item.lastUsed).toLocaleString() + ']') : '';
        opt.textContent = item.path + time;
        sel.appendChild(opt);
      }
    }

    function rememberWorkspace(pathValue) {
      const path = (pathValue || '').trim();
      if (!path) return;
      const now = Date.now();
      const items = readRecent().filter(item => item.path !== path);
      items.unshift({ path, lastUsed: now });
      writeRecent(items);
      renderRecent();
    }

    function useRecent() {
      const selected = document.getElementById('recent').value;
      if (!selected) {
        log('[ERR] Выберите проект из списка.');
        return;
      }
      document.getElementById('workspace').value = selected;
      log('[OK] Выбран проект: ' + selected);
      loadActs();
    }

    function removeRecent() {
      const selected = document.getElementById('recent').value;
      if (!selected) {
        log('[ERR] Нечего удалять.');
        return;
      }
      const items = readRecent().filter(item => item.path !== selected);
      writeRecent(items);
      renderRecent();
      log('[OK] Проект удален из недавних: ' + selected);
    }

    function clearRecent() {
      localStorage.removeItem(RECENT_KEY);
      renderRecent();
      log('[OK] Список недавних проектов очищен.');
    }

    function hydrateFromStorage() {
      renderRecent();
      const items = readRecent();
      if (!items.length) return;
      const last = items[0].path;
      document.getElementById('workspace').value = last;
      log('[OK] Восстановлен последний workspace: ' + last);
    }

    async function pickFolder() {
      const res = await fetch('/api/pick-workspace', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) { log('[ERR] ' + (data.detail || 'Не удалось выбрать папку')); return; }
      if (!data.workspace) { log('[ERR] Папка не была выбрана.'); return; }
      document.getElementById('workspace').value = data.workspace;
      rememberWorkspace(data.workspace);
      log('[OK] Папка выбрана: ' + data.workspace);
      await loadActs();
    }

    async function loadActs() {
      const workspace = ws();
      if (!workspace) { log('[ERR] Укажите путь к workspace.'); return; }
      const url = '/api/acts?workspace=' + encodeURIComponent(workspace);
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) { log('[ERR] ' + (data.detail || 'Не удалось загрузить акты')); return; }

      const sel = document.getElementById('acts');
      sel.innerHTML = '';
      for (const name of data.acts) {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        sel.appendChild(opt);
      }
      rememberWorkspace(workspace);
      log('[OK] Загружено актов: ' + data.acts.length);
    }

    async function validateWs() {
      const workspace = ws();
      if (!workspace) { log('[ERR] Укажите путь к workspace.'); return; }
      const res = await fetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace })
      });
      const data = await res.json();
      if (!res.ok) { log('[ERR] ' + (data.detail || 'Проверка завершилась с ошибкой')); return; }
      rememberWorkspace(workspace);
      for (const line of data.log) log(line);
    }

    async function buildAll() {
      const workspace = ws();
      if (!workspace) { log('[ERR] Укажите путь к workspace.'); return; }
      const res = await fetch('/api/build-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace })
      });
      const data = await res.json();
      if (!res.ok) { log('[ERR] ' + (data.detail || 'Генерация завершилась с ошибкой')); return; }
      rememberWorkspace(workspace);
      for (const line of data.log) log(line);
      await loadActs();
    }

    async function buildOne() {
      const workspace = ws();
      const act = document.getElementById('acts').value;
      if (!workspace) { log('[ERR] Укажите путь к workspace.'); return; }
      if (!act) { log('[ERR] Выберите акт из списка.'); return; }
      const res = await fetch('/api/build-one', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workspace, act })
      });
      const data = await res.json();
      if (!res.ok) { log('[ERR] ' + (data.detail || 'Генерация завершилась с ошибкой')); return; }
      rememberWorkspace(workspace);
      for (const line of data.log) log(line);
    }

    hydrateFromStorage();
  </script>
</body>
</html>
"""


def _get_app() -> FastAPI:
    app = FastAPI(title="Word Template Generator")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return _html()

    @app.post("/api/pick-workspace")
    def pick_workspace() -> dict[str, str]:
        selected = _pick_workspace_native()
        if not selected:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Нативный выбор папки недоступен в этой системе. "
                    "Введите путь вручную."
                ),
            )
        return {"workspace": selected}

    @app.get("/api/acts")
    def acts(workspace: str) -> dict[str, list[str]]:
        try:
            _, act_files = load_workspace(Path(workspace))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"acts": [p.name for p in act_files]}

    @app.post("/api/validate")
    def validate(payload: WorkspacePayload) -> dict[str, list[str]]:
        try:
            cfg, act_files = load_workspace(Path(payload.workspace))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        log: list[str] = []
        temp_out = cfg.root / ".validation_tmp"
        has_errors = False
        for act_file in act_files:
            try:
                result = build_one(
                    project_data=cfg.project_data,
                    act_file=act_file,
                    templates_dir=cfg.templates_dir,
                    output_dir=temp_out,
                    strict=True,
                )
                if result.output_file.exists():
                    result.output_file.unlink()
                log.append(f"[OK] {act_file.name}")
            except Exception as exc:  # noqa: BLE001
                has_errors = True
                log.append(f"[ERR] {act_file.name}: {exc}")
        if temp_out.exists():
            try:
                temp_out.rmdir()
            except OSError:
                pass
        if has_errors:
            raise HTTPException(status_code=400, detail="Validation errors found. See log.")
        log.append("Workspace is valid.")
        return {"log": log}

    @app.post("/api/build-all")
    def build_all(payload: WorkspacePayload) -> dict[str, list[str]]:
        try:
            cfg, act_files = load_workspace(Path(payload.workspace))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not act_files:
            raise HTTPException(status_code=400, detail="No act markdown files found.")

        log: list[str] = []
        for act_file in act_files:
            try:
                result = build_one(
                    project_data=cfg.project_data,
                    act_file=act_file,
                    templates_dir=cfg.templates_dir,
                    output_dir=cfg.output_dir,
                    strict=True,
                )
                log.append(f"[OK] {result.act_file.name} -> {result.output_file}")
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=400, detail=f"{act_file.name}: {exc}") from exc
        log.append(f"Done. Generated {len(act_files)} file(s).")
        return {"log": log}

    @app.post("/api/build-one")
    def build_one_api(payload: BuildOnePayload) -> dict[str, list[str]]:
        try:
            cfg, act_files = load_workspace(Path(payload.workspace))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        act_file = next((p for p in act_files if p.name == payload.act), None)
        if act_file is None:
            raise HTTPException(status_code=400, detail=f"Act not found: {payload.act}")

        try:
            result = build_one(
                project_data=cfg.project_data,
                act_file=act_file,
                templates_dir=cfg.templates_dir,
                output_dir=cfg.output_dir,
                strict=True,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {"log": [f"[OK] {result.act_file.name} -> {result.output_file}"]}

    return app


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def run_web_ui(host: str = "127.0.0.1", port: int | None = None, open_browser: bool = True) -> None:
    if port is None:
        port = _free_port()
    app = _get_app()
    url = f"http://{host}:{port}"
    if open_browser:
        timer = threading.Timer(0.7, lambda: webbrowser.open(url))
        timer.daemon = True
        timer.start()
    uvicorn.run(app, host=host, port=port, log_level="warning")

