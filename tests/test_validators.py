"""Tests for render/validators.py — summary validator + date validator (TDD, fail-fast)."""
import pytest
from render.validators import validate_summary, SummaryError, validate_dates, DateError


def test_too_short_fails():
    with pytest.raises(SummaryError):
        validate_summary("太短")


def test_placeholder_fails():
    text = "○○" * 150  # 字數夠但含 placeholder
    with pytest.raises(SummaryError):
        validate_summary(text)


def test_valid_summary_passes():
    validate_summary("本" * 250)   # 250 中文字、無 placeholder


def test_too_long_fails():
    with pytest.raises(SummaryError):
        validate_summary("長" * 301)


def test_todo_placeholder_fails():
    text = "本" * 249 + "TODO"
    with pytest.raises(SummaryError):
        validate_summary(text)


def test_daitian_placeholder_fails():
    text = "本" * 249 + "待填"
    with pytest.raises(SummaryError):
        validate_summary(text)


def test_xxx_placeholder_fails():
    text = "本" * 249 + "XXX"
    with pytest.raises(SummaryError):
        validate_summary(text)


def test_fangli_placeholder_fails():
    text = "本" * 249 + "範例"
    with pytest.raises(SummaryError):
        validate_summary(text)


def test_exactly_200_passes():
    validate_summary("本" * 200)


def test_exactly_300_passes():
    validate_summary("本" * 300)


def test_199_fails():
    with pytest.raises(SummaryError):
        validate_summary("本" * 199)


# --- P2-3：日期驗證 ---
def test_valid_dates_pass():
    validate_dates("2027-03-01", "2027-03-07")


def test_same_day_dates_pass():
    validate_dates("2027-03-01", "2027-03-01")


def test_start_after_end_fails():
    with pytest.raises(DateError):
        validate_dates("2027-03-10", "2027-03-01")


def test_invalid_date_format_fails():
    with pytest.raises(DateError):
        validate_dates("2027/03/01", "2027-03-07")


def test_nonsense_date_fails():
    with pytest.raises(DateError):
        validate_dates("not-a-date", "2027-03-07")
