"""航班查價比較（純函式層）。

定位：行前查價比較底稿、非訂票工具。航班候選由使用者帶入或外部查詢提供，
本模組做候選正規化 / 排序 / fallback 判定的純函式，產出對照表資料。

排序優先序（相對偏好、非硬門檻）：
    尊重休息時間 > 轉機/候機時間越短越好 > 行李盡量直掛 > 票價

「尊重休息時間」= 三條可計算規則：
    ① 出發端 buffer：到機場留 ≥3hr，避開需凌晨出發的航班（含紅眼）。
    ② 落地端時間：避免凌晨抵達（叫不到車）。
    ③ 時差窗口：時差 >4hr 時，落地至公務首場留 >8hr 調時差（需首場時間）。

候選為 in-memory dict（不入 trip.json schema）；確認後可由使用者另寫進 flights[]。
"""
import re

# 候選「完整性」只看影響航班可用性的欄位（航空公司 / 日期）。
# source_url / queried_date 是「溯源標示」非完整性 gate：缺席由 render 標「來源未確認、僅參考」
# （render 刻意支援無來源候選）。票務代理報價 / 手動輸入常無 URL，列入 required 會把這類
# 公務最常見來源誤標 incomplete、rest_penalty 回哨兵、排到 URL-backed 候選後（甚至全無 URL 時
# rest 規則被完全略過）。溯源紀律由 render 警示承載、不剝奪排序資格。
_REQUIRED_CANDIDATE_KEYS = ("operating_carrier", "flight_date")
# 轉機段 layover_minutes 未知時的排序代值：對齊 _sort_key 同款「保守大值排末位」哨兵
# （rest=10_000 / price=10**9）。需大到任何真實候機分鐘數加總都贏不過（多段長轉機過夜可達上千分鐘）。
_UNKNOWN_LAYOVER_MIN = 10_000


