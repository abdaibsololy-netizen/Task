#!/usr/bin/env bash
# audit.sh — فحص أمني غير تخريبي (non-destructive) لموقع تملكه وتصرّح باختباره.
#
# ما يفعله: بصمة الخادم، الهيدرات الأمنية، الكوكيز، TLS، مسارات مكشوفة شائعة،
# طرق HTTP، تسريب معلومات في الأخطاء، وحدود المعدل — ثم يولّد تقرير Markdown.
#
# ما لا يفعله: لا تنفيذ استغلال، لا تخمين كلمات مرور، لا تعديل بيانات،
# لا استخراج ملفات، ولا حملات حِمل (DoS).
#
# الاستخدام:
#   ./audit.sh --target https://example.com
#   ./audit.sh --target http://20.215.186.30 --out ./audit-out
#   ./audit.sh --target https://example.com --active      # اختبار رصد WAF
#
# --active يرسل حِزمًا "شبيهة بالهجوم" فقط لمعرفة هل نظام الحماية يرصدها،
# وهي بلا استغلال فعلي (بدون استخراج بيانات). لا تستخدمه إلا على نظامك.

set -uo pipefail

BASE=""
OUT="./audit-out"
ACTIVE=0
TIMEOUT=10
UA="OwnerAudit/1.0 (authorized self-test)"

usage() {
  cat <<'EOF'
الاستخدام:
  ./audit.sh --target <URL> [خيارات]

الخيارات:
  --target URL   عنوان الموقع (مثال: https://example.com أو http://1.2.3.4)
  --out DIR      مجلد المخرجات (افتراضي: ./audit-out)
  --active       تشغيل اختبارات الرصد (WAF) الشبيهة بالهجوم — اختيارية
  --timeout N    مهلة كل طلب بالثواني (افتراضي 10)
  -h, --help     هذه المساعدة
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --target) BASE="${2:-}"; shift 2 ;;
    --target=*) BASE="${1#*=}"; shift ;;
    --out) OUT="${2:-}"; shift 2 ;;
    --out=*) OUT="${1#*=}"; shift ;;
    --active) ACTIVE=1; shift ;;
    --timeout) TIMEOUT="${2:-10}"; shift 2 ;;
    --timeout=*) TIMEOUT="${1#*=}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "خيار غير معروف: $1" >&2; usage; exit 2 ;;
  esac
done

if [ -z "$BASE" ]; then
  echo "خطأ: لازم تحدد --target" >&2
  usage
  exit 2
fi

case "$BASE" in
  http://*|https://*) : ;;
  *) BASE="http://$BASE" ;;
esac

# إزالة الشرطة الأخيرة
BASE="${BASE%/}"

mkdir -p "$OUT" || { echo "ما قدرت أنشئ مجلد المخرجات: $OUT" >&2; exit 1; }
TMP="$OUT/.tmp"
mkdir -p "$TMP"
R="$OUT/report.md"
F="$OUT/findings.tsv"
: > "$R"
: > "$F"

HDRF="$TMP/headers.txt"
BODYF="$TMP/body.html"
ERRF="$TMP/curl.err"

# ---------- أدوات مساعدة ----------
say() { printf '%s\n' "$*" >> "$R"; printf '%s\n' "$*"; }

finding() { # severity | title | evidence
  local sev="$1" title="$2" ev="${3:-}"
  printf '%s\t%s\t%s\n' "$sev" "$title" "$ev" >> "$F"
}

hdr() { # اسم الهيدر -> القيمة (آخر استجابة)
  tr -d '\r' < "$HDRF" | grep -i "^$1:" | tail -1 | cut -d: -f2- | sed 's/^ *//'
}

has_hdr() { tr -d '\r' < "$HDRF" | grep -qi "^$1:"; }

