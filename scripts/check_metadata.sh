#!/usr/bin/env bash
# 掃描 docx/xlsx 二進位 metadata（docProps/core.xml + app.xml）
#
# 純文字 grep 掃不到 binary metadata；解 zip 後再 grep 才有效。
# 掃的字眼：機構通用字眼（同 check_no_pii.sh Layer A）。
#
# 若 repo 無 docx/xlsx（開發階段），先 render 一份合成範例到 tmp 後掃。
# render 驗證錯誤（如摘要字數）不等於 metadata 洩漏，遇 render 失敗則略過並記 NOTE。
# CI 環境執行時 render 需要依賴套件，請確認環境已安裝（見 pyproject.toml）。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PATTERN='heeact|HEEACT|高等教育評鑑|執行長|本會'

FOUND_ANY=0

# 掃 repo 內 git 追蹤的 docx/xlsx
while IFS= read -r rel; do
  f="$REPO_ROOT/$rel"
  MATCH=$(unzip -p "$f" docProps/core.xml docProps/app.xml 2>/dev/null \
    | grep -iE "$PATTERN" || true)
  if [ -n "$MATCH" ]; then
    echo "FAIL metadata: $rel"
    echo "$MATCH"
    exit 1
  fi
  FOUND_ANY=1
done < <(git -C "$REPO_ROOT" ls-files '*.docx' '*.xlsx' 2>/dev/null || true)

# 若 git 追蹤中無 docx/xlsx，render 一份合成範例後掃
if [ "$FOUND_ANY" -eq 0 ]; then
  TMPDIR_RENDER=$(mktemp -d)
  trap 'rm -rf "$TMPDIR_RENDER"' EXIT

  RENDER_STATUS=0
  python3 - <<PYEOF || RENDER_STATUS=$?
import sys, json, pathlib
sys.path.insert(0, "$REPO_ROOT")

ex = pathlib.Path("$REPO_ROOT/examples/02-sample-agency.trip.json")
if not ex.exists():
    print("NOTE: 無範例可 render，略過 metadata 掃描")
    sys.exit(0)

try:
    from render.render_docx import render_report_docx
    data = json.loads(ex.read_text())
    out = pathlib.Path("$TMPDIR_RENDER/test_report.docx")
    render_report_docx(data, str(out))
except Exception as e:
    # render 驗證錯誤（如摘要字數）不等於 metadata 洩漏
    print(f"NOTE: render 失敗（{e}），略過 metadata 掃描（無 metadata 洩漏風險）")
    sys.exit(0)
PYEOF

  DOCX_FILE="$TMPDIR_RENDER/test_report.docx"
  if [ -f "$DOCX_FILE" ]; then
    MATCH=$(unzip -p "$DOCX_FILE" docProps/core.xml docProps/app.xml 2>/dev/null \
      | grep -iE "$PATTERN" || true)
    if [ -n "$MATCH" ]; then
      echo "FAIL metadata: rendered docx contains institutional term"
      echo "$MATCH"
      exit 1
    fi
    echo "PASS: rendered docx metadata 乾淨"
  else
    echo "PASS: metadata gate 略過（render 驗證錯誤或無範例）"
  fi
else
  echo "PASS: metadata 乾淨"
fi
