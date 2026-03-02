from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import (
    DEFAULT_OUTPUT_DIR_NAME,
    DEFAULT_TEMPLATE_NAME,
    TEMPLATE_FILE_EXTENSIONS,
    TEMPLATE_KEYWORDS,
)
from ..utils.frontmatter import read_frontmatter
from .models import WorkspaceConfig


def _value(data: dict[str, Any], en: str, ru: str, default: Any = None) -> Any:
    if en in data:
        return data[en]
    if ru in data:
        return data[ru]
    return default


def load_project(project_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    project_file = project_dir / "project.md"
    project_data = read_frontmatter(project_file)
    acts_dir = project_dir / "acts"
    act_files = sorted(acts_dir.glob("*.md"))
    return project_data, act_files


def list_template_files(workspace_dir: Path) -> list[Path]:
    allowed = {ext.lower() for ext in TEMPLATE_FILE_EXTENSIONS}
    return sorted(
        p
        for p in workspace_dir.iterdir()
        if p.is_file() and p.suffix.lower() in allowed
    )


def suggest_template_name(workspace_dir: Path, preferred: str | None = None) -> str | None:
    templates = list_template_files(workspace_dir)
    if not templates:
        return None

    names = {p.name for p in templates}
    if preferred and preferred in names:
        return preferred

    if len(templates) == 1:
        return templates[0].name

    keywords = tuple(k.casefold() for k in TEMPLATE_KEYWORDS)
    keyword_matches = [
        p.name
        for p in templates
        if any(keyword in p.stem.casefold() for keyword in keywords)
    ]
    if len(keyword_matches) == 1:
        return keyword_matches[0]
    if len(keyword_matches) > 1:
        return sorted(keyword_matches)[0]

    if DEFAULT_TEMPLATE_NAME in names:
        return DEFAULT_TEMPLATE_NAME
    return templates[0].name


def load_workspace(workspace_dir: Path) -> tuple[WorkspaceConfig, list[Path]]:
    project_file = workspace_dir / "project.md"
    project_data: dict[str, Any] = {
        "template": DEFAULT_TEMPLATE_NAME,
        "fields": {},
    }
    if project_file.exists():
        optional_project_data = read_frontmatter(project_file)
        optional_fields = _value(optional_project_data, "fields", "поля", {}) or {}
        if not isinstance(optional_fields, dict):
            raise ValueError("project.md: fields/поля must be a dictionary.")
        project_data.update({k: v for k, v in optional_project_data.items() if k not in {"fields", "поля"}})
        project_data["fields"] = {
            **project_data.get("fields", {}),
            **optional_fields,
        }
        project_ref: Path | None = project_file
    else:
        project_ref = None

    configured_template_name = str(_value(project_data, "template", "шаблон", DEFAULT_TEMPLATE_NAME))
    template_name = suggest_template_name(workspace_dir, preferred=configured_template_name) or configured_template_name
    project_data["template"] = template_name
    templates_dir = workspace_dir
    output_dir = workspace_dir / DEFAULT_OUTPUT_DIR_NAME
    acts_dir = workspace_dir / "acts"
    if acts_dir.exists():
        act_files = sorted(p for p in acts_dir.glob("*.md"))
    else:
        acts_dir = workspace_dir
        act_files = sorted(
            p for p in workspace_dir.glob("*.md") if p.name not in {"README.md", "project.md"}
        )

    config = WorkspaceConfig(
        root=workspace_dir,
        project_file=project_ref,
        acts_dir=acts_dir,
        templates_dir=templates_dir,
        output_dir=output_dir,
        template_name=template_name,
        project_data=project_data,
    )
    return config, act_files