request() { # path [curl opts...]
  local path="$1"; shift
  local url="${BASE%/}${path}"
  local meta
  meta=$(curl -sS -m "$TIMEOUT" -A "$UA" "$@" -D "$HDRF" -o "$BODYF" \
          -w '%{http_code}|%{time_total}|%{size_download}' "$url" 2>"$ERRF") || true
  [ -z "$meta" ] && meta="000|0|0"
  STATUS="${meta%%|*}"
  local rest="${meta#*|}"
  RTIME="${rest%%|*}"
  SIZE="${rest##*|}"
  [ -z "$STATUS" ] && STATUS="000"
  CUR_URL="$url"
}

HOSTPORT="${BASE#*://}"; HOSTPORT="${HOSTPORT%%/*}"
HOST="${HOSTPORT%%:*}"
PORT=""
case "$HOSTPORT" in *:*) PORT="${HOSTPORT##*:}" ;; esac
if [ -z "$PORT" ]; then
  case "$BASE" in https://*) PORT=443 ;; *) PORT=80 ;; esac
fi

START_TS=$(date -u '+%Y-%m-%d %H:%M UTC')

say "# تقرير فحص أمني — $BASE"
say ""
say "- **الهدف:** \`$BASE\`"
say "- **الوقت (UTC):** $START_TS"
say "- **نوع الفحص:** غير تخريبي (إعدادات وهيدرات ومسارات شائعة)"
say "- **الوضع النشط (WAF):** $([ "$ACTIVE" -eq 1 ] && echo 'مُفعّل' || echo 'غير مُفعّل')"
say ""
say "> هذا التقرير يساعدك على معرفة ما هو مكشوف **ظاهريًا**، وليس إثباتًا لعدم وجود ثغرات."
say ""

# ---------- 1) الاتصال وإعادة التوجيه ----------
say "## 1) الاتصال وإعادة التوجيه"
say ""
say '| القياس | القيمة |'
say '|---|---|'

request "/"
ROOT_STATUS="$STATUS"; ROOT_TIME="$RTIME"
REDIRECT_TO=$(hdr 'location')
say "| حالة الصفحة الرئيسية | \`$ROOT_STATUS\` |"
say "| زمن الاستجابة | ${ROOT_TIME}s |"
say "| إعادة توجيه | ${REDIRECT_TO:-لا يوجد} |"

# نسخة تتبع التحويلات
request "/" -L --max-redirs 5
FINAL_STATUS="$STATUS"; FINAL_URL=$(curl -sS -m "$TIMEOUT" -A "$UA" -L -o /dev/null -w '%{url_effective}' "${BASE}/" 2>/dev/null)
[ -z "$FINAL_URL" ] && FINAL_URL="$BASE"
say "| الحالة النهائية بعد التحويلات | \`$FINAL_STATUS\` |"
say "| الرابط النهائي | \`${FINAL_URL:-$BASE}\` |"
say ""

if [ "$ROOT_STATUS" = "000" ]; then
  say "**تعذّر الوصول للهدف من بيئة التشغيل هذه.** تأكد أن الموقع شغّال، وأن الجهاز الذي تشغّل منه السكربت يستطيع الوصول إليه (جدار ناري / Azure NSG / Cloudflare)."
  say ""
  finding "BLOCKER" "تعذّر الوصول إلى الموقع" "curl exit error — راجع $ERRF"
  printf '## الخلاصة\n\nلا يمكن إكمال الفحص: تعذّر الاتصال بالهدف.\n' >> "$R"
  echo "تعذّر الاتصال. راجع $R"
  exit 3
fi

# HTTPS redirect
if [ "$PORT" = "80" ] || [ "${BASE%%:*}" = "http" ]; then
  if [ -n "$REDIRECT_TO" ] && printf '%s' "$REDIRECT_TO" | grep -qi '^https://'; then
    say "- ✅ HTTP يعيد التوجيه إلى HTTPS."
  else
    say "- ⚠️ **لا يوجد تحويل إلى HTTPS** (أو الهدف يعمل على HTTP فقط). أي كلمة مرور أو توكن يمر غير مشفّر."
    finding "MEDIUM" "لا يوجد تحويل إجباري من HTTP إلى HTTPS" "location=${REDIRECT_TO:-<none>}"
  fi
  say ""
