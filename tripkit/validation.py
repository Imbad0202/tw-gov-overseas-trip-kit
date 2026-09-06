"""CLI 共用驗證；錯誤附欄位路徑，提醒不當作核准判定。"""
import json
import math
from datetime import date

from jsonschema import Draft202012Validator, FormatChecker

from calc.per_diem import compute_trip_per_diem
from render.validators import validate_dates, validate_summary
from tripkit.resources import resource_text

BODY_KEYS = ("purpose", "process", "insights_and_recommendations")


def _finite(value, path="$"):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{path}: JSON 不接受 NaN / Infinity")
    if isinstance(value, dict):
        for key, item in value.items():
            _finite(item, f"{path}.{key}")
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _finite(item, f"{path}[{i}]")


def validate_schema(data, name):
    _finite(data)
    schema = json.loads(resource_text("schemas", name))
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data))
    if errors:
        messages = []
        for error in errors[:12]:
            path = "$" + "".join(f"[{p}]" if isinstance(p, int) else f".{p}"
                                  for p in error.absolute_path)
            messages.append(f"{path}: {error.message}")
        raise ValueError("\n".join(messages))


def validate_trip(data, *, report=False, allow_incomplete_report=False):
    validate_schema(data, "trip.schema.json")
    trip = data["trip"]
    validate_dates(trip["start_date"], trip["end_date"])
    for path, value in (("agency.full_name", data["agency"]["full_name"]),
                        ("traveler.name", data["traveler"]["name"]),
                        ("trip.country", trip["country"])):
        if not value.strip():
            raise ValueError(f"$.{path}: 不可只填空白")
    warnings = []
    if report:
        validate_summary(data.get("summary", ""))
        body = data.get("report_content", {})
        missing = [key for key in BODY_KEYS if not body.get(key)
                   or any(not p.strip() for p in body[key])]
        if missing:
            message = "report_content 缺少正式段落：" + ", ".join(missing)
            if not allow_incomplete_report:
                raise ValueError(message + "；只產骨架請明示 --allow-incomplete-report")
            warnings.append(message + "；report.docx 為待補骨架，請補寫後再送核")
    return warnings


def validate_finance(data):
    validate_schema(data, "trip-finance.schema.json")
    inputs = data["per_diem_inputs"]
    segments = inputs["segments"]
    if not segments and not inputs.get("manual_items"):
        raise ValueError("$.per_diem_inputs: 至少填一筆日支或人工項目，不能產出空經費表")
    compute_trip_per_diem(segments, inputs.get("manual_items"), inputs.get("approved_days"),
                          approved_start_date=inputs.get("approved_start_date"))
    warnings = []
    if segments and inputs.get("approved_days") is None:
        warnings.append("未填 approved_days：不會自動排除未核准延返日，請核對核准期間")
    if segments and not segments[0].get("reimbursable", True) and not inputs.get("approved_start_date"):
        warnings.append("首日不列日支：如為因私提前出國，請另填 approved_start_date，避免核准期間提前起算")
    if any(not seg.get("rate_source") for seg in segments):
        warnings.append("部分日支未填 rate_source：請核對適用年度、城市／季節的官方數額並記錄來源")
    if any(seg["per_diem_base"] == 0 and seg.get("reimbursable", True) for seg in segments):
        warnings.append("部分可報支日的 per_diem_base 為 0，請確認是否尚未填值")
    if any(seg.get("cash_allowance_usd", 0) > 0 and
           seg.get("cash_allowance_usd", 0) >= seg["per_diem_base"] * 0.1 and
           seg.get("host_provided") in ("board_only", "lodging_only") for seg in segments):
        warnings.append("部分供膳宿且津貼達日支10%：現模型只扣零用補足，高額津貼須依用途及機關認定覆核")
    if segments:
        dates = [date.fromisoformat(seg["date"]) for seg in segments]
        if any((b - a).days > 1 for a, b in zip(dates, dates[1:])):
            warnings.append("逐日資料有缺日；核准日數仍按日曆日計，私人日請保留並填 reimbursable=false")
        if (dates[-1] - dates[0]).days >= 30 or any(seg.get("day_index_same_place", 1) > 30 for seg in segments):
            warnings.append("長駐請確認同地日序、曆月分界及豁免：目前採 30/90 日模型，非自動曆月認定")
        returns = [i for i, seg in enumerate(segments) if seg.get("is_return_day")]
        if len(returns) > 1 or (returns and returns[-1] != len(segments) - 1):
            raise ValueError("$.per_diem_inputs.segments: 單趟僅最後一筆可標返國日；多趟請分檔")
        if not returns:
            warnings.append("未標返國當日；如為完整出差請核對末日，部分期間試算可省略")
        if any(seg.get("is_return_day") and (seg.get("host_provided", "none") != "none"
                or seg.get("cash_allowance_usd") or seg.get("day_index_same_place", 1) > 30)
               for seg in segments):
            warnings.append("返國日與供膳宿／津貼／長駐併用：現模型先取30%再乘遞減，請人工覆核，非個案認定")
    if any(m["amount_usd"] < 0 for m in inputs.get("manual_items", [])):
        warnings.append("人工項目含負值調整，請於 note 註明扣除／退款／避免重複計列的依據")
    return warnings


def validate_pair(trip_data, finance_data):
    """同次提供兩份資料時避免串錯機關或日期；私人日仍應列入日期範圍。"""
    if trip_data["agency"]["full_name"] != finance_data["agency"]["full_name"]:
        raise ValueError("trip 與 finance 的 agency.full_name 不一致")
    segments = finance_data["per_diem_inputs"]["segments"]
    if segments:
        trip = trip_data["trip"]
        if segments[0]["date"] != trip["start_date"] or segments[-1]["date"] != trip["end_date"]:
            raise ValueError("finance 首末日期須與 trip 起訖一致；部分期間請單獨產經費表")
    warnings = []
    if trip_data["trip"]["purpose_category"] in ("進修", "研究", "實習"):
        warnings.append("此出國類別可能適用另一補助制度；報告可產出，日支試算須先確認適用對象")
    return warnings
