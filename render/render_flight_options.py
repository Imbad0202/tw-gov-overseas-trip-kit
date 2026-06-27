"""航班候選比較底稿 HTML renderer（通用、機關參數化、無特定機關設計）。

定位：行前查價比較底稿、非訂票。對照表只排序、不顯示分數/名次；
排序理由用優缺點/決策點文字說明，不給假精確分數。

安全：所有來自 data 的字串值輸出進 HTML 前一律 html.escape()；
source_url 僅允許 http/https scheme 進 href（防 javascript:/data: scheme XSS）。
"""
import html
import pathlib

# 字級用 class、不用 inline px（無 inline 小字）；色票為中性灰藍、不綁特定機構品牌色。
_CSS = """
<style>
body { font-family: "Noto Sans TC","PingFang TC",sans-serif; font-size: 16px; color:#222; }
h1 { font-size: 24px; } h2 { font-size: 20px; }
.mono { font-family: ui-monospace,monospace; font-size: 14px; }
table { border-collapse: collapse; width: 100%; }
th,td { border:1px solid #ccc; padding:8px; font-size:16px; }
th { background:#334155; color:#fff; }
.advisory { background:#fff8e6; padding:12px 14px; margin-top:14px; }
.advisory h3 { font-size:16px; margin:0 0 6px; }
.footer { color:#666; font-size:14px; margin-top:10px; }
.overnight { background:#fff4e0; font-weight:bold; }
.incomplete-warn { background:#fde8e8; color:#b91c1c; padding:8px 12px; font-weight:bold; margin:8px 0; }
.pros { color:#1a7f37; } .cons { color:#c0392b; }
</style>
"""


def _esc(s):
    return html.escape(str(s)) if s is not None else ""


def _safe_url(url):
    """只允許 http/https scheme 的 URL 進 href，否則回 None（防 javascript:/data: scheme XSS）。"""
    if not url:
        return None
    u = str(url).strip()
    low = u.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return u
    return None


def _summary_table(rows):
    head = ("<tr><th>選項</th><th>轉機</th><th>最早出發</th>"
            "<th>最晚抵達</th><th>總程</th><th>參考票價</th></tr>")
    body = ""
    for r in rows:
        price = _esc(r["price"]) if r.get("price") else "待票務代理報價"
        body += (f"<tr><td>{_esc(r['label'])}</td><td>{_esc(r['transfers'])}</td>"
                 f"<td class='mono'>{_esc(r['earliest_dep'])}</td>"
                 f"<td class='mono'>{_esc(r['latest_arr'])}</td>"
                 f"<td>{_esc(r.get('total_duration'))}</td><td>{price}</td></tr>")
    return f"<h2>候選摘要比較</h2><table>{head}{body}</table>"