fi

# ---------- 2) الهيدرات الأمنية ----------
say "## 2) الهيدرات الأمنية"
say ""
say '| الهيدر | الحالة | القيمة |'
say '|---|---|---|'

check_hdr() { # name | severity | وصف
  local name="$1" sev="$2" desc="$3"
  if has_hdr "$name"; then
    local v; v=$(hdr "$name")
    say "| \`$name\` | ✅ موجود | \`${v:0:110}\` |"
  else
    say "| \`$name\` | ❌ ناقص | $desc |"
    finding "$sev" "هيدر ناقص: $name" "$desc"
  fi
}

check_hdr "strict-transport-security" "MEDIUM" "يمنع الرجوع لـHTTP ويهدّد MITM"
check_hdr "content-security-policy" "MEDIUM" "يقلّل XSS وحقن السكربتات"
check_hdr "x-content-type-options" "LOW" "يمنع MIME sniffing"
check_hdr "x-frame-options" "LOW" "يمنع Clickjacking (أو استخدم CSP frame-ancestors)"
check_hdr "referrer-policy" "LOW" "يمنع تسريب الروابط الحساسة"
check_hdr "permissions-policy" "LOW" "يقيد صلاحيات المتصفح (كاميرا/موقع...)"
say ""

# كشف التقنيات
SRV=$(hdr 'server'); PWR=$(hdr 'x-powered-by'); ASP=$(hdr 'x-aspnet-version'); RAY=$(hdr 'cf-ray'); VIA=$(hdr 'via')
AZURE=$(hdr 'x-azure-ref'); MSEDGE=$(hdr 'x-msedge-ref')
say "**بصمة الخادم:**"
say ""
say "- \`Server\`: ${SRV:-غير معلن}"
say "- \`X-Powered-By\`: ${PWR:-غير معلن}"
say "- \`X-AspNet-Version\`: ${ASP:-غير معلن}"
say "- Cloudflare: ${RAY:+نعم (رؤوس CF موجودة)}${RAY:-لا يظهر}"
say "- وسيط (Via): ${VIA:-لا يظهر}"
say "- Azure Front Door/Gateway: ${AZURE:+نعم}${AZURE:-لا يظهر}"
say "- Azure Edge (msedge): ${MSEDGE:+نعم}${MSEDGE:-لا يظهر}"
say ""

if [ -n "$SRV" ] || [ -n "$PWR" ] || [ -n "$ASP" ]; then
  say "- ℹ️ كشف الإصدارات يسهّل على المهاجم اختيار ثغرة معروفة؛ يُفضّل إخفاؤها/توحيدها."
  finding "LOW" "كشف تقنية/إصدار الخادم" "Server=${SRV:-} X-Powered-By=${PWR:-} X-AspNet-Version=${ASP:-}"
fi
say ""

# ---------- 3) الكوكيز ----------
say "## 3) الكوكيز (Set-Cookie)"
say ""
COOKIES=$(tr -d '\r' < "$HDRF" | grep -i '^set-cookie:' || true)
if [ -z "$COOKIES" ]; then
  say "لا توجد كوكيز مثبتة على الصفحة الرئيسية (طبيعي إذا لم تكن مسجّلًا للدخول)."
  say ""
  say "> للتحقق الكامل: سجّل الدخول من متصفحك، ثم افتح DevTools ← Application ← Cookies وافحص الأعلام."
  say ""
