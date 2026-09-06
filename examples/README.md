# 合成範例與填寫方式

所有範例均為虛構示範，不代表實際人員、行程、票價、緊急電話或官方日支額。

| 檔案 | 用途 |
|---|---|
| `02-sample-agency.trip.json` | 可跑的五日行程、摘要、三章本文、住宿與聯絡；須以實況替換 |
| `02-sample-agency.trip-finance.json` | 配套五日日支，合成基準 165 美元；午／晚餐依議程示範扣補 |
| `03-flight-options.json` | 獨立航班比較候選：直飛與轉機過夜；非即時查價 |
| `04-mixed-scenarios.trip-finance.json` | 多城市、供膳宿津貼、機上歇夜、私人日、延返與退款，總額 823 美元 |
| `01-blank-template.trip.json` | 舊式欄位說明範本，含 `_comment`，須刪除註解並填值才可驗證 |

## 建立自己的資料

安裝後執行：

```bash
python -m tripkit init --directory data/my-trip
```

產生 `trip.json`、`finance.json`、`flight-options.json`，不覆寫既有資料。從這份可跑的範例改值，比複製帶註解的舊範本簡單。`data/` 與 `output/` 已被 Git 忽略。

先填兩檔的 `agency.full_name`，再填 `trip.json` 的人員與起訖日期，以及 `finance.json` 的逐日資料。費用沒有從行程自動推導：議程改了供餐或住宿，請同步更新財務檔。

## 報告本文

只產手冊與審核表不用摘要與本文。要產報告時，`summary` 須有 200–300 個中文字且無佔位符，另填以下段落陣列：

```json
{
  "report_title": "出國報告名稱",
  "report_date": "2027-10-01",
  "report_content": {
    "purpose": ["依邀請函與核准計畫撰寫的正式目的。"],
    "process": ["第一段實際會議過程。", "第二段實際參訪觀察。"],
    "insights_and_recommendations": ["心得。", "第一項具體建議；無建議則寫無。"]
  }
}
```

此片段須併入已有基本資料的 `trip.json`。段落只檢查結構與有無內容，工具不查證事件真實性。未填章節，Python renderer 保留提示；CLI 需明示 `--allow-incomplete-report` 才產骨架，摘要仍須合格。

## 每日日支

一人一趟、每日一筆、日期遞增。填當日適用的官方基準額，並留來源：

```json
{
  "date": "2027-09-02",
  "country": "示範國",
  "lodging_city": "示範城",
  "per_diem_base": 100,
  "host_provided": "board_and_lodging",
  "meals_not_provided": ["dinner"],
  "cash_allowance_usd": 5,
  "rate_source": "合成值；實際須記官方表名稱、生效日、城市／季節與網址",
  "note": "示範：主辦供宿與早午餐，另給津貼。"
}
```

這是 `per_diem_inputs.segments` 中的一筆；合成額 100 下，零用補足 5、未供晚餐 8，當日合計 13 美元。

| 情境 | 欄位 |
|---|---|
| 自理膳宿 | `host_provided: "none"`（預設） |
| 供膳宿／供膳不供宿／供宿不供膳 | `board_and_lodging / board_only / lodging_only` |
| 只供部分餐 | 有供膳模式＋`meals_not_provided` 列未供的早／午／晚餐 |
| 返國日 | `is_return_day: true`；單趟僅末日，勿混同機上歇夜 |
| 私人／不報支日 | `reimbursable: false`＋`exclusion_reason`，保留日期與原基準額 |
| 未核准延返 | 設 `approved_days`；從核准起日（`approved_start_date`，預設首筆日期）起算，超期自動歸零 |
| 已核准延返 | 當日填 `approved_extension: true`，`note` 記核定依據 |
| 長駐 | 人工填 `day_index_same_place`，確認 30/90 日模型是否適合案件；豁免另填 `reduction_exempt` |

`manual_items` 僅收美元；機票、保險、退款等需人工判斷後填 `amount_usd`。原幣金額／匯率／憑證記於 `note`。完整情境與不支援範圍見[情境覆蓋表](../docs/情境覆蓋表.md)。

## 驗證與產出

```bash
python -m tripkit validate --trip data/my-trip/trip.json --finance data/my-trip/finance.json
python -m tripkit render --trip data/my-trip/trip.json --finance data/my-trip/finance.json --outputs report review finance handbook --out output/my-trip
python -m tripkit flights --input data/my-trip/flight-options.json --out output/my-trip/flight_options.html
```

航班輸入契約在 `schema/flight-options.schema.json`，與 `trip.json` 的已選定 `flights[]` 分開；候選可缺票價或身分資料，不完整候選保留並提示，格式錯誤會列欄位路徑。查詢日與來源請保留；`first_duty_local` 只帶時刻，不能解決完整跨日時間軸。

Python 使用者可先呼叫 `tripkit.validation.validate_trip`／`validate_finance`／`validate_pair`，或自行使用 `Draft202012Validator(..., format_checker=FormatChecker())`。原有 `render.*` 與 `calc.*` 函式保留；不要把低階 renderer 當成完整資料驗證入口。
