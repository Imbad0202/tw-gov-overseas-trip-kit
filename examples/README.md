# examples/

本目錄提供兩種合成範例，協助各機關快速了解 `trip.json` 與 `trip-finance.json` 的欄位填寫方式。
所有範例均為**完全虛構**：機關名稱「○○部」、人名「王示範」、日期 2027 年、城市曼谷（組合非特定活動），不代表任何真實機關、人員或出訪紀錄。

---

## 檔案說明

| 檔名 | 說明 |
|---|---|
| `01-blank-template.trip.json` | 帶 `_comment` 提示的空白範本（用於複製後填寫，驗證前須刪除所有 `_comment` 欄位） |
| `02-sample-agency.trip.json` | 合成行程範例（通過 `trip.schema.json`） |
| `02-sample-agency.trip-finance.json` | 合成費用明細範例（通過 `trip-finance.schema.json`） |

---

## 如何帶入你機關的範例

### 1. 複製空白範本

```bash
cp examples/01-blank-template.trip.json my-trip.json
```

### 2. 填入機關資料

開啟 `my-trip.json`，依 `_comment` 說明填入：

- `agency.full_name`：你機關的正式全銜（必填）
- `traveler.name`：出國人員姓名（必填）
- `trip.purpose_category`：出國類別，限用 schema 列舉值（必填）
- `trip.country` / `trip.city`：出訪國家與城市（city 對應日支表，未列入填「其他」）
- `trip.start_date` / `trip.end_date`：ISO 8601 格式（必填）

### 3. 刪除所有 `_comment` 欄位後驗證

注意：空白範本的 `_comment` 欄位**不符合** `additionalProperties: false` 規則，填寫完畢後必須刪除再驗證。

```bash
# 建議使用 check-jsonschema（pip install check-jsonschema）
check-jsonschema --schemafile schema/trip.schema.json my-trip.json
```

或以 Python 方式驗證：

```python
import json, pathlib
from jsonschema import validate, Draft7Validator
schema = json.loads(pathlib.Path("schema/trip.schema.json").read_text())
data   = json.loads(pathlib.Path("my-trip.json").read_text())
validate(instance=data, schema=schema)
```

### 4. 建立費用明細檔

參考 `02-sample-agency.trip-finance.json`，依當年度官方日支表填入每日的 `per_diem_base`（美元）。
工具不內建日支表數額，需承辦人查表後手動填入。

```bash
check-jsonschema --schemafile schema/trip-finance.schema.json my-trip-finance.json
```

### 5. 執行計算與輸出

工具以 Python API 呼叫，無 `python -m calc` 入口。請參考 `SKILL.md` 或 `README.md` 的快速使用範例：

```python
# 請在專案根目錄（tw-gov-overseas-trip-kit/）執行
import json, pathlib
from calc.per_diem import compute_trip_per_diem
from render.render_html import render_html
from render.render_docx import render_report_docx, render_review_table_docx
from render.render_finance_xlsx import render_finance_xlsx

trip = json.loads(pathlib.Path("my-trip.json").read_text(encoding="utf-8"))
fin  = json.loads(pathlib.Path("my-trip-finance.json").read_text(encoding="utf-8"))
result = compute_trip_per_diem(fin["per_diem_inputs"]["segments"],
                               fin["per_diem_inputs"].get("manual_items"),
                               approved_days=fin["per_diem_inputs"].get("approved_days"))
render_html(trip, "pre_trip.html")
render_report_docx(trip, "report.docx")
render_review_table_docx(trip, "review_table.docx")
render_finance_xlsx(fin, "finance.xlsx")
```

---

## 注意事項

- 日支基準額（`per_diem_base`）需填入**當年度**行政院核定之日支表數額，工具不自動查表。
- `01-blank-template.trip.json` 因含 `_comment` 額外欄位，**不通過 schema 驗證**，僅供填寫參考。
- 驗證通過不等同核准，各機關仍須依規定程序辦理。
