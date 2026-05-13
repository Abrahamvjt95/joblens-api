from __future__ import annotations
import re
from typing import Optional


# Conversion rates to EUR (approximate, for normalization only)
_TO_EUR = {"EUR": 1.0, "GBP": 1.17, "USD": 0.92, "CHF": 1.04, "SEK": 0.087}

_CURRENCY_SYMBOLS = {
    "£": "GBP", "$": "USD", "€": "EUR", "CHF": "CHF", "kr": "SEK",
}

_CURRENCY_CODES = {"gbp": "GBP", "usd": "USD", "eur": "EUR", "chf": "CHF"}


def _detect_currency(text: str) -> str:
    t = text.lower()
    for symbol, code in _CURRENCY_SYMBOLS.items():
        if symbol in t:
            return code
    for code_str, code in _CURRENCY_CODES.items():
        if code_str in t:
            return code
    return "GBP"  # Adzuna default is UK


def _parse_number(raw: str) -> Optional[int]:
    """Extract numeric salary from a string like '80k', '80,000', '80000'."""
    raw = raw.replace(",", "").replace(" ", "").lower()
    match = re.search(r"(\d+(?:\.\d+)?)(k?)", raw)
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2) == "k":
        value *= 1000
    return int(value)


def parse_salary(
    raw: str | int | float | None,
    raw_max: str | int | float | None = None,
    currency_hint: str | None = None,
) -> tuple[Optional[int], Optional[int], Optional[str]]:
    """
    Parse salary from various formats into (min, max, currency).

    Handles:
      - Numeric pair:   parse_salary(60000, 80000)
      - Text range:     parse_salary("£60k - £80k")
      - Single value:   parse_salary("90000")
      - Null input:     parse_salary(None) → (None, None, None)
    """
    if raw is None:
        return None, None, None

    # Adzuna gives two numeric fields
    if isinstance(raw, (int, float)) and raw_max is not None:
        currency = currency_hint or "GBP"
        return int(raw), int(raw_max), currency

    if isinstance(raw, (int, float)):
        return int(raw), None, currency_hint or "GBP"

    text = str(raw).strip()
    if not text:
        return None, None, None

    currency = currency_hint or _detect_currency(text)

    # Range pattern: handles optional currency symbol before each number
    # e.g. "£60k - £80k" / "$80,000-$120,000" / "€50k–€70k" / "60k to 80k"
    range_match = re.search(
        r"[£$€]?(\d[\d,\.]*k?)\s*[-–to]+\s*[£$€]?(\d[\d,\.]*k?)", text, re.IGNORECASE
    )
    if range_match:
        lo = _parse_number(range_match.group(1))
        hi = _parse_number(range_match.group(2))
        return lo, hi, currency

    # Single value: "90000" / "90k"
    single = _parse_number(text)
    return single, None, currency


def normalize_to_annual(value: int | None, period: str | None) -> Optional[int]:
    """Convert hourly/daily/monthly salaries to annual."""
    if value is None:
        return None
    period = (period or "").lower()
    if any(t in period for t in ("hour",)):            # hourly, per hour
        return value * 8 * 220
    if any(t in period for t in ("day", "daily")):     # day, daily, per day
        return value * 220
    if any(t in period for t in ("month",)):           # monthly, per month
        return value * 12
    return value
