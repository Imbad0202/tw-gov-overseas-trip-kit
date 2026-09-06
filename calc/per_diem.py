"""日支試算（114.05.13 修正規則）。基準額由使用者查適用年度官方表。

內部以 Decimal 累計、總計後才進位；公開結果維持 float / int，方便 JSON 與 Excel。
長駐仍採既有 30 / 90 日模型，曆月起訖及與供膳宿、返國日併用須人工覆核。
"""
from datetime import date
from decimal import Decimal, ROUND_CEILING
import re

LODGING, MEAL, INCIDENTAL = 0.70, 0.20, 0.10
RETURN_DAY = 0.30
MEAL_SHARE = {"breakfast": 0.04, "lunch": 0.08, "dinner": 0.08}
HOST_OPTIONS = ("none", "board_and_lodging", "board_only", "lodging_only")


def _money(value, name, *, signed=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError(f"{name} 須為有限數值")
    result = Decimal(str(value))
    if not result.is_finite() or (not signed and result < 0):
        raise ValueError(f"{name} 須為{'有限' if signed else '非負有限'}數值")
    return result


def _integer(value, name, minimum):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} 須為 ≥ {minimum} 的整數")


def _daily_decimal(per_diem, *, is_return_day=False, host_provided="none",
                   meals_not_provided=None, cash_allowance_usd=0):
    pd = _money(per_diem, "per_diem_base")
    cash = _money(cash_allowance_usd, "cash_allowance_usd")
    if host_provided not in HOST_OPTIONS:
        raise ValueError(f"unknown host_provided: {host_provided!r}")
    if not isinstance(is_return_day, bool):
        raise ValueError("is_return_day 須為布林值")
    meals = [] if meals_not_provided is None else meals_not_provided
    if (not isinstance(meals, (list, tuple))
            or any(not isinstance(m, str) or m not in MEAL_SHARE for m in meals)
            or len(set(meals)) != len(meals)):
        raise ValueError("meals_not_provided 須為不重複的 breakfast / lunch / dinner")
    if meals and host_provided not in ("board_only", "board_and_lodging"):
        raise ValueError("meals_not_provided 僅用於有供膳的情形")
    if cash and host_provided == "none":
        raise ValueError("僅領現金津貼、未供膳宿的情形須人工認定，不能直接套全額日支")
    if is_return_day:
        return pd * Decimal("0.30")
    if host_provided == "none":
        return pd
    fixed = {"board_and_lodging": "0", "board_only": "0.70", "lodging_only": "0.20"}
    incidental = max(Decimal(0), pd * Decimal("0.10") - cash)
    meal_topup = pd * sum((Decimal(str(MEAL_SHARE[m])) for m in meals), Decimal(0))
    return pd * Decimal(fixed[host_provided]) + incidental + meal_topup


def daily_amount(per_diem, *, is_return_day, host_provided, meals_not_provided,
                 cash_allowance_usd=0.0):
    """單日未進位金額。機上歇夜用 lodging_only；返國當日才用 is_return_day。"""
    return float(_daily_decimal(
        per_diem, is_return_day=is_return_day, host_provided=host_provided,
        meals_not_provided=meals_not_provided, cash_allowance_usd=cash_allowance_usd))


def long_stay_factor(day_index_in_same_place, *, exempt=False):
    """既有 30 / 90 日分界；非曆月判定器，日序及豁免由承辦認定。"""
    _integer(day_index_in_same_place, "day_index_same_place", 1)
    if not isinstance(exempt, bool):
        raise ValueError("reduction_exempt 須為布林值")
    if exempt or day_index_in_same_place <= 30:
        return 1.0
    return 0.80 if day_index_in_same_place <= 90 else 0.70


def _segment_dates(segments):
    """有日期時一日一筆、遞增；保留舊 API 全部不帶日期的呼叫方式。"""
    if not any("date" in seg for seg in segments):
        return None
    dates = []
    for i, seg in enumerate(segments):
        raw = seg.get("date")
        try:
            if not isinstance(raw, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
                raise ValueError
            current = date.fromisoformat(raw)
        except ValueError as exc:
            raise ValueError(f"segments[{i}].date 須為有效 YYYY-MM-DD 日期") from exc
        if dates and current <= dates[-1]:
            raise ValueError(f"segments[{i}].date 須按日期遞增、每日只能一筆（跨城市也不重複列日支）")
        dates.append(current)
    return dates


def compute_trip_per_diem(segments, manual_items=None, approved_days=None, *, approved_start_date=None):
    """累計逐日日支及人工美元項目。

    approved_days 以 approved_start_date（未填用首日）起的日曆日計。
    漏列日期不會把延返擠進核准期間；因私提前出國須另填核准起日。
    reimbursable=False 排除私人／不報支日；approved_extension 不會覆蓋這個明示排除。
    """
    segments = list(segments)
    if approved_days is not None:
        _integer(approved_days, "approved_days", 0)
    dates = _segment_dates(segments)
    approval_start = dates[0] if dates else None
    if approved_start_date is not None:
        if approved_days is None or not dates:
            raise ValueError("approved_start_date 須搭配 approved_days 及逐日日期")
        if not isinstance(approved_start_date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", approved_start_date):
            raise ValueError("approved_start_date 須為有效 YYYY-MM-DD 日期")
        try:
            approval_start = date.fromisoformat(approved_start_date)
        except ValueError as exc:
            raise ValueError("approved_start_date 須為有效 YYYY-MM-DD 日期") from exc
    per_segment, subtotal = [], Decimal(0)
    for i, seg in enumerate(segments):
        for flag in ("reimbursable", "approved_extension"):
            if flag in seg and not isinstance(seg[flag], bool):
                raise ValueError(f"segments[{i}].{flag} 須為布林值")
        _money(seg["per_diem_base"], "per_diem_base")
        day_offset = (dates[i] - approval_start).days if dates else i
        reason = ""
        if not seg.get("reimbursable", True):
            if not isinstance(seg.get("exclusion_reason"), str) or not seg["exclusion_reason"].strip():
                raise ValueError(f"segments[{i}].exclusion_reason 須說明不報支原因")
            reason = f"不列日支：{seg['exclusion_reason']}"
        elif approved_days is not None and day_offset < 0:
            reason = "早於核准出差期間，不列日支"
        elif (approved_days is not None and day_offset >= approved_days
              and not seg.get("approved_extension", False)):
            reason = "超出核准日數，不得報支（第三點）"
        amt = Decimal(0)
        if not reason:
            amt = _daily_decimal(
                seg["per_diem_base"], is_return_day=seg.get("is_return_day", False),
                host_provided=seg.get("host_provided", "none"),
                meals_not_provided=seg.get("meals_not_provided", []),
                cash_allowance_usd=seg.get("cash_allowance_usd", 0))
            factor = long_stay_factor(seg.get("day_index_same_place", 1),
                                      exempt=seg.get("reduction_exempt", False))
            amt *= Decimal(str(factor))
        row = {**seg, "amount_usd": float(amt)}
        if reason:
            row["note"] = "；".join(filter(None, [seg.get("note"), reason]))
        else:
            subtotal += amt
        per_segment.append(row)
    manual_total = sum((_money(m["amount_usd"], "amount_usd", signed=True)
                        for m in (manual_items or [])), Decimal(0))
    grand = int((subtotal + manual_total).to_integral_value(rounding=ROUND_CEILING))
    return {"per_segment": per_segment, "subtotal_usd": float(subtotal),
            "manual_total_usd": float(manual_total), "grand_total_usd": grand}