else
  say '```'
  printf '%s\n' "$COOKIES" >> "$R"; printf '%s\n' "$COOKIES"
  say '```'
  say ""
  while IFS= read -r c; do
    [ -z "$c" ] && continue
    name=$(printf '%s' "$c" | sed 's/^[Ss]et-[Cc]ookie: *//' | cut -d= -f1)
    case "$c" in *[Ss]ecure*) : ;; *) finding "MEDIUM" "كوكي بدون Secure: $name" "$c" ;; esac
    case "$c" in *[Hh]ttp[Oo]nly*) : ;; *) finding "MEDIUM" "كوكي بدون HttpOnly: $name" "$c" ;; esac
    case "$c" in *[Ss]ame[Ss]ite*) : ;; *) finding "LOW" "كوكي بدون SameSite: $name" "$c" ;; esac
  done <<< "$COOKIES"
  say "المطلوب: \`Secure\` + \`HttpOnly\` + \`SameSite=Lax/Strict\` لكل كوكي جلسة."
  say ""
fi

# ---------- 4) TLS ----------
say "## 4) شهادة TLS وإصدارات البروتوكول"
say ""
if command -v openssl >/dev/null 2>&1; then
  if timeout 8 bash -c "</dev/tcp/$HOST/443" 2>/dev/null; then
    CERT=$(echo | timeout 12 openssl s_client -connect "$HOST:443" -servername "$HOST" 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName 2>/dev/null)
    if [ -n "$CERT" ]; then
      say '```'
      printf '%s\n' "$CERT" >> "$R"; printf '%s\n' "$CERT"
      say '```'
      say ""
      NOTAFTER=$(printf '%s\n' "$CERT" | awk -F= '/notAfter/{print $2}')
      if [ -n "$NOTAFTER" ]; then
        EXP_EPOCH=$(date -d "$NOTAFTER" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        if [ "$EXP_EPOCH" -gt 0 ]; then
          DAYS=$(( (EXP_EPOCH - NOW_EPOCH) / 86400 ))
          if [ "$DAYS" -lt 0 ]; then
            say "- ❌ الشهادة **منتهية** منذ $((DAYS * -1)) يوم."
            finding "HIGH" "شهادة TLS منتهية" "notAfter=$NOTAFTER"
          elif [ "$DAYS" -lt 30 ]; then
            say "- ⚠️ الشهادة تنتهي خلال **$DAYS يوم**."
            finding "MEDIUM" "شهادة TLS تنتهي قريبًا" "notAfter=$NOTAFTER"
          else
            say "- ✅ الشهادة صالحة (تنتهي بعد $DAYS يوم)."
          fi
        fi
      fi
    else
      say "- تعذّر قراءة الشهادة (قد يكون 443 مغلقًا أو الهدف IP بدون SNI)."
    fi

    # إصدارات قديمة
    for v in tls1 tls1_1; do
      if echo | timeout 8 openssl s_client -connect "$HOST:443" -servername "$HOST" "-$v" >/dev/null 2>&1; then
        say "- ❌ البروتوكول \`$v\` **مفعّل** — إصدار قديم وضعيف."
        finding "HIGH" "بروتوكول TLS قديم مفعّل: $v" ""
      else
        say "- ✅ \`$v\` معطّل."
      fi
    done
  else
    say "- منفذ 443 غير مفتوح/غير متاح من هنا — لا يوجد فحص TLS."
    say ""
  fi
else
  say "- \`openssl\` غير مثبت — تم تخطي فحص TLS."
  say ""
fi

# ---------- 5) المسارات الحساسة ----------
say "## 5) مسارات حسّاسة شائعة"
say ""
say '| المسار | الحالة | الحجم | ملاحظة |'
say '|---|---|---|---|'

check_path() { # path | severity-if-present | ملاحظة
  local p="$1" sev="$2" note="$3"
  request "$p"
  local st="$STATUS" sz="$SIZE" flag=""
  case "$st" in
    200)
      flag="⚠️ متاح"
      if [ "$p" = "/.git/HEAD" ] && grep -q '^ref:' "$BODYF" 2>/dev/null; then
        flag="❌ مستودع Git مكشوف"
        finding "CRITICAL" "مستودع Git مكشوف" "$p يعرض مراجع git"
      elif [ "$p" = "/.env" ] && grep -qiE '^[A-Z_]+=' "$BODYF" 2>/dev/null; then
        flag="❌ ملف بيئة مكشوف"
        finding "CRITICAL" "ملف .env مكشوف" "$p يحتوي متغيرات بيئة"
      else
        finding "$sev" "مسار حسّاس يرجع 200: $p" "$note"
      fi
      ;;
    401|403)
      flag="🔒 محمي ($st)"
      case "$sev" in
        CRITICAL|HIGH) finding "MEDIUM" "مسار حسّاس موجود لكنه محمي: $p" "HTTP $st — تأكد أن الحماية على مستوى الخادم لا تعتمد على إخفاء المسار" ;;
      esac
      ;;
    301|302|307|308) flag="↪ تحويل ($st)" ;;
    404) flag="غير موجود" ;;
    000) flag="تعذّر" ;;
    *) flag="($st)" ;;
  esac
  say "| \`$p\` | \`$st\` | ${sz}B | $flag |"
}

