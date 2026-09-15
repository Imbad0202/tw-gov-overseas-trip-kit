#!/usr/bin/env python3
"""版本一致性與必要宣告檢查（轉 public 前安全 gate）。

驗項：
1. CITATIONS.md 含三個法規版本字串（114.05.13、1140101390、1140103430）
2. CHANGELOG.md 含 [1.0.0] entry
3. DISCLAIMER.md 含四層免責（正確性、AI 基本法、公務 AI 規範、個資法）
4. README.md 含版本參照（114.05.13）
5. 版本號對齊：SKILL.md frontmatter、pyproject.toml、plugin.json、README / README_EN badge、CHANGELOG 最新 entry
6. README / README_EN 的 **Last Updated** 日期等於 CHANGELOG 最新 entry 日期
7. README / README_EN 有「## What's new in v<當前版本>」段

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

# 5-7. 版本號 / Last Updated / What's new 對齊（發版文件對齊紀律）
def _read(name: str) -> str:
    return (REPO / name).read_text(encoding="utf-8")


def _first(pat: str, text: str, label: str) -> str:
    m = re.search(pat, text, re.M)
    if not m:
        ERRORS.append(f"MISSING {label}: {pat!r}")
        return ""
    return m.group(1)


versions = {
    "SKILL.md": _first(r"^version:\s*([0-9]+\.[0-9]+\.[0-9]+)", _read("SKILL.md"), "SKILL.md version"),
    "pyproject.toml": _first(r'^version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"', _read("pyproject.toml"), "pyproject version"),
    "plugin.json": _first(r'"version":\s*"([0-9]+\.[0-9]+\.[0-9]+)"', _read(".claude-plugin/plugin.json"), "plugin.json version"),
    "README.md badge": _first(r"badge/version-v([0-9]+\.[0-9]+\.[0-9]+)", _read("README.md"), "README badge"),
    "README_EN.md badge": _first(r"badge/version-v([0-9]+\.[0-9]+\.[0-9]+)", _read("README_EN.md"), "README_EN badge"),
    "CHANGELOG.md": _first(r"^## \[([0-9]+\.[0-9]+\.[0-9]+)\]", _read("CHANGELOG.md"), "CHANGELOG entry"),
}
if len(set(versions.values())) > 1:
    ERRORS.append("VERSION MISMATCH: " + ", ".join(f"{k}={v or '?'}" for k, v in versions.items()))
current = versions["pyproject.toml"]

changelog_date = _first(r"^## \[[0-9.]+\] — ([0-9]{4}-[0-9]{2}-[0-9]{2})", _read("CHANGELOG.md"), "CHANGELOG date")
for name in ("README.md", "README_EN.md"):
    text = _read(name)
    updated = _first(r"\*\*Last Updated\*\*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text, f"{name} Last Updated")
    if updated and changelog_date and updated != changelog_date:
        ERRORS.append(f"DATE MISMATCH: {name} Last Updated {updated} != CHANGELOG {changelog_date}")
    if current and not re.search(rf"^## What's new in v{re.escape(current)}\s*$", text, re.M):
        ERRORS.append(f"MISSING in {name}: '## What's new in v{current}'")

# 結果
if ERRORS:
    for e in ERRORS:
        print(f"FAIL: {e}")
    sys.exit(1)

print("PASS: 版本一致性與必要宣告全部就位")
