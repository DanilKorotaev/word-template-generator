from __future__ import annotations

import os


def _env_csv(name: str, default: str) -> tuple[str, ...]:
    raw = os.getenv(name, default)
    parts = [item.strip() for item in raw.split(",")]
    return tuple(item for item in parts if item)


DEFAULT_TEMPLATE_NAME = os.getenv("WTG_DEFAULT_TEMPLATE_NAME", "template.docx")
DEFAULT_OUTPUT_DIR_NAME = os.getenv("WTG_DEFAULT_OUTPUT_DIR_NAME", "generated")
VALIDATION_TMP_DIR_NAME = os.getenv("WTG_VALIDATION_TMP_DIR_NAME", ".validation_tmp")
TEMPLATE_KEYWORDS = _env_csv("WTG_TEMPLATE_KEYWORDS", "template,шаблон")
TEMPLATE_FILE_EXTENSIONS = tuple(
    ext if ext.startswith(".") else f".{ext}" for ext in _env_csv("WTG_TEMPLATE_EXTENSIONS", ".docx,.docm")
)