check_path "/.git/HEAD" "CRITICAL" "كود المصدر وتاريخه"
check_path "/.env" "CRITICAL" "مفاتيح وقواعد بيانات"
check_path "/.env.local" "CRITICAL" "مفاتيح"
check_path "/.svn/wc.db" "HIGH" "مستودع SVN مكشوف"
check_path "/.DS_Store" "LOW" "كشف أسماء ملفات"
check_path "/backup.zip" "HIGH" "نسخة احتياطية"
check_path "/db.sql" "HIGH" "قاعدة بيانات"
check_path "/phpinfo.php" "HIGH" "تسريب إعدادات PHP"
check_path "/server-status" "MEDIUM" "حالة Apache"
check_path "/actuator" "HIGH" "Spring Boot endpoints"
check_path "/actuator/env" "HIGH" "متغيرات بيئة Spring"
check_path "/swagger-ui/" "MEDIUM" "توثيق API مكشوف"
check_path "/api-docs" "MEDIUM" "توثيق API مكشوف"
check_path "/graphql" "MEDIUM" "GraphQL — تأكد من تعطيل introspection والتفويض"
check_path "/metrics" "HIGH" "مقاييس Prometheus قد تكشف بنية النظام"
check_path "/admin" "MEDIUM" "لوحة إدارة — تأكد من المصادقة وMFA"
check_path "/login" "LOW" "صفحة دخول — تأكد من rate limit وMFA"
check_path "/robots.txt" "INFO" "قد يكشف مسارات"
check_path "/sitemap.xml" "INFO" "خريطة الموقع"
check_path "/.well-known/security.txt" "INFO" "قناة الإبلاغ عن الثغرات"

say ""
say "> الحالات 401/403 تعني أن المسار موجود لكن محمي — راجع هل الحماية كافية."
say ""

# قائمة مجلدات
request "/"
if grep -qi 'Index of /' "$BODYF" 2>/dev/null; then
  say "- ❌ **Directory listing مفعّل** على الصفحة الرئيسية — كل الملفات قابلة للتصفح."
  finding "MEDIUM" "Directory listing مفعّل" "/"
  say ""
fi

# ---------- 6) طرق HTTP ----------
say "## 6) طرق HTTP"
say ""
request "/" -X OPTIONS
ALLOW=$(hdr 'allow')
say "- \`OPTIONS\` → \`$STATUS\` — Allow: ${ALLOW:-غير معلن}"
if printf '%s' "$ALLOW" | grep -qiE 'TRACE|PUT|DELETE|PATCH'; then
  say "  - ⚠️ طرق غير متوقعة معلنة: $ALLOW — راجع هل هي مطلوبة فعلًا."
  finding "LOW" "طرق HTTP إضافية معلنة" "Allow=$ALLOW"
fi

request "/" -X TRACE
TRACE_STATUS="$STATUS"
if [ "$TRACE_STATUS" = "200" ] && grep -qi 'TRACE /' "$BODYF" 2>/dev/null; then
  say "- ❌ \`TRACE\` **مفعّل** ويعيد صدى الطلب (Cross-Site Tracing)."
  finding "MEDIUM" "TRACE مفعّل" "يعيد صدى الطلب"
