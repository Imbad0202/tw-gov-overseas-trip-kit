"""行前手冊 HTML renderer（通用、機關參數化、零 HEEACT 元素）。

佔位符注入機制：
  template 含兩個佔位符字串：
    <!--HANDBOOK_TITLE-->  → 注入文件標題（用於 <title> 與 <h1>）
    <!--HANDBOOK_BODY-->   → 注入主體 HTML 片段

  renderer 用 str.replace() 取代佔位符，完全避開 CSS 大括號與
  str.format() 的衝突問題。

安全：所有來自 data 的字串值輸出進 HTML 前一律 html.escape()。
"""
import html
import pathlib

from render.validators import format_country_region, validate_dates

TEMPLATE = pathlib.Path(__file__).parent / "templates" / "pre_trip.html"

# ── 私有 helper：HTML escape 快捷函式 ──────────────────────────────────────

def _e(value) -> str:
    """把任意值轉字串後 HTML escape，防注入。"""
    return html.escape(str(value)) if value is not None else ""


# ── 私有 helper：各區塊渲染 ────────────────────────────────────────────────

def _render_basic_info(data: dict) -> str:
    """渲染固定基本資訊區（機關全銜、出國人員、期間、類別等）。

    此區塊為必填，呼叫端一律渲染（不像其餘四個可選區塊按需呼叫）。
    """
    agency = data["agency"]
    traveler = data["traveler"]
    trip = data["trip"]

    country_region = _e(format_country_region(trip))

    rows = [
        ("機關全銜", _e(agency["full_name"])),
    ]
    if agency.get("unit"):
        rows.append(("承辦單位", _e(agency["unit"])))

    rows.append(("出國人員", _e(traveler["name"])))

    if traveler.get("title"):
        rows.append(("職稱", _e(traveler["title"])))

    rows += [
        ("派赴國家地區", country_region),
        ("出國期間", f"{_e(trip['start_date'])}　至　{_e(trip['end_date'])}"),
        ("出國類別", _e(trip["purpose_category"])),
    ]

    if trip.get("organization"):
        rows.append(("境外主辦單位", _e(trip["organization"])))

    cells = "".join(
        f'<div class="label">{label}</div><div class="value">{value}</div>'
        for label, value in rows
    )
    return f'<div class="info-grid">{cells}</div>\n'


def _render_itinerary(itinerary: list) -> str:
    """渲染逐日議程區塊；空陣列呼叫者不呼叫此函式。"""
    day_blocks = []
    for day in itinerary:
        items = day.get("items") or []
        if not items:
            # schema 要求 items 非空，但防禦性跳過
            continue

        # 組出當天標題（date 與 label 都選填，可能只有其中一個）
        date_str = _e(day["date"]) if day.get("date") else ""
        label_str = _e(day["label"]) if day.get("label") else ""
        heading = "　".join(filter(None, [date_str, label_str])) or "行程"

        # 判斷是否有「地點」欄（至少一個 item 有 location 才渲染該欄）
        has_time = any(item.get("time") for item in items)
        has_location = any(item.get("location") for item in items)

        # 表格標頭
        th_time = "<th>時間</th>" if has_time else ""
        th_loc = "<th>地點</th>" if has_location else ""
        header_row = f"<tr>{th_time}<th>事項</th>{th_loc}</tr>"

        # 表格列
        table_rows = []
        for item in items:
            td_time = f"<td>{_e(item.get('time', ''))}</td>" if has_time else ""
            td_loc = f"<td>{_e(item.get('location', ''))}</td>" if has_location else ""

            activity_html = _e(item["activity"])
            if item.get("note"):
                activity_html += f'<div class="item-note">※ {_e(item["note"])}</div>'

            table_rows.append(f"<tr>{td_time}<td>{activity_html}</td>{td_loc}</tr>")

        table_html = (
            '<table class="itinerary-table">'
            f"{header_row}"
            f"{''.join(table_rows)}"
            "</table>"
        )
        day_blocks.append(
            f'<div class="day-block">'
            f'<div class="day-label">{heading}</div>'
            f"{table_html}"
            "</div>"
        )

    if not day_blocks:
        return ""

    inner = "\n".join(day_blocks)
    return f"<section><h2>逐日行程</h2>{inner}</section>\n"


