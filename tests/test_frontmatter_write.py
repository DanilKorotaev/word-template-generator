from __future__ import annotations

from pathlib import Path

from word_template_generator.utils.frontmatter import (
    build_frontmatter_document,
    read_frontmatter,
    read_frontmatter_with_body,
    serialize_yaml,
    write_frontmatter,
)


def test_serialize_yaml_multiline_and_quoted_strings() -> None:
    payload = {
        "fields": {
            "simple": "text value",
            "special": 'значение: "тест"',
            "multiline": "строка 1\nстрока 2",
        }
    }

    dumped = serialize_yaml(payload)

    assert 'special: "значение: \\"тест\\""' in dumped
    assert "multiline: |" in dumped


def test_write_frontmatter_preserves_body(tmp_path: Path) -> None:
    target = tmp_path / "act.md"
    write_frontmatter(
        target,
        {
            "output_name": "act_001",
            "fields": {"описание": "Тест"},
        },
        body="Тело markdown\nвторая строка",
    )

    data_only = read_frontmatter(target)
    data_with_body, body = read_frontmatter_with_body(target)

    assert data_only["output_name"] == "act_001"
    assert data_with_body["fields"]["описание"] == "Тест"
    assert body == "Тело markdown\nвторая строка"


def test_build_frontmatter_document_without_body() -> None:
    text = build_frontmatter_document({"template": "test.docx"})
    assert text.startswith("---\n")
    assert text.endswith("---\n")
