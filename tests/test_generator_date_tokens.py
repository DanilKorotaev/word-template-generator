from __future__ import annotations

import unittest

from word_template_generator.core.generator import _merge_fields


class GeneratorDateTokenTests(unittest.TestCase):
    def test_date_field_respects_editor_format(self) -> None:
        context = _merge_fields(
            project_data={},
            act_data={
                "поля": {"дата": "04.03.2026"},
                "_editor": {"field_types": {"дата": {"type": "date", "format": "d MMMMG yyyy г."}}},
            },
        )
        self.assertEqual(context["дата"], "4 марта 2026 г.")

    def test_date_token_with_format(self) -> None:
        context = _merge_fields(
            project_data={},
            act_data={
                "поля": {
                    "дата": "04.03.2026",
                    "дата_текст": "[[дата|d MMMMG yyyy г.]]",
                }
            },
        )
        self.assertEqual(context["дата"], "04.03.2026")
        self.assertEqual(context["дата_текст"], "4 марта 2026 г.")

    def test_iso_date_from_yaml_object(self) -> None:
        context = _merge_fields(
            project_data={},
            act_data={"поля": {"дата": "2026-03-04", "дата_short": "[[дата|dd.MM.yy]]"}},
        )
        self.assertEqual(context["дата"], "04.03.2026")
        self.assertEqual(context["дата_short"], "04.03.26")

    def test_today_tokens(self) -> None:
        context = _merge_fields(
            project_data={},
            act_data={"поля": {"date_now": "[[today]]", "date_now_text": "[[сегодня|d MMMMG yyyy]]"}},
        )
        self.assertRegex(context["date_now"], r"^\d{2}\.\d{2}\.\d{4}$")
        self.assertRegex(context["date_now_text"], r"^\d{1,2}\s+[а-яё]+\s+\d{4}$")

    def test_today_value_as_field(self) -> None:
        context = _merge_fields(
            project_data={},
            act_data={"поля": {"дата_сдачи": "сегодня"}},
        )
        self.assertRegex(context["дата_сдачи"], r"^\d{2}\.\d{2}\.\d{4}$")

    def test_invalid_date_raises_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid date value"):
            _merge_fields(project_data={}, act_data={"поля": {"дата": "32.13.2026"}})

    def test_non_date_value_with_format_stays_string(self) -> None:
        context = _merge_fields(
            project_data={},
            act_data={"поля": {"объект": "дом Б-473", "описание": "[[объект|dd.MM.yyyy]]"}},
        )
        self.assertEqual(context["описание"], "дом Б-473")


if __name__ == "__main__":
    unittest.main()