else
  say "- ✅ \`TRACE\` غير مفعّل (\`$TRACE_STATUS\`)."
fi
say ""

# ---------- 7) تسريب معلومات في الأخطاء ----------
say "## 7) معالجة الأخطاء"
say ""
NOPE="/this-path-should-not-exist-$$"
request "$NOPE"
say "- طلب مسار غير موجود → \`$STATUS\`"
LEAKS=""
for pat in 'Traceback \(most recent call last\)' 'Traceback' 'SQLSTATE' 'ORA-[0-9]' 'at java\.' 'Microsoft OLE DB' 'Warning:.*on line' 'stack trace' 'Exception in thread' 'DEBUG = True' 'Django Version' 'Whoops'; do
  if grep -qiE "$pat" "$BODYF" 2>/dev/null; then
    case "$pat" in
      *Traceback*) LEAKS="$LEAKS Traceback" ;;
      *) LEAKS="$LEAKS $(printf '%s' "$pat" | sed 's/\\\\//g')" ;;
    esac
  fi
done
LEAKS=$(printf '%s' "$LEAKS" | tr ' ' '\n' | awk 'NF' | sort -u | tr '\n' ' ' | sed 's/ $//')
if [ -n "$LEAKS" ]; then
  say "- ❌ صفحة الخطأ تسرّب تفاصيل تقنية:$LEAKS"
  finding "HIGH" "تسريب معلومات تقنية في صفحة الخطأ" "$LEAKS"
else
  say "- ✅ لا تظهر آثار Stack Trace أو استعلام SQL في صفحة الخطأ."
fi
say ""

# ---------- 8) حدود المعدل ----------
say "## 8) حدود المعدل (Rate limiting)"
say ""
CODES=""
for _ in $(seq 1 20); do
  s=$(curl -sS -m "$TIMEOUT" -A "$UA" -o /dev/null -w '%{http_code}' "${BASE}/" 2>/dev/null || echo 000)
  CODES="$CODES $s"
  sleep 0.15
done
UNIQ=$(printf '%s\n' $CODES | sort | uniq -c | tr '\n' ' ')
say "- 20 طلبًا خلال ~4 ثوانٍ → التوزيع: \`$UNIQ\`"
if printf '%s' "$CODES" | grep -qE '\b429\b'; then
  say "- ✅ يوجد Rate limiting (429)."
elif printf '%s' "$CODES" | grep -qE '\b(403|503)\b'; then
  say "- ✅ يوجد حجب (403/503) بعد سلسلة طلبات."
else
  say "- ⚠️ لا يظهر أي حجب/429. الصفحة الرئيسية قد تكون عامة، لكن تأكد من وجود حد على **/login و/API** تحديدًا."
  finding "INFO" "لا يظهر Rate limiting على الصفحة الرئيسية" "20 طلبًا بلا 429"
fi
say ""
say "> هذا الاختبار على الصفحة الرئيسية فقط. اختبر \`/login\` يدويًا (5–10 محاولات خاطئة) وتأكد من القفل/التأخير."
say ""