def _candidate_blocks(candidates, advisories_by_candidate):
    out = ""
    for i, c in enumerate(candidates):
        label = chr(ord("A") + i)
        legs = c.get("legs", [])
        # incomplete 候選 rank 刻意保留（排最後不刪），但顯示端須標警示，
        # 否則非法時刻（24:00）/缺時刻（待補）的壞班表會被當正常表呈現、誤導使用者採用。
        incomplete_notice = ("<p class='incomplete-warn'>⚠ 此候選資料不完整"
                             "（時刻或欄位有缺漏 / 格式異常），請使用者核對後補列，勿直接採用。</p>"
                             if c.get("incomplete") else "")
        if legs:
            legs_html = ""
            for leg in legs:
                cls = " class='overnight'" if leg.get("overnight") else ""
                prefix = "【轉機過夜】" if leg.get("overnight") else ""
                # 跨日抵達標 +1、避免 21:55→07:25 被當當日抵達誤導接駁判斷
                _arr_suffix = "+1" if leg.get("arr_next_day") and leg.get("arr_time") else ""
                # 跨日出發標 +1、轉機次日才出發時 dep 時刻同樣需標明避免誤判前一日銜接
                _dep_suffix = "+1" if leg.get("dep_next_day") and leg.get("dep_time") else ""
                legs_html += (f"<tr{cls}><td class='mono'>{_esc(leg.get('flight_no', ''))}</td>"
                              f"<td>{prefix}{_esc(leg.get('route', ''))}</td>"
                              f"<td class='mono'>{_esc(leg.get('dep_time', '待補'))}{_dep_suffix}→{_esc(leg.get('arr_time', '待補'))}{_arr_suffix}</td></tr>")
            legs_block = f"{incomplete_notice}<table>{legs_html}</table>"
        else:
            legs_block = "<p>（此候選航段資料不完整，請使用者補列）</p>"
        # 艙等：顯示中文艙等名（艙等是核心比較欄、也是商務/頭等資格提醒依據）
        _CABIN_LABELS = {
            "economy": "經濟艙",
            "premium_economy": "豪華經濟艙",
            "business_with_eligibility": "商務艙（待核定）",
            "first_with_eligibility": "頭等艙（待核定）",
            "business": "商務艙（待核定）",
            "first": "頭等艙（待核定）",
        }
        cabin_raw = c.get("cabin")
        cabin_label = _CABIN_LABELS.get(cabin_raw, "艙等未定") if cabin_raw else "艙等未定"
        pros = "、".join(_esc(p) for p in c.get("pros", []))
        cons = "、".join(_esc(x) for x in c.get("cons", []))
        # 溯源守則：每筆標來源 + 查詢日（source_url 不可信、必 _esc + scheme allowlist）
        source_url = c.get("source_url")
        queried_date = c.get("queried_date")
        if source_url:
            safe = _safe_url(source_url)
            if safe:
                provenance = (f"來源：<a href='{_esc(safe)}' rel='noopener noreferrer'>"
                              f"{_esc(safe)}</a>（查詢日 {_esc(queried_date or '不明')}）")
            else:
                provenance = (f"來源：{_esc(source_url)}"
                              f"（查詢日 {_esc(queried_date or '不明')}，連結格式未驗證）")
        else:
            provenance = "來源未確認、僅參考"
        out += (f"<h2>選項 {label}</h2>"
                f"<p><strong>艙等：</strong>{_esc(cabin_label)}</p>"
                f"{legs_block}"
                f"<p><span class='pros'>優：</span>{pros}　"
                f"<span class='cons'>缺：</span>{cons}</p>"
                f"<p><strong>決策點：</strong>{_esc(c.get('decision_note'))}</p>"
                f"<p class='footer'>{provenance}</p>")
        advs = advisories_by_candidate.get(label, [])
        if advs:
            items = "".join(f"<li>{_esc(a)}</li>" for a in advs)
            out += (f"<div class='advisory'><h3>規定提醒（供使用者確認、非系統判定）</h3>"
                    f"<ul>{items}</ul></div>")
    return out


def _build_html(data: dict) -> str:
    """組航班候選比較底稿 HTML 字串。

    data["layout"] 目前僅作語意標記（如 "card"/"table"），
    summary 比較列與候選航段區塊統一呈現；
    未來若需依 layout 分出不同版面結構再於此分支。
    """
    body = _summary_table(data.get("summary_rows", []))
    body += _candidate_blocks(data.get("candidates", []),
                              data.get("advisories_by_candidate", {}))
    footer = _esc(data.get("footer", ""))
    disclaimer = ("本表為查價比較參考（同 Skyscanner / Google Flights 性質），"
                  "僅供規劃、非訂位保證；實際航班 / 票價 / 可售艙位以票務代理報價為準。"
                  "排序為相對偏好參考、非客觀計分。")
    return (f"<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
            f"{_CSS}</head><body><h1>{_esc(data.get('title',''))}</h1>"
            f"{body}<p class='footer'>{footer}　{disclaimer}</p></body></html>")


def render_flight_options(data: dict, out_path: str) -> None:
    """航班候選比較底稿 HTML 渲染、寫入 out_path。"""
    pathlib.Path(out_path).write_text(_build_html(data), encoding="utf-8")
