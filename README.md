# tw-gov-overseas-trip-kit

台灣公務機關出國報告文件產生工具，對齊**行政院出國報告綜合處理要點附件一／二**格式，並援引**國外出差旅費報支要點**（114.05.13 修正）計算規則。

> English version: [README_EN.md](README_EN.md)

---

## 格式來源

| 法規 | 版本 | 說明 |
|---|---|---|
| 行政院出國報告綜合處理要點 | 107.06.20 附件一／二 | 出國報告主格式 |
| 國外出差旅費報支要點 | 114.05.13 修正（院授主預字第1140101390號函） | 費用計算規則 |
| 生活費日支數額表 | 114.10.31 修正、115.1.1 生效（院授主預字第1140103430號函） | 日支費基礎——**不內建，由使用者帶入** |

完整法源清單：[docs/sources/README.md](docs/sources/README.md)

---

## 功能

- **日支費計算**：依報支要點規則處理返國當日30%折算、供膳宿補足至10%、長期駐留遞減（逾1月80%／逾3月70%）、核准日數邊界等情境
- **出國報告渲染**：DOCX（Word 可編輯，附件一格式）出國報告書與附件二審核表
- **行前手冊**（可選）：資料驅動 HTML（逐日議程／住宿／緊急聯絡／注意事項，皆選填），可瀏覽器開啟或 `cmd+P` 列印 PDF
- **財務規劃表**：Excel 格式旅費規劃表（對應旅費報告表，非附件二）；審核表（附件二格式）另由 DOCX 渲染產出
- **資料驗證**：schema 驗證必填欄位、agency required 欄位；摘要字數 200–300 中文字、禁交占位符

---

## 安裝

```bash
pip install -e ".[dev]"
```

需要 Python 3.10+。

---

## 快速使用

```python
# 請在專案根目錄（tw-gov-overseas-trip-kit/）執行
import json, pathlib
from jsonschema import validate
from calc.per_diem import compute_trip_per_diem
from render.render_html import render_html
from render.render_finance_xlsx import render_finance_xlsx

trip = json.loads(pathlib.Path("examples/02-sample-agency.trip.json").read_text(encoding="utf-8"))
fin = json.loads(pathlib.Path("examples/02-sample-agency.trip-finance.json").read_text(encoding="utf-8"))
result = compute_trip_per_diem(fin["per_diem_inputs"]["segments"],
                               fin["per_diem_inputs"].get("manual_items"),
                               approved_days=fin["per_diem_inputs"].get("approved_days"))
render_html(trip, "pre_trip.html")
render_finance_xlsx(fin, "finance.xlsx")
```

詳見 `examples/` 目錄中的合成範例。

---

## 重要聲明

本工具僅協助產生符合格式之文件範本，使用者須對所產出文件之正確性及內容**自負其責**；送核前應依貴機關規定完成審核。

完整免責聲明：[DISCLAIMER.md](DISCLAIMER.md)
版本與法源：[CITATIONS.md](CITATIONS.md)
來源聲明：[PROVENANCE.md](PROVENANCE.md)

---

## 授權

MIT License — 詳見 [LICENSE](LICENSE)
