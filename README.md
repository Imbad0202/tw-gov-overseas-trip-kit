# tw-gov-overseas-trip-kit

[![Version](https://img.shields.io/badge/version-v1.4.0-blue)](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-Buy%20Me%20a%20Coffee-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/crucify020v)

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
- **航班查價比較**（可選）：行前查價底稿——把航班候選依「休息時間 > 轉機/候機 > 行李直掛 > 票價」相對排序，產 HTML 對照表供選擇核定。只排序不顯分數、附票務代理免責；定位為比較底稿、非訂票工具，選定後可寫入 `flights[]`（不連動核銷）
- **資料驗證**：schema 驗證必填欄位、agency required 欄位；摘要字數 200–300 中文字、禁交占位符

---

## 適用範圍與限制

本工具對齊的是**行政院出國報告要點附件一／二 + 國外出差旅費報支要點計算**這個各機關共通的底層格式，不是任何單一機關的客製版面。

**運作方式**：使用者把**資料**填進 `trip.json`（機關、人員、行程、日期等），工具**生成**對齊上述格式的 DOCX／XLSX／HTML。工具**不讀取、也不對齊個別機關自訂的格式範本檔**（例如某校的出國報告範本 `.odt`、旅費報告表 `.doc`）。

**因此**：

- 各機關（含各大學）的出國報告書、審核表多承襲行政院要點，工具產出與其**高度對齊**；若貴機關版面另有客製（校徽、頁首、額外簽核欄），請在工具產出的 DOCX 上自行補上。
- 旅費計算對齊報支要點規則，但**旅費報告表的固定版面**（交通工具班次表、供宿供膳勾選欄、多段會核簽章等）多為各機關自訂，工具產出的是通用試算表，非特定機關版面。
- **事前的出國計畫／申請簽核表**（如校務基金出國計畫表，含計畫主持人、單位會核、首長核示）屬各機關自訂的行政流程文件，**不在本工具範圍**。

一句話：工具給的是「共通底層」，客製層留給各機關自己補。

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

## 作為 AI Skill 使用（跨 vendor）

除了當 Python 套件直接呼叫，本工具也封裝為 AI skill，可在多種 AI 工具中使用。核心是帶 frontmatter 的 `SKILL.md`，各 vendor 入口指向同一份內容：

| 使用情境 | 入口 | 做法 |
|---|---|---|
| claude.ai / cowork | `skill.zip` | 至 [Releases](https://github.com/Imbad0202/tw-gov-overseas-trip-kit/releases) 下載 `tw-gov-overseas-trip-kit-skill-vX.Y.Z.zip` 上傳載入 |
| Claude Code | `.claude-plugin/plugin.json` | clone 後以 plugin 載入，或 `git clone` 至 `~/.claude/skills/` |
| Codex / Gemini 等 CLI | `AGENTS.md` / `GEMINI.md` | clone 後置於工作目錄，agent 會讀取（兩者皆指向 `SKILL.md`） |
| 任何 vendor | clone 即用 | clone repo，各入口檔在根目錄就位 |

使用時請 AI 帶入貴機關資料（`trip.json`），並依當年度官方日支表填 `per_diem_base`（工具不內建日支數額表）。進階用法見 [SKILL.md](SKILL.md)。

> **報告本文需自行充實**：出國報告書的本文三章節（目的／過程／心得及建議）產出時為「標題＋撰寫提示」骨架，**不是完成的內容**。只填基本欄位與摘要會得到空殼報告。請搭配出差的會議逐字稿／筆記／參訪記錄等素材充實本文，使內容翔實。**本工具不提供逐字稿錄製／轉錄功能**，素材由使用者自備。素材若涉機密或他人個資，請依《行政院及所屬機關（構）使用生成式 AI 參考指引》及貴機關規定處理（見 [DISCLAIMER.md](DISCLAIMER.md)）。

---

## 重要聲明

本工具僅協助產生符合格式之文件範本，使用者須對所產出文件之正確性及內容**自負其責**；送核前應依貴機關規定完成審核。

完整免責聲明：[DISCLAIMER.md](DISCLAIMER.md)
版本與法源：[CITATIONS.md](CITATIONS.md)
來源聲明：[PROVENANCE.md](PROVENANCE.md)

---

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
