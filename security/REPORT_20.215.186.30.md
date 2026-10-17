# 🔐 تقرير فحص أمني — Smart SOC Platform
**الهدف:** `http://20.215.186.30` · **التاريخ:** 2026-10-17 · **النطاق:** فحص آلي + تحليل يدوي
**الأدوات:** `security/` (audit · probe · recon_app · verify_findings · secrets_scan) · **عدد الفحوص:** ~6,400 طلب

---

## 1) الملخص التنفيذي

منصة **Smart SOC Platform** (nginx 1.31.7 + FastAPI + Vue/React SPA) — **نقاط القراءة الحسّاسة
مفتوحة تماماً بلا أي مصادقة**.

أخطر نتيجة: `GET /api/alerts/{id}` يرجع **كائن التنبيه كاملاً** بلا توكن — بما فيه
`hostname` (أسماء أجهزة الإنتاج)، `source_ip` / `destination_ip` / `destination_domain`،
`command_line` (سطر أوامر Powershell الكامل)، `file_hash` / `file_hash_md5`،
`certificate_fingerprint`، `dns_query`، `ai_recommendations`، `analyst_verdict`،
وحقول `threat_intel`. تم التحقق: **25/25 تنبيهاً قُرئت بلا مصادقة**.

هذه ليست "بيانات تجريبية" — هذه **قائمة مؤشرات اختراق (IOC) كاملة** لمنشأتك: كل اسم جهاز،
كل IP داخلي، كل hash ملف، كل سطر أوامر. مهاجم يقرأها يجد مباشرة أين يهاجم.

ثغرة جذرية واحدة تفسّرها: **الواجهة الأمامية ترسل `Authorization: Bearer …` لكن الخادم
لا يفرض التحقق على مسارات القراءة** (الاعتماد موجود في JS فقط، لا في طبقة الـ API).

**خطأ التصميم الذي فسّر النتائج** (من وصف المشروع نفسه):
> "Read/triage/investigate endpoints stay open so dashboards and analysts keep working without friction"

النية حسنة لكن الأثر عكسي تماماً: لوحات المعلومات تعمل بلا تأخير — لكن **أي شخص على الإنترنت**
يقرأ بياناتك بنفس الشكل.

| الخطورة | العدد |
|---|---|
| 🔴 Critical | 2 |
| 🟠 High | 3 |
| 🟡 Medium | 4 |
| 🟢 Low | 2 |

---

## 2) النتائج المؤكدة (بأدلة)

### 🔴 CRITICAL-01 — قراءة كل التنبيهات وبيانات الأدلة بلا مصادقة
**Broken Access Control — CWE-285 / CWE-639**

| النقطة | الحالة | الدليل |
|---|---|---|
| `GET /api/alerts/{alert_id}` | **200** بلا توكن | 25/25 تنبيهاً قُرئ |
| `GET /api/alerts/{alert_id}/evidence` | **200** بلا توكن | raw_event + full_log + normalized_event |
| `GET /api/alerts/{alert_id}/investigation-status/{task_id}` | **200** | حالة مهام التحقيق |

**الحقول المسرّبة (من كائن التنبيه الحقيقي):**
```
alert_name, severity, category, hostname (WIN-SERVER-2022), source_ip, destination_ip,
destination_port, destination_domain, command_line, file_name, file_hash, file_hash_md5,
certificate_fingerprint, is_signed, dns_query, granted_access, image_loaded,
ai_summary, ai_recommendations, analyst_verdict, analyst_reviewed_by, composite_risk_score,
domain_threat_intel, file_threat_intel, investigation_status, investigation_last_error …
```

**الأثر**
- تسريب كامل لبنية شبكتك الداخلية وأسماء أجهزتك.
- تسريب hashes الملفات → enables malicious-file lookup / living-off-the-land.
- تسريب `command_line` → تسريب أدوات و TTPs المستخدمة داخلياً.
- تسريب `analyst_reviewed_by` → تسمية مُشغّلي SOC (تسهيل دراسات موجّهة).
- `investigation_last_error` قد يحتوي آثاراً داخلية (tracebacks) — تسريب بنية النظام.

**الإصلاح**
```python
# app/api/alerts.py
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/api/alerts", tags=["alerts"], dependencies=[Depends(get_current_user)])

@router.get("/{alert_id}")
def get_alert(alert_id: int, user = Depends(get_current_user)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "not found")
    return alert            # بعد فرض المصادقة
```
> **مهم:** إن أردت إبقاء لوحات المعلومات تعمل بلا دخول، استخدم **قراءة-عامة محدّدة الحقول**
> (projection: id, severity, category, created_at) بدل إرجاع الكائن كاملاً. لا تعطِ
> `hostname / IP / command_line / file_hash` لقارئ غير موثوق.

