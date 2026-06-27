"""航班查價：候選正規化 + 相對排序（休息三規則）。

排序為相對比較非 gate、永遠給最佳解、只排序不顯分。
休息規則：①出發≥3hr buffer避凌晨 ②落地避凌晨 ③時差>4hr留>8hr。
"""
import pytest

from calc import flight_rank as m


def _cand(dep, arr, layovers=0):
    return m.normalize_candidate({
        "legs": [{"flight_no": "X1", "route": "AAA→BBB",
                  "dep_time": dep, "arr_time": arr}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26",
        "transfers": layovers,
    })


# ── 正規化 ──

def _raw():
    return {
        "legs": [{"flight_no": "ZZ205", "route": "AAA(AAA)→BBB(BBB)",
                  "dep_time": "08:50", "arr_time": "11:40"}],
        "operating_carrier": "ZZ", "marketing_carrier": "ZZ",
        "flight_date": "2027-08-12",
        "source_url": "https://example.com/...", "queried_date": "2027-06-26",
    }


def test_complete_candidate_not_incomplete():
    c = m.normalize_candidate(_raw())
    assert c["incomplete"] is False
    assert m.is_complete_candidate(c) is True


def test_missing_operating_carrier_marks_incomplete():
    raw = _raw(); del raw["operating_carrier"]
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_missing_flight_date_marks_incomplete():
    raw = _raw(); del raw["flight_date"]
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_empty_legs_marks_incomplete():
    raw = _raw(); raw["legs"] = []
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_legs_null_marks_incomplete_no_crash():
    raw = _raw(); raw["legs"] = None
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_non_dict_leg_entry_marks_incomplete_no_crash():
    """legs 內含非 dict entry（[null] / [str] / [int]）→ 標 incomplete、不拋 TypeError。
    其他 malformed 資料都是標 incomplete 保持可用、一個壞 leg 不該讓整流程崩。"""
    for bad_legs in ([None], ["str"], [123],
                     [{"flight_no": "X", "route": "A→B", "dep_time": "10:00", "arr_time": "11:00"}, None]):
        raw = _raw(); raw["legs"] = bad_legs
        c = m.normalize_candidate(raw)
        assert c["incomplete"] is True, f"{bad_legs} 應標 incomplete"
        assert m.rank_candidates([c]) == [c]  # 不拋


def test_marketing_carrier_defaults_to_operating():
    raw = _raw(); del raw["marketing_carrier"]
    c = m.normalize_candidate(raw)
    assert c["marketing_carrier"] == "ZZ"


# ── 跨日時刻後綴解析 ──

def test_next_day_arr_suffix_parsed():
    raw = _raw()
    raw["legs"][0]["arr_time"] = "07:25+1"
    raw["legs"][0]["dep_time"] = "21:55"
    c = m.normalize_candidate(raw)
    assert c["legs"][0]["arr_time"] == "07:25"
    assert c["legs"][0]["arr_next_day"] is True
    assert c["incomplete"] is False
    assert len(m.rank_candidates([c])) == 1  # 不拋 ValueError


def test_dep_time_next_day_suffix_also_parsed():
    raw = _raw()
    raw["legs"][0]["dep_time"] = "23:50+1"
    c = m.normalize_candidate(raw)
    assert c["legs"][0]["dep_time"] == "23:50"
    assert m.rank_candidates([c])


def test_dep_time_next_day_sets_flag():
    """轉機段次日出發 dep_time '08:00+1' → 剝後綴 + 設 dep_next_day 旗標（對稱 arr 處理）。
    否則 detail 表顯示 08:00 看似早於前段抵達、誤導。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→C", "dep_time": "18:00", "arr_time": "23:00"},
        {"flight_no": "X2", "route": "C→B", "dep_time": "08:00+1", "arr_time": "10:00+1"},
    ]
    c = m.normalize_candidate(raw)
    assert c["legs"][1]["dep_time"] == "08:00"
    assert c["legs"][1]["dep_next_day"] is True
    assert c["incomplete"] is False


def test_multiday_offset_rejected_as_incomplete():
    """+2 以上多日 offset 異常罕見、收成布林會低報抵達日（顯示 +1）→ 標 incomplete 不假裝 +1。"""
    raw = _raw()
    raw["legs"][0]["dep_time"] = "23:00"
    raw["legs"][0]["arr_time"] = "05:00+2"
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True
    assert m.rank_candidates([c]) == [c]  # 排最後、不拋


def test_malformed_time_marks_incomplete_not_crash():
    raw = _raw()
    raw["legs"][0]["arr_time"] = "garbage"
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True
    assert m.rank_candidates([c]) == [c]


def test_out_of_range_time_marks_incomplete():
    """非法時刻（HH>23 或 MM>59）→ 標 incomplete、不得當 valid 排序。
    e.g. 24:75 / 99:99 / 25:00 / 08:60 兩個數字欄位但非真實時間。"""
    for bad in ("24:75", "99:99", "25:00", "08:60", "24:00"):
        raw = _raw()
        raw["legs"][0]["dep_time"] = bad
        c = m.normalize_candidate(raw)
        assert c["incomplete"] is True, f"{bad} 應標 incomplete"
        assert m.rank_candidates([c]) == [c]  # 不拋、排最後


def test_valid_boundary_times_accepted():
    """合法邊界時刻（00:00 / 23:59 / 單位數小時 8:50）仍接受。"""
    for ok in ("00:00", "23:59", "8:50"):
        raw = _raw()
        raw["legs"][0]["dep_time"] = ok
        c = m.normalize_candidate(raw)
        assert c["incomplete"] is False, f"{ok} 應為合法時刻"


# ── 推斷轉機段 ──

def test_multileg_without_is_layover_marker_inferred():
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "AAA→CCC", "dep_time": "10:00", "arr_time": "13:00"},
        {"flight_no": "X2", "route": "CCC→BBB", "dep_time": "15:00", "arr_time": "17:00"},
    ]
    c = m.normalize_candidate(raw)
    assert c["legs"][0]["is_layover"] is False
    assert c["legs"][1]["is_layover"] is True


def test_explicit_is_layover_marker_respected():
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "AAA→CCC", "dep_time": "10:00", "arr_time": "13:00",
         "is_layover": True},
        {"flight_no": "X2", "route": "CCC→BBB", "dep_time": "15:00", "arr_time": "17:00",
         "is_layover": False},
    ]
    c = m.normalize_candidate(raw)
    assert c["legs"][0]["is_layover"] is True
    assert c["legs"][1]["is_layover"] is False


def test_single_leg_not_marked_layover():
    c = m.normalize_candidate(_raw())
    assert c["legs"][0]["is_layover"] is False


def test_mixed_is_layover_markers_infer_only_missing():
    """部分 leg 顯式標、部分省略時：per-leg 只推斷缺的、尊重顯式。
    修前全域旗標：任一 leg 顯式即停全部推斷、省略的轉機段漏標 → 排序漏算。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→C", "dep_time": "10:00", "arr_time": "13:00",
         "is_layover": False},  # 首段顯式 False
        {"flight_no": "X2", "route": "C→B", "dep_time": "15:00", "arr_time": "17:00",
         "layover_minutes": 90, "baggage_through": False},  # 轉機段省略 is_layover
    ]
    c = m.normalize_candidate(raw)
    assert c["legs"][0]["is_layover"] is False   # 尊重顯式
    assert c["legs"][1]["is_layover"] is True    # 缺標的第 2 段→推斷轉機後段
    # 排序維度看得到 90 分候機 + 未直掛
    assert m._sort_key(c)[3] == 90   # layover_total
    assert m._sort_key(c)[4] == 1    # bags_through（未直掛）


