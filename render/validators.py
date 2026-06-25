"""renderer 前置 validator：摘要字數 + placeholder 禁交 + 日期邏輯（fail fast，不印空段）。"""
import re
from datetime import date


class SummaryError(ValueError):
    pass


class DateError(ValueError):
    pass


PLACEHOLDERS = ("○○", "TODO", "待填", "XXX", "範例")


def format_country_region(trip: dict) -> str:
    """組「派赴國家地區」字串：country + city，city 與 country 同名時去重
    （避免印出「新加坡 新加坡」這類城市即國家的重複）。html / docx 共用，
    確保兩個 deliverable 的地點呈現一致。"""
    country = (trip.get("country") or "").strip()
    city = (trip.get("city") or "").strip()
    if city and city != country:
        return f"{country} {city}"
    return country


def _cjk_count(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text))


def validate_summary(text: str) -> None:
    for ph in PLACEHOLDERS:
        if ph in text:
            raise SummaryError(f"摘要含未填佔位符『{ph}』，禁止交件")
    n = _cjk_count(text)
    if not (200 <= n <= 300):
        raise SummaryError(f"摘要中文字數須 200-300，目前 {n}")


def validate_dates(start_date: str, end_date: str) -> None:
    """P2-3：驗證 start_date <= end_date，同時確認格式為合法 ISO 8601 date。
    任一格式錯誤或 start > end 均 raise DateError。"""
    try:
        s = date.fromisoformat(start_date)
    except (ValueError, TypeError) as exc:
        raise DateError(f"start_date 格式錯誤：{start_date!r}") from exc
    try:
        e = date.fromisoformat(end_date)
    except (ValueError, TypeError) as exc:
        raise DateError(f"end_date 格式錯誤：{end_date!r}") from exc
    if s > e:
        raise DateError(f"start_date ({start_date}) 晚於 end_date ({end_date})")
