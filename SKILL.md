---
name: tw-gov-overseas-trip-kit
version: 1.3.0
description: >
  台灣公務機關出國報告文件產生工具。對齊行政院出國報告綜合處理要點附件一／二格式，
  援引國外出差旅費報支要點（114.05.13）計算日支費。從一份 trip.json 產出五種輸出：
  出國報告書 docx（附件一）、審核表 docx（附件二）、經費規劃表 xlsx、行前手冊 html
  （可選，逐日議程／住宿／緊急聯絡／注意事項，可印 PDF）、航班查價對照表 html
  （可選，行前查價底稿、相對排序、非訂票工具）。使用者帶入自己機關的資料，
  日支數額表由使用者填當年度官方版本（不內建）。觸發：產出國報告、出國報告書、審核表、
  經費規劃表、行前手冊、日支費計算、國外出差旅費、出差核銷文件、航班查價、航班比價、班機比較。
license: MIT
---

# SKILL.md — tw-gov-overseas-trip-kit 進階用法

> **版本鎖定提醒**：本工具的計算規則對齊「國外出差旅費報支要點」114.05.13 修正版。
> 日支數額表（生活費日支數額表）**不內建於工具**，須由使用者帶入當年度官方版本。
> 詳見本文〈日支基準額填值流程〉一節及 [DISCLAIMER.md](DISCLAIMER.md)。

---

## 目錄