def _coerce_int(v):
    """排序鍵非負數值欄位韌性：外部 scraper / LLM 常把數值給成字串（'90' / '12000'）。
    int 直接用；可解析非負整數字串轉 int；其他（None / 非數值 / 浮點字串 / 負值）→ None 表未知，
    交由呼叫端套保守哨兵（不得當 0 插隊、不得拿字串去跟 int 比較而崩排序）。
    layover_minutes / transfers / price_twd 皆非負量，負值（'-30' / -1）無意義、視為未知，
    否則負值排序時被當「比 0 更優」讓垃圾候選插隊到合法選項前。
    bool 是 int 子型、但布林欄位不該走此路徑，明確排除避免 True→1 誤用。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if v >= 0 else None
    if isinstance(v, str):
        s = v.strip()
        if re.fullmatch(r"\d+", s):
            return int(s)
    return None


def _transfer_count(c: dict) -> int:
    """轉機次數：顯式 transfers（非負）優先；否則用「真轉機段數」(is_layover:true)。
    顯式 is_layover:false（同機 / 技術停靠）的中間段不算轉機、不該被當銜接罰或顯示。
    排序鍵與摘要顯示共用此函式，避免兩處各算一份而漂移（排序當 1、摘要顯示 2 的內部不一致）。
    normalize 對省略 is_layover 的 idx≥1 段會補推斷 True，故正常全轉機行程仍得 len-1。"""
    transfers = _coerce_int(c.get("transfers"))
    if transfers is not None:
        return transfers
    return sum(1 for l in c.get("legs", []) if l.get("is_layover"))


_LEG_DEFAULTS = {
    "dep_tz": None, "arr_tz": None, "dep_next_day": False, "arr_next_day": False,
    "is_layover": False, "layover_minutes": None, "baggage_through": None,
    "overnight": False, "duration_min": None,
}


# 收緊到合法時鐘：HH 0-23（允許單位數）、MM 00-59；非法值（24:75/25:00/08:60）→ 不匹配 → 標 incomplete。
_TIME_RE = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)(?:\+(\d+))?$")


def _split_next_day(t):
    """解析時刻：'HH:MM' 或 'HH:MM+1'（外部查詢常用跨日後綴）。
    回 (HH:MM 純時刻, 是否跨日, 是否可解析)。正規時刻為 HH:MM、跨日另用布林旗標承載。
    +2 以上多日 offset 異常罕見、布林旗標無法承載（會被重建成 +1 低報抵達日）→ 視為不可解析。"""
    if not isinstance(t, str):
        return t, False, False
    m = _TIME_RE.match(t.strip())
    if not m:
        return t, False, False
    hh, mm, plus = m.group(1), m.group(2), m.group(3)
    if plus is not None and int(plus) > 1:
        return t, False, False  # 多日 offset 無法用布林承載、標不可解析
    return f"{int(hh):02d}:{mm}", bool(plus and int(plus) > 0), True


def normalize_candidate(raw: dict) -> dict:
    """補齊候選必標欄位、標 incomplete。不憑印象補值：缺就標 incomplete。
    無 leg（空 legs）亦視為 incomplete（無航段的候選無意義）。
    另：跨日後綴（HH:MM+1）解析成 HH:MM + arr_next_day 旗標（對齊 HH:MM 格式）；
    多段候選若來源完全未標 is_layover、推斷第 2..n 段為轉機後段（避免排序漏算轉機成本）。"""
    c = dict(raw)
    c["marketing_carrier"] = c.get("marketing_carrier") or c.get("operating_carrier")
    raw_legs = c.get("legs") or []
    legs = []
    _bad_time = False
    _bad_leg = False
    for idx, raw_leg in enumerate(raw_legs):
        # 非 dict 的 leg entry（null / str / int）→ 標 incomplete、不崩；放空 leg 佔位保留段數。
        if not isinstance(raw_leg, dict):
            _bad_leg = True
            legs.append(dict(_LEG_DEFAULTS))
            continue
        leg = {**_LEG_DEFAULTS, **raw_leg}
        # 跨日後綴解析：剝 +N、跨日設旗標；dep / arr 端對稱（轉機次日出發 dep_time '08:00+1'
        # 需設 dep_next_day，否則 detail 表 08:00 看似早於前段抵達而誤導接駁判斷）。
        if leg.get("dep_time") is not None:
            leg["dep_time"], _dep_next, dep_ok = _split_next_day(leg["dep_time"])
            _bad_time = _bad_time or not dep_ok
            if _dep_next:
                leg["dep_next_day"] = True
        if leg.get("arr_time") is not None:
            leg["arr_time"], _arr_next, arr_ok = _split_next_day(leg["arr_time"])
            _bad_time = _bad_time or not arr_ok
            if _arr_next:
                leg["arr_next_day"] = True
        # per-leg 推斷轉機段：僅對「來源未顯式標 is_layover」的 leg 補；顯式值（含 False）尊重不覆寫。
        # 第 2..n 段（idx≥1）為轉機後段。混合標記時只補缺的、不因任一顯式即停全部推斷。
        if "is_layover" not in (raw_leg if isinstance(raw_leg, dict) else {}) and idx >= 1:
            leg["is_layover"] = True
        legs.append(leg)
    c["legs"] = legs
    # leg 完整 = 時刻齊 + 身分欄位（flight_no/route）齊。缺身分欄位（scraper/OCR miss）→ incomplete：
    #   schema flights[] required flight_no/route，缺則選定後無法寫回 trip.json、render 也須警示。
    _legs_incomplete = any(
        not l.get("dep_time") or not l.get("arr_time")
        or not l.get("flight_no") or not l.get("route")
        for l in legs)
    c["incomplete"] = (any(not c.get(k) for k in _REQUIRED_CANDIDATE_KEYS)
                       or not legs or _legs_incomplete or _bad_time or _bad_leg)
    return c


def is_complete_candidate(c: dict) -> bool:
    return not c.get("incomplete", True)


def _hhmm_to_min(t: str) -> int:
    h, mm = t.split(":")
    return int(h) * 60 + int(mm)


def rest_penalty(candidate: dict, first_duty_local: str | None = None,
                 tz_diff_hours: int = 0) -> int:
    """休息違規分（越高越差、僅供排序、不對外顯示）。

    規則①出發 buffer：到機場需 ≥3hr，出門時間 = 起飛 - 3hr；
        若推算出門落在 03:00-06:00（凌晨）→ 重罰。
    規則②落地時間：抵達落在 00:00-05:00（凌晨叫不到車）→ 罰。
    規則③時差窗口：tz_diff>4 且 落地至首場公務 <8hr → 罰（需 first_duty_local）。
    """
    legs = candidate.get("legs", [])
    if not legs or candidate.get("incomplete"):
        return 10_000  # 無資料或 incomplete 候選、排最後
    if not legs[0].get("dep_time") or not legs[-1].get("arr_time"):
        return 10_000  # partial leg 缺時刻、排最後
    dep = _hhmm_to_min(legs[0]["dep_time"])
    arr = _hhmm_to_min(legs[-1]["arr_time"])
    penalty = 0
    # 規則①：出門 = 起飛 - 180min（跨日用 mod 處理）
    leave_home = (dep - 180) % (24 * 60)
    if 3 * 60 <= leave_home < 6 * 60:
        penalty += 100
    elif leave_home < 3 * 60:
        penalty += 60  # 深夜出門、次差
    # 規則①補：凌晨/清晨起飛（00:00-06:00）→ 紅眼/超早班直接罰。
    # mod wrap 洞：00:30 起飛 → leave_home=21:30（前晚）→ 規則① 罰 0；但 00:30 起飛是紅眼應罰。
    # dep 直接落在 0-360min 即為凌晨起飛，兩層取疊加（penalty 不重置）。
    if 0 <= dep < 6 * 60:
        penalty += 100
    # 規則②：凌晨抵達
    if 0 <= arr < 5 * 60:
        penalty += 80
    # 規則②補：跨日紅眼（任一段「夜間 21:00-24:00 出發且該段本身跨午夜」）。
    #   23:30→06:30+1 這類橫跨睡眠時段的紅眼：leave_home 傍晚（規則①不觸發）、
    #   dep 非凌晨（規則①補不觸發）、arr 06:30 非凌晨（規則②不觸發）→ 三規則全漏。
    #   紅眼可落在任一段（首/中/末）→ 掃描所有段、任一命中即補罰一次（不疊加）。
    #   判據用「該段本身跨午夜」（arr 時刻 < dep 時刻）而非 arr_next_day 旗標：
    #   arr_next_day 混入「日曆隔日」語意——過夜後隔天傍晚段 22:00+1→23:30+1 的 arr_next_day 也 True、
    #   但 23:30 > 22:00 不跨午夜、非紅眼，用旗標會誤罰。跨午夜的鐵證是 arr 時刻繞回（< dep）。
    if any(
        l.get("dep_time") and l.get("arr_time")
        and 21 * 60 <= _hhmm_to_min(l["dep_time"]) < 24 * 60
        and _hhmm_to_min(l["arr_time"]) < _hhmm_to_min(l["dep_time"])
        for l in legs):
        penalty += 80
    # 規則③：時差調整窗口（用 abs 涵蓋西行負時差、避開符號洞）
    #   規則要求「留 >8hr」調整，故剛好 8hr 整（gap==480）仍屬不足、用 <= 一併罰。
    #
    #   資料模型限制（明示設計選擇）：候選只帶純時刻 + 跨日布林，first_duty_local 也只是純時刻、
    #   無日期維度。「落地到首場公務的真實 gap」需雙方絕對日期，候選資料不含——
    #   07:00+1 落地 + 08:00 首場可能是 1hr（首場當天）或 25hr（首場隔天），同輸入兩種正解。
    #   此處 mod 取「落地後最近的該時刻」為 gap：假設首場緊接落地——對公務出差常態正確
    #   （落地當天 / 隔天一早開會），對極寬鬆行程（落地後 >24hr 才首場）會過罰、但那種行程
    #   時差非排序重點、影響可接受。跨日抵達不跳過此規則：跳過會漏掉 07:00+1→08:00 這類
    #   真緊迫紅眼+時差案例（公務常態），漏罰傷害 > 罕見過罰。完整正解需 datetime，與
    #   「輕量查價底稿」定位不符，故在現有模型內選定「首場緊接落地」這個對常態正確的假設。
    if first_duty_local and abs(tz_diff_hours) > 4:
        gap = (_hhmm_to_min(first_duty_local) - arr) % (24 * 60)
        if gap <= 8 * 60:
            penalty += 50
    return penalty


def _sort_key(c: dict, first_duty_local=None, tz_diff_hours=0):
    """排序鍵：休息 > 轉機/候機 > 行李直掛 > 票價（相對偏好優先序）。

    incomplete 候選 sort_key 第一位給 1 → 排最後但不刪除。
    """
    rest = rest_penalty(c, first_duty_local=first_duty_local, tz_diff_hours=tz_diff_hours)
    # 轉機段（is_layover）才有候機/行李直掛語意；末段/直飛段不納入。
    layover_legs = [l for l in c.get("legs", []) if l.get("is_layover")]
    # transfers 與摘要顯示共用 _transfer_count（顯式優先、否則真轉機段數）、避免兩處漂移。
    transfers = _transfer_count(c)
    # 轉機段 layover_minutes 缺值/非數值=未知、不得當 0 分鐘（最理想）插隊到已知短轉機前。
    #   未知記 _UNKNOWN_LAYOVER_MIN（大值、保守不憑印象）；直飛無轉機段 → total=0、不受影響。
    #   _coerce_int 攔字串數值（scraper '90'）與垃圾（'abc'→未知），避免 int+str 崩 sum()。
    layover_total = sum(
        (lm if (lm := _coerce_int(l.get("layover_minutes"))) is not None else _UNKNOWN_LAYOVER_MIN)
        for l in layover_legs)
    # 行李直掛只看轉機段（要掛到下一段）；末段/直飛段預設 None 不算「沒直掛」。
    #   無轉機段（直飛）→ bags_through=0（不扣）；任一轉機段未直掛 → 1。
    bags_through = 0 if all(l.get("baggage_through") for l in layover_legs) else 1
    # 無價/非數值價=排序時不利、但不主導（第四順位）；字串 '12000' coerce 成 int 才能與 int 互比。
    price = _coerce_int(c.get("price_twd"))
    if price is None:
        price = 10 ** 9
    return (1 if c.get("incomplete") else 0, rest, transfers, layover_total, bags_through, price)


def rank_candidates(candidates: list, first_duty_local=None, tz_diff_hours=0) -> list:
    """相對排序、永遠回所有候選（不篩除）。最佳在前。

    入口防呆 normalize 每個候選（normalize_candidate 冪等）：呼叫端若已先 normalize、
    再跑一次不變；若傳 raw scraper/LLM 輸出（漏 is_layover 推斷 / 字串數值 / 缺欄位），
    這裡補正規化、避免轉機被當零成本排序、避免字串數值崩、incomplete 正確標記。
    回傳正規化後的候選、下游 render 拿到一致的正規化欄位。"""
    normalized = [normalize_candidate(c) for c in candidates]
    return sorted(normalized, key=lambda c: _sort_key(
        c, first_duty_local=first_duty_local, tz_diff_hours=tz_diff_hours))


def choose_layout(candidates: list) -> str:
    """全候選單段直飛 → table；任一含 ≥2 航段 → card（整份統一、不混排）。"""
    for c in candidates:
        if len(c.get("legs", [])) >= 2:
            return "card"
    return "table"


def summary_rows(candidates: list) -> list:
    """每候選一行摘要比較列（無論表格/卡片都先出此列）。

    latest_arr 跨日（末段 arr_next_day）帶 +1：摘要表是第一眼比較處、
    末段時刻已剝後綴、不在此補旗標會讓跨日抵達顯示成當日、誤導比較。
    """
    rows = []
    for i, c in enumerate(candidates):
        legs = c.get("legs", [])
        last = legs[-1] if legs else None
        latest_arr = last.get("arr_time") if last else None
        if latest_arr and last.get("arr_next_day"):
            latest_arr = f"{latest_arr}+1"
        # 首段跨日出發在摘要也帶 +1（鏡像 latest_arr）：detail 顯示 08:00+1、
        # 摘要不標會讓使用者誤判同日出發（摘要是第一眼比較處）。
        first = legs[0] if legs else None
        earliest_dep = first.get("dep_time") if first else None
        if earliest_dep and first.get("dep_next_day"):
            earliest_dep = f"{earliest_dep}+1"
        rows.append({
            "label": chr(ord("A") + i),
            "total_duration": c.get("total_duration"),
            # 摘要轉機次數與排序鍵共用 _transfer_count、避免顯示與排序內部不一致。
            "transfers": _transfer_count(c),
            "earliest_dep": earliest_dep,
            "latest_arr": latest_arr,
            "price": c.get("price_twd"),
        })
    return rows
