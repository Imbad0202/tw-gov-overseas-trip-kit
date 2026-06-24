"""經費規劃表 xlsx。日支明細 + B 類 manual + 總計（R6 進位）+ 動態簽章列。"""
import openpyxl
from calc.per_diem import compute_trip_per_diem


def render_finance_xlsx(data: dict, out_path: str) -> None:
    """產生經費規劃表 xlsx。

    Args:
        data: 包含 agency、per_diem_inputs、signatures 的 dict。
        out_path: 輸出 xlsx 路徑。
    """
    agency = data["agency"]
    inputs = data["per_diem_inputs"]
    result = compute_trip_per_diem(
        inputs["segments"],
        inputs.get("manual_items"),
        approved_days=inputs.get("approved_days"),
    )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "經費規劃表"

    # 標題列
    ws["A1"] = f"{agency['full_name']} 出國經費規劃表"

    # 表頭
    ws.append(["日期", "留宿地", "日支基準(US$)", "當日應領(US$)"])

    # 逐日日支明細
    for seg in result["per_segment"]:
        ws.append([
            seg.get("date", ""),
            seg.get("lodging_city", ""),
            seg["per_diem_base"],
            round(seg["amount_usd"], 2),
        ])

    # B 類 manual_items
    for m in inputs.get("manual_items", []):
        ws.append([m["label"], "(人工填入)", "", m["amount_usd"]])

    # 總計列（R6 尾數進位整數）
    ws.append(["總計(US$，尾數進位整數)", "", "", result["grand_total_usd"]])

    # 動態簽章列（從 data['signatures'] 陣列生成，不寫死角色）
    ws.append([])
    ws.append([s["role"] for s in data.get("signatures", [])])

    wb.save(out_path)
