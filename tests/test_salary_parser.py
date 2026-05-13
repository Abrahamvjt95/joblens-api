import pytest
from normalizer.salary_parser import parse_salary, normalize_to_annual


class TestParseSalaryNumeric:
    def test_two_integers_returns_range(self):
        lo, hi, cur = parse_salary(60000, 80000)
        assert lo == 60000
        assert hi == 80000
        assert cur == "GBP"

    def test_single_integer_returns_min_only(self):
        lo, hi, cur = parse_salary(75000)
        assert lo == 75000
        assert hi is None

    def test_float_values_are_truncated(self):
        lo, hi, _ = parse_salary(60000.9, 80000.1)
        assert lo == 60000
        assert hi == 80000

    def test_none_returns_triple_none(self):
        assert parse_salary(None) == (None, None, None)


class TestParseSalaryText:
    def test_gbp_range_with_k_suffix(self):
        lo, hi, cur = parse_salary("£60k - £80k")
        assert lo == 60000
        assert hi == 80000
        assert cur == "GBP"

    def test_usd_range_with_commas(self):
        lo, hi, cur = parse_salary("$80,000-$120,000")
        assert lo == 80000
        assert hi == 120000
        assert cur == "USD"

    def test_eur_range(self):
        lo, hi, cur = parse_salary("€50k–€70k")
        assert lo == 50000
        assert hi == 70000
        assert cur == "EUR"

    def test_single_value_text(self):
        lo, hi, _ = parse_salary("90000")
        assert lo == 90000
        assert hi is None

    def test_single_k_suffix(self):
        lo, hi, _ = parse_salary("90k")
        assert lo == 90000
        assert hi is None

    def test_empty_string_returns_none(self):
        assert parse_salary("") == (None, None, None)

    def test_currency_hint_overrides_detection(self):
        _, _, cur = parse_salary("60000", currency_hint="EUR")
        assert cur == "EUR"

    def test_range_with_to_separator(self):
        lo, hi, _ = parse_salary("60k to 80k")
        assert lo == 60000
        assert hi == 80000


class TestNormalizeToAnnual:
    def test_hourly_rate(self):
        assert normalize_to_annual(50, "hourly") == 50 * 8 * 220

    def test_daily_rate(self):
        assert normalize_to_annual(400, "daily") == 400 * 220

    def test_monthly_rate(self):
        assert normalize_to_annual(5000, "monthly") == 60000

    def test_annual_unchanged(self):
        assert normalize_to_annual(60000, "annual") == 60000

    def test_none_returns_none(self):
        assert normalize_to_annual(None, "annual") is None
