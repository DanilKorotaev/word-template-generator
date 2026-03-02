from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import DEFAULT_OUTPUT_DIR_NAME, DEFAULT_TEMPLATE_NAME
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

    template_name = str(_value(project_data, "template", "шаблон", DEFAULT_TEMPLATE_NAME))
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

