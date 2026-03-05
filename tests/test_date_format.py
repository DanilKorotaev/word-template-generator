from __future__ import annotations

import datetime as dt
import unittest

from word_template_generator.utils.date_format import DEFAULT_DATE_FORMAT, format_date, parse_date


class DateFormatTests(unittest.TestCase):
    def test_parse_date_supported_formats(self) -> None:
        self.assertEqual(parse_date("04.03.2026"), dt.date(2026, 3, 4))
        self.assertEqual(parse_date("2026-03-04"), dt.date(2026, 3, 4))
        self.assertEqual(parse_date("04/03/2026"), dt.date(2026, 3, 4))

    def test_parse_date_today_aliases(self) -> None:
        base = dt.date(2026, 3, 4)
        self.assertEqual(parse_date("today", today=base), base)
        self.assertEqual(parse_date("сегодня", today=base), base)

    def test_parse_date_invalid_value_raises(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid date value"):
            parse_date("32.13.2026", field_name="дата")

    def test_format_date_supported_tokens(self) -> None:
        value = dt.date(2026, 3, 4)
        self.assertEqual(format_date(value, "dd.MM.yyyy"), "04.03.2026")
        self.assertEqual(format_date(value, "d MMMMG yyyy г."), "4 марта 2026 г.")
        self.assertEqual(format_date(value, "d MMMM yyyy"), "4 март 2026")
        self.assertEqual(format_date(value, "dd.MM.yy"), "04.03.26")
        self.assertEqual(format_date(value, DEFAULT_DATE_FORMAT), "04.03.2026")


if __name__ == "__main__":
    unittest.main()

