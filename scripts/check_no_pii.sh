#!/usr/bin/env bash
# 轉 public 前安全 gate：掃描 git 追蹤 / 未追蹤檔 + commit message 歷史。
#
# 掃描範圍：*.py *.md *.json *.html *.sh（含 tests/ 與 scripts/），
# 以 git ls-files 自動排除 .gitignore 路徑。
#
# 兩類 pattern：
#   1. 通用普世洩漏（內建）：session URL、本機絕對路徑——任何 repo 都不該含。
#   2. 機構／個人專屬機敏詞（選用，外部載入）：本工具本身不內建任何特定機關字眼，
#      避免 lint 腳本反而洩漏「在防哪個機構」。維護者若需掃自己的機敏詞，
#      設環境變數 TWGOK_EXTRA_DENYLIST 指向本機檔（每行一個 regex，# 開頭為註解），
#      該檔不應提交進本 repo。格式見 scripts/extra-denylist.example.txt。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 通用普世洩漏：session URL / 本機絕對路徑（public repo 不應含）
SESSION_PATTERN='Claude-Session|claude\.ai/code/session|/Users/|/home/[^/]'

# 選用：外部機敏詞清單（不進 repo）。組成額外 regex；無則留空（grep -E '' 會全中，故需判斷）。
EXTRA_PATTERN=""
if [ -n "${TWGOK_EXTRA_DENYLIST:-}" ] && [ -f "${TWGOK_EXTRA_DENYLIST}" ]; then
  EXTRA_PATTERN=$(grep -vE '^\s*(#|$)' "${TWGOK_EXTRA_DENYLIST}" | paste -sd '|' -)
fi

TARGET_GLOBS=('*.py' '*.md' '*.json' '*.html' '*.sh')

# 對單一 pattern 掃一組檔案，命中即印（含檔名:行號）。pattern 為空則不掃。
scan_files() {
  local pattern="$1"; shift
  local listcmd=("$@")
  [ -z "$pattern" ] && return 0
  git -C "$REPO_ROOT" "${listcmd[@]}" "${TARGET_GLOBS[@]}" \
    | while IFS= read -r rel; do
        grep -In -E "$pattern" "$REPO_ROOT/$rel" \
          | grep -v 'SESSION_PATTERN=' | grep -v 'EXTRA_PATTERN=' \
          | sed "s|^|$rel:|" || true
      done
}

fail_if() {  # $1=hits $2=訊息
  if [ -n "$1" ]; then echo "FAIL: $2"; echo "$1"; exit 1; fi
}

# 1. 通用普世洩漏（追蹤檔）
fail_if "$(scan_files "$SESSION_PATTERN" ls-files)" "命中 session URL 或本機絕對路徑（追蹤檔）"
# 1b. 通用普世洩漏（未追蹤檔——git ls-files 看不到，誤落 repo 的開發報告等）
fail_if "$(scan_files "$SESSION_PATTERN" ls-files --others --exclude-standard)" \
        "命中 session URL 或本機絕對路徑（未追蹤檔——勿提交，或移出 repo）"
# 1c. 通用普世洩漏（commit message 歷史；刪檔不刪歷史）
fail_if "$(git -C "$REPO_ROOT" log --all --format='%H %s%n%b' \
            | grep -InE "$SESSION_PATTERN" | grep -v 'SESSION_PATTERN=' || true)" \
        "commit message 含 session URL 或本機絕對路徑（需 rewrite 歷史）"

# 2. 外部機敏詞（追蹤檔 + 未追蹤檔 + commit message），僅在維護者設了 denylist 時生效
if [ -n "$EXTRA_PATTERN" ]; then
  fail_if "$(scan_files "$EXTRA_PATTERN" ls-files)" "命中機敏詞（追蹤檔，來自 TWGOK_EXTRA_DENYLIST）"
  fail_if "$(scan_files "$EXTRA_PATTERN" ls-files --others --exclude-standard)" \
          "命中機敏詞（未追蹤檔，來自 TWGOK_EXTRA_DENYLIST）"
  fail_if "$(git -C "$REPO_ROOT" log --all --format='%H %s%n%b' \
              | grep -InE "$EXTRA_PATTERN" | grep -v 'EXTRA_PATTERN=' || true)" \
          "commit message 含機敏詞（來自 TWGOK_EXTRA_DENYLIST，需 rewrite 歷史）"
  echo "PASS: 無 session URL / 本機路徑，且無 TWGOK_EXTRA_DENYLIST 機敏詞（追蹤檔 + 未追蹤檔 + commit 歷史）"
else
  echo "PASS: 無 session URL / 本機路徑（追蹤檔 + 未追蹤檔 + commit 歷史）。未設 TWGOK_EXTRA_DENYLIST，略過機敏詞掃描"
fi
