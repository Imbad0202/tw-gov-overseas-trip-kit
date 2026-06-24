# tests/test_schema_finance.py
import json, pathlib, pytest
from jsonschema import validate, ValidationError

SCHEMA = json.loads(pathlib.Path("schema/trip-finance.schema.json").read_text(encoding="utf-8"))

def test_signatures_is_array():
    ok = {
        "agency": {"full_name": "○○部"},
        "signatures": [{"role": "出國人", "name": ""}, {"role": "單位主管", "name": ""}],
        "per_diem_inputs": {"segments": []},
    }
    validate(ok, SCHEMA)

def test_segment_requires_per_diem_base():
    # segment 缺 per_diem_base（required）→ fail
    bad = {
        "agency": {"full_name": "○○部"},
        "per_diem_inputs": {"segments": [{"date": "2027-03-01"}]},
    }
    with pytest.raises(ValidationError):
        validate(bad, SCHEMA)


# --- P1-4：schema minimum / uniqueItems ---
def test_negative_per_diem_base_rejected():
    # P1-4：per_diem_base minimum: 0，負值應 fail
    bad = {
        "agency": {"full_name": "○○部"},
        "per_diem_inputs": {"segments": [{"date": "2027-03-01", "per_diem_base": -100}]},
    }
    with pytest.raises(ValidationError):
        validate(bad, SCHEMA)


def test_negative_cash_allowance_rejected():
    # P1-4：cash_allowance_usd minimum: 0，負值應 fail
    bad = {
        "agency": {"full_name": "○○部"},
        "per_diem_inputs": {"segments": [
            {"date": "2027-03-01", "per_diem_base": 300, "cash_allowance_usd": -10}
        ]},
    }
    with pytest.raises(ValidationError):
        validate(bad, SCHEMA)


def test_duplicate_meals_not_provided_rejected():
    # P1-4：meals_not_provided uniqueItems: true，重複餐別應 fail
    bad = {
        "agency": {"full_name": "○○部"},
        "per_diem_inputs": {"segments": [
            {"date": "2027-03-01", "per_diem_base": 300,
             "meals_not_provided": ["dinner", "dinner"]}
        ]},
    }
    with pytest.raises(ValidationError):
        validate(bad, SCHEMA)
