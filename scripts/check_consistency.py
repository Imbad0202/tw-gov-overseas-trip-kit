#!/usr/bin/env python3
"""版本一致性與必要宣告檢查（轉 public 前安全 gate）。

驗項：
1. CITATIONS.md 含三個法規版本字串（114.05.13、1140101390、1140103430）
2. CHANGELOG.md 含 [1.0.0] entry
3. DISCLAIMER.md 含四層免責（正確性、AI 基本法、公務 AI 規範、個資法）
4. README.md 含版本參照（114.05.13）

fail 即 exit 1。
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
ERRORS: list[str] = []


def check(label: str, path: Path, patterns: list[str]) -> None:
    if not path.exists():
        ERRORS.append(f"MISSING FILE: {path.relative_to(REPO)}")
        return
    text = path.read_text(encoding="utf-8")
    for pat in patterns:
        if not re.search(pat, text):
            ERRORS.append(f"MISSING in {path.relative_to(REPO)}: {pat!r}")


# 1. CITATIONS — 三個法規版本字串
check(
    "CITATIONS",
    REPO / "CITATIONS.md",
    [
        r"114\.05\.13",          # 國外出差旅費報支要點修正日期
        r"1140101390",           # 院授主預字第1140101390號函
        r"1140103430",           # 院授主預字第1140103430號函
    ],
)

# 2. CHANGELOG — [1.0.0] entry 存在
check(
    "CHANGELOG",
    REPO / "CHANGELOG.md",
    [r"\[1\.0\.0\]"],
)

# 3. DISCLAIMER — 四層免責存在（關鍵詞各一）
check(
    "DISCLAIMER",
    REPO / "DISCLAIMER.md",
    [
        r"正確性",       # 第1層：格式僅協助，使用者自負
        r"人工智慧基本法",  # 第2層：AI 基本法
        r"公務",        # 第3層：公務 AI 規範
        r"個人資料保護法", # 第4層：個資法
    ],
)

# 4. README — 版本參照
check(
    "README",
    REPO / "README.md",
    [r"114\.05\.13"],
)

# 結果
if ERRORS:
    for e in ERRORS:
        print(f"FAIL: {e}")
    sys.exit(1)

print("PASS: 版本一致性與必要宣告全部就位")
