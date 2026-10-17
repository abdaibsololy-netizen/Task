#!/usr/bin/env bash
# =====================================================================
#  run_audit.sh — فحص أمني شامل لنظامك المنشور + مراجعة الكود
# =====================================================================
#  الاستخدام:
#     ./security/run_audit.sh https://example.com
#     ./security/run_audit.sh https://example.com --quick
#     ./security/run_audit.sh https://example.com --skip-probe
# =====================================================================
set -uo pipefail

TARGET="${1:-}"
QUICK=0
SKIP_PROBE=0
SKIP_CODE=0
for a in "$@"; do
  case "$a" in
    --quick) QUICK=1 ;;
    --skip-probe) SKIP_PROBE=1 ;;
    --skip-code) SKIP_CODE=1 ;;
  esac
done

if [ -z "$TARGET" ]; then
  echo "❌ الاستخدام: ./security/run_audit.sh <رابط-الموقع> [--quick] [--skip-probe] [--skip-code]"
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/security/findings"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="python3"
mkdir -p "$OUT"

echo "════════════════════════════════════════════════════"
echo " 🔐 فحص أمني — $TARGET"
echo " $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "════════════════════════════════════════════════════"

# ── 1) الأسرار المسرّبة في المستودع ─────────────────────────────
echo -e "\n[1/5] 🔑 مسح الأسرار في المستودع (ملفات + تاريخ git) …"
"$PY" "$ROOT/security/secrets_scan.py" --path "$ROOT" --out "$OUT" 2>&1 | tail -25

# ── 2) مراجعة ساكنة لكود البوت ───────────────────────────────────
if [ "$SKIP_CODE" -eq 0 ]; then
  echo -e "\n[2/5] 🧩 تحليل ساكن للكود (bandit) …"
  if [ -x "$ROOT/.venv/bin/bandit" ]; then
    "$ROOT/.venv/bin/bandit" -r "$ROOT/bot" "$ROOT/data" -x "$ROOT/bot/.venv,$ROOT/.venv,__pycache__" -f screen -ll 2>&1 | tail -40
    "$ROOT/.venv/bin/bandit" -r "$ROOT/bot" "$ROOT/data" -x "$ROOT/bot/.venv,$ROOT/.venv,__pycache__" -f json -o "$OUT/bandit.json" -q 2>/dev/null
    echo "  📄 $OUT/bandit.json"
  else
    echo "  ⚠️  bandit غير مثبّت —: pip install -r security/requirements.txt"
  fi
else
  echo -e "\n[2/5] ⏭️  تخطّي التحليل الساكن"
fi

# ── 3) الفحص العام للموقع ────────────────────────────────────────
echo -e "\n[3/5] 🌐 الفحص العام (TLS/ترويسات/كوكيز/CORS/مسارات/إعادة توجيه …)"
if [ "$QUICK" -eq 1 ]; then
  "$PY" "$ROOT/security/audit.py" "$TARGET" --out "$OUT" --skip-active
else
  "$PY" "$ROOT/security/audit.py" "$TARGET" --out "$OUT"
fi

# ── 4) فحوص الحقن ────────────────────────────────────────────────
if [ "$SKIP_PROBE" -eq 0 ] && [ "$QUICK" -eq 0 ]; then
  echo -e "\n[4/5] 💉 فحوص الحقن (SQLi/XSS/traversal/cmd/SSTI/SSRF/CRLF) …"
  "$PY" "$ROOT/security/probe.py" "$TARGET" --out "$OUT" 2>&1 | tail -30
else
  echo -e "\n[4/5] ⏭️  تخطّي فحوص الحقن"
fi

# ── 5) الأسرار داخل الموقع المنشور ───────────────────────────────
echo -e "\n[5/5] 🔍 أسرار مسرّبة داخل الموقع المنشور (HTML + JS) …"
"$PY" "$ROOT/security/secrets_scan.py" --url "$TARGET" --out "$OUT" 2>&1 | tail -20

echo -e "\n════════════════════════════════════════════════════"
echo " ✅ انتهى الفحص — التقارير في: $OUT"
ls -1t "$OUT" | head -10
echo "════════════════════════════════════════════════════"
