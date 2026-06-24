"""TDD: render_finance_xlsx — 逐日日支明細 + B 類 manual_items + 總計（R6 進位）+ 動態簽章列。"""
import openpyxl
from render.render_finance_xlsx import render_finance_xlsx

DATA = {
    "agency": {"full_name": "○○部"},
    "per_diem_inputs": {"segments": [
        {"date": "2027-03-01", "per_diem_base": 284, "lodging_city": "曼谷", "country": "泰國"},
        {"date": "2027-03-02", "per_diem_base": 284, "lodging_city": "曼谷", "country": "泰國", "is_return_day": True},
    ], "manual_items": [{"label": "商務艙差額", "amount_usd": 500}]},
    "signatures": [{"role": "出國人", "name": ""}, {"role": "主辦單位", "name": ""}],
}


def test_total_and_signatures(tmp_path):
    out = tmp_path / "finance.xlsx"
    render_finance_xlsx(DATA, str(out))
    wb = openpyxl.load_workbook(str(out))
    ws = wb.active
    cells = [c.value for row in ws.iter_rows() for c in row if c.value is not None]
    joined = " ".join(str(c) for c in cells)
    assert "○○部" in joined
    assert "出國人" in joined and "主辦單位" in joined   # 動態簽章
    assert "商務艙差額" in joined                        # B 類 manual_items label 有輸出
    # 曼谷 284 + 返國日 284*0.3=85.2 + 500 = 869.2 → R6 進位 870
    assert 870 in cells
