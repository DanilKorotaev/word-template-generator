from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import VALIDATION_TMP_DIR_NAME
from ..core.generator import build_one
from ..core.workspace import load_workspace
from ..utils.native_dialog import pick_workspace_native
from .schemas import BuildOnePayload, WorkspacePayload

router = APIRouter()


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
def acts(workspace: str) -> dict[str, list[str]]:
    try:
        _, act_files = load_workspace(Path(workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"acts": [p.name for p in act_files]}


@router.post("/api/validate")
def validate(payload: WorkspacePayload) -> dict[str, list[str]]:
    try:
        cfg, act_files = load_workspace(Path(payload.workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    log: list[str] = []
    temp_out = cfg.root / VALIDATION_TMP_DIR_NAME
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


@router.post("/api/build-all")
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


@router.post("/api/build-one")
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