def test_explicit_false_on_connecting_leg_respected():
    """轉機段顯式標 is_layover=False（罕見、但尊重來源）→ 不被推斷覆寫。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→C", "dep_time": "10:00", "arr_time": "13:00"},
        {"flight_no": "X2", "route": "C→B", "dep_time": "15:00", "arr_time": "17:00",
         "is_layover": False},  # 顯式 False
    ]
    c = m.normalize_candidate(raw)
    assert c["legs"][1]["is_layover"] is False


# ── 休息三規則 ──

def test_early_morning_departure_penalized():
    early = _cand("07:00", "11:40")
    later = _cand("10:00", "14:40")
    assert m.rest_penalty(early) > m.rest_penalty(later)


def test_midnight_arrival_penalized():
    midnight = _cand("18:00", "02:00")
    daytime = _cand("10:00", "14:00")
    assert m.rest_penalty(midnight) > m.rest_penalty(daytime)


def test_red_eye_0030_penalized():
    assert m.rest_penalty(_cand("00:30", "08:00")) > m.rest_penalty(_cand("10:00", "14:00"))


def test_early_dawn_0500_penalized():
    assert m.rest_penalty(_cand("05:00", "09:00")) > m.rest_penalty(_cand("10:00", "14:00"))


def test_jet_lag_window_penalized():
    cand = _cand("08:00", "14:00")
    with_jetlag = m.rest_penalty(cand, first_duty_local="18:00", tz_diff_hours=6)
    no_jetlag = m.rest_penalty(cand, first_duty_local="18:00", tz_diff_hours=0)
    assert with_jetlag > no_jetlag


def test_negative_tz_diff_still_penalized():
    cand = _cand("08:00", "14:00")
    with_neg = m.rest_penalty(cand, first_duty_local="18:00", tz_diff_hours=-6)
    no_tz = m.rest_penalty(cand, first_duty_local="18:00", tz_diff_hours=0)
    assert with_neg > no_tz


def test_small_negative_tz_not_penalized():
    cand = _cand("08:00", "14:00")
    small = m.rest_penalty(cand, first_duty_local="18:00", tz_diff_hours=-3)
    no_tz = m.rest_penalty(cand, first_duty_local="18:00", tz_diff_hours=0)
    assert small == no_tz


def test_overnight_redeye_before_midnight_penalized():
    """跨日紅眼（23:30→06:30+1）睡眠被切斷、應劣於日間班；
    leave_home 傍晚 + dep 非凌晨 + arr 非凌晨 → 舊三規則全漏、須補跨日紅眼罰。"""
    redeye = m.normalize_candidate({
        "legs": [{"flight_no": "X1", "route": "A→B", "dep_time": "23:30",
                  "arr_time": "06:30", "arr_next_day": True}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    day = _cand("10:00", "14:00")
    assert m.rest_penalty(redeye) > m.rest_penalty(day)


def test_multileg_redeye_uses_final_leg_departure():
    """多段：首段日間 feeder（18:00→20:00）+ 末段紅眼（23:30→06:30+1）→ 紅眼在末段，
    須用末段出發判定、首段 dep 會漏罰。應劣於日間班。"""
    multi = m.normalize_candidate({
        "legs": [
            {"flight_no": "X1", "route": "A→B", "dep_time": "18:00", "arr_time": "20:00"},
            {"flight_no": "X2", "route": "B→C", "dep_time": "23:30", "arr_time": "06:30",
             "arr_next_day": True, "is_layover": True},
        ],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    day = _cand("10:00", "14:00")
    assert m.rest_penalty(multi) > m.rest_penalty(day)


def test_redeye_in_first_leg_penalized():
    """紅眼在首段（非末段）：23:30→06:30+1 後接 09:00+1→13:00+1 日間轉機 →
    綁死 legs[-1] 會漏（末段日間）。正解掃描所有段、首段紅眼即罰。"""
    redeye_first = m.normalize_candidate({
        "legs": [
            {"flight_no": "X1", "route": "A→B", "dep_time": "23:30", "arr_time": "06:30",
             "arr_next_day": True},
            {"flight_no": "X2", "route": "B→C", "dep_time": "09:00", "arr_time": "13:00",
             "dep_next_day": True, "arr_next_day": True, "is_layover": True},
        ],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    day = _cand("10:00", "14:00")
    assert m.rest_penalty(redeye_first) > m.rest_penalty(day)


def test_multileg_night_start_daytime_final_not_redeye_penalized():
    """反向：首段夜間出發（22:00）但末段日間出發（09:00+1）→ 末段非紅眼，
    不得用首段 dep 誤判整段為紅眼。末段日間出發那筆不該吃紅眼罰。"""
    night_start = m.normalize_candidate({
        "legs": [
            {"flight_no": "X1", "route": "A→B", "dep_time": "22:00", "arr_time": "23:30"},
            {"flight_no": "X2", "route": "B→C", "dep_time": "09:00", "arr_time": "11:00",
             "dep_next_day": True, "arr_next_day": True, "is_layover": True},
        ],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    # 末段 09:00 日間出發 → 不吃紅眼罰（80）；與一個確定吃紅眼罰的單段比應更低
    redeye_single = m.normalize_candidate({
        "legs": [{"flight_no": "Y1", "route": "A→B", "dep_time": "23:30",
                  "arr_time": "06:30", "arr_next_day": True}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    assert m.rest_penalty(night_start) < m.rest_penalty(redeye_single)


def test_overnight_then_evening_leg_not_redeye():
    """過夜後隔天傍晚段 22:00+1→23:30+1：arr_next_day True（日曆隔日）但 23:30>22:00 不跨午夜、
    非紅眼。判據用「arr<dep 跨午夜」而非 arr_next_day 旗標、否則誤罰。應不吃紅眼罰。"""
    overnight_evening = m.normalize_candidate({
        "legs": [
            {"flight_no": "X1", "route": "A→B", "dep_time": "18:00", "arr_time": "20:00"},
            {"flight_no": "X2", "route": "B→C", "dep_time": "22:00", "arr_time": "23:30",
             "dep_next_day": True, "arr_next_day": True, "is_layover": True},
        ],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    # 末段 22:00→23:30 不跨午夜（23:30>22:00）→ 不該吃紅眼 80 罰；與真紅眼比應更低
    redeye = m.normalize_candidate({
        "legs": [{"flight_no": "Y1", "route": "A→B", "dep_time": "23:30",
                  "arr_time": "06:30", "arr_next_day": True}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    assert m.rest_penalty(overnight_evening) < m.rest_penalty(redeye)


def test_jet_lag_tight_window_next_day_arrival_penalized():
    """跨日抵達 + 首場緊接落地（07:00+1 落地、08:00 首場、時差6）→ gap 僅 1hr、該罰時差。
    設計選擇：first_duty_local 無日期維度，mod 取「落地後最近該時刻」假設首場緊接落地——
    對公務出差常態（落地當天/隔天一早開會）正確；跨日不跳過此規則、否則漏掉真緊迫紅眼+時差。"""
    arr_next = m.normalize_candidate({
        "legs": [{"flight_no": "X1", "route": "A→B", "dep_time": "20:00",
                  "arr_time": "07:00", "arr_next_day": True}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26"})
    with_tz = m.rest_penalty(arr_next, first_duty_local="08:00", tz_diff_hours=6)
    no_tz = m.rest_penalty(arr_next, first_duty_local="08:00", tz_diff_hours=0)
    assert with_tz > no_tz  # gap 1hr <8hr → 時差罰生效（跨日不豁免）


def test_jet_lag_exactly_eight_hours_penalized():
    """規則③需留 >8hr；落地 14:00 首場 22:00 gap 剛好 8hr 整 → 不足、應罰（< 改 <=）。"""
    cand = _cand("08:00", "14:00")
    exactly_8h = m.rest_penalty(cand, first_duty_local="22:00", tz_diff_hours=6)
    no_jetlag = m.rest_penalty(cand, first_duty_local="22:00", tz_diff_hours=0)
    assert exactly_8h > no_jetlag


def test_jet_lag_over_eight_hours_not_penalized():
    """gap 8hr01min（> 8hr）→ 足夠調整、不罰（邊界另一側、確認沒過罰）。"""
    cand = _cand("08:00", "14:00")
    over_8h = m.rest_penalty(cand, first_duty_local="22:01", tz_diff_hours=6)
    no_jetlag = m.rest_penalty(cand, first_duty_local="22:01", tz_diff_hours=0)
    assert over_8h == no_jetlag


# ── 排序行為 ──

def test_rank_never_drops_complete_candidates():
    ranked = m.rank_candidates([_cand("07:00", "11:40"), _cand("06:00", "10:40")])
    assert len(ranked) == 2


def test_better_rest_ranked_first():
    ranked = m.rank_candidates([_cand("06:00", "10:00"), _cand("10:00", "14:00")])
    assert ranked[0]["legs"][0]["dep_time"] == "10:00"


def test_incomplete_ranked_last():
    complete = _cand("10:00", "14:00")
    incomplete = m.normalize_candidate({
        "legs": [{"flight_no": "X2", "route": "AAA→BBB",
                  "dep_time": "08:00", "arr_time": "11:00"}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
    })
    ranked = m.rank_candidates([incomplete, complete])
    assert ranked[0]["legs"][0].get("dep_time") == "10:00"


def test_transfers_null_does_not_crash_rank():
    cand_null = m.normalize_candidate({
        "legs": [{"flight_no": "X1", "route": "AAA→BBB",
                  "dep_time": "10:00", "arr_time": "14:00"}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26", "transfers": None,
    })
    assert len(m.rank_candidates([cand_null, _cand("10:00", "14:00")])) == 2


# ── 第十輪 edge：layover/baggage 只看轉機段 ──

def _two_leg(layover_minutes, baggage_through, is_layover=True):
    """兩段候選：第二段為轉機段（慣例：轉機資訊掛轉機後那段）。"""
    return m.normalize_candidate({
        "legs": [
            {"flight_no": "X1", "route": "AAA→CCC", "dep_time": "10:00", "arr_time": "13:00"},
            {"flight_no": "X2", "route": "CCC→BBB", "dep_time": "15:00", "arr_time": "17:00",
             "is_layover": is_layover, "layover_minutes": layover_minutes,
             "baggage_through": baggage_through},
        ],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26",
    })


def test_unknown_layover_not_ranked_before_known_short():
    unknown = _two_leg(layover_minutes=None, baggage_through=True)
    known_short = _two_leg(layover_minutes=30, baggage_through=True)
    ranked = m.rank_candidates([unknown, known_short])
    assert ranked[0]["legs"][1]["layover_minutes"] == 30
    assert m._sort_key(unknown)[3] > m._sort_key(known_short)[3]


def test_direct_flight_not_penalized_for_baggage():
    assert m._sort_key(_cand("10:00", "14:00"))[4] == 0


def test_transfer_without_through_baggage_penalized():
    assert m._sort_key(_two_leg(layover_minutes=90, baggage_through=False))[4] == 1


# ── layout / summary ──

def test_choose_layout_direct_is_table():
    assert m.choose_layout([_cand("10:00", "14:00")]) == "table"


def test_choose_layout_multileg_is_card():
    multi = m.normalize_candidate({
        "legs": [{"flight_no": "X1", "route": "AAA→CCC", "dep_time": "10:00", "arr_time": "13:00"},
                 {"flight_no": "X2", "route": "CCC→BBB", "dep_time": "15:00", "arr_time": "17:00"}],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26",
    })
    assert m.choose_layout([multi]) == "card"


def test_summary_rows_labels_and_fields():
    rows = m.summary_rows([_cand("08:50", "11:40"), _cand("10:00", "14:00")])
    assert [r["label"] for r in rows] == ["A", "B"]
    assert rows[0]["earliest_dep"] == "08:50"


def test_summary_latest_arr_keeps_next_day_marker():
    """跨日抵達在摘要列也要帶 +1（摘要表是第一眼比較處、不標會誤導成當日抵達）。"""
    raw = _raw()
    raw["legs"][0]["dep_time"] = "21:55"
    raw["legs"][0]["arr_time"] = "07:25+1"
    c = m.normalize_candidate(raw)
    rows = m.summary_rows([c])
    assert rows[0]["latest_arr"] == "07:25+1"


def test_summary_latest_arr_same_day_no_marker():
    rows = m.summary_rows([_cand("08:50", "11:40")])
    assert rows[0]["latest_arr"] == "11:40"


def test_summary_earliest_dep_keeps_next_day_marker():
    """首段跨日出發在摘要列也要帶 +1（detail 顯示 08:00+1、摘要不標會誤判同日出發）。"""
    raw = _raw()
    raw["legs"][0]["dep_time"] = "08:00+1"
    raw["legs"][0]["arr_time"] = "10:00+1"
    c = m.normalize_candidate(raw)
    rows = m.summary_rows([c])
    assert rows[0]["earliest_dep"] == "08:00+1"


def test_summary_earliest_dep_same_day_no_marker():
    rows = m.summary_rows([_cand("08:50", "11:40")])
    assert rows[0]["earliest_dep"] == "08:50"


# ── 排序鍵數值欄位型別韌性（外部 scraper/LLM 給字串數值不得崩排序）──

def test_string_layover_minutes_does_not_crash_rank():
    """轉機段 layover_minutes 來自 scraper 為字串 '90' → 排序不得 int+str 崩、仍回所有候選。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→C", "dep_time": "10:00", "arr_time": "13:00"},
        {"flight_no": "X2", "route": "C→B", "dep_time": "15:00", "arr_time": "17:00",
         "layover_minutes": "90", "baggage_through": True},
    ]
    c = m.normalize_candidate(raw)
    ranked = m.rank_candidates([c])
    assert len(ranked) == 1


