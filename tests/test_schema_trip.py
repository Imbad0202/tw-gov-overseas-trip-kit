# tests/test_schema_trip.py
import json, pathlib, pytest
from jsonschema import validate, ValidationError

SCHEMA = json.loads(pathlib.Path("schema/trip.schema.json").read_text(encoding="utf-8"))

def test_missing_agency_full_name_fails():
    bad = {"agency": {"unit": "某單位"}, "traveler": {"name": "王小明"}}
    with pytest.raises(ValidationError):
        validate(bad, SCHEMA)

def test_unknown_top_level_property_fails():
    bad = {"agency": {"full_name": "某機關"}, "extra_field": "leak"}
    with pytest.raises(ValidationError):
        validate(bad, SCHEMA)

def test_valid_minimal_passes():
    ok = {
        "agency": {"full_name": "○○部"},
        "traveler": {"name": "王小明", "title": "科員"},
        "trip": {"purpose_category": "開會", "country": "日本",
                 "start_date": "2027-03-01", "end_date": "2027-03-05"},
    }
    validate(ok, SCHEMA)  # 不拋例外
