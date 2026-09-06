"""情境組合與錯算回歸：期望值由例中各日金額獨立列出。"""
import json
from pathlib import Path

import openpyxl
import pytest

from calc.per_diem import compute_trip_per_diem
from render.render_finance_xlsx import render_finance_xlsx
from tripkit.validation import validate_finance, validate_trip


def test_multi_city_private_day_extension(tmp_path):
    data = json.loads(Path("examples/04-mixed-scenarios.trip-finance.json").read_text())
    validate_finance(data)
    inputs = data["per_diem_inputs"]
    result = compute_trip_per_diem(inputs["segments"], inputs["manual_items"], inputs["approved_days"])
    assert [s["amount_usd"] for s in result["per_segment"]] == [30, 13, 200, 0, 0, 100, 30]
    assert result["grand_total_usd"] == 823
    assert result["per_segment"][4]["per_diem_base"] == 200  # 排除不竄改原始基準額
    out = tmp_path / "finance.xlsx"
    render_finance_xlsx(data, str(out))
    wb = openpyxl.load_workbook(out)
    assert "私人" in wb.active["F6"].value
    assert "超出核准" in wb.active["F7"].value
    assert "示範退款" in wb.active["F12"].value
    wb.close()


def test_missing_dates_do_not_move_extension_inside_approval():
    data = [{"date": "2027-01-01", "per_diem_base": 100},
            {"date": "2027-01-03", "per_diem_base": 100}]
    assert compute_trip_per_diem(data, approved_days=2)["grand_total_usd"] == 100


def test_private_early_departure_does_not_consume_approved_days():
    data = [{"date": f"2027-01-0{i}", "per_diem_base": 100} for i in range(1, 5)]
    data[0].update(reimbursable=False, exclusion_reason="因私提前出國")
    result = compute_trip_per_diem(data, approved_days=2, approved_start_date="2027-01-02")
    assert [s["amount_usd"] for s in result["per_segment"]] == [0, 100, 100, 0]


def test_manual_case_can_keep_facts_on_an_excluded_day():
    data = [{"per_diem_base": 100, "cash_allowance_usd": 5,
             "reimbursable": False, "exclusion_reason": "改由人工核定完整金額"}]
    assert compute_trip_per_diem(data, [{"amount_usd": 70}])["grand_total_usd"] == 70


def test_decimal_rounding_does_not_add_a_dollar():
    # binary float: 0.1 + 0.2 + 0.7 can cross an integer after repeated additions.
    result = compute_trip_per_diem([{"per_diem_base": 0.1}] * 100)
    assert result["subtotal_usd"] == 10
    assert result["grand_total_usd"] == 10
    assert compute_trip_per_diem([{"per_diem_base": 0.1}], [{"amount_usd": 0.9}])["grand_total_usd"] == 1


@pytest.mark.parametrize("patch", [
    {"per_diem_base": float("nan")}, {"per_diem_base": float("inf")},
    {"per_diem_base": True}, {"day_index_same_place": 0},
    {"host_provided": "none", "cash_allowance_usd": 5},
    {"meals_not_provided": ["dinner", "dinner"]},
    {"reimbursable": False},
])
def test_dangerous_inputs_fail(patch):
    with pytest.raises(ValueError):
        compute_trip_per_diem([{"per_diem_base": 100, **patch}])


@pytest.mark.parametrize("dates", [("2027-01-01", "2027-01-01"), ("2027-01-02", "2027-01-01")])
def test_duplicate_or_unsorted_days_rejected(dates):
    with pytest.raises(ValueError, match="每日只能一筆"):
        compute_trip_per_diem([{"date": d, "per_diem_base": 100} for d in dates])


def test_negative_approved_days_rejected():
    with pytest.raises(ValueError, match="approved_days"):
        compute_trip_per_diem([], approved_days=-1)


def test_empty_optional_handbook_blocks_are_valid():
    data = json.loads(Path("examples/02-sample-agency.trip.json").read_text())
    data.update(itinerary=[], lodging=[], emergency_contacts=[], notes=[])
    validate_trip(data)


def test_spreadsheet_text_cannot_become_formula(tmp_path):
    out = tmp_path / "literal.xlsx"
    render_finance_xlsx({"agency": {"full_name": "示範"}, "per_diem_inputs": {
        "segments": [], "manual_items": [{"label": "=1+1", "amount_usd": 5, "note": "=SUM(A1)"}]}}, out)
    wb = openpyxl.load_workbook(out)
    assert wb.active["A3"].data_type == "s"
    assert wb.active["F3"].value == "=SUM(A1)"
    wb.close()
