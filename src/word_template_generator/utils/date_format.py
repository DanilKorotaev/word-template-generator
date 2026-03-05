from __future__ import annotations

import datetime as dt
import re

DEFAULT_DATE_FORMAT = "dd.MM.yyyy"

MONTHS_NOM = [
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
]

MONTHS_GEN = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]

MONTHS_SHORT = [
    "янв",
    "фев",
    "мар",
    "апр",
    "май",
    "июн",
    "июл",
    "авг",
    "сен",
    "окт",
    "ноя",
    "дек",
]

_SUPPORTED_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\d{2}\.\d{2}\.\d{4}$"), "%d.%m.%Y"),
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%d/%m/%Y"),
]


def parse_date(value: object, *, today: dt.date | None = None, field_name: str | None = None) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if not isinstance(value, str):
        return None

    raw = value.strip()
    if not raw:
        return None

    if raw.lower() in {"today", "сегодня"}:
        return today or dt.date.today()

    for regex, fmt in _SUPPORTED_PATTERNS:
        if not regex.fullmatch(raw):
            continue
        try:
            return dt.datetime.strptime(raw, fmt).date()
        except ValueError as exc:
            target = f" for '{field_name}'" if field_name else ""
            raise ValueError(f"Invalid date value{target}: '{raw}'") from exc
    return None


def format_date(value: dt.date, fmt: str) -> str:
    result = fmt
    result = result.replace("MMMMG", MONTHS_GEN[value.month - 1])
    result = result.replace("MMMM", MONTHS_NOM[value.month - 1])
    result = result.replace("MMM", MONTHS_SHORT[value.month - 1])
    result = result.replace("MM", f"{value.month:02d}")
    result = result.replace("M", str(value.month))
    result = result.replace("dd", f"{value.day:02d}")
    result = result.replace("d", str(value.day))
    result = result.replace("yyyy", str(value.year))
    result = result.replace("yy", f"{value.year % 100:02d}")
    return result