1. [輸出文件用途](#輸出文件用途)
2. [行前手冊（可選 deliverable）](#行前手冊可選-deliverable)
3. [航班查價比較（可選 deliverable）](#航班查價比較可選-deliverable)
4. [輸入 schema 路徑](#輸入-schema-路徑)
5. [充實報告本文（目的／過程／心得及建議）](#充實報告本文目的過程心得及建議)
6. [啟動流程：帶入你機關的範例](#啟動流程帶入你機關的範例)
7. [日支基準額填值流程（`per_diem_base`）](#日支基準額填值流程per_diem_base)
8. [B 類人工值填入](#b-類人工值填入)
9. [計算器 scope 邊界](#計算器-scope-邊界)
10. [docx 轉 PDF 指引](#docx-轉-pdf-指引)
11. [法規版本鎖定提醒與免責聲明](#法規版本鎖定提醒與免責聲明)

---

## 輸出文件用途

| 輸出文件 | 產生函式 | 用途 |
|---|---|---|
| 出國報告書（`.docx`） | `render.render_docx.render_report_docx(data, out_path)` | 對齊行政院出國報告綜合處理要點**附件一**格式，含封面、摘要、壹目的/貳過程/參心得及建議章節與頁碼。為可編輯 Word 文件，送核前於 Word 補填本文內容。 |
| 審核表（`.docx`） | `render.render_docx.render_review_table_docx(data, out_path)` | 對齊**附件二**審核表，10 項勾選欄（出國人員自我檢核 + 計畫主辦機關審核）+ 三段簽章列。 |
| 經費規劃表（`.xlsx`） | `render.render_finance_xlsx.render_finance_xlsx(data, out_path)` | 逐日日支明細 + B 類人工項目 + 尾數進位整數總計（美元）+ 動態簽章列。 |
| 行前手冊（`.html`，**可選**） | `render.render_html.render_html(data, out_path)` | 供出差同仁攜帶的行前手冊，資料驅動：逐日議程／住宿／緊急聯絡／注意事項皆為選填，缺漏即不渲染該區塊。可直接用瀏覽器開啟，或 `cmd+P` 列印為 PDF。詳見〈行前手冊（可選 deliverable）〉一節。 |
| 航班查價對照表（`.html`，**可選**） | `render.render_flight_options.render_flight_options(data, out_path)` | 行前查價比較底稿：把航班候選相對排序成對照表供選擇核定。排序純函式在 `calc.flight_rank`。只排序不顯分數、附票務代理免責。詳見〈航班查價比較（可選 deliverable）〉一節。 |

報告書 docx 與審核表 docx 讀取 `schema/trip.schema.json` 格式的資料；
經費規劃表讀取 `schema/trip-finance.schema.json` 格式的資料；
行前手冊 HTML 讀取 `schema/trip.schema.json` 格式的資料；
航班查價對照表讀取候選比較資料（in-memory dict，非 trip.json）。

---

## 行前手冊（可選 deliverable）

行前手冊是供出差同仁攜帶的整理頁，**非必產**：每個機關、每趟出差未必都有需求。報告書、審核表、經費規劃表是核銷與上呈所需，行前手冊則是依需要才產生。

### 資料驅動，缺漏即不渲染

手冊讀 `trip.schema.json`，下列四個區塊**全部選填**，缺欄位或填空陣列時，該區塊完全不出現（不留空表格、不印佔位字）：

| 區塊 | 欄位 | 說明 |
|---|---|---|
| `itinerary` | 逐日陣列，每日 `{date?, label?, items[]}`；item `{time?, activity, location?, note?}` | 逐日議程／行程表。`items` 與 `activity` 為必填，其餘選填。支援多日多段（多天、每天多個時段）。 |
| `lodging` | 陣列 `{name, address?, phone?, check_in?, check_out?, note?}` | 住宿資訊。多段行程可多筆。`name` 必填。 |
| `emergency_contacts` | 陣列 `{label, name?, phone?, note?}` | 緊急聯絡，例如駐外館處、境外主辦、國內承辦窗口。`label` 必填。 |
| `notes` | 字串陣列 | 注意事項清單（簽證、時差、核銷、保密等）。 |

只填基本資訊（機關、出國人員、國家、期間、類別）也能產出——此時手冊只有抬頭資訊區，四個可選區塊都不渲染。

### 產生與列印

```python
from render.render_html import render_html
render_html(trip, "handbook.html")
```

產出為單一 self-contained HTML（內嵌樣式、無外部字型或 CDN，可離線開啟）。瀏覽器開啟後 `cmd+P`（macOS）／`Ctrl+P`（Windows）即可列印或另存 PDF；樣式已設定 A4 版面與分頁，列印時自動避免區塊被切斷。

格式不限定固定版面：政府訪問團、外交行程等較複雜的多日多段行程，靠 `itinerary` 的逐日結構承載，機關按需填入需要的區塊即可。

### 進一步美化（可選，非依賴）

本工具產出的手冊採通用中性視覺，已可直接交付使用。若希望針對特定場合再做視覺打磨，可自行搭配 `impeccable` 等前端設計 skill 對產出的 HTML 再加工。**此為選用項目，工具本身不依賴、也不會自動呼叫任何外部 skill**；未安裝這類 skill 不影響手冊正常產出。

---

## 航班查價比較（可選 deliverable）

行前準備階段的查價底稿：得知公務行程後，把幾個航班候選整理成對照表、相對排序，供選擇與核定。**定位是比較底稿、非訂票工具**，也**不往後連動核銷**——班機確定後以實際購票資訊為準。

### 兩個模組

| 模組 | 職責 |
|---|---|
| `calc.flight_rank` | 純函式：候選正規化（`normalize_candidate`）、相對排序（`rank_candidates`）、版面判定（`choose_layout`）、摘要列（`summary_rows`）。零外部依賴。 |
| `render.render_flight_options` | 把排序後的候選資料渲染成 HTML 對照表、寫入檔案。 |

### 排序規則（相對偏好、非硬門檻）

> 尊重休息時間 > 轉機/候機時間越短越好 > 行李盡量直掛 > 票價

「尊重休息時間」是三條可計算規則：①出發端留 ≥3hr buffer、避凌晨出發（含紅眼）；②避免凌晨抵達；③時差 >4hr 時落地至公務首場留 >8hr 調時差。硬航線可能每個候選都違反某些原則——此時**不罷工**，永遠在矮子裡挑高個、給最佳解，缺點在該候選決策點老實標明。

### 呈現守則

對照表**只排順序、不顯示分數/名次**（避免被當客觀計分），排序理由用優缺點/決策點文字說明；附免責「以票務代理報價為準、非訂位保證」。跨日抵達標 `+1`、轉機過夜標明。

### 候選資料形狀

候選為 in-memory dict（`legs[]` 每段含 `dep_time`/`arr_time`/`is_layover`/`layover_minutes`/`baggage_through` 等），**不入 trip.json**。選定後若要寫進行程，再轉成 `flights[]` entry（標 `source: searched`）——這步是選用、且不連動其他文件。

---

## 輸入 schema 路徑

```
schema/trip.schema.json          ← 報告書 / 行前手冊 / 審核表
schema/trip-finance.schema.json  ← 經費規劃表
```

兩者均採 JSON Schema Draft 2020-12，`additionalProperties: false`（多出欄位即 fail）。

必填欄位（`trip.schema.json`）：`agency.full_name`、`traveler.name`、`trip.purpose_category`、`trip.country`、`trip.start_date`、`trip.end_date`。

必填欄位（`trip-finance.schema.json`）：`agency.full_name`、`per_diem_inputs.segments`（每筆需有 `date` 和 `per_diem_base`）。

**`summary` 欄位契約**：`summary` 在 schema 中並非 `required`（html／xlsx／審核表不需要），但**呼叫 `render_report_docx`（出國報告書）時為必填且格式受強制驗證**：須含 200–300 個中文字，且不含佔位符（`○○`、`TODO`、`待填`、`XXX`、`範例`）。不合格即 raise `SummaryError` 並中止，不產出 docx。產出報告書前請確認 `trip.json` 的 `summary` 欄位已填入 200–300 字的正式摘要。其餘 render 函式（html／xlsx／審核表）不觸發此檢核。

---

## 充實報告本文（目的／過程／心得及建議）

**重要：本工具產出的出國報告書，本文三章節（壹目的／貳過程／參心得及建議）是「標題＋灰色撰寫提示」的骨架，不是完成的內容。** 只填封面欄位與摘要、本文留空，產出的是空殼報告，不符合行政院出國報告要點「本文須具備目的、過程、心得及建議」的要求。

協助使用者產出報告時，**請主動引導使用者提供出差實況素材來充實本文**，而非只填基本欄位就交件：

- **過程**：出差期間的會議逐字稿、會議筆記、議程記錄、參訪觀察記錄、簡報與發言內容。據此寫出翔實的過程，而非泛泛帶過。
- **目的**：行前計畫、邀請函、簽辦核准文件、出國計畫表所載目的。
- **心得及建議**：使用者的觀察、收穫、可供機關研辦的具體建議（逐項分列；倘無建議寫「無」）。

引導方式範例：「為了讓報告本文完整，請提供你這趟出差的會議逐字稿或筆記、參訪記錄、以及你的心得與建議，我會據此撰寫『過程』與『心得及建議』章節。若只填基本資訊，本文會是空白骨架。」

**本工具不提供逐字稿錄製／轉錄功能**——逐字稿／筆記由使用者自行準備並提供。

**機敏資料提醒**：出差素材（尤其會議逐字稿）可能含機密資訊或他人個資。依《行政院及所屬機關（構）使用生成式 AI 參考指引》，機密文書不得使用生成式 AI 輔助；提供素材前請確認不含機密、未經同意公開之資訊或與案件無關之個資，並依貴機關規定處理。詳見 [DISCLAIMER.md](DISCLAIMER.md)。

---

## 啟動流程：帶入你機關的範例

工具不附含任何真實機關資料。啟動時請依以下步驟帶入貴機關資料：

**步驟一：複製合成範例作為起點**

```bash
cp examples/02-sample-agency.trip.json        my-agency.trip.json
cp examples/02-sample-agency.trip-finance.json my-agency.trip-finance.json
```

**步驟二：替換機關欄位**

開啟 `my-agency.trip.json`，將 `agency` 欄位的 `"○○部"` 改為貴機關全銜，`unit`、`head_title` 填實際值。`traveler` 填出差人員職稱與姓名。

```json
{
  "agency": {
    "full_name": "貴機關全銜",
    "unit": "業務單位名稱",
    "head_title": "機關首長職稱"
  },
  "traveler": {
    "name": "出差人姓名",
    "title": "職稱",
    "rank": "職等（艙等判定供承辦參考）"
  },
  "trip": { "..." : "..." }
}
```

**步驟三：填 `per_diem_base`**

每個 `segment` 的 `per_diem_base` 填當年度官方日支基準額（美元）。填值方式詳見下一節。

**步驟四：執行產生**

```python
# 請在專案根目錄（tw-gov-overseas-trip-kit/）執行
import json, pathlib
from jsonschema import Draft202012Validator, FormatChecker
from calc.per_diem import compute_trip_per_diem
from render.render_html import render_html
from render.render_docx import render_report_docx, render_review_table_docx
from render.render_finance_xlsx import render_finance_xlsx

trip = json.loads(pathlib.Path("my-agency.trip.json").read_text(encoding="utf-8"))
fin  = json.loads(pathlib.Path("my-agency.trip-finance.json").read_text(encoding="utf-8"))

# 驗證輸入：務必帶 FormatChecker，否則 schema 的 "format": "date" 不會被檢查，
# 非法日期字串（如 2027-13-99）會被誤放（jsonschema 預設不啟用 format 檢查）。
schema = json.loads(pathlib.Path("schema/trip.schema.json").read_text(encoding="utf-8"))
Draft202012Validator(schema, format_checker=FormatChecker()).validate(trip)

render_html(trip, "pre_trip.html")
render_report_docx(trip, "report.docx")
render_review_table_docx(trip, "review_table.docx")
render_finance_xlsx(fin, "finance.xlsx")
```

產出後，`report.docx` 在 Word 補填壹目的/貳過程/參心得本文，再轉 PDF 送核。

---

## 日支基準額填值流程（`per_diem_base`）

### 核心原則

工具**不內建**日支數額表。原因：數額表每年更新，若內建則版本過時即產生系統性錯誤，使用者無從察覺。因此每個 `segment` 的 `per_diem_base` 須由使用者（或 Claude Code 執行時）查**當年度**官方表填入。

### 取得方式 A：承辦手動查填

前往主計總處法規查詢系統，查詢現行「生活費日支數額表」（法規代號 FL028084）：

```
https://law.dgbas.gov.tw/lawsingle.aspx?lid=FL028084
```

確認版本年度（生效日期）與出差日期相符後，按城市/國家查對應數額填入每筆 `segment.per_diem_base`。

### 取得方式 B：請 Claude Code 執行時 WebFetch 代填

在 Claude Code session 中要求：

```
請 WebFetch 主計總處現行生活費日支數額表（FL028084），
幫我找出 [城市名] 的 [年度] 數額，填入 per_diem_base。
```

Claude Code 會嘗試取得當年度數額，填入後請確認：

1. **版本年度**：Claude 取得的是哪一版（生效日）？是否涵蓋出差日期？
2. **核銷責任**：Claude 代填的數額供起草參考，使用者**自負核銷責任**，送核前需對照原始法規頁面再確認。

### 填值原則（R4/R5）

這些是法規規定的填值判斷準則，工具不自動實作（靠填值者遵循）：

| 情境 | 填值方式 |
|---|---|
| 同日跨多地區 | 填**當日留宿地**之數額（報支要點 R4） |
| 城市未列於數額表 | 填該國「其他」欄數額（R5） |
| 國家未列於數額表 | 填地理或政治上最近國數額（R5） |
| 季節性城市（分高/低峰區間） | 填出差**當日**所屬區間之數額 |

### 欄位補充說明

- `lodging_city`：記錄留宿城市，顯示於明細表，不影響計算。
- `per_diem_base`：計算基礎，單位美元，影響所有折扣/遞減計算。

---

## B 類人工值填入

計算器自動處理「A 類」（日支費本體：住宿 70%/膳食 20%/零用 10%、返國當日 30%、長期遞減、核准日數截斷）。以下項目屬「B 類」，計算器**不自動判定**，由承辦人工計算後填入 `manual_items`：

| 項目 | 說明 |
|---|---|
| 機票（艙等） | 艙等依職等判定（要點另規，工具不判）。機票金額由承辦填實際票價或上限額。 |
| 覈實住宿費 | 住宿費覈實報支情形（適用特定條件）由承辦填實際金額。 |
| 禮品及雜費 | 依機關規定，由承辦填許可金額。 |
| 匯率調整 | 若以新台幣核銷，匯率換算由承辦依財政部公告匯率計算後填入。 |

填法：

```json
{
  "per_diem_inputs": {
    "manual_items": [
      {
        "label": "經濟艙機票（台北—目的地往返）",
        "amount_usd": 420,
        "note": "依貴機關覆核之依據"
      },
      {
        "label": "禮品費",
        "amount_usd": 50,
        "note": "依機關規定核可金額"
      }
    ]
  }
}
```

`manual_items` 的 `amount_usd` 原樣累加進 `grand_total_usd`，不另行公式處理。

---

## 計算器 scope 邊界

以下情形**不在計算器自動處理範圍**，需承辦人工判斷：

**第十點 — 駐外人員**

本工具適用一般短期出差人員。駐外人員（常駐境外機構人員）依要點第十點另有規定，本工具不涵蓋，不得直接套用。

**第十八點 — 受刑期限返國**

因受刑期限提前返國之費用計算涉及個案核定，本工具不自動處理，由承辦依第十八點規定另行計算。

**第二十三點 — 跨修法分段**

出差期間橫跨要點修正前後（數額表版本更替），計算器不自動分段套用不同版本數額，由承辦手動分段計算後分別填入各 `segment.per_diem_base`，或以 `manual_items` 補差額。

**機上/交通工具歇夜（B-6）**

搭乘飛機或交通工具之夜間行程，不適用 `is_return_day=true`（返國當日 30%）。機上歇夜應視為「供宿不供膳」，將該日 `host_provided` 設為 `"lodging_only"`（膳食 20% + 零用補足）。兩種旗標意義不同，不可混用。

**P1-2 例外（長期遞減豁免）**

國際會議/談判、外交部紅色警示地區、籌設使領館代表處辦事處等情形，可設 `reduction_exempt: true` 關閉遞減，但**是否符合豁免條件**由承辦人工判定，工具不驗證原因。

---

## docx 轉 PDF 指引

行政院出國報告要點要求送交 ODF 或 PDF 格式。本工具產出 `.docx` 為中間格式（Word 可編輯，補填本文後轉出）。

**方式一：Word / LibreOffice 手動轉換**

在 Microsoft Word 或 LibreOffice Writer 開啟 `.docx` 後：

- Windows/macOS Word：`檔案 → 匯出 → 建立 PDF/XPS` 或 `cmd+P → 儲存成 PDF`
- macOS Word：`cmd+P → PDF → 儲存成 PDF`

**方式二：LibreOffice 命令列轉換（自動化腳本適用）**

```bash
libreoffice --headless --convert-to pdf report.docx
libreoffice --headless --convert-to pdf review_table.docx
```

需先安裝 LibreOffice（`brew install --cask libreoffice` 或官網下載）。轉出的 PDF 與 `.docx` 同目錄。

**注意**：PDF 送核後，原 `.docx` 建議留存備查，勿刪除（若補正需重新產 PDF）。

---

## 法規版本鎖定提醒與免責聲明

### 法規版本

| 法規 | 本工具對齊版本 |
|---|---|
| 國外出差旅費報支要點 | 114.05.13 修正（計算規則） |
| 行政院出國報告綜合處理要點 | 107.06.20 附件一/二格式 |
| 生活費日支數額表 | **不內建**，由使用者帶入當年度版本 |

使用前請確認貴機關出差日期適用的法規版本。若報支要點已再修正，本工具尚未跟進，計算結果可能與現行規定不符。

### 數額表自負責任

無論以何種方式取得 `per_diem_base`（手動查填或請 Claude Code WebFetch 代填），**使用者自負確認責任**。Claude Code 取得之數額可能因頁面更新、取值解讀等原因產生誤差，送核前應對照主計總處法規系統原始頁面核實。

### 免責聲明全文

詳見 [DISCLAIMER.md](DISCLAIMER.md)：

1. **正確性**：本工具僅協助產生符合格式之文件範本，使用者須對所產出文件之正確性及內容自負其責；送核前應依貴機關規定完成審核。
2. **AI 基本法**：使用本工具應遵守《人工智慧基本法》（中華民國 114 年 12 月 23 日立法院三讀通過）。
3. **公務 AI 規範**：公務人員使用應遵守《行政院及所屬機關（構）使用生成式 AI 參考指引》（112 年 10 月 3 日函頒）及所屬機關自訂規範。
4. **個資法**：使用者應遵守《個人資料保護法》，切勿將機敏個資或未經同意之他人資料輸入至公開之 AI 模型。
