from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def read_frontmatter(path: Path) -> dict[str, Any]:
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