**تحقّق بعد الإصلاح**
```bash
curl -i http://20.215.186.30/api/alerts/1     # المتوقع: 401 {"error":"Could not validate credentials"}
```

---

### 🔴 CRITICAL-02 — حقن تنبيهات مزوّرة (Ingest/Webhook بلا مصادقة)
**CWE-306 Missing Authentication for Critical Function**

| النقطة | الدليل | الحالة |
|---|---|---|
| `POST /api/alerts/ingest` | `422` (وصلت لمرحلة التحقق من الجسم — أي أنها **لا تطلب مصادقة**) | مفتوح |
| `POST /api/alerts/webhook` | `422` | مفتوح |

مواصفة المشروع نفسها تصف `/api/alerts/webhook` بأنه "intentionally THIN": يحفظ التنبيه الخام
**ويُدرج مهمة Celery** لمعالجة threat-intel/MITRE/UEBA/AI.

**الأثر**
- ⇒ أي شخص يستطيع إدخال تنبيهات مزوّرة ⇒ تلويث إحصاءات SOC، إغراق المحلّل،
  poisoning لخلاصة الـ AI والـ `composite_risk_score` (محتوى الـ AI مبني على التنبيهات).
- ⇒ كل تنبيه مزوّر يُطلق مهمة Celery تستهلك VirusTotal / AbuseIPDB / OTX
  (استنزاف حصة الـ API) ⇒ تكلفة + ضغط على الخادم.
- ⇒ تلاعب بالأدلة: تنبيه حقيقي وحيد ناقص/مُعدّل = إتلاف أدلة جنائية.

**الإصلاح**
```python
# 1) سر مشترك للـ webhook
WEBHOOK_SECRET = os.environ["WAZUH_WEBHOOK_SECRET"]

@router.post("/webhook", dependencies=[Depends(verify_webhook_secret)])
def wazuh_webhook(payload: WazuhWebhookRequest, request: Request):
    supplied = request.headers.get("X-Webhook-Secret", "")
    if not hmac.compare_digest(supplied, WEBHOOK_SECRET):
        raise HTTPException(401, "invalid webhook secret")
    ...
# 2) للأمان: allowlist لعنوان Wazuh manager على مستوى الشبكة (nginx)
```
```nginx
location /api/alerts/webhook {
    allow 10.0.0.0/8;      # شبكة Wazuh فقط
    deny  all;
    proxy_pass http://127.0.0.1:8000;
}
```

---

### 🟠 HIGH-01 — إحصاءات وتغطية MITRE ATT&CK مكشوفة
| النقطة | الدليل |
|---|---|
| `GET /api/alerts/stats/summary` | `{"total_alerts":3614,"severity_breakdown":{"critical":79,"high":1279,"medium":131,"low":2038,"info":87},…}` |
| `GET /api/alerts/mitre/navigator-layer` | طبقة MITRE كاملة: `{"domain":"enterprise-attack","versions":{"navigator":"4.9.1","layer":"4.5"},"techniques":[…]}` |

**الأثر**
- `stats/summary` → خريطة حجم الخطر: كم تنبيه حرج لديك، وكم "عالي" — يكشف للمهاجم
  **التصنيفات التي يهمّها** (e.g., "79 تنبيهاً حرجاً").
- `navigator-layer` → **خريطة التغطية الأمنية الكاملة**: أي تقنية ATT&CK ترصدها وأيّها لا ترصدها.
  المهاجم يقرأها ليختار المسار **غير المرصود** بالضبط. هذه ثغرة معلوماتية من الدرجة الأولى في
  منصة SOC.

**الإصلاح:** ضعهما خلف `require_roles(["analyst","admin"])` (أو على الأقل JWT صالح).

---

### 🟠 HIGH-02 — لا يوجد HTTPS إطلاقاً
**CWE-319 Cleartext Transmission of Sensitive Information**

- `https://20.215.186.30:443` → `ConnectTimeout` (لا يستمع).
- كل شيء على HTTP: **كلمات المرور، توكنات JWT، API keys، وبيانات التنبيهات** تمر عبر الشبكة نصّاً صريحاً.

**الأثر:** أي ISP / Wi‑Fi مقاهي / جهة وسط على الطريق يقرأ كل شيء ويعترض التوكنات ⇒ اختراق كامل.
**الإصلاح**
```bash
certbot --nginx -d your-domain.com
```
```nginx
server {
    listen 80;  server_name your-domain.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;  server_name your-domain.com;
    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    ...
}
```

