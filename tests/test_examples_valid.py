"""
Task 11 — Examples validation tests.
Verifies that synthetic example files:
1. Pass trip.schema.json validation
2. Pass trip-finance.schema.json validation
3. Contain no real PII markers (HEEACT / 高等教育評鑑)
"""
import json
import pathlib

from jsonschema import validate

REPO = pathlib.Path(__file__).parent.parent

TRIP_SCHEMA = json.loads((REPO / "schema" / "trip.schema.json").read_text(encoding="utf-8"))
FIN_SCHEMA = json.loads((REPO / "schema" / "trip-finance.schema.json").read_text(encoding="utf-8"))


def test_sample_trip_valid():
    data = json.loads((REPO / "examples" / "02-sample-agency.trip.json").read_text(encoding="utf-8"))
    validate(data, TRIP_SCHEMA)


def test_sample_finance_valid():
    data = json.loads(
        (REPO / "examples" / "02-sample-agency.trip-finance.json").read_text(encoding="utf-8")
    )
    validate(data, FIN_SCHEMA)


def test_no_real_pii_in_examples():
    for f in (REPO / "examples").glob("*.json"):
        txt = f.read_text(encoding="utf-8")
        assert "HEEACT" not in txt, f"{f.name} contains 'HEEACT'"
        assert "高等教育評鑑" not in txt, f"{f.name} contains '高等教育評鑑'"
