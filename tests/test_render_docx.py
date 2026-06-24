# tests/test_render_docx.py
import pathlib, pytest
from docx import Document
from render.render_docx import render_report_docx

DATA = {
    "agency": {"full_name": "○○部", "unit": "綜合規劃司"},
    "traveler": {"name": "王測試", "title": "科員"},
    "trip": {"purpose_category": "開會", "country": "日本",
             "start_date": "2027-03-01", "end_date": "2027-03-05"},
    "summary": "本" * 250,
}

def test_renders_required_sections(tmp_path):
    out = tmp_path / "report.docx"
    render_report_docx(DATA, str(out))
    doc = Document(str(out))
    texts = "\n".join(p.text for p in doc.paragraphs)
    assert "壹、目的" in texts
    assert "貳、過程" in texts
    assert "參、心得及建議" in texts
    assert "○○部" in texts          # 機關名從 agency 讀
    assert "綜合規劃司" in texts      # 單位欄

def test_bad_summary_fails(tmp_path):
    bad = {**DATA, "summary": "太短"}
    with pytest.raises(Exception):
        render_report_docx(bad, str(tmp_path / "x.docx"))