# ---------- 9) اختبار الرصد (اختياري) ----------
if [ "$ACTIVE" -eq 1 ]; then
  say "## 9) اختبار رصد WAF/IDS (حِزم شبيهة بالهجوم — بلا استغلال)"
  say ""
  request "/"
  BASE_STATUS="$STATUS"
  say "- خط الأساس بدون حِمل: \`$BASE_STATUS\`"
  say ""
  say '| النوع | الحالة | الاستنتاج |'
  say '|---|---|---|'

  probe() { # label | param-value
    local label="$1" payload="$2"
    # ترميز URL
    local enc=""
    enc=$(printf '%s' "$payload" | python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.stdin.read()))' 2>/dev/null || true)
    if [ -z "$enc" ]; then
      local i c
      for (( i=0; i<${#payload}; i++ )); do
        c="${payload:i:1}"
        case "$c" in
          [a-zA-Z0-9.~_-]) enc+="$c" ;;
          *) enc+=$(printf '%%%02X' "'$c") ;;
        esac
      done
    fi
    request "/?q=${enc}"
    local st="$STATUS"
    local blocked="لا يبدو محجوبًا"
    case "$st" in
      400|403|406|418|429|451|503) blocked="محجوب/مرفوض (\`$st\`)" ;;
    esac
    local reflected=""
    if grep -qF "$payload" "$BODYF" 2>/dev/null; then
      reflected=" — ⚠️ الحِمل يظهر حرفيًا في الرد"
      finding "MEDIUM" "انعكاس حِمل غير مُرمَّز في الرد ($label)" "/?q=..."
    fi
    say "| $label | \`$st\` | $blocked$reflected |"
  }

  probe "SQLi-looking" "1' OR '1'='1"
  probe "XSS-looking" "<script>alert(1)</script>"
  probe "Path traversal-looking" "../../../../etc/passwd"
  probe "SSTI-looking" "{{7*7}}"
  probe "Command-looking" "; id;"
  say ""
  say "> إذا كانت كل الحالات 200 ولا شيء يُحجب: إما لا يوجد WAF/IDS، أو لا يرصد هذه الوسائط، **أو نظامك يرصد فقط ولا يحجب** — وهذا آخر احتمال عادة. راجع سجلات نظامك بالتواريخ أعلاه للتأكد هل سجّل هذه الطلبات."
  say ""
fi

# ---------- الخلاصة ----------
say "## 10) الخلاصة والأولويات"
say ""
if [ -s "$F" ]; then
  say '| الخطورة | العدد |'
  say '|---|---|'
  for sev in CRITICAL HIGH MEDIUM LOW INFO BLOCKER; do
    n=$(cut -f1 "$F" | grep -cx "$sev" || true)
    [ "${n:-0}" -gt 0 ] && say "| $sev | $n |"
  done
  say ""
  say "### أبرز النتائج"
  say ""
  for want in CRITICAL HIGH MEDIUM; do
    while IFS=$'\t' read -r sev title ev; do
      [ "$sev" = "$want" ] || continue
      say "- **[$sev]** $title${ev:+ — \`$ev\`}"
    done < "$F"
  done
  say ""
else
  say "لم تُرصد ملاحظات بارزة في الفحص السطحي. هذا **لا يعني** أن الموقع آمن؛ راجع الاختبارات اليدوية أدناه."
  say ""
fi

say "### ما لم يغطّه هذا الفحص"
say ""
say "- منطق التطبيق (IDOR، تصعيد صلاحيات، منطق الدفع/الرصيد)."
say "- الحقن الحقيقي في نقاط النهاية الفعلية (يحتاج جلسة وطلب مصرّحين ووكيل مثل Burp/ZAP)."
say "- أمن التسجيل/الاستعادة/الرفع، والأسرار داخل الكود أو في مستودع Git."
say "- سلسلة التوريد (نسخ المكتبات)، وإعدادات السحابة (Azure NSG، مفاتيح التخزين)."
say ""
say "### الخطوات التالية المقترحة"
say ""
say "1. أغلق أي مسار ظهر بحالة 200 من القسم 5 (خصوصًا \`.git\` و\`.env\`)."
say "2. أضف الهيدرات الناقصة من القسم 2 عند الوسيط/الخادم."
say "3. فعّل Rate limiting وMFA على \`/login\` ولوحة الإدارة."
say "4. أعد تشغيل هذا الفحص بعد الإصلاحات وقارن النتائج."
say ""
say "---"
say "أُنتج بواسطة \`security-check/audit.sh\` — فحص غير تخريبي على نظام يملكه المستخدم."
say ""
say "الملفات الخام: \`$TMP\` — والملخص في \`$F\`."

echo ""
echo "✅ التقرير: $R"
echo "📋 الملاحظات: $F"
