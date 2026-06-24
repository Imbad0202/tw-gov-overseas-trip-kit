"""docx CJK 字型工具：每個 run 設 w:eastAsia，否則 Word fallback 成新細明體。不附字型檔。"""
from docx.shared import Pt
from docx.oxml.ns import qn


def set_run_font(run, name_latin="Times New Roman", name_eastasia="細明體", size_pt=12, bold=False):
    """設定 run 的字型（拉丁＋東亞 CJK）與字級、粗體。

    Args:
        run: python-docx Run 物件
        name_latin: 拉丁字型名稱，預設 "Times New Roman"
        name_eastasia: 東亞（CJK）字型名稱，預設 "細明體"；寫入 w:eastAsia 屬性。
            注意：只寫名稱，不附字型檔（細明體為商業字型）。
        size_pt: 字級（pt），預設 12
        bold: 是否粗體，預設 False

    Returns:
        run（方便鏈式呼叫）
    """
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.name = name_latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), name_eastasia)  # 關鍵：CJK 字型走 eastAsia
    rfonts.set(qn("w:ascii"), name_latin)
    return run
