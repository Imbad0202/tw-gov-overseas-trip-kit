"""
Examples validation tests.
Verifies that synthetic example files:
1. Pass trip.schema.json validation
2. Pass trip-finance.schema.json validation
3. Are clearly synthetic (carry placeholder / demo markers), so no real agency
   data has crept in — asserted positively to avoid hard-coding any real
   organization name in a public repo.
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


def test_examples_are_synthetic():
    """每個 example 必須帶合成標記（示範 / ○○ / △△），確保未混入真實機關資料。
    正向斷言（要求合成標記存在），不黑名單特定機構名——後者會在 public repo
    洩漏防護對象，且漏列就失效。"""
    markers = ("示範", "○○", "△△")
    for f in (REPO / "examples").glob("*.json"):
        txt = f.read_text(encoding="utf-8")
        assert any(m in txt for m in markers), (
            f"{f.name} 未帶任何合成標記 {markers}，疑似混入真實資料"
        )