def test_string_price_does_not_crash_rank():
    """price_twd 字串 '10000' 與 int 12000 混排 → 不得 str<int 崩、字串價仍正確比較。"""
    base = {"legs": [{"flight_no": "X1", "route": "A→B",
                      "dep_time": "10:00", "arr_time": "14:00"}],
            "operating_carrier": "ZZ", "flight_date": "2027-08-12",
            "source_url": "u", "queried_date": "2027-06-26"}
    a = m.normalize_candidate({**base, "price_twd": "10000"})
    b = m.normalize_candidate({**base, "price_twd": 12000})
    ranked = m.rank_candidates([a, b])
    assert len(ranked) == 2
    # 字串 '10000' 應被當 10000 比較、排在 12000 之前
    assert ranked[0]["price_twd"] in ("10000", 10000)


def test_nonnumeric_sort_field_treated_as_unknown():
    """非數值垃圾（layover_minutes 'abc'）→ 視為未知大值、不崩、不插隊到已知短轉機前。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→C", "dep_time": "10:00", "arr_time": "13:00"},
        {"flight_no": "X2", "route": "C→B", "dep_time": "15:00", "arr_time": "17:00",
         "layover_minutes": "abc"},
    ]
    c = m.normalize_candidate(raw)
    ranked = m.rank_candidates([c])
    assert len(ranked) == 1


def test_string_transfers_does_not_crash_rank():
    """transfers 字串 '1' → 排序不得 str 與 int 比較崩。"""
    raw = _raw()
    raw["transfers"] = "1"
    c = m.normalize_candidate(raw)
    ranked = m.rank_candidates([c])
    assert len(ranked) == 1


def test_missing_provenance_not_incomplete():
    """票務代理報價 / 手動輸入無 source_url / queried_date → 不得標 incomplete。
    溯源缺席由 render 標「來源未確認、僅參考」（設計刻意支援），非完整性 gate；
    否則公務最常見的代理報價被當 incomplete、rest 規則被略過、排到 URL-backed 候選後。"""
    raw = _raw()
    del raw["source_url"]
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is False
    assert m.is_complete_candidate(c) is True


def test_quotes_without_url_still_ranked_by_rest():
    """全候選皆無 source_url（代理報價情境）→ rest 規則仍生效、非全部 incomplete 並列。
    日間班應排在紅眼班之前（rest 規則沒被 incomplete 哨兵吃掉）。"""
    base = {"operating_carrier": "ZZ", "flight_date": "2027-08-12"}  # 無 source_url/queried_date
    day = m.normalize_candidate({**base, "legs": [
        {"flight_no": "X1", "route": "A→B", "dep_time": "10:00", "arr_time": "14:00"}]})
    redeye = m.normalize_candidate({**base, "legs": [
        {"flight_no": "Y1", "route": "A→B", "dep_time": "23:30", "arr_time": "06:30",
         "arr_next_day": True}]})
    assert day["incomplete"] is False and redeye["incomplete"] is False
    ranked = m.rank_candidates([redeye, day])
    assert ranked[0]["legs"][0]["flight_no"] == "X1"  # 日間班排前（rest 規則生效）


def test_leg_missing_flight_no_marks_incomplete():
    """leg 時刻齊但缺 flight_no（scraper/OCR miss）→ 標 incomplete。
    schema flights[] required flight_no，缺則選定後無法寫回 trip.json；顯示也須警示。"""
    raw = _raw()
    raw["legs"] = [{"route": "A→B", "dep_time": "08:00", "arr_time": "10:00"}]  # 無 flight_no
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_leg_missing_route_marks_incomplete():
    """leg 時刻齊但缺 route → 標 incomplete（同 flight_no，schema required）。"""
    raw = _raw()
    raw["legs"] = [{"flight_no": "ZZ1", "dep_time": "08:00", "arr_time": "10:00"}]  # 無 route
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_leg_empty_string_identity_marks_incomplete():
    """flight_no/route 為空字串（非缺鍵）也無用 → 標 incomplete。"""
    raw = _raw()
    raw["legs"] = [{"flight_no": "", "route": "", "dep_time": "08:00", "arr_time": "10:00"}]
    c = m.normalize_candidate(raw)
    assert c["incomplete"] is True


def test_rank_normalizes_raw_candidates():
    """rank_candidates 對 raw（未先 normalize）輸入也須防呆 normalize：
    raw 多段未標 is_layover 不得當零轉機、raw 字串數值不得崩、incomplete 不得當完整。"""
    raw_multi = {
        "legs": [
            {"flight_no": "X1", "route": "A→B", "dep_time": "08:00", "arr_time": "10:00"},
            {"flight_no": "X2", "route": "B→C", "dep_time": "11:00", "arr_time": "13:00",
             "layover_minutes": "90"},  # 字串數值 + 未標 is_layover
        ],
        "operating_carrier": "ZZ", "flight_date": "2027-08-12",
        "source_url": "u", "queried_date": "2027-06-26",
    }
    ranked = m.rank_candidates([raw_multi])  # 不得崩
    assert len(ranked) == 1
    # normalize 後第 2 段應被推斷為轉機段（is_layover）
    assert ranked[0]["legs"][1].get("is_layover") is True


def test_negative_numeric_values_treated_as_unknown():
    """不可能負值（layover_minutes '-30' / transfers -1 / price '-100'）→ 視為未知，
    不得當「比 0 更優」插隊到合法候選前。負量在這些非負欄位無意義。"""
    assert m._coerce_int("-30") is None
    assert m._coerce_int(-1) is None
    assert m._coerce_int("-100") is None
    # 0 與正值仍合法
    assert m._coerce_int("0") == 0
    assert m._coerce_int(90) == 90


def test_negative_price_does_not_jump_ahead():
    """price_twd '-100'（垃圾負值）不得排在合法 12000 之前（被當未知大值排後）。"""
    base = {"legs": [{"flight_no": "X1", "route": "A→B",
                      "dep_time": "10:00", "arr_time": "14:00"}],
            "operating_carrier": "ZZ", "flight_date": "2027-08-12",
            "source_url": "u", "queried_date": "2027-06-26"}
    cheap = m.normalize_candidate({**base, "price_twd": 12000})
    garbage = m.normalize_candidate({**base, "price_twd": "-100"})
    ranked = m.rank_candidates([garbage, cheap])
    assert ranked[0]["price_twd"] == 12000  # 合法價在前、負值垃圾排後


def test_explicit_non_layover_leg_not_counted_as_transfer():
    """中間段顯式 is_layover:false（同機/技術停靠）+ 無 top-level transfers →
    transfers fallback 應從真轉機段（is_layover:true）數推導、非 len-1，否則高估轉機罰分。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→B", "dep_time": "08:00", "arr_time": "10:00"},
        {"flight_no": "X1", "route": "B→C", "dep_time": "10:30", "arr_time": "12:00",
         "is_layover": False},  # 同機技術停靠、非真轉機
        {"flight_no": "X2", "route": "C→D", "dep_time": "14:00", "arr_time": "16:00"},
    ]
    c = m.normalize_candidate(raw)
    # is_layover:true 段數 = 1（末段推斷），故 transfers 應為 1 非 2
    assert m._sort_key(c)[2] == 1


def test_summary_transfers_matches_sort_key():
    """摘要顯示的 transfers 須與排序鍵一致（同機技術停靠不得排序當 1、顯示當 2）。"""
    raw = _raw()
    raw["legs"] = [
        {"flight_no": "X1", "route": "A→B", "dep_time": "08:00", "arr_time": "10:00"},
        {"flight_no": "X1", "route": "B→C", "dep_time": "10:30", "arr_time": "12:00",
         "is_layover": False},  # 同機技術停靠
        {"flight_no": "X2", "route": "C→D", "dep_time": "14:00", "arr_time": "16:00"},
    ]
    c = m.normalize_candidate(raw)
    rows = m.summary_rows([c])
    assert rows[0]["transfers"] == m._sort_key(c)[2] == 1


def test_summary_direct_flight_zero_transfers():
    """直飛單段 → 摘要 transfers=0（回歸保護：_transfer_count 換掉 len-1 不得破直飛）。"""
    rows = m.summary_rows([_cand("08:00", "11:00")])
    assert rows[0]["transfers"] == 0
