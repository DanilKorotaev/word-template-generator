from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

import yaml


def _yaml_representer_str(dumper: yaml.SafeDumper, data: str) -> yaml.ScalarNode:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    if any(char in data for char in ':#{}[]&*?|-><!%@`"\''):
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def serialize_yaml(data: dict[str, Any]) -> str:
    dumper_cls = type("FrontmatterSafeDumper", (yaml.SafeDumper,), {})
    dumper_cls.add_representer(str, _yaml_representer_str)
    dumped = yaml.dump(
        data,
        Dumper=dumper_cls,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    return dumped.rstrip() + "\n"


def build_frontmatter_document(data: dict[str, Any], body: str = "") -> str:
    yaml_text = serialize_yaml(data)
    clean_body = body.lstrip("\r\n")
    if clean_body:
        return f"---\n{yaml_text}---\n{clean_body.rstrip()}\n"
    return f"---\n{yaml_text}---\n"


def _split_frontmatter(text: str, path: Path) -> tuple[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path} does not start with markdown front matter.")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            yaml_text = "\n".join(lines[1:idx]).strip()
            body = "\n".join(lines[idx + 1 :]).rstrip()
            return yaml_text, body
    raise ValueError(f"{path} has invalid front matter block.")


def read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    yaml_text, _ = _split_frontmatter(text, path)
    data = yaml.safe_load(yaml_text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} front matter must be a YAML object.")
    return data


def read_frontmatter_with_body(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    yaml_text, body = _split_frontmatter(text, path)
    data = yaml.safe_load(yaml_text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} front matter must be a YAML object.")
    return data, body


def safe_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)


def write_frontmatter(path: Path, data: dict[str, Any], body: str = "") -> None:
    safe_write(path, build_frontmatter_document(data, body))