---

### 🟠 HIGH-03 — Trigger بلا مصادقة لخط معالجة AI/threat-intel (تحقّق يدوي مطلوب)
`POST /api/alerts/{alert_id}/investigate` — **بلا `security` في المواصفة**، والوصف يشرح أنها
تطلق: VirusTotal + AbuseIPDB + AlienVault OTX + MITRE + UEBA + **AI**.

> ⚠️ **لم أضغط هذا المسار** (التزاماً بطلبك "لا تخرّب"). التحقق يحتاج حساباً.
> **كيف تتحقّق بنفسك (30 ثانية):**
> ```bash
> curl -i -X POST "http://20.215.186.30/api/alerts/1/investigate"
> # إن رجعت 200/202 بلا 401 → الغياب مؤكّد
> ```
> **الأثر المتوقع:** استنزاف حصة VirusTotal/OTX، إغواء طابور Celery، وتكلفة AI لكل طلب.

**الإصلاح:** `Depends(get_current_user)` + `require_roles(["analyst","admin"])` + rate limit على المسار.

---

### 🟡 MEDIUM-01 — خريطة الـ API كاملة منشورة (OpenAPI + Swagger + ReDoc)
| المسار | الحجم |
|---|---|
| `GET /api/openapi.json` | 163 KB · **123 مساراً** مع كل المخططات والبارامترات |
| `GET /api/docs` | Swagger UI (الواجهة نفسها في React تحجبه بـ `minRole:"admin"` — لكن الخادم ينشره) |
| `GET /api/redoc` | ReDoc |

**الأثر:** مهاجم يحصل على **قائمة كاملة بكل نقطة نهاية وكل مخطط طلب** — لا يحتاج تخميناً.
**الإصلاح (في الإنتاج):**
```python
app = FastAPI(
    openapi_url=None,      # أو محمي
    docs_url=None,
    redoc_url=None,
)
# أو: اربطه بـ Basic-auth / allowlist
```
> ملاحظة: ربط `/api/docs` بـ `minRole` في الواجهة **ليس** حماية — الحماية على الخادم.

---

### 🟡 MEDIUM-02 — كشف حالة النظام الداخلية
| المسار | ما يسرّبه |
|---|---|
| `GET /health/deep` | `status`, `database`, `schema` (+ `missing_tables`, `missing_columns`), `rules.loaded_rules: 38`, `redis`, `broker`, **`cors_origins_count: 9`** |
| `GET /readyz` | `redis_cache`, `broker`, `schema` |
| `GET /livez` | `status` |

**الأثر:** خريطة الاعتماديات + عدد قواعد الكشف + عدد نطاقات CORS ⇒ تسهيل شن حملات موجّهة.
**الإصلاح:** `/health` 공개 فقط لـ `{status}`؛ و`/health/deep` محصور (شبكة داخلية أو توكن خدمة).

---

### 🟡 MEDIUM-03 — ترويسات أمان ناقصة
| الترويسة | الحالة | الأثر |
|---|---|---|
| `Content-Security-Policy` | ❌ مفقودة | لا حماية ضد XSS (و `unsafe-inline` غير مُقيّد) |
| `Strict-Transport-Security` | ❌ مفقودة | (يتبع غياب HTTPS) |
| `Referrer-Policy` | ❌ مفقودة | تسريب مسار كامل في الـ Referer |
| `Permissions-Policy` | ❌ مفقودة | |
| `Server: nginx/1.31.7` | ⚠️ يكشف الإصدار | استهداف ثغرة nginx معروفة |
| `X-Frame-Options: SAMEORIGIN` | ✅ موجود | |
| `X-Content-Type-Options: nosniff` | ✅ موجود | |

**الإصلاح (nginx):**
```nginx
server_tokens off;                                  # أخفِ إصدار nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self'" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
```

---

### 🟡 MEDIUM-04 — لا تحديد معدل على الـ API (خارج تسجيل الدخول)
8 طلبات متتالية على `/` كلها `200` بلا `429`. تسجيل الدخول **محمى** (10 محاولات ⇒ `429` ✅)
لكن بقية المسارات (اقرأ فقط) بلا حدّ ⇒ **استنزاف حصة AI/threat-intel** عبر
`/api/alerts/{id}/investigate` المتكرر (انظر HIGH-03).

**الإصلاح:** `slowapi` / `nginx limit_req` على مسارات المعالجة الثقيلة تحديداً.

---

