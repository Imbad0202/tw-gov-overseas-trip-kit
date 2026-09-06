# tw-gov-overseas-trip-kit

[![Version](https://img.shields.io/badge/version-v1.5.0-blue)](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

台灣公務機關出國報告文件產生工具，對齊**行政院出國報告綜合處理要點附件一／二**格式，並援引**國外出差旅費報支要點**（114.05.13 修正、115.01.01 生效）計算規則。

> English version: [README_EN.md](README_EN.md)

---

## 三步跑出第一份文件

需要 Python 3.10+。首次在專案根目錄執行；安裝後可從任意資料夾使用。

**1. 安裝到獨立環境**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Windows PowerShell 使用 `py -m venv .venv`，再以 `.venv\Scripts\Activate.ps1` 啟用環境；也可直接以 `.venv\Scripts\python.exe` 取代下方的 `python`。

**2. 建立合成資料，直接試跑**

```bash
python -m tripkit init --directory data/my-trip
python -m tripkit render --trip data/my-trip/trip.json --finance data/my-trip/finance.json --out output/my-trip
```

會產出 `pre_trip.html`（手冊）、`review_table.docx`（審核表）、`finance.xlsx`（美元經費規劃）。資料及票價是合成示範，日支額**不是官方費率**，實際使用前務必替換。`data/`、`output/` 已排除於 Git 追蹤。

**3. 改資料、驗證，再依需要產出**

```bash
python -m tripkit validate --trip data/my-trip/trip.json --finance data/my-trip/finance.json
python -m tripkit render --trip data/my-trip/trip.json --finance data/my-trip/finance.json --out output/revised
```

只需編輯兩份 JSON：

| 資料 | 先改哪些欄位 |
|---|---|
| `trip.json` | `agency` 機關、`traveler` 人員、`trip` 目的地／日期／類別；兩檔機關名稱須一致 |
| `finance.json` | `segments` 每日一筆、查官方表填 `per_diem_base` 並記 `rate_source`；`approved_days` 核准期間（因私提前出國另填 `approved_start_date`）、供膳宿、返國日；`manual_items` 人工美元項目 |
| 手冊選填 | 議程 `itinerary`、住宿 `lodging`、聯絡 `emergency_contacts`、提醒 `notes`；可省略或填 `[]` |
| 報告選填 | `summary` 200–300 中文字；`report_content` 三章段落陣列；`report_title / report_date` 名稱與繳交日期 |

資料欄位範例見 [examples/README.md](examples/README.md)；依案件查填法見[情境覆蓋表](docs/情境覆蓋表.md)。`validate` 與 `render` 都檢查合法日期、欄位及計算輸入；驗證錯誤會列欄位路徑，驗證不過不產半套文件。

### 依需要選文件

```bash
# 只產手冊，不需要摘要與本文
python -m tripkit render --trip data/my-trip/trip.json --outputs handbook --out output/handbook

# 四種文件一起產；報告須有合格摘要及三章本文
python -m tripkit render --trip data/my-trip/trip.json --finance data/my-trip/finance.json --outputs report review finance handbook --out output/full

# 航班比較使用獨立候選資料，不查票、不訂位、不連動核銷
python -m tripkit flights --input data/my-trip/flight-options.json --out output/flights.html
```

報告本文未備妥但確實需要骨架時，加 `--allow-incomplete-report`，摘要仍須合格。完成後在 Word 核閱並轉 ODF／PDF。既有檔案預設不覆寫；確定要取代才加 `--force`，或改用新的輸出資料夾。

### 常見卡關

| 訊息／情形 | 處理方式 |
|---|---|
| `No module named tripkit/docx/openpyxl` | 使用已安裝套件的同一個 Python；啟用 `.venv` 後重新安裝 |
| JSON 格式錯誤 | 依行號修正引號、逗號；JSON 不接受註解。舊空白範本的 `_comment` 須移除 |
| `report_content` 缺段落 | 補寫三章；行前先產手冊即可；骨架用明示選項 |
| 摘要字數不合格 | `--outputs report` 會檢查 200–300 中文字與佔位符；標點／英數不計入中文字數 |
| 財務日期不一致／重複 | 每日一筆、按日期排列；同時提供兩檔時首末日一致；部分期間只提供 `--finance` |
| 日支額為 0／未填來源 | 查適用出差日期的官方表；工具不自動查表或判斷金額是否正確 |
| 改了 Excel，金額沒重算 | Excel 是產出快照；修改 JSON 後重新產檔，並保留手動編輯版本 |

所有指令都有 `--help`；亦可使用短指令 `tripkit`。Python 函式用法見 [SKILL.md](SKILL.md)。

---

## 格式來源

| 法規 | 版本 | 說明 |
|---|---|---|
| 行政院出國報告綜合處理要點 | 107.06.20 附件一／二 | 出國報告主格式 |
| 國外出差旅費報支要點 | 114.05.13 修正、115.01.01 生效（院授主預字第1140101390號函） | 費用計算規則 |
| 生活費日支數額表 | 114.10.31 修正、115.1.1 生效（院授主預字第1140103430號函） | 日支費基礎——**不內建，由使用者帶入** |

完整法源清單：[docs/sources/README.md](docs/sources/README.md)

---

## 功能

- **日支費計算**：返國日、供膳宿／餐別／津貼、核准日數、私人日排除；以十進位累計避免進位誤差。長駐有 30/90 日簡化模型，須人工覆核曆月與組合情境
- **出國報告渲染**：DOCX（Word 可編輯，附件一格式）出國報告書與附件二審核表
- **行前手冊**（可選）：資料驅動 HTML（逐日議程／住宿／緊急聯絡／注意事項，皆選填），可瀏覽器開啟或 `cmd+P` 列印 PDF
- **財務規劃表**：Excel 格式旅費規劃表（對應旅費報告表，非附件二）；審核表（附件二格式）另由 DOCX 渲染產出
- **航班查價比較**（可選）：行前查價底稿——把航班候選依「休息時間 > 轉機/候機 > 行李直掛 > 票價」相對排序，產 HTML 對照表供選擇核定。只排序不顯分數、附票務代理免責；定位為比較底稿、非訂票工具，選定後可寫入 `flights[]`（不連動核銷）
- **資料驗證**：schema 驗證必填欄位、agency required 欄位；摘要字數 200–300 中文字、禁交占位符

---

## 適用範圍與限制

本工具對齊的是**行政院出國報告要點附件一／二 + 國外出差旅費報支要點計算**這個各機關共通的底層格式，不是任何單一機關的客製版面。

**運作方式**：使用者把**資料**填進 `trip.json`（機關、人員、行程、日期等），工具**生成**對齊上述格式的 DOCX／XLSX／HTML。工具**不讀取、也不對齊個別機關自訂的格式範本檔**（例如某校的出國報告範本 `.odt`、旅費報告表 `.doc`）。

**因此**：

- 各機關可參考行政院要點格式；設置校務基金的國立專科以上學校不直接納入該要點第 1 點的學校範圍，應另確認主管機關與校內規定；若貴機關版面另有客製（校徽、頁首、額外簽核欄），請在工具產出的 DOCX 上自行補上。
- 旅費計算對齊報支要點規則，但**旅費報告表的固定版面**（交通工具班次表、供宿供膳勾選欄、多段會核簽章等）多為各機關自訂，工具產出的是通用試算表，非特定機關版面。
- **事前的出國計畫／申請簽核表**（如校務基金出國計畫表，含計畫主持人、單位會核、首長核示）屬各機關自訂的行政流程文件，**不在本工具範圍**。

目前支援一人一趟的文件與美元規劃。多人分攤、臺幣核銷、預支沖銷、特殊身分及機關簽核流程須另處理。完整可用／人工／不適用清單見[情境覆蓋表](docs/情境覆蓋表.md)，法規方向見[個案指引](docs/延返與個案指引.md)。

---

## 作為 AI Skill 使用（跨 vendor）

除了當 Python 套件直接呼叫，本工具也封裝為 AI skill，可在多種 AI 工具中使用。核心是帶 frontmatter 的 `SKILL.md`，各 vendor 入口指向同一份內容：

| 使用情境 | 入口 | 做法 |
|---|---|---|
| claude.ai / cowork | `skill.zip` | 至 [Releases](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases) 下載 `tw-gov-overseas-trip-kit-skill-vX.Y.Z.zip` 上傳載入 |
| Claude Code | `.claude-plugin/plugin.json` | clone 後以 plugin 載入，或 `git clone` 至 `~/.claude/skills/` |
| Codex / Gemini 等 CLI | `AGENTS.md` / `GEMINI.md` | clone 後置於工作目錄，agent 會讀取（兩者皆指向 `SKILL.md`） |
| 任何 vendor | clone 即用 | clone repo，各入口檔在根目錄就位 |

使用時請 AI 帶入貴機關資料（`trip.json`），並依當年度官方日支表填 `per_diem_base`（工具不內建日支數額表）。進階用法見 [SKILL.md](SKILL.md)。

> **報告本文需自行充實**：出國報告書的本文三章節可由 `report_content` 帶入；未填章節會保留「標題＋撰寫提示」骨架，**不是完成的內容**。只填基本欄位與摘要會得到空殼報告。請搭配出差的會議逐字稿／筆記／參訪記錄等素材充實本文，使內容翔實。**本工具不提供逐字稿錄製／轉錄功能**，素材由使用者自備。素材若涉機密或他人個資，請依《行政院及所屬機關（構）使用生成式 AI 參考指引》及貴機關規定處理（見 [DISCLAIMER.md](DISCLAIMER.md)）。

---

## 重要聲明

本工具僅協助產生符合格式之文件範本，使用者須對所產出文件之正確性及內容**自負其責**；送核前應依貴機關規定完成審核。

完整免責聲明：[DISCLAIMER.md](DISCLAIMER.md)
版本與法源：[CITATIONS.md](CITATIONS.md)
來源聲明：[PROVENANCE.md](PROVENANCE.md)

---

## 開發與驗證

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m pip wheel . --no-deps --wheel-dir dist
python scripts/check_wheel.py dist/tw_gov_overseas_trip_kit-1.5.0-py3-none-any.whl
```

CI 在 Python 3.10 / 3.13 跑測試，另驗證安裝 wheel 後在專案外產出全部五種文件，避免漏打包樣板或範例。

## 授權

MIT License — 詳見 [LICENSE](LICENSE)

---

## 支持這個專案

如果這個工具對你有幫助：

- 按個 [Star](https://github.com/Imbad0202/tw-gov-overseas-trip-kit) 讓更多人看到
- 分享給承辦出國案件的同仁、或任何需要產出出國報告的人
- [Buy Me a Coffee](https://buymeacoffee.com/crucify020v) 支持開發者持續更新
- 發現問題或有建議？歡迎開 [Issue](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/issues)

## 作者

**Cheng-I Wu** — [GitHub](https://github.com/Imbad0202) | [Buy Me a Coffee](https://buymeacoffee.com/crucify020v)
