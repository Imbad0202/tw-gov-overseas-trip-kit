# Changelog

All notable changes to tw-gov-overseas-trip-kit are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