### 🟢 LOW-01 — الإصدار والتعريفات مكشوفة
`Server: nginx/1.31.7` → `server_tokens off;`

### 🟢 LOW-02 — رابط التوثيق ظاهر في القوائم
`/api/docs` + `/api/redoc` + `/api/openapi.json` — مغطى في MEDIUM-01.

---

## 3) ما تم فحصه ولم يجد ثغرة ✅

| الفحص | النتيجة |
|---|---|
| **حقن SQL** (خطأ/منطقي/زمني) على 168 نقطة إدخال | ❌ لا شيء — **0 من 5,040 probe** |
| **XSS معكوس** (script/onerror/svg) | ❌ لا شيء |
| **Path Traversal / Command Injection / SSTI / SSRF / CRLF** | ❌ لا شيء |
| **CORS** | ✅ لا يعكس Origin غريب — `ACAO` فارغ مع `Origin: https://evil.example` (القائمة 9 نطاقات مسموحة فقط) |
| **حذف/تعديل التنبيهات** | ✅ محمي — `DELETE` → `401` ، `PUT` → `401/404` (تحقّق بمعرّف غير موجود، بلا إيذاء بيانات) |
| **تسجيل الدخول** | ✅ rate limiting فعّال (10 ⇒ `429` "Too many attempts. Try again in 55 seconds") |
| **كشف المستخدم** | ✅ رسالة موحّدة "Incorrect username or password" |
| **رسائل الأخطاء** | ✅ بلا tracebacks ولا آثار FastAPI/SQLAlchemy |
| **أسرار داخل حزمة JS** (1.09 MB) | ❌ لا مفاتيح ولا JWT ولا private keys ولا كلمات مرور |
| **نقاط API المحمية** (auth, users, api-keys, MFA, detection-rules, analytics) | ✅ كلها `401` |
| **تسريب أسرار في المستودع** | ❌ لا شيء (لا في الملفات ولا في تاريخ git) |

---

## 4) لم يُنفَّذ عمداً (التزاماً بـ "لا تخرّب" + needing credentials)

1. **تسجيل دخول حقيقي** → فحص JWT (خوارزمية `alg`, عمر التوكن, تخزين المفتاح) — يحتاج حساب اختبار.
2. **`POST /api/alerts/ingest` / `/webhook` ببيانات صالحة** → كان سيُنشئ تنبيهات وهمية عندك.
3. **`POST /api/alerts/{id}/investigate`** → كان سيستهلك حصة VirusTotal/OTX ويشغّل AI.
4. **`POST /api/auth/register`** → كان سيُنشئ مستخدماً (المسار موصوف admin-only؛ تحقّقت أنه بلا حماية في المواصفة فقط).
5. **تعديل تنبيه حقيقي** — استُخدم معرّف غير موجود `999999999` فقط.

---

## 5) خطة المعالجة (بالأولوية)

| # | الإجراء | effort | أثر |
|---|---|---|---|
| 1 | **فرض JWT على `GET /api/alerts/{id}` و`/evidence` و`/investigation-status`** | س |Critical |
| 2 | **حماية `stats/summary` و`mitre/navigator-layer`** بـ role | ص | High |
| 3 | **سر مشترك + allowlist لـ `ingest` و`webhook`** | ص | Critical |
| 4 | **تفعيل HTTPS + HSTS** (certbot) | ص | High |
| 5 | **`investigate` خلف مصادقة + rate limit** | ص | High |
| 6 | **إخفاء `/api/openapi.json` و`/api/docs` و`/api/redoc`** في الإنتاج | ص | Medium |
| 7 | **تقييد `/health/deep` و`/readyz`** | ص | Medium |
| 8 | **ترويسات nginx** (CSP, Referrer-Policy, Permissions-Policy, server_tokens off) | ص | Medium |
| 9 | مراجعة قائمة الـ CORS (9 نطاقات) وتقليصها | ص | تحصين |
| 10 | **مفتاح التوقيع في query string** (Bot) + المستودع العام | — | راجع `SECURITY_NOTES.md` |

---

## 6) كيف تُعيد الفحص

```bash
# من جهازك أو من السيرفر (البيئة هنا مقيّدة الشبكة — استخدم Actions أو جهازك)
./security/run_audit.sh http://20.215.186.30
.venv/bin/python security/verify_findings.py http://20.215.186.30
```

أو عبر GitHub Actions (الهدف في `security/scan_target.txt`):
```bash
git commit --allow-empty -m "scan" && git push
git fetch origin scan-results:scan-results --force
```

**نقطة تحكّم:** عدّل `security/scan_target.txt` لتغيير الهدف.
