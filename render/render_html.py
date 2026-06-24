"""行前須知 HTML（通用、機關參數化、零 HEEACT 元素）。"""
import pathlib
from render.validators import validate_dates

TEMPLATE = pathlib.Path(__file__).parent / "templates" / "pre_trip.html"


def render_html(data: dict, out_path: str) -> None:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    trip = data["trip"]
    validate_dates(trip["start_date"], trip["end_date"])
    country_region = f"{trip['country']} {trip['city']}".strip() if trip.get("city") else trip["country"]
    html = tpl.format(
        agency=data["agency"]["full_name"],
        traveler=data["traveler"]["name"],
        country_region=country_region,
        start=trip["start_date"], end=trip["end_date"],
        category=trip["purpose_category"],
    )
    pathlib.Path(out_path).write_text(html, encoding="utf-8")
