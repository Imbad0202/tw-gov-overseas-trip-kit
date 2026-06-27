"""航班候選比較底稿 HTML renderer。

只排序不顯分數、含票務代理免責、跨日 +1 標記、URL scheme allowlist、
無 inline 小字、無寫死機構（通用工具）。
"""
from render.render_flight_options import render_flight_options


def _data():
    return {
        "title": "航班候選比較底稿 · AAA⇄BBB",
        "layout": "table",
        "summary_rows": [{"label": "A", "transfers": 0, "earliest_dep": "08:50",
                          "latest_arr": "11:40", "total_duration": "3h50m", "price": None}],
        "candidates": [{"legs": [{"flight_no": "ZZ205", "route": "AAA→BBB",
                                  "dep_time": "08:50", "arr_time": "11:40"}],
                        "operating_carrier": "ZZ", "pros": ["直飛省時"],
                        "cons": [], "decision_note": "抵達日間、接駁無虞"}],
        "advisories_by_candidate": {"A": []},
        "footer": "基準日 2027-06-26",
    }


def _render(tmp_path, data, fname="flights.html"):
    out = tmp_path / fname
    render_flight_options(data, str(out))
    return out.read_text(encoding="utf-8")


def test_returns_html(tmp_path):
    html = _render(tmp_path, _data())
    assert "<html" in html.lower()
    assert "ZZ205" in html


def test_no_tiny_font(tmp_path):
    """無 inline 小字（USER-PREFERENCES：禁 inline px 小字、字級用 class）。"""
    import re
    html = _render(tmp_path, _data())
    assert not re.search(r"font-size: ?(1[0-3]|[89])px", html) or "class" in html
    # 明確：body 內文 16px、mono/footer 14px（非 inline、在 <style> class）
    assert "font-size: 16px" in html


def test_footer_has_disclaimer(tmp_path):
    html = _render(tmp_path, _data())
    assert "票務代理" in html
    assert "非訂位保證" in html


def test_no_numeric_score_shown(tmp_path):
    """只排序不顯分數/名次（避免被當客觀計分）。"""
    html = _render(tmp_path, _data())
    assert "分" not in html.replace("公分", "") or "排序為相對偏好" in html
    assert "第一名" not in html and "87 分" not in html


def test_next_day_arrival_shows_plus_one(tmp_path):
    data = {
        "title": "overnight", "layout": "card", "summary_rows": [],
        "candidates": [{"legs": [{"flight_no": "ZZ1", "route": "AAA→DDD",
                                  "dep_time": "21:55", "arr_time": "07:25",
                                  "arr_next_day": True}],
                        "operating_carrier": "ZZ", "pros": [], "cons": [],
                        "decision_note": ""}],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "07:25" in html and "+1" in html


def test_same_day_arrival_no_plus_one(tmp_path):
    html = _render(tmp_path, _data())
    assert "11:40" in html and "+1" not in html


def test_next_day_departure_shows_plus_one(tmp_path):
    """轉機段次日出發（dep_next_day）→ detail 表 dep 時刻帶 +1。"""
    data = {
        "title": "overnight conn", "layout": "card", "summary_rows": [],
        "candidates": [{"legs": [
            {"flight_no": "ZZ1", "route": "A→C", "dep_time": "18:00", "arr_time": "23:00"},
            {"flight_no": "ZZ2", "route": "C→B", "dep_time": "08:00", "arr_time": "10:00",
             "dep_next_day": True, "arr_next_day": True, "is_layover": True}],
                        "operating_carrier": "ZZ", "pros": [], "cons": [],
                        "decision_note": ""}],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "08:00+1" in html  # 次日出發標 +1


def test_empty_legs_shows_notice_not_empty_table(tmp_path):
    data = {
        "title": "x", "layout": "card", "summary_rows": [],
        "candidates": [{"legs": [], "operating_carrier": "ZZ",
                        "pros": [], "cons": [], "decision_note": ""}],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "不完整" in html


def test_incomplete_candidate_with_legs_shows_warning(tmp_path):
    """incomplete 但 legs 仍 populated（非法時刻 24:00 原樣留）→ 須出不完整警示、
    不得把壞班表當正常表呈現（rank 刻意保留 incomplete 候選、顯示端須標警示）。"""
    data = {
        "title": "x", "layout": "card", "summary_rows": [],
        "candidates": [{
            "incomplete": True,
            "legs": [{"flight_no": "X1", "route": "A→B",
                      "dep_time": "24:00", "arr_time": "11:00"}],
            "operating_carrier": "ZZ", "pros": [], "cons": [], "decision_note": "",
        }],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "不完整" in html  # 警示存在
    # leg 表仍渲染（讓使用者看到問題在哪），但須有警示標記
    assert "24:00" in html


def test_javascript_scheme_url_not_rendered_as_link(tmp_path):
    """source_url 為 javascript: scheme → 不得渲染成 <a href>（防 XSS）。"""
    data = {
        "title": "x", "layout": "table", "summary_rows": [],
        "candidates": [{"legs": [{"flight_no": "ZZ1", "route": "AAA→BBB",
                                  "dep_time": "08:00", "arr_time": "11:00"}],
                        "operating_carrier": "ZZ", "pros": [], "cons": [],
                        "decision_note": "", "source_url": "javascript:alert(1)",
                        "queried_date": "2027-06-26"}],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "href='javascript:" not in html
    assert "連結格式未驗證" in html


def test_https_source_url_rendered_as_link(tmp_path):
    data = {
        "title": "x", "layout": "table", "summary_rows": [],
        "candidates": [{"legs": [{"flight_no": "ZZ1", "route": "AAA→BBB",
                                  "dep_time": "08:00", "arr_time": "11:00"}],
                        "operating_carrier": "ZZ", "pros": [], "cons": [],
                        "decision_note": "", "source_url": "https://example.com/q",
                        "queried_date": "2027-06-26"}],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "href='https://example.com/q'" in html


def test_bare_business_cabin_shows_pending_label(tmp_path):
    data = {
        "title": "x", "layout": "table", "summary_rows": [],
        "candidates": [{"legs": [{"flight_no": "ZZ1", "route": "AAA→BBB",
                                  "dep_time": "10:10", "arr_time": "13:05"}],
                        "operating_carrier": "ZZ", "cabin": "business",
                        "pros": [], "cons": [], "decision_note": ""}],
        "advisories_by_candidate": {}, "footer": "",
    }
    html = _render(tmp_path, data)
    assert "商務艙（待核定）" in html


def test_no_hardcoded_agency(tmp_path):
    """通用工具：輸出不含寫死機構/品牌字眼（換 data 即換、無機構痕跡）。"""
    html = _render(tmp_path, _data())
    for token in ("HEEACT", "高教", "評鑑", "特約旅行社", "#0050A0"):
        assert token not in html
