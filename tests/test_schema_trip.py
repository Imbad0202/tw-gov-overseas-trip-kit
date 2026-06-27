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


def _base():
    return {
        "agency": {"full_name": "○○部"},
        "traveler": {"name": "王小明", "title": "科員"},
        "trip": {"purpose_category": "開會", "country": "日本",
                 "start_date": "2027-03-01", "end_date": "2027-03-05"},
    }


def test_flights_optional_omitted_passes():
    """flights 為 optional：省略不影響驗證。"""
    validate(_base(), SCHEMA)


def test_valid_flights_passes():
    data = {**_base(), "flights": [{
        "leg_n": 1, "date": "2027-03-01", "route": "城市A(AAA)→城市B(BBB)",
        "departure_time": "08:50", "arrival_time": "11:40", "flight_no": "ZZ123",
        "is_layover": False, "source": "searched",
    }]}
    validate(data, SCHEMA)


def test_flight_missing_required_field_fails():
    data = {**_base(), "flights": [{
        "leg_n": 1, "date": "2027-03-01", "route": "城市A(AAA)→城市B(BBB)",
        "departure_time": "08:50", "arrival_time": "11:40",  # 缺 flight_no
    }]}
    with pytest.raises(ValidationError):
        validate(data, SCHEMA)


def test_flight_bad_time_pattern_fails():
    data = {**_base(), "flights": [{
        "leg_n": 1, "date": "2027-03-01", "route": "城市A(AAA)→城市B(BBB)",
        "departure_time": "8:50", "arrival_time": "11:40", "flight_no": "ZZ123",  # 非 HH:MM（單位數）
    }]}
    with pytest.raises(ValidationError):
        validate(data, SCHEMA)


def test_flight_out_of_range_time_fails():
    """非法時鐘（24:75 / 25:00 / 08:60）→ schema 擋（pattern 收緊到 HH 0-23/MM 0-59）。"""
    for bad in ("24:75", "25:00", "08:60", "24:00"):
        data = {**_base(), "flights": [{
            "leg_n": 1, "date": "2027-03-01", "route": "城市A(AAA)→城市B(BBB)",
            "departure_time": bad, "arrival_time": "11:40", "flight_no": "ZZ123",
        }]}
        with pytest.raises(ValidationError):
            validate(data, SCHEMA)


def test_flight_unknown_field_fails():
    """additionalProperties:false — 未知欄位被擋（防 schema 漂移）。"""
    data = {**_base(), "flights": [{
        "leg_n": 1, "date": "2027-03-01", "route": "城市A(AAA)→城市B(BBB)",
        "departure_time": "08:50", "arrival_time": "11:40", "flight_no": "ZZ123",
        "bogus": "leak",
    }]}
    with pytest.raises(ValidationError):
        validate(data, SCHEMA)


def test_flight_empty_route_fails():
    """route 為 required 但空字串無用（航班資訊不可辨識）→ minLength:1 應擋。"""
    data = {**_base(), "flights": [{
        "leg_n": 1, "date": "2027-03-01", "route": "",
        "departure_time": "08:50", "arrival_time": "11:40", "flight_no": "ZZ123",
    }]}
    with pytest.raises(ValidationError):
        validate(data, SCHEMA)


def test_flight_empty_flight_no_fails():
    """flight_no 為 required 但空字串無用（無從核銷/辨識）→ minLength:1 應擋。"""
    data = {**_base(), "flights": [{
        "leg_n": 1, "date": "2027-03-01", "route": "城市A(AAA)→城市B(BBB)",
        "departure_time": "08:50", "arrival_time": "11:40", "flight_no": "",
    }]}
    with pytest.raises(ValidationError):
        validate(data, SCHEMA)


def test_flight_departure_time_next_day_field_accepted():
    """跨日出發旗標：pipeline（dep_next_day）+ renderer（08:00+1）都支援跨日出發，
    schema 須對稱有 departure_time_next_day（否則選定跨日連接航班無法寫入 trip.json）。"""
    data = {**_base(), "flights": [{
        "leg_n": 2, "date": "2027-03-01", "route": "城市B(BBB)→城市C(CCC)",
        "departure_time": "08:00", "arrival_time": "10:00", "flight_no": "ZZ456",
        "departure_time_next_day": True, "arrival_time_next_day": True,
        "is_layover": True,
    }]}
    validate(data, SCHEMA)  # 不得拋
