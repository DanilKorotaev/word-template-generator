from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from ..config import DEFAULT_OUTPUT_DIR_NAME, VALIDATION_TMP_DIR_NAME
from ..core.generator import build_one
from ..core.workspace import list_template_files, load_workspace, suggest_template_name
from ..utils.native_dialog import pick_workspace_native
from .schemas import BuildOnePayload, WorkspacePayload

router = APIRouter()


def _resolved_project_data(cfg_template_data: dict[str, Any], template_name: str | None) -> dict[str, Any]:
    merged = dict(cfg_template_data)
    if template_name:
        merged["template"] = template_name
        merged["шаблон"] = template_name
    return merged


def _resolved_output_dir(workspace_root: Path, output_dir: str | None) -> Path:
    if not output_dir or not output_dir.strip():
        return workspace_root / DEFAULT_OUTPUT_DIR_NAME
    requested = Path(output_dir.strip())
    return requested if requested.is_absolute() else workspace_root / requested


def _list_workspace_dirs(workspace_root: Path) -> list[str]:
    names = sorted(
        entry.name
        for entry in workspace_root.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )
    if DEFAULT_OUTPUT_DIR_NAME not in names:
        names.insert(0, DEFAULT_OUTPUT_DIR_NAME)
    return names


@router.post("/api/pick-workspace")
def pick_workspace() -> dict[str, str]:
    selected = pick_workspace_native()
    if not selected:
        raise HTTPException(
            status_code=400,
            detail=(
                "Нативный выбор папки недоступен в этой системе. "
                "Введите путь вручную."
            ),
        )
    return {"workspace": selected}


@router.get("/api/acts")
def acts(workspace: str) -> dict[str, Any]:
    try:
        cfg, act_files = load_workspace(Path(workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    templates = [p.name for p in list_template_files(cfg.templates_dir)]
    selected_template = suggest_template_name(cfg.templates_dir, preferred=cfg.template_name) or cfg.template_name
    return {
        "acts": [p.name for p in act_files],
        "templates": templates,
        "selected_template": selected_template,
        "output_dirs": _list_workspace_dirs(cfg.root),
        "selected_output_dir": cfg.output_dir.name,
    }


@router.post("/api/validate")
def validate(payload: WorkspacePayload) -> dict[str, list[str]]:
    try:
        cfg, act_files = load_workspace(Path(payload.workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    template_name = payload.template or cfg.template_name
    project_data = _resolved_project_data(cfg.project_data, template_name)
    log: list[str] = []
    temp_out = cfg.root / VALIDATION_TMP_DIR_NAME
    has_errors = False
    for act_file in act_files:
        try:
            result = build_one(
                project_data=project_data,
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


@router.post("/api/build-all")
def build_all(payload: WorkspacePayload) -> dict[str, list[str]]:
    try:
        cfg, act_files = load_workspace(Path(payload.workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not act_files:
        raise HTTPException(status_code=400, detail="No act markdown files found.")

    template_name = payload.template or cfg.template_name
    project_data = _resolved_project_data(cfg.project_data, template_name)
    output_dir = _resolved_output_dir(cfg.root, payload.output_dir)

    log: list[str] = []
    for act_file in act_files:
        try:
            result = build_one(
                project_data=project_data,
                act_file=act_file,
                templates_dir=cfg.templates_dir,
                output_dir=output_dir,
                strict=True,
            )
            log.append(f"[OK] {result.act_file.name} -> {result.output_file}")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"{act_file.name}: {exc}") from exc
    log.append(f"Done. Generated {len(act_files)} file(s).")
    return {"log": log}


@router.post("/api/build-one")
def build_one_api(payload: BuildOnePayload) -> dict[str, list[str]]:
    try:
        cfg, act_files = load_workspace(Path(payload.workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    act_file = next((p for p in act_files if p.name == payload.act), None)
    if act_file is None:
        raise HTTPException(status_code=400, detail=f"Act not found: {payload.act}")

    template_name = payload.template or cfg.template_name
    project_data = _resolved_project_data(cfg.project_data, template_name)
    output_dir = _resolved_output_dir(cfg.root, payload.output_dir)

    try:
        result = build_one(
            project_data=project_data,
            act_file=act_file,
            templates_dir=cfg.templates_dir,
            output_dir=output_dir,
            strict=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"log": [f"[OK] {result.act_file.name} -> {result.output_file}"]}

