from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate
from fastapi import APIRouter, HTTPException

from ..config import DEFAULT_OUTPUT_DIR_NAME, VALIDATION_TMP_DIR_NAME
from ..core.generator import build_one
from ..core.workspace import list_template_files, load_workspace, suggest_template_name
from ..utils.frontmatter import read_frontmatter_with_body, write_frontmatter
from ..utils.native_dialog import pick_workspace_native
from .schemas import (
    BuildOnePayload,
    DeleteActPayload,
    OpenFilePayload,
    SaveActPayload,
    WorkspacePayload,
)

router = APIRouter()


DATE_VALUE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$|^\d{4}-\d{2}-\d{2}$")


def _value(data: dict[str, Any], en: str, ru: str, default: Any = None) -> Any:
    if en in data:
        return data[en]
    if ru in data:
        return data[ru]
    return default


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


def _result_file_payload(act_name: str, output_file: Path) -> dict[str, Any]:
    resolved = output_file.resolve()
    mtime = resolved.stat().st_mtime if resolved.exists() else 0
    return {"act": act_name, "path": str(resolved), "name": resolved.name, "mtime": mtime}


def _sanitize_act_filename(raw_name: str) -> str:
    filename = (raw_name or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Имя файла не задано")
    if not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Имя акта должно заканчиваться на .md")
    if Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Имя файла не должно содержать путь")
    return filename


def _resolve_act_path(workspace_root: Path, acts_dir: Path, filename: str) -> Path:
    target_dir = acts_dir if acts_dir.exists() else workspace_root
    target = (target_dir / filename).resolve()
    root = target_dir.resolve()
    if not target.is_relative_to(root):
        raise HTTPException(status_code=400, detail="Некорректный путь к акту")
    return target


def _resolve_template_path(templates_dir: Path, template_name: str) -> Path:
    clean_name = (template_name or "").strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="Шаблон не выбран")

    templates_root = templates_dir.resolve()
    target = (templates_dir / clean_name).resolve()
    if not target.is_relative_to(templates_root):
        raise HTTPException(status_code=400, detail="Некорректный путь к шаблону")
    if target.suffix.lower() not in {".docx", ".docm"}:
        raise HTTPException(status_code=400, detail="Поддерживаются только .docx или .docm")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return target


def _infer_field_type(value: Any) -> str:
    if isinstance(value, (int, float)):
        return "number"
    if not isinstance(value, str):
        return "text"
    if "\n" in value:
        return "multiline"
    if "[[" in value and "]]" in value:
        return "reference"
    if DATE_VALUE_RE.fullmatch(value.strip()):
        return "date"
    return "text"


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


