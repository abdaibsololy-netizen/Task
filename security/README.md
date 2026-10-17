# 🔐 حزمة الفحص الأمني — PumpBot

أدوات جاهزة لفحص نظامك المنشور على الإنترنت (نطاقك أنت) و**مراجعة كود البوت** في نفس المستودع.
كل الأدوات **غير هدّامة**: تقرأ، لا تحذف، ولا تعدّل بيانات.

> ⚖️ **النطاق المسموح**: فحص موقعك أو خوادمك أنت فقط. الأداة ترسل طلبات HTTP عادية
> (GET/HEAD) + payloads قراءة فقط. أي استخدام خارج هذا النطاق مخالف.

---

## ⚡ التشغيل السريع

```bash
# 0) تجهيز البيئة (مرة واحدة)
cd /home/user/Task
python3 -m venv .venv
.venv/bin/pip install -r security/requirements.txt

# 1) فحص شامل لنظامك المنشور
./security/run_audit.sh https://your-site.com

# خيارات:
./security/run_audit.sh https://your-site.com --quick        # فحص غير مؤثر فقط (سريع)
./security/run_audit.sh https://your-site.com --skip-probe   # بدون فحوص الحقن
```

المخرجات تُحفظ في `security/findings/` (JSON للآلة + Markdown للتقرير).

---

## 🧰 الأدوات

| الأداة | الوظيفة | الأمر |
|---|---|---|
| `audit.py` | فحص عام: TLS، ترويسات، كوكيز، CORS، مسارات حساسة، رسائل خطأ، TRACE، Host header، Open Redirect، IDOR، تحديد معدل | `python security/audit.py <URL>` |
| `probe.py` | فحوص الحقن: SQLi (خطأ/منطقي/زمني)، XSS، Path Traversal، Command Injection، SSTI، SSRF، CRLF | `python security/probe.py <URL>` |
| `secrets_scan.py` | أسرار مسرّبة: ملفات المستودع + تاريخ git + HTML/JS الموقع | `python security/secrets_scan.py [--url <URL>]` |
| `run_audit.sh` | يشغّل كل ما سبق بالترتيب | `./security/run_audit.sh <URL>` |
| bandit | تحليل ساكن لكود البوت (`bot/`, `data/`) | `.venv/bin/bandit -r bot data` |

### أمثلة

```bash
# فحص عام فقط
.venv/bin/python security/audit.py https://site.com --out security/findings

# فحص حقن على رابط ومعامل محدّد
.venv/bin/python security/probe.py https://site.com \
    --url "https://site.com/search?q=test" --param q --only sqli,xss

# أسرار داخل الموقع المنشور (JS bundles شائعة فيها مفاتيح API)
.venv/bin/python security/secrets_scan.py --url https://site.com

# أسرار داخل المستودع + تاريخ git
.venv/bin/python security/secrets_scan.py --path .
```

---

## 📋 ماذا تغطّي الأدوات؟

### audit.py
| المحور | أمثلة |
|---|---|
| TLS | شهادة منتهية/قاربت الانتهاء، بروتوكول قديم، HTTP متاح بلا تحويل، HSTS، mixed content |
| الترويسات | CSP، X-Frame-Options، X-Content-Type-Options، Referrer-Policy، Permissions-Policy، كشف الإصدار |
| الكوكيز | Secure / HttpOnly / SameSite |
| CORS | `ACAO: *`، انعكاس Origin غريب، `*` مع credentials |
| كشف المعلومات | `.git/HEAD`، `.env`، `actuator/env`، `heapdump`، dumps، `swagger.json`، صفحات خطأ بآثار Django/SQLAlchemy… |
| HTTP | TRACE/PUT/DELETE مسموحة، Host header injection، Open Redirect، تحديد معدل |
| API | مسارات API بلا مصادقة، مؤشر IDOR |

### probe.py
- **SQLi**: خطأ قائم (`'`, `UNION SELECT`) • منطقي (`' OR '1'='1` مقابل `' AND '1'='2`) • زمني (`SLEEP(3)`)
- **XSS**: انعكاس `<script>` / `onerror` / `<svg onload>` بدون تهريب
- **Path Traversal**: `../../etc/passwd`، `..%2f`، `/proc/self/environ`
- **Command Injection**: `;id` ، `|id` ، `$(id)` — قراءة فقط
- **SSTI**: `{{7*7}}` ، `${7*7}` ، `<%= 7*7 %>`
- **SSRF**: `169.254.169.254` (بيانات وصفية سحابية)، `127.0.0.1`، `10.0.0.1`
- **CRLF**: حقن ترويسات

> كل payload يحمل marker فريداً ويُقارَن بالاستجابة الأساسية — لا يوجد استغلال فعلي
> ولا تعديل للبيانات.

### secrets_scan.py
مفاتيح Solana (base58/JSON) • مفاتيح PEM • توكن تيليجرام • AWS • GitHub • Slack • Discord webhook •
Stripe • Google API • Infura/Alchemy • Helius • JWT • إسنادات `api_key/secret/token/password` عامة •
بيانات دخول داخل URL.

---

## 📂 نتائج فحص جاهزة

| التقرير | الهدف | التاريخ |
|---|---|---|
| [`REPORT_20.215.186.30.md`](REPORT_20.215.186.30.md) | Smart SOC Platform — `http://20.215.186.30` | 2026-10-17 |
| [`reports/soc-2026-10-17/`](reports/soc-2026-10-17/) | الملفات الخام (JSON/MD + دليل OpenAPI المكشوف) | 2026-10-17 |

---

## 📝 تقرير النتائج

1. انسخ `security/FINDINGS_TEMPLATE.md` إلى `security/findings/REPORT_<date>.md`
2. لكل ملاحظة: الخطورة، الدليل (طلب/استجابة)، الأثر، خطوات الإصلاح
3. رتّبها: Critical → High → Medium → Low

**قاعدة الخطورة:**

| الخطورة | المعنى |
|---|---|
| Critical | اختراق كامل / تسريب أسرار / تنفيذ أوامر |
| High | استغلال مباشر بلا شروط خاصة (SQLi, XSS, IDOR مفتوح) |
| Medium | يحتاج تفاعل المستخدم أو شرطاً (Open Redirect, CSP مفقود) |
| Low | تقوية وتحصين (معلومات محدودة، ترويسات ناقصة) |

---

## 🔁 بعد الإصلاح

- أعد الفحص: `./security/run_audit.sh <URL>` وقارن `security/findings/`
- لا تنشر التقرير كـ issue عام قبل مراجعة محتواه (قد يحتوي أسراراً)

---

## 🧩 مراجعة كود البوت (`bot/`)

`run_audit.sh` يشغّل أيضاً تحليل bandit على `bot/` و`data/`.
نقاط يجب مراجعتها يدوياً في كود البوت (راجع `SECURITY_NOTES.md`):

- تمرير مفتاح API داخل **query string** (`bot/executor.py`) — يُسجَّل في سجلات الخادم والـ proxies
- مفتاح Helius داخل رابط WebSocket (`bot/copytrade.py`) — نفس الملاحظة
- **المستودع عام** — الكود وبيانات المحفظة واسم حساب التداول كلها مكشوفة
- `bot/portfolio.py` يكتب ملفات الحالة بصلاحيات افتراضية (0644)
