from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

import yaml
from docxtpl import DocxTemplate

TOKEN_RE = re.compile(r"\[\[([^\[\]\n]+?)\]\]")


@dataclass
class BuildResult:
    act_file: Path
    output_file: Path
    template_file: Path
    missing_variables: list[str]


@dataclass
class WorkspaceConfig:
    root: Path
    project_file: Path | None
    acts_dir: Path
    templates_dir: Path
    output_dir: Path
    template_name: str
    project_data: dict[str, Any]


def _value(data: dict[str, Any], en: str, ru: str, default: Any = None) -> Any:
    if en in data:
        return data[en]
    if ru in data:
        return data[ru]
    return default


def _read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path} does not start with markdown front matter.")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path} has invalid front matter block.")
    data = yaml.safe_load(parts[1]) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} front matter must be a YAML object.")
    return data


def _merge_fields(project_data: dict[str, Any], act_data: dict[str, Any]) -> dict[str, Any]:
    project_fields = _value(project_data, "fields", "поля", {}) or {}
    act_fields = _value(act_data, "fields", "поля", {}) or {}
    if not isinstance(project_fields, dict) or not isinstance(act_fields, dict):
        raise ValueError("fields/поля must be dictionaries in project and act markdown.")

    merged = {**project_fields, **act_fields}
    context = dict(merged)

    number_data = _value(act_data, "number", "номер", _value(project_data, "number", "номер"))
    if number_data:
        if isinstance(number_data, int):
            context["number"] = str(number_data)
            context["number_value"] = number_data
        elif isinstance(number_data, str):
            context["number"] = number_data
        elif isinstance(number_data, dict):
            prefix = str(_value(number_data, "prefix", "префикс", ""))
            value = _value(number_data, "value", "значение")
            if value is None:
                raise ValueError("number.value (or номер.значение) is required when number is an object.")
            context["number"] = f"{prefix}{value}"
            context["number_prefix"] = prefix
            context["number_value"] = value
        else:
            raise ValueError("number must be int, string, or object with prefix/value.")
        context["номер"] = context.get("number")
        context["номер_значение"] = context.get("number_value")
        context["номер_префикс"] = context.get("number_prefix", "")

    return _resolve_tokens(context)


def _resolve_tokens(context: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(context)
    for _ in range(10):
        changed = False
        for key, value in resolved.items():
            if not isinstance(value, str):
                continue

            def repl(match: re.Match[str]) -> str:
                token = match.group(1).strip()
                replacement = resolved.get(token)
                return "" if replacement is None else str(replacement)

            new_value = TOKEN_RE.sub(repl, value)
            if new_value != value:
                resolved[key] = new_value
                changed = True
        if not changed:
            return resolved
    raise ValueError("Too many token resolution passes. Check for circular [[token]] references.")


def load_project(project_dir: Path) -> tuple[dict[str, Any], list[Path]]:
    project_file = project_dir / "project.md"
    project_data = _read_frontmatter(project_file)
    acts_dir = project_dir / "acts"
    act_files = sorted(acts_dir.glob("*.md"))
    return project_data, act_files


def load_workspace(workspace_dir: Path) -> tuple[WorkspaceConfig, list[Path]]:
    project_file = workspace_dir / "project.md"
    project_data: dict[str, Any] = {
        "template": "template.docx",
        "fields": {},
    }
    if project_file.exists():
        optional_project_data = _read_frontmatter(project_file)
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

    template_name = str(_value(project_data, "template", "шаблон", "template.docx"))
    templates_dir = workspace_dir
    output_dir = workspace_dir / "generated"
    acts_dir = workspace_dir / "acts"
    if acts_dir.exists():
        act_files = sorted(p for p in acts_dir.glob("*.md"))
    else:
        # Flat mode: any markdown except reserved control files.
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


def build_one(
    project_data: dict[str, Any],
    act_file: Path,
    templates_dir: Path,
    output_dir: Path,
    strict: bool = True,
) -> BuildResult:
    act_data = _read_frontmatter(act_file)
    template_name = _value(act_data, "template", "шаблон") or _value(project_data, "template", "шаблон")
    if not template_name:
        raise ValueError(f"No template defined for {act_file.name}.")

    template_file = templates_dir / str(template_name)
    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_file}")

    context = _merge_fields(project_data, act_data)

    tpl = DocxTemplate(str(template_file))
    missing = sorted(tpl.get_undeclared_template_variables(context=context))
    if strict and missing:
        raise ValueError(f"{act_file.name}: missing values for {', '.join(missing)}")

    tpl.render(context)

    output_name = _value(act_data, "output_name", "имя_файла") or act_file.stem
    output_file = output_dir / f"{output_name}.docx"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    tpl.save(str(output_file))

    return BuildResult(
        act_file=act_file,
        output_file=output_file,
        template_file=template_file,
        missing_variables=missing,
    )

