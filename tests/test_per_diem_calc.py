# tests/test_per_diem_calc.py
from calc.per_diem import compute_trip_per_diem, daily_amount, long_stay_factor

def test_full_day_normal():
    assert daily_amount(300, is_return_day=False, host_provided="none", meals_not_provided=[]) == 300

def test_return_day_30pct():
    # 返國/歇夜當日 = 30%（第九點末）
    assert daily_amount(300, is_return_day=True, host_provided="none", meals_not_provided=[]) == 90

def test_board_and_lodging_topup_to_10pct():
    # 供膳宿、無現金津貼 → 零用補足至 10% = 30（第九點1項1款）
    assert daily_amount(300, is_return_day=False, host_provided="board_and_lodging",
                        meals_not_provided=[]) == 30

def test_board_and_lodging_with_cash_allowance():
    # P1-1：供膳宿但已收現金津貼 20 → 只補足 30-20=10，非無條件給 30
    assert daily_amount(300, is_return_day=False, host_provided="board_and_lodging",
                        meals_not_provided=[], cash_allowance_usd=20) == 10

def test_cash_allowance_exceeds_incidental():
    # 已收現金津貼 ≥ 10% → 零用補足 0（不倒扣）
    assert daily_amount(300, is_return_day=False, host_provided="board_and_lodging",
                        meals_not_provided=[], cash_allowance_usd=50) == 0

def test_board_only_70_plus_topup():
    # 供膳不供宿 → 住宿70%(210) + 零用補足10%(30) = 240
    assert daily_amount(300, is_return_day=False, host_provided="board_only", meals_not_provided=[]) == 240

def test_lodging_only_20_plus_topup():
    # 供宿不供膳 → 膳食20%(60) + 零用補足10%(30) = 90
    assert daily_amount(300, is_return_day=False, host_provided="lodging_only", meals_not_provided=[]) == 90

def test_partial_meals_not_provided():
    # 供膳宿但未供晚餐 → 零用補足30 + 補晚餐8%(24) = 54
    assert daily_amount(300, is_return_day=False, host_provided="board_and_lodging",
                        meals_not_provided=["dinner"]) == 54

# --- P1-2：長期駐留遞減 + 例外 ---
def test_long_stay_reduction():
    assert long_stay_factor(15) == 1.0      # 第1月全額
    assert long_stay_factor(45) == 0.80     # 第2月起 80%
    assert long_stay_factor(120) == 0.70    # 第4月起 70%

def test_long_stay_boundaries():
    # off-by-one 邊界（第十一點：逾1月未逾3月 / 逾3月）
    assert long_stay_factor(30) == 1.0      # 第30日仍第1月全額
    assert long_stay_factor(31) == 0.80     # 第31日起 80%
    assert long_stay_factor(90) == 0.80     # 第90日仍 80%
    assert long_stay_factor(91) == 0.70     # 第91日起 70%

def test_long_stay_exempt():
    # P1-2：國際會議/紅色警示/籌設使領館 → 不遞減（第十一點除外）
    assert long_stay_factor(120, exempt=True) == 1.0

# --- P1-5：超出核准日數 ---
def test_exceed_approved_days_not_reimbursed():
    segs = [{"per_diem_base": 284},
            {"per_diem_base": 284},   # index 1，超出核准 1 日
            {"per_diem_base": 284}]   # index 2，超出
    out = compute_trip_per_diem(segs, approved_days=1)
    # 只第 1 日(284)可報，後兩日 0 → 進位 284
    assert out["grand_total_usd"] == 284

def test_approved_extension_still_reimbursed():
    # P1-5/B-5：超出核准但延返經核准（患病/意外/不可歸責事由，第三、十二點）→ 仍可報
    segs = [{"per_diem_base": 284},
            {"per_diem_base": 284, "approved_extension": True}]
    out = compute_trip_per_diem(segs, approved_days=1)
    assert out["grand_total_usd"] == 568   # 284 + 284

def test_grand_total_rounds_up():
    # R6：總計尾數不足一元進位
    segs = [{"per_diem_base": 178, "is_return_day": True}]
    out = compute_trip_per_diem(segs)        # 178 * 0.30 = 53.4 → 54
    assert out["grand_total_usd"] == 54

def test_manual_items_included():
    segs = [{"per_diem_base": 284}]
    out = compute_trip_per_diem(segs, manual_items=[{"label": "商務艙差額", "amount_usd": 500}])
    assert out["grand_total_usd"] == 784     # 284 + 500

def test_in_transit_lodging_not_return_day():
    # B-6：機上歇夜（非返國）走供宿不供膳 lodging_only，膳食20%+零用補足10%=30%，非返國日 30%
    # 兩者在曼谷 284 下數字巧合都 0.30，但組成不同、且機上歇夜可因供餐再補 → 用 lodging_only 才正確
    assert daily_amount(284, is_return_day=False, host_provided="lodging_only",
                        meals_not_provided=[]) == 284 * 0.30   # 膳食20%+零用10%
    # 返國當日才用 is_return_day
    assert daily_amount(284, is_return_day=True, host_provided="none", meals_not_provided=[]) == 284 * 0.30


# --- P1-3：invalid host_provided fail-fast ---
def test_invalid_host_provided_raises():
    import pytest
    with pytest.raises(ValueError, match="unknown host_provided"):
        daily_amount(300, is_return_day=False, host_provided="board-and-lodging",
                     meals_not_provided=[])
