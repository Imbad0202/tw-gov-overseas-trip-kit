"""日支計算器。規則溯源報支要點 114.05.13 + 數額表附註。A 類自動算，B 類(manual_items)原樣納入。
dual-track 修正：P1-1 供膳宿「補足至10%」非一律給10%（第九點）；P1-2 長期駐留遞減有例外（第十一點）；
P1-5 超出核准日數不得報支（第三、十二點）；B-6 返國當日≠機上歇夜（第九點末 vs 第九點2項）。
數額不內建：per_diem_base 由 segment 輸入（使用者查當年度官方表填，工具不內建年年變動的數額表）。"""
import math

LODGING, MEAL, INCIDENTAL = 0.70, 0.20, 0.10      # 要點第七點2項
RETURN_DAY = 0.30                                   # 要點第九點末項（返國當日）
MEAL_SHARE = {"breakfast": 0.04, "lunch": 0.08, "dinner": 0.08}  # 要點第九點3項

def daily_amount(per_diem, *, is_return_day, host_provided, meals_not_provided,
                 cash_allowance_usd=0.0):
    """單日應領（未進位，回 float）。
    P1-1（第九點1項）：供膳宿/供膳不供宿/供宿不供膳時，零用費是「報支**或補足**至日支10%」，
    即零用實得 = max(0, 日支*10% - 已收現金津貼)，不是無條件再給 10%。
    cash_allowance_usd = 主辦另給之現金津貼（承辦填）。
    B-6（codex 任務B）：**返國當日 ≠ 機上歇夜**。is_return_day=True 僅指返國當日（第九點末，30%）。
    機上/交通工具歇夜屬「其他來源供宿」（第九點2項），應走「供宿不供膳」——承辦把該日 segment 的
    host_provided 設 "lodging_only"（膳食20%+零用補足），**不要設 is_return_day**。兩者不可混用。
    """
    if is_return_day:
        return per_diem * RETURN_DAY            # 返國當日（第九點末項）。機上歇夜不走這條，見上 docstring B-6
    incidental_topup = max(0.0, per_diem * INCIDENTAL - cash_allowance_usd)  # P1-1 補足邏輯
    if host_provided == "none":
        return per_diem                          # 全額（津貼情形不適用 none）
    elif host_provided == "board_and_lodging":   # 供膳宿：僅零用補足
        base_fixed = 0.0
    elif host_provided == "board_only":          # 供膳不供宿：住宿70% + 零用補足
        base_fixed = per_diem * LODGING
    elif host_provided == "lodging_only":        # 供宿不供膳：膳食20% + 零用補足
        base_fixed = per_diem * MEAL
    else:
        raise ValueError(f"unknown host_provided: {host_provided!r}")
    # 供膳情形下，未供之餐別可補（第九點3項）
    meal_topup = 0.0
    if host_provided in ("board_and_lodging", "board_only"):
        meal_topup = per_diem * sum(MEAL_SHARE[m] for m in (meals_not_provided or []))
    return base_fixed + incidental_topup + meal_topup

# P1-2：第十一點長期駐留遞減「例外」（國際會議/談判、紅色警示地區、籌設使領館代表處辦事處）
# 由呼叫端以 exempt=True 表達，不在此列舉字串原因（避免死碼）。
#
# P1-4 day_index_same_place 預設值警告：
# segment 未填 day_index_same_place 時預設第 1 日（不遞減）。
# 長駐案件（同一地點逾 30 日）承辦須逐日填入正確日序，否則遞減不生效，計算結果將偏高。

def long_stay_factor(day_index_in_same_place, *, exempt=False):
    """同一地點駐留遞減係數（第十一點）。day_index 從 1 起算。
    P1-2：exempt=True（國際會議/談判、外交部紅色警示地區、籌設使領館代表處辦事處）→ 不遞減。"""
    if exempt:
        return 1.0
    if day_index_in_same_place <= 30:        # 第1月：全額
        return 1.0
    if day_index_in_same_place <= 90:        # 逾1月未逾3月：第2月起 80%
        return 0.80
    return 0.70                               # 逾3月：第4月起 70%

def compute_trip_per_diem(segments, manual_items=None, approved_days=None):
    """P1-5（第三、十二點）：approved_days = 核准出差日數。超出核准日數之 segment 不得報支，
    除非該 segment 標 approved_extension=True。
    B-5（codex 任務B）：放寬例外——第三點允許「不可歸責於出差人員之事由」+ 第十二點「患病/意外阻滯
    經核准」皆可延報。故旗標用通用 approved_extension（涵蓋患病、意外、不可歸責事由經核准），
    不限縮為 illness。承辦判定該延返是否經核准。"""
    per_segment, subtotal = [], 0.0
    for i, seg in enumerate(segments):
        # P1-5/B-5：超出核准日數且非「經核准延返」→ 該日 0
        if approved_days is not None and i >= approved_days and not seg.get("approved_extension", False):
            per_segment.append({**seg, "per_diem_base": 0, "amount_usd": 0.0,
                                "note": "超出核准日數，不得報支（第三點）"})
            continue
        pd = seg["per_diem_base"]   # 當地當日基準額（輸入帶入，非內建查表）
        amt = daily_amount(pd, is_return_day=seg.get("is_return_day", False),
                           host_provided=seg.get("host_provided", "none"),
                           meals_not_provided=seg.get("meals_not_provided", []),
                           cash_allowance_usd=seg.get("cash_allowance_usd", 0.0))
        # P1-2：長期駐留遞減係數乘在最後。
        # 注意：返國當日（is_return_day=True）若仍在長期駐留期內，30% 基礎再乘遞減係數，
        # 屬有意識設計——返國當日既已只領 30%，再依駐留折減符合報支要點精神，不視為漏洞。
        amt *= long_stay_factor(seg.get("day_index_same_place", 1),
                                exempt=seg.get("reduction_exempt", False))  # P1-2
        per_segment.append({**seg, "per_diem_base": pd, "amount_usd": amt})
        subtotal += amt
    manual_total = sum(m["amount_usd"] for m in (manual_items or []))
    grand = math.ceil(subtotal + manual_total)     # R6：**總計後才** ceil（數額表附註4，gemini P2）
    return {"per_segment": per_segment, "subtotal_usd": subtotal,
            "manual_total_usd": manual_total, "grand_total_usd": grand}
