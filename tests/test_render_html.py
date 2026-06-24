# tests/test_render_html.py
import pathlib
from render.render_html import render_html

DATA = {"agency": {"full_name": "○○部"},
        "traveler": {"name": "王測試"},
        "trip": {"purpose_category": "開會", "country": "日本",
                 "start_date": "2027-03-01", "end_date": "2027-03-05"}}

def test_html_parametrized(tmp_path):
    out = tmp_path / "pre_trip.html"
    render_html(DATA, str(out))
    html = out.read_text(encoding="utf-8")
    assert "○○部" in html and "日本" in html
    assert "HEEACT" not in html and "heeact" not in html   # 零 HEEACT

def test_no_hardcoded_agency(tmp_path):
    other = {**DATA, "agency": {"full_name": "△△署"}}
    out = tmp_path / "x.html"
    render_html(other, str(out))
    assert "△△署" in out.read_text(encoding="utf-8")
