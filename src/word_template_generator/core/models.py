from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


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