@router.get("/api/template-path")
def template_path(workspace: str, template: str) -> dict[str, str]:
    try:
        cfg, _ = load_workspace(Path(workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    target = _resolve_template_path(cfg.templates_dir, template)
    return {"path": str(target)}


@router.get("/api/act-data")
def act_data(workspace: str, act: str) -> dict[str, Any]:
    try:
        cfg, _ = load_workspace(Path(workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = _sanitize_act_filename(act)
    act_file = _resolve_act_path(cfg.root, cfg.acts_dir, filename)
    if not act_file.exists() or not act_file.is_file():
        raise HTTPException(status_code=404, detail="Акт не найден")

    try:
        act_payload, _ = read_frontmatter_with_body(act_file)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    number_raw = _value(act_payload, "number", "номер", None)
    number: dict[str, Any] = {"prefix": "", "value": None}
    if isinstance(number_raw, dict):
        number["prefix"] = str(_value(number_raw, "prefix", "префикс", ""))
        number["value"] = _value(number_raw, "value", "значение")
    elif isinstance(number_raw, (int, str)):
        number["value"] = number_raw

    fields_raw = _value(act_payload, "fields", "поля", {}) or {}
    if not isinstance(fields_raw, dict):
        raise HTTPException(status_code=400, detail="fields/поля должны быть словарем")
    editor_meta = act_payload.get("_editor", {}) if isinstance(act_payload.get("_editor", {}), dict) else {}
    field_types_meta = editor_meta.get("field_types", {}) if isinstance(editor_meta.get("field_types", {}), dict) else {}

    fields: dict[str, dict[str, Any]] = {}
    for key, value in fields_raw.items():
        if not isinstance(key, str):
            continue
        field_type = _infer_field_type(value)
        field_meta = field_types_meta.get(key, {}) if isinstance(field_types_meta.get(key, {}), dict) else {}
        if isinstance(field_meta.get("type"), str):
            field_type = field_meta["type"]
        entry: dict[str, Any] = {"value": value, "type": field_type}
        if field_type == "date":
            entry["format"] = field_meta.get("format") or "dd.MM.yyyy"
        fields[key] = entry

    return {
        "filename": act_file.name,
        "template": _value(act_payload, "template", "шаблон", cfg.template_name),
        "output_name": _value(act_payload, "output_name", "имя_файла", act_file.stem),
        "number": number,
        "fields": fields,
    }


@router.post("/api/save-act")
def save_act(payload: SaveActPayload) -> dict[str, str]:
    try:
        cfg, _ = load_workspace(Path(payload.workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = _sanitize_act_filename(payload.filename)
    act_file = _resolve_act_path(cfg.root, cfg.acts_dir, filename)

    if payload.is_new and act_file.exists():
        raise HTTPException(status_code=400, detail="Файл акта уже существует")
    if not payload.is_new and not act_file.exists():
        raise HTTPException(status_code=404, detail="Редактируемый акт не найден")

    body = ""
    if act_file.exists():
        try:
            _, body = read_frontmatter_with_body(act_file)
        except Exception:
            body = ""

    frontmatter_data: dict[str, Any] = {
        "template": payload.data.template or cfg.template_name,
        "output_name": payload.data.output_name or Path(filename).stem,
        "fields": {},
    }
    if not str(frontmatter_data["template"]).strip():
        raise HTTPException(status_code=400, detail="Шаблон не выбран")
    _resolve_template_path(cfg.templates_dir, str(frontmatter_data["template"]))

    if payload.data.number is not None:
        number_prefix = (payload.data.number.prefix or "").strip()
        number_value = payload.data.number.value
        if number_value is None and number_prefix:
            raise HTTPException(status_code=400, detail="Для номера с префиксом нужно указать значение")
        if number_value is not None:
            frontmatter_data["number"] = {
                "prefix": number_prefix,
                "value": number_value,
            }

    editor_types: dict[str, dict[str, str]] = {}
    for raw_key, field in payload.data.fields.items():
        key = raw_key.strip()
        if not key:
            continue
        frontmatter_data["fields"][key] = field.value
        editor_types[key] = {"type": field.type}
        if field.format:
            editor_types[key]["format"] = field.format
    if editor_types:
        frontmatter_data["_editor"] = {"field_types": editor_types}

    try:
        write_frontmatter(act_file, frontmatter_data, body=body)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Не удалось сохранить акт: {exc}") from exc

    return {"status": "ok", "filename": act_file.name}


@router.delete("/api/delete-act")
def delete_act(payload: DeleteActPayload) -> dict[str, str]:
    try:
        cfg, _ = load_workspace(Path(payload.workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    filename = _sanitize_act_filename(payload.filename)
    act_file = _resolve_act_path(cfg.root, cfg.acts_dir, filename)
    if not act_file.exists() or not act_file.is_file():
        raise HTTPException(status_code=404, detail="Акт не найден")

    try:
        act_file.unlink()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Не удалось удалить акт: {exc}") from exc
    return {"status": "ok"}


@router.get("/api/template-variables")
def template_variables(workspace: str, template: str) -> dict[str, list[str]]:
    try:
        cfg, _ = load_workspace(Path(workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    template_file = _resolve_template_path(cfg.templates_dir, template)
    try:
        tpl = DocxTemplate(str(template_file))
        variables = sorted(str(name) for name in tpl.get_undeclared_template_variables(context={}))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать шаблон: {exc}") from exc
    return {"variables": variables}


@router.get("/api/project-fields")
def project_fields(workspace: str) -> dict[str, Any]:
    try:
        cfg, _ = load_workspace(Path(workspace))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fields = _value(cfg.project_data, "fields", "поля", {}) or {}
    if not isinstance(fields, dict):
        fields = {}
    number = _value(cfg.project_data, "number", "номер", None)
    prefix = ""
    if isinstance(number, dict):
        prefix = str(_value(number, "prefix", "префикс", ""))
    return {"fields": fields, "number": {"prefix": prefix}}


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
def build_all(payload: WorkspacePayload) -> dict[str, Any]:
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
    files: list[dict[str, Any]] = []
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
            files.append(_result_file_payload(result.act_file.name, result.output_file))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"{act_file.name}: {exc}") from exc
    log.append(f"Done. Generated {len(act_files)} file(s).")
    return {"log": log, "files": files}


@router.post("/api/build-one")
def build_one_api(payload: BuildOnePayload) -> dict[str, Any]:
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

    return {
        "log": [f"[OK] {result.act_file.name} -> {result.output_file}"],
        "files": [_result_file_payload(result.act_file.name, result.output_file)],
    }


@router.post("/api/open-file")
def open_file(payload: OpenFilePayload) -> dict[str, str]:
    file_path = Path(payload.path).expanduser().resolve()
    if file_path.suffix.lower() not in {".docx", ".docm"}:
        raise HTTPException(status_code=400, detail="Поддерживаются только .docx или .docm")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")

    try:
        if sys.platform == "win32":
            os.startfile(str(file_path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(file_path)])  # noqa: S603
        else:
            subprocess.Popen(["xdg-open", str(file_path)])  # noqa: S603
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Не удалось открыть файл: {exc}") from exc

    return {"status": "ok"}

