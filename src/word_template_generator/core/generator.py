from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate

from ..utils.frontmatter import read_frontmatter
from .models import BuildResult

TOKEN_RE = re.compile(r"\[\[([^\[\]\n]+?)\]\]")


def _value(data: dict[str, Any], en: str, ru: str, default: Any = None) -> Any:
    if en in data:
        return data[en]
    if ru in data:
        return data[ru]
    return default


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


def build_one(
    project_data: dict[str, Any],
    act_file: Path,
    templates_dir: Path,
    output_dir: Path,
    strict: bool = True,
) -> BuildResult:
    act_data = read_frontmatter(act_file)
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

