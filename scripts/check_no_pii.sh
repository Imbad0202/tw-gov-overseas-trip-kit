#!/usr/bin/env bash
# Layer A：機構通用字眼掃描（轉 public 前安全 gate）
#
# 掃描範圍：git 追蹤的 *.py *.md *.json *.html *.sh 檔案（含 tests/ 與 scripts/）。
# 使用 git ls-files 自動排除 .gitignore 中的路徑（.superpowers/、data/ 等）。
#
# 逐行排除合法模式（排除的是「行」，不是「整個目錄」）：
#   - 含 'not in'      → 測試斷言（assert "HEEACT" not in ...），合法
#   - 含 '零 HEEACT'   → render/ docstring 宣告「不含」，合法
#   - 含 '無 HEEACT'   → 同上
#   - 含 '不含 HEEACT' → 同上
#   - 含 'PII'         → 測試 docstring 說明「檢查不含 PII markers (HEEACT ...)」，合法
#   - 含 PATTERN=      → scripts 本身 PATTERN 變數定義行，合法
#
# 個人字眼（人名、機關內部 URL 等）不入此 script，走本機 personal-boundary hook。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PATTERN='HEEACT|高等教育評鑑|財團法人高等教育|高評|評鑑中心|heeact|本會|執行長|處務聯席會議|EIP|教育部上呈|清邁|chiangmai|HERDSA|INQAAHE|AACSB|bali|tokyo|singapore'

# P2-4：session URL / 本機絕對路徑洩漏偵測（public repo 不應含）
SESSION_PATTERN='Claude-Session|claude\.ai/code/session|/Users/|/home/[^/]'

# 取得 git 追蹤的目標副檔名檔案（全目錄，含 tests/ 與 scripts/）
HITS=$(
  git -C "$REPO_ROOT" ls-files \
    '*.py' '*.md' '*.json' '*.html' '*.sh' \
  | while IFS= read -r rel; do
      file="$REPO_ROOT/$rel"
      grep -In -E "$PATTERN" "$file" \
        | grep -vE 'not in' \
        | grep -v '零 HEEACT' \
        | grep -v '無 HEEACT' \
        | grep -v '不含 HEEACT' \
        | grep -v 'PII' \
        | grep -v 'PATTERN=' \
        | sed "s|^|$rel:|" \
      || true
    done
)

if [ -n "$HITS" ]; then
  echo "FAIL: 命中機構字眼（追蹤檔）"
  echo "$HITS"
  exit 1
fi

# 盲區補強 1：未追蹤檔（如誤落 repo 的開發報告）也要掃——git ls-files 看不到
UNTRACKED=$(
  git -C "$REPO_ROOT" ls-files --others --exclude-standard \
    '*.py' '*.md' '*.json' '*.html' '*.sh' \
  | while IFS= read -r rel; do
      grep -In -E "$PATTERN" "$REPO_ROOT/$rel" \
        | grep -vE 'not in' | grep -v '零 HEEACT' | grep -v '無 HEEACT' \
        | grep -v '不含 HEEACT' | grep -v 'PII' | grep -v 'PATTERN=' \
        | sed "s|^|$rel:|" || true
    done
)
if [ -n "$UNTRACKED" ]; then
  echo "FAIL: 命中機構字眼（未追蹤檔——勿提交，或移出 repo）"
  echo "$UNTRACKED"
  exit 1
fi

# 盲區補強 2：commit message 歷史（刪檔不刪歷史；commit msg 本身會洩漏）
MSG_HITS=$(git -C "$REPO_ROOT" log --all --format='%H %s%n%b' \
  | grep -InE "$PATTERN" | grep -v 'PATTERN=' || true)
if [ -n "$MSG_HITS" ]; then
  echo "FAIL: commit message 含機構字眼（需 rewrite 歷史）"
  echo "$MSG_HITS"
  exit 1
fi

# P2-4：session URL / 本機絕對路徑洩漏（追蹤檔）
SESSION_HITS=$(
  git -C "$REPO_ROOT" ls-files \
    '*.py' '*.md' '*.json' '*.html' '*.sh' \
  | while IFS= read -r rel; do
      grep -In -E "$SESSION_PATTERN" "$REPO_ROOT/$rel" \
        | grep -v 'SESSION_PATTERN=' \
        | sed "s|^|$rel:|" \
      || true
    done
)
if [ -n "$SESSION_HITS" ]; then
  echo "FAIL: 命中 session URL 或本機絕對路徑（追蹤檔）"
  echo "$SESSION_HITS"
  exit 1
fi

# P2-4：session URL / 本機絕對路徑洩漏（commit message 歷史）
SESSION_MSG_HITS=$(git -C "$REPO_ROOT" log --all --format='%H %s%n%b' \
  | grep -InE "$SESSION_PATTERN" | grep -v 'SESSION_PATTERN=' || true)
if [ -n "$SESSION_MSG_HITS" ]; then
  echo "FAIL: commit message 含 session URL 或本機絕對路徑（需 rewrite 歷史）"
  echo "$SESSION_MSG_HITS"
  exit 1
fi

echo "PASS: 無機構字眼 + 無 session URL / 本機路徑（追蹤檔 + 未追蹤檔 + commit message 歷史皆掃）"