def _render_lodging(lodging: list) -> str:
    """渲染住宿資訊區塊；空陣列呼叫者不呼叫此函式。"""
    # 選填欄位：(key, 表頭)。某欄全部住宿都沒填時，整欄不渲染。
    optional_cols = [
        ("address", "地址"),
        ("phone", "電話"),
        ("check_in", "入住"),
        ("check_out", "退房"),
        ("note", "備註"),
    ]
    present = [(key, label) for key, label in optional_cols
               if any(lg.get(key) for lg in lodging)]

    header_cells = "".join(f"<th>{label}</th>" for _, label in present)
    header_row = f"<tr><th>住宿名稱</th>{header_cells}</tr>"

    table_rows = []
    for lg in lodging:
        cells = "".join(f"<td>{_e(lg.get(key, ''))}</td>" for key, _ in present)
        table_rows.append(f"<tr><td>{_e(lg['name'])}</td>{cells}</tr>")

    table_html = (
        '<table class="lodging-table">'
        f"{header_row}"
        f"{''.join(table_rows)}"
        "</table>"
    )
    return f"<section><h2>住宿資訊</h2>{table_html}</section>\n"


def _render_emergency_contacts(contacts: list) -> str:
    """渲染緊急聯絡資訊區塊；空陣列呼叫者不呼叫此函式。"""
    cards = []
    for c in contacts:
        lines = [f'<div class="contact-label">{_e(c["label"])}</div>']
        if c.get("name"):
            lines.append(f'<div class="contact-line">{_e(c["name"])}</div>')
        if c.get("phone"):
            lines.append(f'<div class="contact-line contact-phone">{_e(c["phone"])}</div>')
        if c.get("note"):
            lines.append(f'<div class="contact-line">{_e(c["note"])}</div>')
        cards.append(f'<div class="contact-card">{"".join(lines)}</div>')

    inner = f'<div class="contact-list">{"".join(cards)}</div>'
    return f"<section><h2>緊急聯絡</h2>{inner}</section>\n"


def _render_notes(notes: list) -> str:
    """渲染注意事項清單；空陣列呼叫者不呼叫此函式。

    呼叫端的 `if notes:` 只擋空 list，擋不掉 [""]/[None] 這類非空但無內容的
    list，故此處仍需逐筆過濾；過濾後全空則回空字串、不渲染區塊。
    """
    items = "".join(f"<li>{_e(n)}</li>" for n in notes if n)
    if not items:
        return ""
    return f'<section><h2>行前注意事項</h2><ul class="notes-list">{items}</ul></section>\n'


# ── 公開 API ────────────────────────────────────────────────────────────────

def render_html(data: dict, out_path: str) -> None:
    """從 data 生成行前手冊 HTML，寫入 out_path。

    函式簽名固定（整合測試依賴），不可更改。
    """
    tpl = TEMPLATE.read_text(encoding="utf-8")

    trip = data["trip"]
    validate_dates(trip["start_date"], trip["end_date"])

    # ── 標題 ──
    agency_name = _e(data["agency"]["full_name"])
    title = f"{agency_name} 出國行前手冊"

    # ── 主體 ──
    body_parts = [_render_basic_info(data)]

    itinerary = data.get("itinerary") or []
    if itinerary:
        body_parts.append(_render_itinerary(itinerary))

    lodging = data.get("lodging") or []
    if lodging:
        body_parts.append(_render_lodging(lodging))

    contacts = data.get("emergency_contacts") or []
    if contacts:
        body_parts.append(_render_emergency_contacts(contacts))

    notes = data.get("notes") or []
    if notes:
        body_parts.append(_render_notes(notes))

    body_html = "".join(body_parts)

    # ── 佔位符替換（不用 str.format()，避免 CSS {} 衝突）──
    html_out = tpl.replace("<!--HANDBOOK_TITLE-->", title).replace(
        "<!--HANDBOOK_BODY-->", body_html
    )

    pathlib.Path(out_path).write_text(html_out, encoding="utf-8")
