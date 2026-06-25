# tests/test_render_html.py
import pathlib
from render.render_html import render_html

DATA = {"agency": {"full_name": "○○部"},
        "traveler": {"name": "王測試"},
        "trip": {"purpose_category": "開會", "country": "日本",
                 "start_date": "2027-03-01", "end_date": "2027-03-05"}}


def _render(tmp_path, data, fname="pre_trip.html"):
    out = tmp_path / fname
    render_html(data, str(out))
    return out.read_text(encoding="utf-8")


def test_html_parametrized(tmp_path):
    html = _render(tmp_path, DATA)
    assert "○○部" in html and "日本" in html
    assert "HEEACT" not in html and "heeact" not in html   # 零 HEEACT


def test_no_hardcoded_agency(tmp_path):
    other = {**DATA, "agency": {"full_name": "△△署"}}
    html = _render(tmp_path, other, "x.html")
    assert "△△署" in html


# ── 行前手冊：可選區塊（甲-基礎） ───────────────────────────────────────────

# 以 <h2> 標題標籤判斷區塊是否「實際渲染」——CSS 註解含中文區塊名，
# 用裸字串包含會誤判，必須比對標題標籤。
_SECTION_HEADINGS = ["<h2>逐日行程", "<h2>住宿資訊", "<h2>緊急聯絡", "<h2>行前注意事項"]


def test_minimal_has_no_optional_sections(tmp_path):
    """只有必填欄位時，四個可選區塊都不渲染（資料驅動、空區塊跳過）。"""
    html = _render(tmp_path, DATA)
    for h in _SECTION_HEADINGS:
        assert h not in html, f"未提供資料卻渲染了區塊：{h}"
    # 基本資訊區一律渲染
    assert "派赴國家地區" in html
    # 佔位符不可殘留
    assert "HANDBOOK_TITLE" not in html and "HANDBOOK_BODY" not in html


def test_empty_arrays_skipped(tmp_path):
    """空陣列等同於缺欄位，不渲染該區塊。"""
    data = {**DATA, "itinerary": [], "lodging": [], "emergency_contacts": [], "notes": []}
    html = _render(tmp_path, data)
    for h in _SECTION_HEADINGS:
        assert h not in html, f"空陣列卻渲染了區塊：{h}"


def test_full_handbook_renders_all_sections(tmp_path):
    """齊備資料時四個區塊都渲染。"""
    data = {
        **DATA,
        "itinerary": [
            {"date": "2027-03-01", "label": "第一日",
             "items": [{"time": "09:00", "activity": "報到", "location": "會場"}]},
        ],
        "lodging": [{"name": "示範旅館", "phone": "+81-3-0000-0000"}],
        "emergency_contacts": [{"label": "駐外館處", "phone": "+81-3-1111-1111"}],
        "notes": ["記得帶護照"],
    }
    html = _render(tmp_path, data)
    assert "逐日行程" in html and "第一日" in html and "報到" in html
    assert "住宿資訊" in html and "示範旅館" in html
    assert "緊急聯絡" in html and "駐外館處" in html
    assert "行前注意事項" in html and "記得帶護照" in html


def test_multi_day_multi_segment(tmp_path):
    """多日多段：每天多個時段都要渲染。"""
    days = [
        {"date": f"2027-03-0{d}", "label": f"第{d}日",
         "items": [{"time": f"{h:02d}:00", "activity": f"議程{d}-{h}"} for h in (9, 11, 14)]}
        for d in (1, 2, 3)
    ]
    data = {**DATA, "itinerary": days}
    html = _render(tmp_path, data)
    for d in (1, 2, 3):
        assert f"第{d}日" in html
        for h in (9, 11, 14):
            assert f"議程{d}-{h}" in html


def test_optional_item_fields_omitted_cleanly(tmp_path):
    """item 缺 time/location/note 時不印 None、不留空欄位文字。"""
    data = {**DATA, "itinerary": [
        {"label": "純事項日", "items": [{"activity": "只有事項"}]}]}
    html = _render(tmp_path, data)
    assert "只有事項" in html
    assert "None" not in html


def test_html_escape_prevents_injection(tmp_path):
    """資料中的 HTML 特殊字元必須被 escape，不可形成可執行標籤。"""
    data = {**DATA, "notes": ["<script>alert(1)</script> & <b>x</b>"]}
    html = _render(tmp_path, data)
    # 原始尖角標籤不可出現在輸出（已被 escape）
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html


def test_no_placeholder_or_none_in_full_render(tmp_path):
    """齊備資料渲染後不可有佔位符殘留或 None 漏字。"""
    data = {
        **DATA,
        "itinerary": [{"label": "X", "items": [{"activity": "A"}]}],
        "lodging": [{"name": "L"}],
        "emergency_contacts": [{"label": "E"}],
        "notes": ["N"],
    }
    html = _render(tmp_path, data)
    assert "HANDBOOK_TITLE" not in html and "HANDBOOK_BODY" not in html
    assert ">None<" not in html and "None" not in html
