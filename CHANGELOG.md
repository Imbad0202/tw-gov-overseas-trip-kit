# Changelog

All notable changes to tw-gov-overseas-trip-kit are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.6.1] — 2026-09-15

### 新增
- README 與 README_EN 補「Last Updated」與「What's new in v<版本>」段，發版文件對齊紀律第 2、3 條就位。
- `scripts/check_consistency.py` 新增三條檢查：SKILL.md／pyproject.toml／plugin.json／兩份 README badge／CHANGELOG 最新 entry 六處版本號互相一致；兩份 README 的 Last Updated 等於 CHANGELOG 最新 entry 日期；兩份 README 含當前版本的 What's new 段。CI 的 consistency workflow 每次 push 都跑。

## [1.6.0] — 2026-09-15

### 新增
- **解釋彙編逐案索引**（`docs/解釋彙編逐案索引.md`）：依要點各點整理主計總處 107.4 修編《國外出差旅費報支要點解釋彙編》全部案例（壹 依要點 23 點整理 84 案、貳 其他相關解釋 9 案，共 93 案），每案列問題、函釋文號與日期、要旨，並逐案標與現行 114.05.13 條文的差異，區分「彙編編修時已加註的舊變動」（如歇夜與返國日 40%→30%、日支劃分 60/30/10→70/20/10）與「114.05.13 後的變動」（日期基準本國時間→當地時間、匯率即期→現金並以匯率證明為判準、雜費 600→1,100 元、登機證存根款刪除、第 4 點刪「長途」、艙等三級用語與例外）。彙編為公開政府資料；索引只做整理與差異標註，不放 PDF、不覆蓋現行條文。

### 變更
- `SKILL.md`、`README.md`、`docs/sources/README.md`、`docs/延返與個案指引.md` 補逐案索引連結；法源清單第 3 項改列主計總處全文 PDF 網址。SKILL.md 原「不內建函釋個案庫、不引用函釋文號」一句移除。

## [1.5.0] — 2026-09-06

### 新增
- `tripkit init / validate / render / flights` 指令入口、中文欄位錯誤與覆寫保護；先驗證再產檔。
- 報告名稱、繳交日期、`report_content` 三章段落；CLI 預設不產缺本文報告，骨架須明示。
- 私人／不報支日 `reimbursable / exclusion_reason`、日支 `rate_source / note`，Excel 顯示計算條件與原始基準。
- 航班與混合差旅情境範例、完整情境覆蓋表；安裝 wheel 後在專案外產出五文件的 CI 驗證。

### 修正
- 十進位累計避免浮點誤差使總額多進位；有日期時核准日數按日曆期間，缺日不把延返擠進核准範圍；`approved_start_date` 可分開因私出發日與核准起日。
- 拒絕重複／倒序日期、非有限金額、負核准日數與無效同地日序；四個手冊選填區塊接受空陣列。
- wheel 打包 HTML 樣板、schema 與合成範例；Excel 文字不再解讀為公式。
- 依官方 114.05.13 修正、115.01.01 生效規定更新市區交通、艙等、機票憑證、刷卡手續費、匯率及適用範圍指引；修正日支表未列國家選取與附件二用途說明。
- 安全掃描改用 NUL 分隔檔名，修正中文／空白／特殊字元檔名漏掃。
- 明示長駐 30/90 日模型、臺幣核銷、跨規則版本與複雜組合限制；例中移除固定免簽天數。

## [1.4.0] — 2026-07-09

### 新增

- **個案報支方向指引**（`docs/延返與個案指引.md`）：整理國外出差旅費報支常見個案的方向性參考，按 A–H 八區組織（人員適用／交通費／艙等／生活費日支／供膳宿扣補／延後返國·不可抗力／手續費·保險·雜費·匯率／進修研習·受刑返國·跨修法）。每題以「方向 → 需向官方確認的點 → 工具端如何反映」呈現。定位為方向性參考、非個案認定：只講往哪個方向想、該確認什麼，不下結論、不給可照抄金額比例，一律導回主計總處與貴機關核定。不內建函釋個案庫、不引用函釋文號、不含特定機構或個案數字。
- **延後返國／不可抗力滯留**：新增颱風、氣候、班機延誤等非可歸責事由滯留的報支方向（第 12 點，經確實證明並經核准者得按日報支；旺季訂不到票等可歸責事由多不得報支），工具端以 `segment.approved_extension` 反映。

### 變更

- **SKILL.md**：新增「個案報支方向指引」導引段，指向 `docs/延返與個案指引.md`。
- **DISCLAIMER.md**：新增第 5 條「非法規諮詢」——個案方向僅供參考，不構成法規解釋、報支保證或個案認定，認定權責在主計總處與各機關。

---

## [1.3.0] — 2026-06-27

### 新增

- **航班查價比較**（可選 deliverable）：行前準備階段的查價底稿。新增 `calc/flight_rank.py`（純函式：候選正規化、相對排序、版面判定、摘要列）與 `render/render_flight_options.py`（HTML 對照表 renderer，寫檔簽名對齊既有 render 模組）。排序依「尊重休息時間 > 轉機/候機越短 > 行李盡量直掛 > 票價」相對偏好優先序；休息時間=三條可計算規則（出發 buffer 避凌晨、避凌晨抵達、時差窗口）。對照表只排順序、不顯分數/名次（避免假精確計分），附票務代理免責、跨日 `+1` 標記、source_url scheme allowlist 防 XSS。定位為比較底稿、非訂票工具，**不連動核銷**——選定後可選擇性寫入 `flights[]`。
- **schema 新增 optional `flights[]`**：航段資訊欄位（leg_n／date／route／departure_time／arrival_time／flight_no 等），含 `source` enum（searched／ocr）區分查價選定與素材抽取。不列入 required、缺席不影響其他文件，無 migration。範例檔 `02-sample-agency.trip.json` 加 city-neutral 航班示例。

