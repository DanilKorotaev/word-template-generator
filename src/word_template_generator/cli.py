from __future__ import annotations

import socket
import webbrowser
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

import typer

from .core import (
    build_one,
    load_project,
    load_workspace,
)

app = typer.Typer(help="Word Template Generator (DOCX from markdown).")


def _can_bind(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
            return True
        except OSError:
            return False


def _is_http_alive(url: str) -> bool:
    try:
        with urlrequest.urlopen(url, timeout=1.2) as response:
            return int(response.status) < 500
    except (urlerror.URLError, TimeoutError, OSError):
        return False


@app.command("build-all")
def build_all(
    project_dir: Path = typer.Option(
        Path("projects/demo"),
        "--project-dir",
        help="Directory with project.md and acts/*.md",
    ),
    templates_dir: Path = typer.Option(
        Path("templates"),
        "--templates-dir",
        help="Directory with .docx templates",
    ),
    output_dir: Path = typer.Option(
        Path("output"),
        "--output-dir",
        help="Directory for generated .docx files",
    ),
    strict: bool = typer.Option(
        True,
        "--strict/--no-strict",
        help="Fail if any template marker is missing in context.",
    ),
) -> None:
    project_data, act_files = load_project(project_dir)
    if not act_files:
        raise typer.BadParameter(f"No act files found in {project_dir / 'acts'}")

    built = 0
    for act_file in act_files:
        result = build_one(
            project_data=project_data,
            act_file=act_file,
            templates_dir=templates_dir,
            output_dir=output_dir,
            strict=strict,
        )
        built += 1
        typer.echo(f"[OK] {result.act_file.name} -> {result.output_file}")
        if result.missing_variables and not strict:
            typer.echo(f"     missing: {', '.join(result.missing_variables)}")

    typer.echo(f"Done. Generated {built} file(s).")


@app.command("build-one")
def build_single(
    act: str = typer.Argument(..., help="Act id (filename stem) or filename .md"),
    project_dir: Path = typer.Option(Path("projects/demo"), "--project-dir"),
    templates_dir: Path = typer.Option(Path("templates"), "--templates-dir"),
    output_dir: Path = typer.Option(Path("output"), "--output-dir"),
    strict: bool = typer.Option(True, "--strict/--no-strict"),
) -> None:
    project_data, _ = load_project(project_dir)

    act_filename = act if act.endswith(".md") else f"{act}.md"
    act_file = project_dir / "acts" / act_filename
    if not act_file.exists():
        raise typer.BadParameter(f"Act not found: {act_file}")

    result = build_one(
        project_data=project_data,
        act_file=act_file,
        templates_dir=templates_dir,
        output_dir=output_dir,
        strict=strict,
    )
    typer.echo(f"[OK] {result.act_file.name} -> {result.output_file}")
    if result.missing_variables and not strict:
        typer.echo(f"     missing: {', '.join(result.missing_variables)}")


@app.command("validate")
def validate(
    project_dir: Path = typer.Option(Path("projects/demo"), "--project-dir"),
    templates_dir: Path = typer.Option(Path("templates"), "--templates-dir"),
) -> None:
    project_data, act_files = load_project(project_dir)
    has_errors = False

    for act_file in act_files:
        try:
            result = build_one(
                project_data=project_data,
                act_file=act_file,
                templates_dir=templates_dir,
                output_dir=Path(".validation_tmp"),
                strict=True,
            )
            if result.output_file.exists():
                result.output_file.unlink()
            typer.echo(f"[OK] {act_file.name}")
        except Exception as exc:  # noqa: BLE001
            has_errors = True
            typer.echo(f"[ERR] {act_file.name}: {exc}")

    temp_dir = Path(".validation_tmp")
    if temp_dir.exists():
        try:
            temp_dir.rmdir()
        except OSError:
            pass

    if has_errors:
        raise typer.Exit(code=1)
    typer.echo("All act files are valid.")


def main() -> None:
    app()


@app.command("ws-build-all")
def ws_build_all(
    workspace_dir: Path = typer.Option(
        ...,
        "--workspace-dir",
        help="Flat doc workspace with template.docx and act markdown files",
    ),
    strict: bool = typer.Option(True, "--strict/--no-strict"),
) -> None:
    cfg, act_files = load_workspace(workspace_dir)
    if not act_files:
        raise typer.BadParameter("No act markdown files found in workspace.")

    built = 0
    for act_file in act_files:
        result = build_one(
            project_data=cfg.project_data,
            act_file=act_file,
            templates_dir=cfg.templates_dir,
            output_dir=cfg.output_dir,
            strict=strict,
        )
        built += 1
        typer.echo(f"[OK] {result.act_file.name} -> {result.output_file}")
    typer.echo(f"Done. Generated {built} file(s).")


@app.command("ws-build-one")
def ws_build_one(
    act: str = typer.Argument(..., help="Act id (stem) or markdown filename"),
    workspace_dir: Path = typer.Option(..., "--workspace-dir"),
    strict: bool = typer.Option(True, "--strict/--no-strict"),
) -> None:
    cfg, _ = load_workspace(workspace_dir)
    act_name = act if act.endswith(".md") else f"{act}.md"
    act_candidates = [
        cfg.acts_dir / act_name,
        cfg.root / act_name,
    ]
    act_file = next((p for p in act_candidates if p.exists()), None)
    if act_file is None:
        raise typer.BadParameter(f"Act file not found for: {act}")

    result = build_one(
        project_data=cfg.project_data,
        act_file=act_file,
        templates_dir=cfg.templates_dir,
        output_dir=cfg.output_dir,
        strict=strict,
    )
    typer.echo(f"[OK] {result.act_file.name} -> {result.output_file}")


@app.command("ws-validate")
def ws_validate(
    workspace_dir: Path = typer.Option(..., "--workspace-dir"),
) -> None:
    cfg, act_files = load_workspace(workspace_dir)
    has_errors = False
    temp_out = cfg.root / ".validation_tmp"

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
            typer.echo(f"[OK] {act_file.name}")
        except Exception as exc:  # noqa: BLE001
            has_errors = True
            typer.echo(f"[ERR] {act_file.name}: {exc}")

    if temp_out.exists():
        try:
            temp_out.rmdir()
        except OSError:
            pass

    if has_errors:
        raise typer.Exit(code=1)
    typer.echo("Workspace is valid.")


@app.command("init-workspace")
def init_workspace(
    workspace_dir: Path = typer.Option(..., "--workspace-dir"),
) -> None:
    workspace_dir.mkdir(parents=True, exist_ok=True)
    readme_file = workspace_dir / "README.md"
    generated_dir = workspace_dir / "generated"
    generated_dir.mkdir(exist_ok=True)

    if not readme_file.exists():
        readme_file.write_text(
            """# Document Workspace

Required files:
- `template.docx` as base template
- one or more act markdown files (`*.md`) in root
  (or use `acts/*.md` folder variant)

Generated files go to `generated/`.

Optional:
- `project.md` with shared defaults (fields/template)
""",
            encoding="utf-8",
        )

    typer.echo(f"[OK] Workspace initialized: {workspace_dir}")
    typer.echo("[NEXT] Put your template into template.docx and add act markdown files.")


@app.command("ui")
def launch_ui() -> None:
    try:
        from .desktop.tk_app import run_ui

        run_ui()
    except RuntimeError as exc:
        typer.echo(f"[ERR] {exc}")
        typer.echo("[TIP] macOS: install python.org Python or Homebrew python-tk package for your Python version.")
        typer.echo("[TIP] You can continue with CLI: ws-build-all / ws-build-one.")
        raise typer.Exit(code=1)


@app.command("web-ui")
def launch_web_ui(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8090, "--port", help="Port for local Web UI (default: 8090)"),
    no_open: bool = typer.Option(False, "--no-open", help="Do not auto-open browser"),
) -> None:
    try:
        from .web.server import run_web_ui
    except ModuleNotFoundError as exc:
        typer.echo("[ERR] Web UI dependencies are missing.")
        typer.echo("[TIP] Reinstall project: pip install -e .")
        raise typer.Exit(code=1) from exc

    typer.echo("[INFO] Web UI запускается в local-first режиме.")
    typer.echo("[INFO] Workspace должен быть доступен на том же компьютере, где запущен Python.")
    url = f"http://{host}:{port}"
    if not _can_bind(host, port):
        if _is_http_alive(url):
            typer.echo(f"[OK] Web UI уже запущен: {url}")
            if not no_open:
                webbrowser.open(url)
            return
        typer.echo(f"[ERR] Port {port} is already in use.")
        typer.echo("[TIP] Close conflicting process or run with --port <another-port>.")
        raise typer.Exit(code=1)
    try:
        run_web_ui(host=host, port=port, open_browser=not no_open)
    except RuntimeError as exc:
        typer.echo(f"[ERR] {exc}")
        typer.echo("[TIP] Usually you already have one running app on the same port.")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    main()