### 變更

- **SKILL.md／README／plugin.json**：輸出文件由四種擴為五種，補航班查價說明段與觸發詞（航班查價／航班比價／班機比較）。

---

## [1.2.0] — 2026-06-25

### 新增

- **出國報告書本文撰寫提示**：本文三章節（壹目的／貳過程／參心得及建議）原為標題＋空白段落，使用者只填基本欄位即交件會產出空殼報告。改為在各章節放灰色括號撰寫提示，引導使用者依出差實況（會議逐字稿／筆記／參訪記錄）充實本文；SKILL.md 加「充實報告本文」引導，讓 AI 主動請使用者提供素材。本工具不提供逐字稿錄製／轉錄功能；機敏素材提醒依生成式 AI 使用規範處理。
- **sponsorship**：`.github/FUNDING.yml` 設 Buy Me a Coffee，README 加 Sponsor badge 與「支持這個專案」段（中英）。

### 變更

- **README 補跨 vendor skill 使用段 + version badge**（中英）：說明 skill.zip／plugin／AGENTS-GEMINI／clone 各入口，補回原本缺少的版本標記。

---

## [1.1.0] — 2026-06-25

### 新增

- **行前手冊（可選 deliverable）**：`render/render_html.py` 從單薄的行前須知重做成資料驅動的完整行前手冊，支援逐日議程／住宿／緊急聯絡／注意事項（皆選填、缺漏即不渲染），多日多段行程，通用中性視覺，可瀏覽器開啟或 `cmd+P` 列印 PDF。
- **跨 vendor skill 打包**：SKILL.md 補 YAML frontmatter（name／version／description），可作 claude.ai／cowork 的 skill 使用；新增 `.claude-plugin/plugin.json` 供 Claude Code plugin 載入；`AGENTS.md`／`GEMINI.md` symlink 至 SKILL.md，供 Codex／Gemini 等其他 vendor 通用。

### 變更

- **README／README_EN 補「適用範圍與限制」**：工具對齊行政院附件一／二共通底層格式，不讀取個別機關自訂範本；客製版面與事前申請簽核表留各機關自補。
- **行前手冊內文字級全面 ≥14px**（含列印基準），確保印出 PDF 攜帶時不偏小。

### 修正

- **派赴國家地區 country==city 去重**：抽 `validators.format_country_region` 共用 helper，html／docx 一致，避免印出「新加坡 新加坡」。
- **文件驗證範例改用 `Draft202012Validator` + `FormatChecker`**，使 schema `"format": "date"` 確實生效。

### 安全（轉 public 強化）

- 移除程式與測試中寫死的特定機構字眼。
- PII lint 機敏詞清單外移本機（`TWGOK_EXTRA_DENYLIST` 環境變數載入），repo 內僅保留普世洩漏偵測（session URL／本機路徑），避免 lint 腳本本身洩漏防護對象；新增 `scripts/extra-denylist.example.txt` 示範格式。

---

## [1.0.0] — 2026-06-24

### 首版發布

本版本完成台灣公務機關出國報告文件產生工具之初版，對齊行政院出國報告綜合處理要點附件一／二格式，以及國外出差旅費報支要點（114.05.13 修正版）。

### 新增功能

- **日支費計算器**（`calc/per_diem.py`）：依報支要點規則計算出差日支費，支援返國當日30%折算、供膳宿補足至10%、長期駐留遞減（逾1月80%／逾3月70%）、核准日數邊界等情境。
- **資料驗證**（`render/validators.py`）：摘要字數 200–300 中文字、禁交占位符（fail-fast 前置驗證）。
- **Schema 定義**（`schema/trip.schema.json`、`schema/trip-finance.schema.json`）：出國報告與財務表格欄位結構（JSON Schema），對齊附件一／二欄位名稱。
- **行前手冊 HTML 渲染**（`render/render_html.py`，**可選 deliverable**）：輸出供出差同仁攜帶的行前手冊，資料驅動，逐日議程／住宿／緊急聯絡／注意事項皆為選填（缺漏即不渲染該區塊），支援多日多段行程，採通用中性視覺、可瀏覽器開啟或 `cmd+P` 列印 PDF。
- **DOCX 渲染**（`render/render_docx.py`）：輸出可直接列印之 Word 格式出國報告；`render_review_table_docx` 產出機關內部審查表。
- **財務 Excel 渲染**（`render/render_finance_xlsx.py`）：輸出旅費規劃表（Excel）；`render_review_table_docx` 另產出附件二格式之審核表（DOCX）。
- **合成範例資料**（`examples/`）：提供合成假資料供測試與示範，不含個資。
- **公開慣例檔**：DISCLAIMER（四層免責）、CITATIONS（法規版本鎖定）、PROVENANCE（from-scratch 聲明）、NOTICE、LICENSE（MIT）、`docs/sources/` 法源清單。

### 對齊法規版本

- 國外出差旅費報支要點：114.05.13 修正（院授主預字第1140101390號函）
- 生活費日支數額表：114.10.31 修正、115.1.1 生效（院授主預字第1140103430號函）——**不內建表值，由使用者帶入**
- 行政院出國報告綜合處理要點：107.06.20 附件一／二

### 安全與隱私

- 工具不傳送任何資料至外部服務；全程本機執行。
- 範例資料均為合成假資料。
- 使用者自行帶入之個資由使用者負責，請勿輸入至公開 AI 模型（見 DISCLAIMER 第4層）。
